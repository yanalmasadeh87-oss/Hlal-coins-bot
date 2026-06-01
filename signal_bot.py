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

MIN_SCORE      = 75
SWING_COOLDOWN = 28800
SCALP_COOLDOWN = 14400

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
# STATE — pinned Telegram message survives all restarts/deploys
# ================================================================
sent = {}
_pin_id = None

def save():
    global _pin_id
    if not TG: return
    text = "SSYM:" + json.dumps({"s": sent, "t": time.time()})
    try:
        if _pin_id:
            r = requests.post(TG+"/editMessageText",
                json={"chat_id":CHAT_ID,"message_id":_pin_id,"text":text},timeout=10)
            if r.ok: return
        r = requests.post(TG+"/sendMessage",
            json={"chat_id":CHAT_ID,"text":text,"disable_notification":True},timeout=10)
        if r.ok:
            _pin_id = r.json()["result"]["message_id"]
            requests.post(TG+"/pinChatMessage",
                json={"chat_id":CHAT_ID,"message_id":_pin_id,"disable_notification":True},timeout=10)
    except: pass

def load():
    global sent, _pin_id
    try:
        r = requests.get(TG+"/getChat", params={"chat_id":CHAT_ID}, timeout=10)
        if not r.ok: return
        pin = r.json().get("result",{}).get("pinned_message",{})
        text = pin.get("text","")
        if not text.startswith("SSYM:"): return
        d = json.loads(text[5:])
        if time.time()-d.get("t",0) > 86400: return
        _pin_id = pin.get("message_id")
        now = time.time()
        for k,v in d.get("s",{}).items():
            cd = SWING_COOLDOWN if "swing" in k else SCALP_COOLDOWN
            if now-v < cd: sent[k]=v
        print(f"  [STATE] Restored {len(sent)} cooldowns")
    except Exception as e:
        print(f"  [STATE] {e}")

def on_cooldown(key):
    cd = SWING_COOLDOWN if "swing" in key else SCALP_COOLDOWN
    return time.time()-sent.get(key,0) < cd

def mark_sent(key):
    sent[key] = time.time()
    save()

# ================================================================
# TELEGRAM
# ================================================================
def tg(text):
    try:
        requests.post(TG+"/sendMessage",
            json={"chat_id":CHAT_ID,"text":text,
                  "parse_mode":"HTML","disable_web_page_preview":True},
            timeout=10)
    except Exception as e:
        print("TG error:", e)

# ================================================================
# DATA
# ================================================================
def klines(sym, interval, limit):
    for attempt in range(3):
        try:
            r = requests.get(BN+"/klines",
                params={"symbol":sym+"USDT","interval":interval,"limit":limit},
                timeout=20)
            if r.status_code == 429:
                time.sleep(30); continue
            d = r.json()
            if not d or isinstance(d,dict): return None
            return {
                "c":[float(x[4]) for x in d], "h":[float(x[2]) for x in d],
                "l":[float(x[3]) for x in d], "v":[float(x[5]) for x in d],
                "o":[float(x[1]) for x in d],
            }
        except:
            if attempt < 2: time.sleep(2)
    return None

# ================================================================
# MARKET CONTEXT
# ================================================================
_ctx = None
_ctx_t = 0

def market_ctx():
    global _ctx, _ctx_t
    if time.time()-_ctx_t < 900 and _ctx:
        c = _ctx
        print(f"  CTX: BTC.D={c['btc_d']:.1f}% FG={c['fg']} TOTAL=${c['total']/1e12:.2f}T [cached]")
        return _ctx
    for attempt in range(3):
        try:
            r = requests.get("https://api.coingecko.com/api/v3/global",
                headers={"x-cg-demo-api-key":CG_KEY}, timeout=15)
            if r.status_code == 429:
                time.sleep(20*(attempt+1)); continue
            if r.status_code != 200: break
            d = r.json()["data"]
            btc_d = float(d["market_cap_percentage"]["btc"])
            total = float(d["total_market_cap"]["usd"])
            fg = 50
            try:
                fg = int(requests.get("https://api.alternative.me/fng/?limit=1",
                    timeout=8).json()["data"][0]["value"])
            except: pass
            _ctx = {"btc_d":btc_d,"total":total,"fg":fg}
            _ctx_t = time.time()
            print(f"  CTX: BTC.D={btc_d:.1f}% FG={fg} TOTAL=${total/1e12:.2f}T [LIVE]")
            return _ctx
        except Exception as e:
            print(f"  CTX error: {e}")
    if _ctx:
        print(f"  CTX: using cached BTC.D={_ctx['btc_d']:.1f}%")
    return _ctx

# ================================================================
# INDICATORS
# ================================================================
def rsi(p, n=14):
    if len(p)<n+1: return 50
    g=l=0
    for i in range(1,n+1):
        d=p[i]-p[i-1]
        if d>0: g+=d
        else: l+=abs(d)
    g/=n; l/=n
    for i in range(n,len(p)):
        d=p[i]-p[i-1]
        g=(g*13+max(d,0))/14; l=(l*13+max(-d,0))/14
    return 100 if l==0 else 100-(100/(1+g/l))

def ema(p,n):
    if len(p)<n: return []
    k=2/(n+1); r=[sum(p[:n])/n]
    for x in p[n:]: r.append(x*k+r[-1]*(1-k))
    return r

def macd_bull(p):
    if len(p)<35: return False
    e12=ema(p,12); e26=ema(p,26)
    ml=[e12[i+14]-e26[i] for i in range(len(e26))]
    if len(ml)<9: return False
    sl=ema(ml,9); diff=len(ml)-len(sl)
    hist=[ml[i+diff]-sl[i] for i in range(len(sl))]
    return hist[-1]>hist[-2] if len(hist)>=2 else False

def atr(h,l,c,n=14):
    if len(h)<n+1: return 0
    trs=[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(h))]
    a=sum(trs[:n])/n
    for t in trs[n:]: a=(a*13+t)/14
    return a

# ================================================================
# CHART PHASE DETECTION
# Reads what the chart is actually doing before trying to label it
# ================================================================
def chart_phase(c, h, l):
    """
    Detect the actual market phase from price action.
    Returns: phase, swing_highs, swing_lows, trend_strength
    """
    n = len(c)
    if n < 60: return "unknown", [], [], 0

    # Find significant swing points (adaptive window based on volatility)
    at = atr(h, l, c)
    avg_price = sum(c[-50:])/50
    atr_pct = at/avg_price if avg_price > 0 else 0.03

    # Window adapts to coin volatility
    win = max(5, min(20, int(1/atr_pct * 0.5)))

    swings_h = []  # swing highs
    swings_l = []  # swing lows

    for i in range(win, n-win):
        if h[i] == max(h[i-win:i+win+1]):
            swings_h.append({"i":i, "p":h[i]})
        if l[i] == min(l[i-win:i+win+1]):
            swings_l.append({"i":i, "p":l[i]})

    if len(swings_h) < 2 or len(swings_l) < 2:
        return "unknown", swings_h, swings_l, 0

    # Trend structure from RECENT swings only (last 40% of data)
    recent_from = int(n * 0.6)
    rh = [s for s in swings_h if s["i"] >= recent_from]
    rl = [s for s in swings_l if s["i"] >= recent_from]

    hh = len(rh)>=2 and rh[-1]["p"] > rh[-2]["p"]   # higher high
    hl = len(rl)>=2 and rl[-1]["p"] > rl[-2]["p"]    # higher low
    lh = len(rh)>=2 and rh[-1]["p"] < rh[-2]["p"]    # lower high
    ll = len(rl)>=2 and rl[-1]["p"] < rl[-2]["p"]    # lower low

    cur = c[-1]
    ma20 = sum(c[-20:])/20
    ma50 = sum(c[-50:])/50 if n>=50 else cur
    ma200= sum(c[-200:])/200 if n>=200 else ma50

    # Momentum
    mom = (c[-1]-c[-20])/c[-20]*100 if n>=20 else 0

    # Trend strength 0-100
    strength = 0
    if cur > ma50:  strength += 25
    if cur > ma200: strength += 25
    if ma20 > ma50: strength += 20
    if mom > 0:     strength += 15
    if hh and hl:   strength += 15

    # Phase classification
    if lh and ll and cur < ma50:
        phase = "downtrend"
    elif hh and hl and cur > ma50 and mom > 5:
        phase = "impulse"
    elif hh and hl and cur > ma50:
        phase = "uptrend"
    elif (hh or hl) and cur < ma50 * 1.05:
        phase = "correction"
    elif not hh and not ll:
        phase = "ranging"
    else:
        phase = "transition"

    return phase, swings_h, swings_l, strength

# ================================================================
# ADAPTIVE EW ANALYSIS
# Instead of forcing a fixed pattern, reads what the chart shows
# and finds the most likely EW position
# ================================================================
def analyze_ew(c, h, l, phase, swings_h, swings_l, cur, mode):
    """
    Adaptive EW: reads the chart's actual swing structure,
    determines the most likely wave position, and finds the entry.

    Returns signal dict or None.
    """
    if len(swings_h) < 2 or len(swings_l) < 2:
        return None

    pks = swings_h
    trs = swings_l

    # ── SCENARIO 1: Correction in uptrend (best EW entry) ──────
    # Price made highs, pulled back, now at potential wave 2 or wave 4
    if phase in ("correction", "uptrend", "impulse", "transition"):

        # Find the most recent completed up-move and its correction
        for i in range(len(pks)-1, 0, -1):
            peak    = pks[i]       # most recent high = end of impulse
            prev_tr = None         # trough before the impulse started
            curr_tr = None         # current trough (correction bottom)

            # Find trough after this peak (current correction)
            post_troughs = [t for t in trs if t["i"] > peak["i"]]
            if not post_troughs: continue
            curr_tr = min(post_troughs, key=lambda x: x["p"])

            # Find trough before this peak (wave origin)
            pre_troughs = [t for t in trs if t["i"] < peak["i"]]
            if not pre_troughs: continue
            prev_tr = max(pre_troughs, key=lambda x: x["i"])  # most recent before peak

            impulse_size = peak["p"] - prev_tr["p"]
            if impulse_size <= 0: continue

            correction = peak["p"] - curr_tr["p"]
            retrace_pct = correction / impulse_size

            # Valid EW correction: 23.6% to 78.6% retrace
            if not 0.236 <= retrace_pct <= 0.786: continue

            # Current price must be near the correction low
            if abs(cur - curr_tr["p"]) / curr_tr["p"] > 0.10: continue

            # Classify retrace quality
            if 0.382 <= retrace_pct <= 0.618:
                quality = "golden"
                base_score = 72
            elif 0.236 <= retrace_pct < 0.382:
                quality = "shallow"
                base_score = 65
            elif 0.618 < retrace_pct <= 0.786:
                quality = "deep"
                base_score = 68
            else:
                continue

            # SL = below the correction low (structural level)
            # Use the actual swing low as SL reference
            sl_level = curr_tr["p"]

            # TP targets based on impulse size (Fibonacci extensions)
            tp1 = peak["p"]                        # retrace to previous high
            tp2 = prev_tr["p"] + impulse_size * 1.618  # 1.618 extension
            tp3 = prev_tr["p"] + impulse_size * 2.0    # 2.0 extension
            tp4 = prev_tr["p"] + impulse_size * 2.618  # 2.618 extension

            # Determine wave label (W2 or W4)
            # W2: first significant correction after initial move
            # W4: correction after an extended move (check if there was a prior W2)
            prior_corrections = [t for t in trs if prev_tr["i"] < t["i"] < peak["i"]]
            wave_label = "W4" if len(prior_corrections) >= 1 else "W2"

            return {
                "type": f"EW_{wave_label}",
                "phase": phase,
                "quality": quality,
                "retrace": round(retrace_pct*100, 1),
                "impulse": impulse_size,
                "base_score": base_score,
                "sl_structural": sl_level,   # actual swing low
                "entry": cur,
                "tp1": tp1, "tp2": tp2, "tp3": tp3, "tp4": tp4,
                "peak": peak["p"],
                "origin": prev_tr["p"],
            }

    # ── SCENARIO 2: Trend continuation (higher highs + higher lows) ──
    if phase == "impulse" and len(pks) >= 2 and len(trs) >= 2:
        last_trough = trs[-1]
        last_peak   = pks[-1]
        prev_trough = trs[-2]

        # Pullback to last higher low in strong uptrend
        if (last_trough["p"] > prev_trough["p"] and      # higher low confirmed
            abs(cur - last_trough["p"]) / last_trough["p"] < 0.08):

            move_size = last_peak["p"] - prev_trough["p"]
            sl_level  = last_trough["p"]

            return {
                "type": "TREND_CONT",
                "phase": phase,
                "quality": "pullback",
                "retrace": 0,
                "impulse": move_size,
                "base_score": 62,
                "sl_structural": sl_level,
                "entry": cur,
                "tp1": last_peak["p"],
                "tp2": last_peak["p"] + move_size * 0.618,
                "tp3": last_peak["p"] + move_size,
                "tp4": last_peak["p"] + move_size * 1.618,
                "peak": last_peak["p"],
                "origin": prev_trough["p"],
            }

    return None

# ================================================================
# SCORING — adapts to what the chart actually shows
# ================================================================
def score_signal(sig, c, h, l, phase):
    base = sig["base_score"]

    # RSI bonus — want oversold at correction low
    rv = rsi(c)
    if rv < 30:   base += 10
    elif rv < 40: base += 6
    elif rv < 50: base += 3
    elif rv > 65: base -= 8   # not oversold = weaker entry

    # MACD turning bull
    if macd_bull(c): base += 6

    # Quality bonus
    if sig.get("quality") == "golden": base += 8
    elif sig.get("quality") == "deep": base += 4

    # Phase bonus
    if phase == "impulse":    base += 5
    elif phase == "uptrend":  base += 3
    elif phase == "downtrend": base -= 20  # should never fire but safety

    # Retrace in golden zone
    ret = sig.get("retrace", 0)
    if 38 <= ret <= 62: base += 5

    return min(100, max(0, int(base)))

# ================================================================
# RISK — structural SL with mode-based hard cap
# ================================================================
def build_risk(sig, cur, mode):
    sl_structural = sig["sl_structural"]
    max_sl = 0.03 if mode == "scalp" else 0.06

    # SL below the structural low, but never more than max_sl
    sl_raw = sl_structural * 0.995  # 0.5% buffer below swing low
    sl = max(sl_raw, cur * (1 - max_sl))

    if sl >= cur: sl = cur * (1 - max_sl)

    tp1, tp2, tp3, tp4 = sig["tp1"], sig["tp2"], sig["tp3"], sig["tp4"]

    # Sanity
    if tp1 <= cur: tp1 = cur * (1.05 if mode=="scalp" else 1.08)
    if tp2 <= tp1: tp2 = tp1 * 1.08
    if tp3 <= tp2: tp3 = tp2 * 1.08
    if tp4 <= tp3: tp4 = tp3 * 1.10

    rr = abs((tp2-cur)/(cur-sl)) if cur != sl else 0
    return sl, tp1, tp2, tp3, tp4, round(rr, 1)

# ================================================================
# MAIN ANALYZE FUNCTION
# ================================================================
def analyze(sym, mode):
    interval = "1d" if mode == "swing" else "4h"
    limit    = 500 if mode == "swing" else 400
    d = klines(sym, interval, limit)
    if not d or len(d["c"]) < 100: return None

    c, h, l = d["c"], d["h"], d["l"]
    cur = c[-1]

    # Basic filters
    rv = rsi(c)
    if rv > 72: return None  # overbought

    ma50 = sum(c[-50:])/50 if len(c)>=50 else cur
    ath  = max(c)
    pct_ath = (cur-ath)/ath*100
    in_correction = pct_ath < -20

    # Must be in uptrend or correction within uptrend
    if cur < ma50 and not in_correction: return None

    # Detect chart phase and swing structure
    phase, swings_h, swings_l, strength = chart_phase(c, h, l)

    # Don't trade confirmed downtrends
    if phase == "downtrend": return None

    # HTF weekly filter
    wd = klines(sym, "1w", 52)
    if wd and len(wd["c"]) >= 20:
        wc = wd["c"]
        wma20 = sum(wc[-20:])/20
        if wc[-1] < wma20 * 0.82: return None  # deeply bearish weekly

    # Adaptive EW analysis
    sig = analyze_ew(c, h, l, phase, swings_h, swings_l, cur, mode)
    if not sig: return None

    # Score
    sc = score_signal(sig, c, h, l, phase)
    if sc < MIN_SIGNAL_SCORE: return None

    # Market context
    ctx = market_ctx()
    if ctx:
        if ctx["fg"] <= 20: return None
        if sym not in ("BTC","ETH") and ctx["btc_d"] > 60: return None

    # Build risk levels
    sl, tp1, tp2, tp3, tp4, rr = build_risk(sig, cur, mode)

    if sc >= 90:   sit = "HIGH — STRONG BUY"
    elif sc >= 85: sit = "HIGH — STRONG BUY"
    elif sc >= 80: sit = "MEDIUM-HIGH — STRONG BUY"
    else:          sit = "MEDIUM — BUY"

    return {
        "sym": sym, "mode": mode, "score": sc,
        "struct": sig["type"], "phase": phase,
        "quality": sig.get("quality",""),
        "retrace": sig.get("retrace", 0),
        "cur": cur, "sl": sl, "tp1": tp1, "tp2": tp2, "tp3": tp3, "tp4": tp4,
        "rr": rr, "sit": sit,
        "hold": "Days to weeks" if mode=="swing" else "1-3 days"
    }

# ================================================================
# FORMAT
# ================================================================
def fmt(p):
    if p >= 1000: return "$"+f"{round(p):,}"
    if p >= 1:    return f"${p:.4f}"
    if p >= 0.01: return f"${p:.5f}"
    return f"${p:.7f}"

def pct(a, b):
    return f"({'+' if a>b else ''}{(a-b)/b*100:.1f}%)"

def build_msg(s):
    e = s["cur"]; sl = s["sl"]
    icon = "⚡" if s["mode"]=="scalp" else "📈"
    rr = f"1:{s['rr']}" if s["rr"] > 0 else ""

    t  = f"{icon} <b>{s['mode'].upper()} — {s['sym']}/USDT</b>\n\n"
    t += f"📊 Pattern: {s['struct']} | {s['phase'].title()}"
    if s.get("retrace"): t += f" | {s['retrace']}% retrace"
    t += f"\n\n"
    t += f"💵 Entry: {fmt(e*0.99)} – {fmt(e*1.01)}\n"
    t += f"🛑 SL:    {fmt(sl)} {pct(sl,e)}"
    if rr: t += f" | R:R {rr}"
    t += f"\n\n"
    t += f"🎯 TP1:  {fmt(s['tp1'])} {pct(s['tp1'],e)}\n"
    t += f"🎯 TP2:  {fmt(s['tp2'])} {pct(s['tp2'],e)}\n"
    t += f"🎯 TP3:  {fmt(s['tp3'])} {pct(s['tp3'],e)}\n"
    t += f"🎯 TP4:  {fmt(s['tp4'])} {pct(s['tp4'],e)}\n\n"
    t += f"⏱ Hold: {s['hold']}\n"
    t += f"⚡ Score: {s['score']}/100\n"
    t += f"📊 {s['sit']}"
    return t

# ================================================================
# PRICE ALERTS
# ================================================================
active = {}

def check_alerts():
    for key, tr in list(active.items()):
        if tr.get("closed"): continue
        sym = tr["sym"]
        try:
            d = klines(sym, "15m", 2)
            if not d: continue
            cur = d["c"][-1]
            e=tr["entry"]; sl=tr["sl"]; tp1=tr["tp1"]; tp2=tr["tp2"]; tp3=tr["tp3"]; tp4=tr["tp4"]

            if cur <= sl:
                tg(f"🔴 STOP LOSS — {sym}\nPrice: {fmt(cur)} | Loss: {pct(cur,e)}")
                active[key]["closed"] = True
            elif cur >= tp4 and not tr.get("t4"):
                tg(f"🎯🎯🎯 TP4 — {sym}\nPrice: {fmt(cur)} | {pct(cur,e)}")
                active[key].update({"t4":True,"t3":True,"t2":True,"t1":True,"closed":True})
            elif cur >= tp3 and not tr.get("t3"):
                tg(f"🎯🎯 TP3 — {sym}\nPrice: {fmt(cur)} | {pct(cur,e)}\nSL → TP2: {fmt(tp2)}")
                active[key].update({"t3":True,"t2":True,"t1":True,"sl":tp2})
            elif cur >= tp2 and not tr.get("t2"):
                tg(f"🎯 TP2 — {sym}\nPrice: {fmt(cur)} | {pct(cur,e)}\nSL → TP1: {fmt(tp1)}")
                active[key].update({"t2":True,"t1":True,"sl":tp1})
            elif cur >= tp1 and not tr.get("t1"):
                tg(f"🎯 TP1 — {sym}\nPrice: {fmt(cur)} | {pct(cur,e)}\nSL → Entry: {fmt(e)}")
                active[key].update({"t1":True,"sl":e})
        except: pass

# ================================================================
# API
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
                "version":"V10","active":len([t for t in active.values() if not t.get("closed")]),
                "cooldowns":len(sent),"market":_ctx
            }).encode())
    threading.Thread(target=HTTPServer(("0.0.0.0",PORT),H).serve_forever,daemon=True).start()

# ================================================================
# SCAN LOOP
# ================================================================
def scan_loop():
    scan = 0
    while True:
        scan += 1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scan #{scan}")

        try:
            if requests.get(BN+"/ping", timeout=10).status_code != 200:
                print("Binance down — wait 60s"); time.sleep(60); continue
        except:
            print("Binance unreachable — wait 60s"); time.sleep(60); continue

        sigs = 0
        for sym in COINS:
            for mode in ["swing","scalp"]:
                key = sym+"_"+mode
                if on_cooldown(key): continue
                try:
                    r = analyze(sym, mode)
                    if not r: continue
                    if on_cooldown(key): continue  # final check
                    print(f"  {sym} {mode.upper()} {r['score']}/100 [{r['struct']}|{r['phase']}] SENDING")
                    tg(build_msg(r))
                    mark_sent(key)
                    active[key] = {
                        "sym":sym,"entry":r["cur"],"sl":r["sl"],
                        "tp1":r["tp1"],"tp2":r["tp2"],"tp3":r["tp3"],"tp4":r["tp4"]
                    }
                    sigs += 1
                    time.sleep(3)
                except Exception as e:
                    print(f"  {sym} {mode} error: {e}")
            time.sleep(0.5)

        print(f"Scan #{scan} done — {sigs} signals | next in 15min")
        for _ in range(3):
            time.sleep(300)
            check_alerts()

        if scan % 96 == 0:
            tg(f"[HEARTBEAT] Scan {scan} | Active: {len([t for t in active.values() if not t.get('closed')])}")

# ================================================================
# MAIN
# ================================================================
def main():
    api()
    load()
    market_ctx()
    print(f"SIGNALSYM V10 | {len(COINS)} coins | min score {MIN_SIGNAL_SCORE} | {len(sent)} cooldowns")

    time.sleep(10)
    load()

    threading.Thread(target=scan_loop, daemon=True).start()
    while True:
        time.sleep(60)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("Stopped")
    except Exception as e:
        import traceback; traceback.print_exc()
