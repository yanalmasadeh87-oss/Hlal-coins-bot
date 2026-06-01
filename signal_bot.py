import requests, time, math, os, json, sys, threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.stdout.reconfigure(line_buffering=True)

# ================================================================
# CONFIG
# ================================================================
TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "7975488031:AAHLdeNTM-YIItriXwradU4bPyCMdR-mAIY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID",   "8422276082")
BN      = "https://api.binance.us/api/v3"
TG      = "https://api.telegram.org/bot" + TOKEN
CG_KEY  = "CG-FPGBHDZ1DTNv1Uj1Uowe4pZ7"
PORT    = int(os.getenv("PORT", 8080))

MIN_SIGNAL_SCORE = 75
SWING_COOLDOWN   = 28800   # 8 hours
SCALP_COOLDOWN   = 14400   # 4 hours

COINS = [
    "BTC","ETH","XRP","SOL","BNB","ADA","AVAX","SUI","HBAR","NEAR",
    "DOT","ICP","FTM","ETC","WLD","RENDER","ATOM","KAS","FIL","APT",
    "ARB","VET","SEI","STX","TIA","GRT","OP","THETA","XLM","ALGO",
    "LTC","TON","LINK","POL","XTZ","BCH","INJ","FET","EGLD","FLOW",
    "GALA","AXS","SAND","MANA","ENJ","CHZ","BAT","LPT","STORJ","BAND",
    "NMR","GLM","CELO","ROSE","ANKR","IMX","OCEAN","AKT","AR","HNT",
    "ONE","ZIL","QTUM","DCR","RVN","WAVES","DGB","AUDIO","CVC","POWR",
    "HOT","ASTR","SKL","CTSI","IOTA",
]

# ================================================================
# STATE — stored as pinned Telegram message
# Bot pins its own state message and reads it back on restart.
# Works on ANY platform, survives ALL restarts and deploys.
# ================================================================
sent = {}          # {key: timestamp} — persists via pinned message
_session_sent = {}  # {key: timestamp} — in-memory only, catches within-scan dupes
_pin_msg_id = None # ID of the pinned state message

def _state_text():
    return "SSYM:" + json.dumps({"s": sent, "t": time.time()})

def save():
    """Update or create the pinned state message."""
    global _pin_msg_id
    text = _state_text()
    try:
        if _pin_msg_id:
            # Edit existing message
            r = requests.post(TG + "/editMessageText",
                json={"chat_id": CHAT_ID, "message_id": _pin_msg_id,
                      "text": text}, timeout=10)
            if r.ok:
                return
        # Send new message and pin it
        r = requests.post(TG + "/sendMessage",
            json={"chat_id": CHAT_ID, "text": text,
                  "disable_notification": True}, timeout=10)
        if r.ok:
            _pin_msg_id = r.json()["result"]["message_id"]
            requests.post(TG + "/pinChatMessage",
                json={"chat_id": CHAT_ID, "message_id": _pin_msg_id,
                      "disable_notification": True}, timeout=10)
    except Exception as e:
        print("  [STATE] Save error:", e)

def load():
    """Read state from pinned message on startup."""
    global sent, _pin_msg_id
    try:
        r = requests.get(TG + "/getChat",
            params={"chat_id": CHAT_ID}, timeout=10)
        if not r.ok:
            print("  [STATE] getChat failed"); return
        pin = r.json().get("result", {}).get("pinned_message", {})
        text = pin.get("text", "")
        if not text.startswith("SSYM:"):
            print("  [STATE] No state pin found — fresh start"); return
        d = json.loads(text[5:])
        age = time.time() - d.get("t", 0)
        if age > 86400:
            print("  [STATE] State too old — fresh start"); return
        _pin_msg_id = pin.get("message_id")
        now = time.time()
        for k, v in d.get("s", {}).items():
            cd = SWING_COOLDOWN if "swing" in k else SCALP_COOLDOWN
            if now - v < cd:
                sent[k] = v
        print(f"  [STATE] Restored {len(sent)} cooldowns (age={round(age/60)}min)")
    except Exception as e:
        print("  [STATE] Load error:", e)

def on_cooldown(key):
    cd = SWING_COOLDOWN if "swing" in key else SCALP_COOLDOWN
    # Check both persistent state AND in-memory session state
    in_persistent = time.time() - sent.get(key, 0) < cd
    in_session    = time.time() - _session_sent.get(key, 0) < cd
    return in_persistent or in_session

def mark_sent(key):
    t = time.time()
    sent[key] = t
    _session_sent[key] = t  # also track in session — survives any state failure
    save()

# ================================================================
# TELEGRAM
# ================================================================
def tg(text):
    try:
        requests.post(TG + "/sendMessage",
            json={"chat_id": CHAT_ID, "text": text,
                  "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=10)
    except Exception as e:
        print("TG error:", e)

# ================================================================
# DATA
# ================================================================
def klines(sym, interval, limit):
    try:
        r = requests.get(BN + "/klines",
            params={"symbol": sym+"USDT", "interval": interval, "limit": limit},
            timeout=20)
        if r.status_code == 429: time.sleep(30); return None
        d = r.json()
        if not d or isinstance(d, dict): return None
        return {
            "c": [float(x[4]) for x in d],
            "h": [float(x[2]) for x in d],
            "l": [float(x[3]) for x in d],
            "v": [float(x[5]) for x in d],
            "o": [float(x[1]) for x in d],
        }
    except:
        return None

def global_ath(sym):
    try:
        r = requests.get(BN + "/klines",
            params={"symbol": sym+"USDT", "interval": "1w", "limit": 200}, timeout=15)
        d = r.json()
        return max(float(x[2]) for x in d) if d and not isinstance(d, dict) else 0
    except:
        return 0

# ================================================================
# MARKET CONTEXT — CoinGecko
# ================================================================
_ctx_cache = None
_ctx_time  = 0

def market_ctx():
    global _ctx_cache, _ctx_time
    # Print cached values every scan so they always show in logs
    if time.time() - _ctx_time < 900 and _ctx_cache:
        c = _ctx_cache
        print(f"  CTX: BTC.D={c['btc_d']:.1f}% FG={c['fg']} TOTAL=${c['total']/1e12:.2f}T [cached]")
        return _ctx_cache
    # Fetch fresh from CoinGecko
    for attempt in range(3):
        try:
            r = requests.get("https://api.coingecko.com/api/v3/global",
                headers={"x-cg-demo-api-key": CG_KEY}, timeout=15)
            if r.status_code == 429:
                print(f"  CTX: CoinGecko rate limit — wait 20s")
                time.sleep(20); continue
            if r.status_code != 200:
                print(f"  CTX: CoinGecko status {r.status_code}")
                break
            d = r.json()["data"]
            btc_d = float(d["market_cap_percentage"]["btc"])
            total = float(d["total_market_cap"]["usd"])
            fg = 50
            try:
                fg = int(requests.get("https://api.alternative.me/fng/?limit=1",
                    timeout=8).json()["data"][0]["value"])
            except: pass
            _ctx_cache = {"btc_d": btc_d, "total": total, "fg": fg}
            _ctx_time  = time.time()
            print(f"  CTX: BTC.D={btc_d:.1f}% FG={fg} TOTAL=${total/1e12:.2f}T [LIVE]")
            return _ctx_cache
        except Exception as e:
            print(f"  CTX error attempt {attempt+1}: {e}")
    if _ctx_cache:
        print(f"  CTX: using last known data BTC.D={_ctx_cache['btc_d']:.1f}%")
    return _ctx_cache

# ================================================================
# INDICATORS
# ================================================================
def rsi(p, n=14):
    if len(p) < n+1: return 50
    g = l = 0
    for i in range(1, n+1):
        d = p[i]-p[i-1]
        if d > 0: g += d
        else: l += abs(d)
    g /= n; l /= n
    for i in range(n, len(p)):
        d = p[i]-p[i-1]
        g = (g*13 + max(d,0))/14
        l = (l*13 + max(-d,0))/14
    return 100 if l==0 else 100-(100/(1+g/l))

def ema(p, n):
    if len(p) < n: return []
    k = 2/(n+1); r = [sum(p[:n])/n]
    for x in p[n:]: r.append(x*k + r[-1]*(1-k))
    return r

def macd_bull(p):
    if len(p) < 35: return False
    e12=ema(p,12); e26=ema(p,26)
    ml=[e12[i+14]-e26[i] for i in range(len(e26))]
    if len(ml)<9: return False
    sl=ema(ml,9); diff=len(ml)-len(sl)
    hist=[ml[i+diff]-sl[i] for i in range(len(sl))]
    return hist[-1] > hist[-2] if len(hist)>=2 else False

def atr(h, l, c, n=14):
    if len(h)<n+1: return 0
    trs=[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(h))]
    a = sum(trs[:n])/n
    for t in trs[n:]: a=(a*13+t)/14
    return a

def adx_val(h, l, c, n=14):
    if len(h)<n*2: return 0
    trs=[]; pdm=[]; mdm=[]
    for i in range(1,len(h)):
        trs.append(max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])))
        u=h[i]-h[i-1]; d=l[i-1]-l[i]
        pdm.append(u if u>d and u>0 else 0)
        mdm.append(d if d>u and d>0 else 0)
    at=pt=mt=0
    for i in range(n): at+=trs[i];pt+=pdm[i];mt+=mdm[i]
    at/=n;pt/=n;mt/=n
    for i in range(n,len(trs)):
        at=(at*13+trs[i])/14;pt=(pt*13+pdm[i])/14;mt=(mt*13+mdm[i])/14
    pd=100*pt/at if at else 0; md=100*mt/at if at else 0
    return abs(pd-md)/(pd+md)*100 if (pd+md) else 0

# ================================================================
# PIVOTS
# ================================================================
def pivots(c, h, l, atr_val, mode="swing"):
    n=len(c)
    win = 5 if mode=="scalp" else max(3, min(15, n//35))
    win = max(3, win)
    min_move = 0.05 if mode=="scalp" else 0.08

    pts=[]
    for i in range(win, n-win):
        w=c[i-win:i+win+1]
        if c[i]==max(w) and c[i]>c[i-1] and c[i]>c[i+1]:
            pts.append({"i":i,"p":c[i],"t":"pk"})
        elif c[i]==min(w) and c[i]<c[i-1] and c[i]<c[i+1]:
            pts.append({"i":i,"p":c[i],"t":"tr"})

    # insert start + end
    st="tr" if c[0]<c[min(5,n-1)] else "pk"
    pts.insert(0,{"i":0,"p":c[0],"t":st})
    pts.append({"i":n-1,"p":c[-1],"t":"cur"})

    # merge same-type
    sig=[pts[0]]
    for p in pts[1:]:
        prev=sig[-1]
        if prev["t"]==p["t"]:
            if p["t"]=="pk" and p["p"]>prev["p"]: sig[-1]=p
            elif p["t"]=="tr" and p["p"]<prev["p"]: sig[-1]=p
            continue
        if prev["p"]>0 and abs(p["p"]-prev["p"])/prev["p"] >= min_move:
            sig.append(p)

    # ATR filter — W1 must be meaningful
    if len(sig)>=2 and atr_val>0:
        if abs(sig[1]["p"]-sig[0]["p"]) < atr_val*1.5:
            sig=[sig[0], sig[-1]]

    return sig

# ================================================================
# STRUCTURE DETECTION
# ================================================================
def find_structure(c, h, l, o, pvts, cur):
    pks=[p for p in pvts if p["t"]=="pk"]
    trs=[p for p in pvts if p["t"]=="tr"]
    n=len(pvts)
    best=None

    def better(s):
        nonlocal best
        if not best or s["score"]>best["score"]: best=s

    # EW W2 — trough,peak,trough,peak,trough,peak
    for i in range(n-6,-1,-1):
        if i+5>=n: continue
        p=pvts[i:i+6]
        if [x["t"] for x in p]!=["tr","pk","tr","pk","tr","pk"]: continue
        w0,w1h,w2l=p[0]["p"],p[1]["p"],p[2]["p"]
        w1=w1h-w0
        if w1<=0 or w2l<=w0: continue
        w2r=(w1h-w2l)/w1
        if not 0.382<=w2r<=1.0: continue
        if abs(cur-w2l)/w2l>0.15: continue
        real_trs=[x for x in pvts[:i+3] if x["t"]=="tr"]
        w0r=real_trs[0]["p"] if real_trs else w0
        sc=60+(15 if 0.5<=w2r<=0.786 else 8)
        better({"type":"EW_W2","score":sc,"entry":w2l,
                "w0":w0r,"w1h":w1h,"w1r":w1h-w0r,
                "sl":w0r*0.99,"tp1":w1h})
        break

    # EW W4 — trough,peak,trough,peak,trough
    for i in range(n-5,-1,-1):
        if i+4>=n: continue
        p=pvts[i:i+5]
        if [x["t"] for x in p]!=["tr","pk","tr","pk","tr"]: continue
        w0,w1h,w2l,w3h,w4l=p[0]["p"],p[1]["p"],p[2]["p"],p[3]["p"],p[4]["p"]
        w1=w1h-w0; w3=w3h-w2l
        if w1<=0 or w3<w1 or w4l<=w1h: continue
        w4r=(w3h-w4l)/w3
        if not 0.1<=w4r<=0.786: continue
        if abs(cur-w4l)/w4l>0.15: continue
        sc=58+(15 if 0.236<=w4r<=0.5 else 8)+(5 if w3h-w3*0.786<=cur<=w3h-w3*0.382 else 0)
        better({"type":"EW_W4","score":sc,"entry":w4l,
                "sl":min(w1h*0.99, cur*0.95),
                "w3h":w3h,"w3r":w3,"tp1":w3h})
        break

    # ABC Zigzag
    if len(pks)>=1 and len(trs)>=2:
        lp,lt,pt=pks[-1],trs[-1],trs[-2]
        if lt["i"]>lp["i"]>pt["i"]:
            wa=lp["p"]-pt["p"]; wb=lp["p"]-lt["p"]
            if wa>0 and 0.5<=wb/wa<=1.2:
                ceqa=lp["p"]-wa
                prox=abs(cur-ceqa)/max(abs(ceqa),0.001)*100
                sc=55+(15 if prox<=5 else 8 if prox<=10 else 0)
                real_min=min(trs,key=lambda x:x["p"])["p"]
                better({"type":"ABC","score":sc,"entry":lt["p"],
                        "sl":real_min*0.985,"tp1":lp["p"],"wa":wa})

    # Trend continuation (IMPULSING / TRENDING_UP)
    if len(pks)>=2 and len(trs)>=2:
        hh=pks[-1]["p"]>pks[-2]["p"]
        hl=trs[-1]["p"]>trs[-2]["p"]
        if hh and hl:
            adx=adx_val(h,l,c,14)
            mom=(c[-1]-c[-20])/c[-20]*100 if len(c)>=20 else 0
            if adx>=20 and mom>=2:
                sl=trs[-2]["p"]*0.98
                sc=55+(10 if adx>=30 else 5)+(5 if mom>=5 else 0)
                better({"type":"TREND","score":sc,"entry":trs[-1]["p"],
                        "sl":sl,"tp1":cur+(cur-sl)*1.5})

    return best

# ================================================================
# SCORING
# ================================================================
def score(struct, c, h, l, trend_score):
    if not struct: return 0
    base=struct["score"]
    rv=rsi(c)
    rb=5 if rv<35 else 3 if rv<45 else 0
    mb=5 if macd_bull(c) else 0
    ma50=sum(c[-50:])/50 if len(c)>=50 else c[-1]
    ma20=sum(c[-20:])/20 if len(c)>=20 else c[-1]
    tb=10 if c[-1]>ma50 and ma20>ma50 else 5 if c[-1]>ma50 else -5
    raw=base+rb+mb+tb
    return min(100,max(0,int(raw)))

# ================================================================
# RISK — SL and TPs
# ================================================================
def risk(struct, c, h, l, sl_pct, tp_pcts):
    cur=c[-1]
    sl  = struct.get("sl", cur*(1-sl_pct))
    tp1 = struct.get("tp1", cur*(1+tp_pcts[0]))

    if struct["type"]=="EW_W2":
        w1r=struct["w1r"]; tp1=struct["w1h"]
        tp2=tp1+w1r*0.618; tp3=tp1+w1r; tp4=tp1+w1r*1.618
    elif struct["type"]=="EW_W4":
        w3r=struct["w3r"]; tp1=struct["w3h"]
        tp2=tp1+w3r*0.618; tp3=tp1+w3r; tp4=tp1+w3r*1.618
    elif struct["type"]=="ABC":
        wa=struct["wa"]; tp1=struct["tp1"]
        tp2=tp1+wa*0.618; tp3=tp1+wa; tp4=tp1+wa*1.618
    else:
        rng=cur-sl
        tp2=cur+rng*2.5; tp3=cur+rng*4; tp4=cur+rng*6

    # Sanity: SL below entry, TPs ascending above entry
    if sl>=cur: sl=cur*(1-sl_pct)
    if tp1<=cur: tp1=cur*(1+tp_pcts[0])
    if tp2<=tp1: tp2=tp1*(1+tp_pcts[1])
    if tp3<=tp2: tp3=tp2*(1+tp_pcts[2])
    if tp4<=tp3: tp4=tp3*(1+tp_pcts[3])

    return sl,tp1,tp2,tp3,tp4

# ================================================================
# ANALYZE — main entry point
# ================================================================
def analyze(sym, mode):
    interval = "1d" if mode=="swing" else "4h"
    limit    = 730  if mode=="swing" else 540
    d=klines(sym, interval, limit)
    if not d or len(d["c"])<80: return None

    c,h,l,v,o=d["c"],d["h"],d["l"],d["v"],d["o"]
    cur=c[-1]

    # Daily trend filter
    ma50=sum(c[-50:])/50 if len(c)>=50 else cur
    pct_ath=(cur-max(c))/max(c)*100
    in_correction=pct_ath<-20
    if cur<ma50 and not in_correction: return None

    # Phase
    ma20=sum(c[-20:])/20 if len(c)>=20 else cur
    pvts_=pivots(c,h,l,atr(h,l,c),mode)

    # HTF weekly check
    try:
        wd=klines(sym,"1w",52)
        if wd and len(wd["c"])>=20:
            wc=wd["c"]; wma20=sum(wc[-20:])/20
            if wc[-1]<wma20*0.85: return None  # deeply bearish weekly
    except: pass

    st=find_structure(c,h,l,o,pvts_,cur)
    if not st: return None

    # Score
    ma50t=sum(c[-50:])/50 if len(c)>=50 else cur
    trend_sc=70 if cur>ma50t else 40
    sc=score(st,c,h,l,trend_sc)
    if sc<MIN_SIGNAL_SCORE: return None

    # Raw score gate — structure must be good on its own
    if st["score"]<55: return None

    # Market context adjustments
    ctx=market_ctx()
    if ctx:
        fg=ctx["fg"]
        if fg<=20: return None  # extreme fear
        if sc<80 and ctx["btc_d"]>58: return None  # BTC dominance too high for alts

    sl_pct=0.05; tp_pcts=[0.05,0.05,0.05,0.05]
    sl,tp1,tp2,tp3,tp4=risk(st,c,h,l,sl_pct,tp_pcts)

    rr=abs((tp2-cur)/(cur-sl)) if cur!=sl else 0

    if sc>=90:   sit="HIGH — STRONG BUY"
    elif sc>=85: sit="HIGH — STRONG BUY"
    elif sc>=80: sit="MEDIUM-HIGH — STRONG BUY"
    else:        sit="MEDIUM — BUY"

    return {
        "sym":sym,"mode":mode,"score":sc,"struct":st["type"],
        "cur":cur,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"tp4":tp4,
        "rr":round(rr,1),"sit":sit,
        "hold":"Days to weeks" if mode=="swing" else "1-3 days"
    }

# ================================================================
# FORMAT
# ================================================================
def fmt(p):
    if p>=1000: return "$"+f"{round(p):,}"
    if p>=1:    return f"${p:.4f}"
    if p>=0.01: return f"${p:.5f}"
    return f"${p:.7f}"

def pct(a,b): return f"({'+' if a>b else ''}{(a-b)/b*100:.1f}%)"

def msg(s):
    e=s["cur"]; sl=s["sl"]; tp1=s["tp1"]; tp2=s["tp2"]
    icon="⚡" if s["mode"]=="scalp" else "📈"
    rr=f"1:{s['rr']}" if s['rr']>0 else ""
    t  = f"{icon} <b>{s['mode'].upper()} — {s['sym']}/USDT</b>\n\n"
    t += f"💵 Entry: {fmt(e*0.99)} – {fmt(e*1.01)}\n"
    t += f"🛑 SL:    {fmt(sl)} {pct(sl,e)}"
    if rr: t+=f" | R:R {rr}"
    t += f"\n\n"
    t += f"🎯 TP1:  {fmt(tp1)} {pct(tp1,e)}\n"
    t += f"🎯 TP2:  {fmt(tp2)} {pct(tp2,e)}\n"
    t += f"🎯 TP3:  {fmt(s['tp3'])} {pct(s['tp3'],e)}\n"
    t += f"🎯 TP4:  {fmt(s['tp4'])} {pct(s['tp4'],e)}\n\n"
    t += f"⏱ Hold: {s['hold']}\n"
    t += f"⚡ Score: {s['score']}/100\n"
    t += f"📊 {s['sit']}"
    return t

# ================================================================
# PRICE ALERTS
# ================================================================
active={}

def check_alerts():
    for key,tr in list(active.items()):
        if tr.get("closed"): continue
        sym=tr["sym"]
        try:
            d=klines(sym,"15m",2)
            if not d: continue
            cur=d["c"][-1]; e=tr["entry"]
            sl=tr["sl"]; tp1=tr["tp1"]; tp2=tr["tp2"]; tp3=tr["tp3"]; tp4=tr["tp4"]
            if cur<=sl and not tr.get("done"):
                tg(f"🔴 STOP LOSS — {sym}\nPrice: {fmt(cur)} | Loss: {pct(cur,e)}")
                active[key]["closed"]=True
            elif cur>=tp4 and not tr.get("t4"):
                tg(f"🎯🎯🎯 TP4 HIT — {sym}\nPrice: {fmt(cur)} | {pct(cur,e)}")
                active[key]["t4"]=active[key]["t3"]=active[key]["t2"]=active[key]["t1"]=True
                active[key]["closed"]=True
            elif cur>=tp3 and not tr.get("t3"):
                tg(f"🎯🎯 TP3 HIT — {sym}\nPrice: {fmt(cur)} | {pct(cur,e)}\nSL → TP2: {fmt(tp2)}")
                active[key]["t3"]=active[key]["t2"]=active[key]["t1"]=True; active[key]["sl"]=tp2
            elif cur>=tp2 and not tr.get("t2"):
                tg(f"🎯 TP2 HIT — {sym}\nPrice: {fmt(cur)} | {pct(cur,e)}\nSL → TP1: {fmt(tp1)}")
                active[key]["t2"]=active[key]["t1"]=True; active[key]["sl"]=tp1
            elif cur>=tp1 and not tr.get("t1"):
                tg(f"🎯 TP1 HIT — {sym}\nPrice: {fmt(cur)} | {pct(cur,e)}\nSL → Entry: {fmt(e)}")
                active[key]["t1"]=True; active[key]["sl"]=e
        except: pass

# ================================================================
# API SERVER
# ================================================================
def api():
    class H(BaseHTTPRequestHandler):
        def log_message(self,*a): pass
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "version":"V9","active":len([t for t in active.values() if not t.get("closed")]),
                "cooldowns":len(sent),"market":market_ctx()
            }).encode())
    threading.Thread(target=HTTPServer(("0.0.0.0",PORT),H).serve_forever,daemon=True).start()

# ================================================================
# MAIN
# ================================================================
def main():
    load()
    api()

    # Log startup context immediately
    ctx = market_ctx()
    if ctx:
        print(f"  Startup CTX: BTC.D={ctx['btc_d']:.1f}% FG={ctx['fg']} TOTAL=${ctx['total']/1e12:.2f}T")

    tg(f"[SIGNALSYM V9] Started\n75+ signals only | {len(COINS)} coins\nRestored {len(sent)} cooldowns")
    print(f"SIGNALSYM V9 | {len(COINS)} coins | min score {MIN_SIGNAL_SCORE} | {len(sent)} cooldowns active")

    # Startup delay — prevents duplicate sends when Render restarts
    # during deploy. Wait 10s, then recheck state before first scan.
    print("  Waiting 10s before first scan...")
    time.sleep(10)
    load()  # reload state after delay — catches any concurrent instance
    print(f"  Active cooldowns after reload: {len(sent)}")

    scan=0
    while True:
        scan+=1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scan #{scan}")

        # Binance check
        try:
            if requests.get(BN+"/ping",timeout=10).status_code!=200:
                print("Binance down — wait 60s"); time.sleep(60); continue
        except:
            print("Binance unreachable — wait 60s"); time.sleep(60); continue

        sigs=0
        for sym in COINS:
            for mode in ["swing","scalp"]:
                key=sym+"_"+mode
                if on_cooldown(key):
                    continue   # silent skip
                try:
                    r=analyze(sym,mode)
                    if not r:
                        continue
                    # Final cooldown check — catches concurrent sends
                    if on_cooldown(key):
                        print(f"  {sym} {mode}: cooldown hit after analyze — skip")
                        continue
                    print(f"  {sym} {mode.upper()} {r['score']}/100 [{r['struct']}] SENDING")
                    tg(msg(r))
                    mark_sent(key)  # immediately updates both sent + _session_sent + saves state
                    active[key]={"sym":sym,"entry":r["cur"],"sl":r["sl"],
                                 "tp1":r["tp1"],"tp2":r["tp2"],"tp3":r["tp3"],"tp4":r["tp4"]}
                    sigs+=1
                    time.sleep(3)  # 3s gap between signals
                except Exception as e:
                    print(f"  {sym} {mode} error: {e}")
            time.sleep(0.5)

        print(f"Scan #{scan} done — {sigs} signals | next in 15min")

        # Price alerts every 5 min during wait
        for _ in range(3):
            time.sleep(300)
            check_alerts()

        if scan%96==0:
            tg(f"[HEARTBEAT] Scan {scan} | Active: {len([t for t in active.values() if not t.get('closed')])}")

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt: print("Stopped")
    except Exception as e:
        import traceback; traceback.print_exc()
