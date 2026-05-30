import requests
import time
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────
TELEGRAM_TOKEN = "7975488031:AAHLdeNTM-YIItriXwradU4bPyCMdR-mAIY"
CHAT_ID        = "8422276082"
BN_BASE        = "https://api.binance.com/api/v3"
TG_BASE        = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ── SIGNAL LEVELS ─────────────────────────────────────────────
SWING_SL  = 0.05;  SWING_TP1 = 0.05;  SWING_TP2 = 0.10;  SWING_TP3 = 0.15;  SWING_TP4 = 0.20
SCALP_SL  = 0.03;  SCALP_TP1 = 0.03;  SCALP_TP2 = 0.05;  SCALP_TP3 = 0.08;  SCALP_TP4 = 0.12

# ── HALAL WATCHLIST ───────────────────────────────────────────
HALAL_WATCHLIST = [
    # TIER 1
    {"sym":"BTC",    "tier":1}, {"sym":"ETH",    "tier":1},
    {"sym":"XRP",    "tier":1}, {"sym":"SOL",    "tier":1},
    {"sym":"BNB",    "tier":1}, {"sym":"ADA",    "tier":1},
    {"sym":"AVAX",   "tier":1}, {"sym":"SUI",    "tier":1},
    {"sym":"HBAR",   "tier":1}, {"sym":"NEAR",   "tier":1},
    {"sym":"DOT",    "tier":1}, {"sym":"ICP",    "tier":1},
    {"sym":"FTM",    "tier":1}, {"sym":"ETC",    "tier":1},
    {"sym":"WLD",    "tier":1}, {"sym":"RENDER", "tier":1},
    {"sym":"ATOM",   "tier":1}, {"sym":"KAS",    "tier":1},
    {"sym":"FIL",    "tier":1}, {"sym":"APT",    "tier":1},
    {"sym":"ARB",    "tier":1}, {"sym":"VET",    "tier":1},
    {"sym":"SEI",    "tier":1}, {"sym":"STX",    "tier":1},
    {"sym":"TIA",    "tier":1}, {"sym":"GRT",    "tier":1},
    {"sym":"OP",     "tier":1}, {"sym":"THETA",  "tier":1},
    # TIER 2
    {"sym":"XLM",    "tier":2}, {"sym":"ALGO",   "tier":2},
    {"sym":"LTC",    "tier":2}, {"sym":"TON",    "tier":2},
    {"sym":"LINK",   "tier":2}, {"sym":"POL",    "tier":2},
    {"sym":"XTZ",    "tier":2}, {"sym":"IOTA",   "tier":2},
    {"sym":"BCH",    "tier":2}, {"sym":"IMX",    "tier":2},
    {"sym":"INJ",    "tier":2}, {"sym":"FET",    "tier":2},
    {"sym":"OCEAN",  "tier":2}, {"sym":"AKT",    "tier":2},
    {"sym":"AR",     "tier":2}, {"sym":"HNT",    "tier":2},
    {"sym":"ONE",    "tier":2}, {"sym":"ZIL",    "tier":2},
    {"sym":"QTUM",   "tier":2}, {"sym":"DCR",    "tier":2},
    {"sym":"RVN",    "tier":2}, {"sym":"EGLD",   "tier":2},
    {"sym":"FLOW",   "tier":2}, {"sym":"ANKR",   "tier":2},
    {"sym":"STORJ",  "tier":2}, {"sym":"BAND",   "tier":2},
    {"sym":"NMR",    "tier":2}, {"sym":"GLM",    "tier":2},
    {"sym":"SKL",    "tier":2}, {"sym":"CELO",   "tier":2},
    {"sym":"ROSE",   "tier":2}, {"sym":"CTSI",   "tier":2},
    {"sym":"WAVES",  "tier":2}, {"sym":"DGB",    "tier":2},
    # TIER 3
    {"sym":"GALA",   "tier":3}, {"sym":"AXS",    "tier":3},
    {"sym":"SAND",   "tier":3}, {"sym":"MANA",   "tier":3},
    {"sym":"ENJ",    "tier":3}, {"sym":"CHZ",    "tier":3},
    {"sym":"ASTR",   "tier":3}, {"sym":"BAT",    "tier":3},
    {"sym":"LPT",    "tier":3}, {"sym":"AUDIO",  "tier":3},
    {"sym":"CVC",    "tier":3}, {"sym":"POWR",   "tier":3},
    {"sym":"HOT",    "tier":3},
]

sent_signals  = {}
sent_watches  = {}
scan_count    = 0
active_trades = {}

# ── TELEGRAM ──────────────────────────────────────────────────
def send_msg(msg):
    try:
        requests.post(f"{TG_BASE}/sendMessage",
            json={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML"},
            timeout=10)
    except Exception as e:
        print(f"  TG error: {e}")

# ── BINANCE DATA ──────────────────────────────────────────────
def fetch_klines(sym, interval="1d", limit=365):
    url    = f"{BN_BASE}/klines"
    params = {"symbol":sym+"USDT","interval":interval,"limit":limit}
    try:
        r    = requests.get(url,params=params,timeout=15)
        data = r.json()
        if isinstance(data,dict) and data.get("code"):
            return [],[]
        prices = [float(k[4]) for k in data]
        vols   = [float(k[5]) for k in data]
        return prices,vols
    except Exception as e:
        print(f"  Binance error {sym}: {e}")
        return [],[]

def fetch_ticker(sym):
    try:
        r = requests.get(f"{BN_BASE}/ticker/24hr",
            params={"symbol":sym+"USDT"},timeout=10)
        return r.json()
    except:
        return {}

# ── INDICATORS ────────────────────────────────────────────────
def calc_rsi(prices, period=14):
    if len(prices)<period+1: return 50
    ag=al=0
    for i in range(1,period+1):
        d=prices[i]-prices[i-1]
        if d>0: ag+=d
        else:   al+=abs(d)
    ag/=period; al/=period
    for i in range(period,len(prices)):
        d=prices[i]-prices[i-1]
        ag=(ag*13+(d if d>0 else 0))/14
        al=(al*13+(abs(d) if d<0 else 0))/14
    return 100 if al==0 else 100-(100/(1+ag/al))

def calc_ema(prices, period):
    if len(prices)<period: return []
    k=2/(period+1)
    r=[sum(prices[:period])/period]
    for p in prices[period:]: r.append(p*k+r[-1]*(1-k))
    return r

def calc_macd(prices):
    if len(prices)<35: return 0,0,0,0
    ef=calc_ema(prices,12); es=calc_ema(prices,26)
    ml=[ef[i+14]-es[i] for i in range(len(es))]
    if len(ml)<9: return 0,0,0,0
    sl=calc_ema(ml,9); diff=len(ml)-len(sl)
    hist=[ml[i+diff]-sl[i] for i in range(len(sl))]
    if len(hist)<2: return ml[-1],sl[-1],0,0
    return ml[-1],sl[-1],hist[-1],hist[-2]

def calc_stoch(prices, period=14):
    if len(prices)<period: return 50
    sl=prices[-period:]; high=max(sl); low=min(sl)
    if high==low: return 50
    return ((prices[-1]-low)/(high-low))*100

def calc_ewo(prices):
    if len(prices)<35: return 0
    return sum(prices[-5:])/5-sum(prices[-35:])/35

def calc_smi(prices, period=14):
    if len(prices)<period: return 0
    sl=prices[-period:]; high=max(sl); low=min(sl)
    mid=(high+low)/2; rng=high-low
    if rng==0: return 0
    return ((prices[-1]-mid)/(rng/2))*100

# ── WAVE DETECTION ────────────────────────────────────────────
def detect_pivots(prices, min_move=0.10):
    n=len(prices)
    if n<20: return []
    win=max(3,n//20); pivots=[]
    for i in range(win,n-win):
        sl=prices[i-win:i+win+1]
        if prices[i]==max(sl) and prices[i]>prices[i-1] and prices[i]>prices[i+1]:
            pivots.append({"idx":i,"price":prices[i],"type":"peak"})
        elif prices[i]==min(sl) and prices[i]<prices[i-1] and prices[i]<prices[i+1]:
            pivots.append({"idx":i,"price":prices[i],"type":"trough"})
    st="trough" if prices[0]<prices[min(10,n-1)] else "peak"
    pivots.insert(0,{"idx":0,"price":prices[0],"type":st})
    pivots.append({"idx":n-1,"price":prices[-1],"type":"current"})
    sig=[pivots[0]]
    for p in pivots[1:]:
        prev=sig[-1]
        if prev["type"]==p["type"]:
            if p["type"]=="peak"   and p["price"]>prev["price"]: sig[-1]=p
            elif p["type"]=="trough" and p["price"]<prev["price"]: sig[-1]=p
            continue
        if abs((p["price"]-prev["price"])/prev["price"])>=min_move:
            sig.append(p)
    return sig

def validate_ew(pivots):
    issues=[]
    if len(pivots)>=3:
        w1r=abs(pivots[1]["price"]-pivots[0]["price"])
        if w1r>0:
            w2r=abs(pivots[2]["price"]-pivots[1]["price"])/w1r*100
            if pivots[2]["price"]<pivots[0]["price"]: issues.append("W2>100% W1")
            elif w2r<38: issues.append(f"W2 shallow({w2r:.0f}%)")
    if len(pivots)>=4:
        if abs(pivots[3]["price"]-pivots[2]["price"])<abs(pivots[1]["price"]-pivots[0]["price"]):
            issues.append("W3<W1")
    if len(pivots)>=5 and pivots[4]["price"]<pivots[1]["price"]:
        issues.append("W4 overlaps W1")
    return len(issues)==0,issues

def check_alternation(pivots):
    if len(pivots)<5: return False,"Need W4"
    w1=abs(pivots[1]["price"]-pivots[0]["price"])
    w3=abs(pivots[3]["price"]-pivots[2]["price"])
    if not w1 or not w3: return False,"Cannot calc"
    w2r=abs(pivots[2]["price"]-pivots[1]["price"])/w1*100
    w4r=abs(pivots[4]["price"]-pivots[3]["price"])/w3*100
    alt=(w2r>50 and w4r<40) or (w2r<40 and w4r>40) or abs(w2r-w4r)>15
    return alt,f"W2:{w2r:.0f}% W4:{w4r:.0f}% {'✓' if alt else '≈'}"

def detect_candlestick(prices):
    if len(prices)<3: return "None",False
    p1,p2,p3=prices[-1],prices[-2],prices[-3]
    if p2<p3 and p1>p2 and (p1-p2)>(p3-p2)*0.5: return "Bullish Engulfing",True
    if p2<p3*0.97 and p1>p2*1.02: return "Hammer",True
    if p3>p2 and p2<p1 and p1>(p3+p2)/2: return "Morning Star",True
    if abs(p1-p2)/p2<0.005 and p2<p3*0.98: return "Doji",True
    return "No pattern",False

def detect_diagonal(pivots,prices):
    if len(pivots)<5: return False
    r3=calc_rsi(prices[:min(pivots[3]["idx"]+1,len(prices))])
    r5=calc_rsi(prices[:min(pivots[4]["idx"]+1,len(prices))])
    return pivots[4]["price"]>=pivots[3]["price"] and r5<r3

def check_wave_symmetry(pivots):
    if len(pivots)<5: return False,"Need 5 waves"
    w1=abs(pivots[1]["price"]-pivots[0]["price"])
    w3=abs(pivots[3]["price"]-pivots[2]["price"])
    w2=abs(pivots[2]["price"]-pivots[1]["price"])
    w4=abs(pivots[4]["price"]-pivots[3]["price"])
    score=0; total=0
    if w1>0:
        total+=1
        if w3>=w1: score+=1
    if w2>0 and w4>0:
        total+=1
        if abs(w2-w4)/max(w2,w4)>=0.15: score+=1
    if len(pivots)>=6:
        w5=abs(pivots[5]["price"]-pivots[4]["price"])
        if w3>0:
            total+=1
            if w5<=w3*1.2: score+=1
    pct=score/total*100 if total>0 else 50
    return pct>=60,f"Symmetry {pct:.0f}%"

def calc_blue_box(pivots,current):
    if len(pivots)<3: return False,"No box"
    w1_range=abs(pivots[1]["price"]-pivots[0]["price"])
    direction=1 if pivots[1]["price"]>pivots[0]["price"] else -1
    fib618=pivots[1]["price"]-direction*w1_range*0.618
    fib786=pivots[1]["price"]-direction*w1_range*0.786
    box_top=max(fib618,fib786); box_bot=min(fib618,fib786)
    in_w2_box=box_bot<=current<=box_top
    in_w4_box=False
    if len(pivots)>=5:
        w3_range=abs(pivots[3]["price"]-pivots[2]["price"])
        dir3=1 if pivots[3]["price"]>pivots[2]["price"] else -1
        f382=pivots[3]["price"]-dir3*w3_range*0.382
        f618=pivots[3]["price"]-dir3*w3_range*0.618
        in_w4_box=min(f382,f618)<=current<=max(f382,f618)
    in_box=in_w2_box or in_w4_box
    label="W2 Blue Box ✓" if in_w2_box else "W4 Blue Box ✓" if in_w4_box else "Outside Blue Box"
    return in_box,label

def detect_truncated_w5(pivots,prices):
    if len(pivots)<6: return False,"Need W5"
    w3_high=pivots[3]["price"]; w5_high=pivots[5]["price"]
    truncated=w5_high<w3_high and w5_high>pivots[4]["price"]
    if truncated:
        return True,"Truncated W5 - Reversal imminent - DO NOT ENTER"
    return False,"No truncation"

def calc_fib_retrace(pivots):
    if len(pivots)<3: return 0,False,""
    w1_range=abs(pivots[1]["price"]-pivots[0]["price"])
    if w1_range==0: return 0,False,""
    w2_range=abs(pivots[2]["price"]-pivots[1]["price"])
    retrace=(w2_range/w1_range)*100
    if retrace<38.2:    return retrace,False,"Shallow (<38.2%)"
    elif retrace<=50.0: return retrace,True,"0.382 Fib Zone"
    elif retrace<=61.8: return retrace,True,"0.500 Fib Zone"
    elif retrace<=78.6: return retrace,True,"0.618 Golden Ratio"
    elif retrace<=100:  return retrace,True,"0.786 Deep Fib"
    else:               return retrace,False,"W2 > 100% W1 (Invalid)"

def calc_w4_fib_retrace(pivots):
    if len(pivots)<5: return 0,False,""
    w3_range=abs(pivots[3]["price"]-pivots[2]["price"])
    if w3_range==0: return 0,False,""
    w4_range=abs(pivots[4]["price"]-pivots[3]["price"])
    retrace=(w4_range/w3_range)*100
    if 23.6<=retrace<=50.0:
        return retrace,True,f"W4 Fib {retrace:.0f}% of W3"
    return retrace,False,f"W4 outside Fib ({retrace:.0f}%)"

def calc_c_equals_a(pivots,current):
    if len(pivots)<4: return False,0,0,"Need more data"
    for i in range(len(pivots)-3,-1,-1):
        if i+3>=len(pivots): continue
        p0=pivots[i]; p1=pivots[i+1]; p2=pivots[i+2]; p3=pivots[i+3]
        if not(p0["type"]=="peak" and p1["type"]=="trough" and
               p2["type"]=="peak" and p3["type"]=="trough"): continue
        wave_a=abs(p0["price"]-p1["price"])
        if wave_a==0: continue
        c_start=p2["price"]
        ca_target=c_start-wave_a
        ca_ext=c_start-wave_a*1.618
        ca_ratio=(c_start-current)/wave_a*100
        prox_ca=abs(current-ca_target)/max(abs(ca_target),0.0001)*100
        prox_ext=abs(current-ca_ext)/max(abs(ca_ext),0.0001)*100
        # TIME equality (fatinhijjawi method)
        a_time=p1["idx"]-p0["idx"]; c_time=p3["idx"]-p2["idx"]
        time_ratio=c_time/a_time*100 if a_time>0 else 0
        time_equal=80<=time_ratio<=120
        time_note=f"Time:{time_ratio:.0f}% of A"
        if prox_ca<=5 and time_equal: return True,ca_target,ca_ratio,f"C=A Price+Time ({time_note})"
        if prox_ca<=5: return True,ca_target,ca_ratio,f"C=A Price | {time_note}"
        if prox_ext<=5: return True,ca_ext,ca_ratio,f"C=1.618xA | {time_note}"
        if 80<=ca_ratio<=120: return True,ca_target,ca_ratio,f"Near C=A ({ca_ratio:.0f}% | {time_note})"
        return False,ca_target,ca_ratio,f"C=A at ${ca_target:,.4f} ({ca_ratio:.0f}%)"
    return False,0,0,"No ABC found"

def detect_wxyxz(pivots,current):
    if len(pivots)<8: return False,0,0,"Need 8+ pivots"
    best=None
    for i in range(len(pivots)-5):
        if i+5>=len(pivots): continue
        p0=pivots[i]; p1=pivots[i+1]; p2=pivots[i+2]
        p3=pivots[i+3]; p4=pivots[i+4]; p5=pivots[i+5]
        if not(p0["type"]=="peak" and p1["type"]=="trough" and p2["type"]=="peak" and
               p3["type"]=="trough" and p4["type"]=="peak" and p5["type"]=="trough"): continue
        x1p=abs(p2["price"]-p1["price"]); x1t=p2["idx"]-p1["idx"]
        x2p=abs(p4["price"]-p3["price"]); x2t=p4["idx"]-p3["idx"]
        if x1p==0 or x1t==0: continue
        if x1p/p1["price"]*100<5 or x2p/p3["price"]*100<5: continue
        w_size=abs(p1["price"]-p0["price"]); y_size=abs(p3["price"]-p2["price"])
        if x1p>=w_size*0.8 or x2p>=y_size*0.8: continue
        pr=x2p/x1p*100; tr=x2t/x1t*100
        price_eq=85<=pr<=115; time_eq=85<=tr<=115
        if price_eq and time_eq:
            z=p5["price"]; near_z=abs(current-z)/z*100<=8
            best={"detected":True,"both_equal":True,"price_ratio":pr,
                  "time_ratio":tr,"near_z":near_z,"z_price":z,
                  "label":f"WXYXZ X1=X2 ({pr:.0f}% price | {tr:.0f}% time)"}
            if near_z: break
    if best: return best["detected"],best["z_price"],best["price_ratio"],best["label"]
    return False,0,0,"No WXYXZ found"

# ═══════════════════════════════════════════════════════════════
# CHART STRUCTURE RECOGNIZER
# This is the NEW addition — reads each chart and identifies
# which of the 5 patterns exists, then adapts the analysis.
#
# Each structure has different:
#   - Entry logic
#   - Which EW rules apply
#   - Which checks are REQUIRED vs SITUATIONAL (■ = not applicable)
#   - Signal label shown in Telegram
# ═══════════════════════════════════════════════════════════════

def recognize_chart_structure(pivots, prices, current):
    """
    Reads the chart and identifies the pattern present.
    Returns dict with structure type and applicable checks.

    Structures (priority order — most specific first):
    1. WXYXZ        — Triple combination, X1=X2 (rarest, highest confidence)
    2. EXPANDED_FLAT — B exceeds prior impulse top
    3. RUNNING_CORR  — C stays above A bottom (very bullish)
    4. ABC_ZIGZAG    — Classic 5-3-5 after completed impulse
    5. EW_W4        — Active impulse, price at W4
    6. EW_W2        — After full impulse, price at W2
    7. UNKNOWN       — Cannot identify clear pattern
    """
    if len(pivots) < 4:
        return {"type": "UNKNOWN", "label": "Unknown", "entry_wave": ""}

    n = len(pivots)

    # ── Check WXYXZ first (rarest, most specific) ────────────
    wxyxz_ok, wxyxz_price, wxyxz_ratio, wxyxz_label = detect_wxyxz(pivots, current)
    if wxyxz_ok:
        return {
            "type":        "WXYXZ",
            "label":       "W-X-Y-X-Z Triple Combination",
            "entry_wave":  "Wave Z",
            "entry_price": wxyxz_price,
            "confidence":  "HIGHEST - X1=X2 Confirmed",
            # Swing TPs: from Z bottom toward W origin
            "swing_tp_notes": ["Z bottom", "X2 top", "W origin", "Extension"],
            # Applicable situational checks for this structure
            "sit_applicable": ["wxyxz", "ca_zone", "rsi_ok", "stoch_ok",
                               "macd_ok", "vol_exp", "candlestick"],
            # NOT applicable (■) for this structure
            "sit_na": ["fib_golden", "alternation", "wave_symmetry",
                       "blue_box", "abc_struct", "wave_c_bottom"],
        }

    # ── Check for completed impulse first (needed for ABC types) ─
    impulse_complete = False
    w5_top = 0
    wa_bot = 0
    wb_top = 0
    wc_bot = 0

    # Find completed 5-wave impulse: trough-peak-trough-peak-trough-peak
    for i in range(n - 6, -1, -1):
        if i + 5 >= n:
            continue
        p = pivots[i:i+6]
        types = [x["type"] for x in p]
        if types != ["trough","peak","trough","peak","trough","peak"]:
            continue
        # Validate 3 EW rules
        w0 = p[0]["price"]; w1h = p[1]["price"]; w2l = p[2]["price"]
        w3h = p[3]["price"]; w4l = p[4]["price"]; w5h = p[5]["price"]
        w1  = w1h - w0
        if w1 <= 0: continue
        if w2l <= w0: continue               # Rule 1
        w3 = w3h - w2l; w5 = w5h - w4l
        if w3 <= 0 or (w3 < w1 and w3 < w5): continue  # Rule 2
        if w4l <= w1h: continue              # Rule 3
        if w5h <= w3h: continue
        # Valid impulse found
        impulse_complete = True
        w5_top = w5h
        # Find ABC after this impulse
        post = [pv for pv in pivots if pv["idx"] > p[5]["idx"]]
        if len(post) >= 2:
            a_piv = next((pv for pv in post if pv["type"] == "trough"), None)
            if a_piv:
                wa_bot = a_piv["price"]
                wa_range = w5h - wa_bot
                post_a = [pv for pv in post if pv["idx"] > a_piv["idx"]]
                b_piv = next((pv for pv in post_a if pv["type"] == "peak"), None)
                if b_piv:
                    wb_top = b_piv["price"]
                    wb_ret = (wb_top - wa_bot) / wa_range if wa_range > 0 else 0
                    post_b = [pv for pv in post if pv["idx"] > b_piv["idx"]]
                    c_piv = next((pv for pv in post_b if pv["type"] == "trough"), None)
                    wc_bot = c_piv["price"] if c_piv else current

                    # ── EXPANDED FLAT: B exceeds W5 top ──────────
                    if wb_top > w5h and wa_range > 0:
                        wc_range = wb_top - wc_bot
                        c_vs_a   = wc_range / wa_range if wa_range > 0 else 0
                        c_prog   = min(c_vs_a / 1.236 * 100, 100)
                        if c_prog >= 60:
                            return {
                                "type":        "EXPANDED_FLAT",
                                "label":       "Expanded Flat Correction",
                                "entry_wave":  "Wave C",
                                "entry_price": wc_bot,
                                "wa_bot":      wa_bot,
                                "wb_top":      wb_top,
                                "wc_bot":      wc_bot,
                                "w5_top":      w5_top,
                                "wa_range":    wa_range,
                                "wb_ret_pct":  round(wb_ret * 100, 1),
                                "c_progress":  round(c_prog, 1),
                                "c_t1236":     wb_top - wa_range * 1.236,
                                "c_t1618":     wb_top - wa_range * 1.618,
                                "confidence":  "HIGH - B exceeds W5, C completing",
                                "swing_tp_notes": [
                                    f"Wave B top ${wb_top:,.4f}",
                                    f"1.618xA from C",
                                    f"2.0xA from C",
                                    f"2.618xA from C",
                                ],
                                "sit_applicable": ["wave_c_bottom", "ca_zone", "abc_struct",
                                                   "rsi_ok", "stoch_ok", "macd_ok",
                                                   "vol_dec", "vol_exp", "smi_ok"],
                                "sit_na": ["fib_golden", "blue_box", "alternation",
                                           "wave_symmetry", "wxyxz"],
                            }

                    # ── RUNNING CORRECTION: C above A bottom ─────
                    if 0.38 <= wb_ret <= 0.78 and wa_range > 0:
                        wc_range = wb_top - wc_bot if wc_bot > 0 else 0
                        c_vs_a   = wc_range / wa_range if wa_range > 0 else 0
                        if wc_bot > wa_bot and c_vs_a >= 0.38:
                            return {
                                "type":        "RUNNING_CORRECTION",
                                "label":       "Running Correction (Bullish)",
                                "entry_wave":  "Wave C (Higher Low)",
                                "entry_price": wc_bot,
                                "wa_bot":      wa_bot,
                                "wb_top":      wb_top,
                                "wc_bot":      wc_bot,
                                "w5_top":      w5_top,
                                "wa_range":    wa_range,
                                "wb_ret_pct":  round(wb_ret * 100, 1),
                                "c_vs_a_pct":  round(c_vs_a * 100, 1),
                                "confidence":  "HIGH - Higher low, market very strong",
                                "swing_tp_notes": [
                                    f"Wave B top ${wb_top:,.4f}",
                                    f"W5 top ${w5_top:,.4f}",
                                    f"W5 + 1.0xW1",
                                    f"W5 + 1.618xW1",
                                ],
                                "sit_applicable": ["wave_c_bottom", "abc_struct", "wave_count",
                                                   "rsi_ok", "stoch_ok", "macd_ok",
                                                   "vol_dec", "vol_exp", "smi_ok"],
                                "sit_na": ["fib_golden", "blue_box", "ca_zone",
                                           "alternation", "wxyxz"],
                            }

                    # ── ABC ZIGZAG: B retraces 38-78% of A ───────
                    if 0.38 <= wb_ret <= 0.78 and wa_range > 0:
                        wc_range  = wb_top - wc_bot if wc_bot > 0 else 0
                        c_prog    = wc_range / wa_range * 100 if wa_range > 0 else 0
                        c_eq_a    = wb_top - wa_range
                        c_confirmed = abs(wc_bot - c_eq_a) / max(abs(c_eq_a), 0.0001) < 0.05
                        if c_prog >= 60:
                            return {
                                "type":        "ABC_ZIGZAG",
                                "label":       "ABC Zigzag Correction",
                                "entry_wave":  "Wave C",
                                "entry_price": wc_bot,
                                "wa_bot":      wa_bot,
                                "wb_top":      wb_top,
                                "wc_bot":      wc_bot,
                                "w5_top":      w5_top,
                                "wa_range":    wa_range,
                                "wb_ret_pct":  round(wb_ret * 100, 1),
                                "c_progress":  round(c_prog, 1),
                                "c_eq_a_tgt":  round(c_eq_a, 6),
                                "c_confirmed": c_confirmed,
                                "confidence":  "HIGH - C=A" if c_confirmed else "DEVELOPING",
                                "swing_tp_notes": [
                                    f"Wave B top ${wb_top:,.4f}",
                                    f"W5 top ${w5_top:,.4f}",
                                    f"1.618xA from C",
                                    f"2.618xA from C",
                                ],
                                "sit_applicable": ["wave_c_bottom", "ca_zone", "abc_struct",
                                                   "rsi_ok", "stoch_ok", "macd_ok",
                                                   "vol_dec", "vol_exp", "smi_ok"],
                                "sit_na": ["fib_golden", "blue_box", "alternation",
                                           "wave_symmetry", "wxyxz"],
                            }
        break

    # ── EW W4: Active impulse, price at W4 ───────────────────
    for i in range(n - 5, -1, -1):
        if i + 4 >= n: continue
        p = pivots[i:i+5]
        types = [x["type"] for x in p]
        if types != ["trough","peak","trough","peak","trough"]: continue
        w0=p[0]["price"]; w1h=p[1]["price"]; w2l=p[2]["price"]
        w3h=p[3]["price"]; w4l=p[4]["price"]
        w1=w1h-w0; w3=w3h-w2l
        if w1<=0 or w3<=0: continue
        if w2l<=w0 or w3<w1 or w4l<=w1h: continue
        w4_ret=(w3h-w4l)/w3
        near_w4=abs(current-w4l)/w4l<0.05
        if not near_w4: continue
        w2_ret=(w1h-w2l)/w1
        _, fib_valid, fib_label = calc_fib_retrace(p[:3])
        bb_lo=w3h-w3*0.786; bb_hi=w3h-w3*0.618
        in_bb=(bb_lo<=current<=bb_hi)
        alt_ok=abs(w2_ret-(w3h-w4l)/w3)>0.15
        return {
            "type":        "EW_W4",
            "label":       "Standard EW - W4 Entry",
            "entry_wave":  "W4",
            "entry_price": w4l,
            "w1h":         w1h, "w2l": w2l,
            "w3h":         w3h, "w4l": w4l,
            "w1":          w1,  "w3":  w3,
            "w2_ret":      round(w2_ret, 3),
            "w4_ret":      round(w4_ret, 3),
            "fib_label":   fib_label,
            "fib_valid":   fib_valid,
            "in_blue_box": in_bb,
            "alternation": alt_ok,
            "confidence":  "HIGH" if in_bb else "MEDIUM",
            "swing_tp_notes": [
                f"W3 top ${w3h:,.4f}",
                f"1.618xW1 (W5 proj)",
                f"2.0xW1",
                f"2.618xW1",
            ],
            "sit_applicable": ["fib_golden", "blue_box", "alternation",
                               "wave_symmetry", "wave_count",
                               "rsi_ok", "stoch_ok", "macd_ok",
                               "vol_dec", "vol_exp", "smi_ok", "candlestick"],
            "sit_na": ["wave_c_bottom", "ca_zone", "abc_struct", "wxyxz"],
        }

    # ── EW W2: After full impulse, price at W2 ───────────────
    for i in range(n - 6, -1, -1):
        if i + 5 >= n: continue
        p = pivots[i:i+6]
        types = [x["type"] for x in p]
        if types != ["trough","peak","trough","peak","trough","peak"]: continue
        w0=p[0]["price"]; w1h=p[1]["price"]; w2l=p[2]["price"]
        w3h=p[3]["price"]; w4l=p[4]["price"]; w5h=p[5]["price"]
        w1=w1h-w0
        if w1<=0 or w2l<=w0: continue
        near_w2=abs(current-w2l)/w2l<0.05
        if not near_w2: continue
        w2_ret=(w1h-w2l)/w1
        _, fib_valid, fib_label = calc_fib_retrace(p[:3])
        return {
            "type":        "EW_W2",
            "label":       "Standard EW - W2 Entry",
            "entry_wave":  "W2",
            "entry_price": w2l,
            "w1h":         w1h, "w2l": w2l,
            "w3h":         w3h, "w4l": w4l, "w5h": w5h,
            "w1":          w1,
            "w2_ret":      round(w2_ret, 3),
            "fib_label":   fib_label,
            "fib_valid":   fib_valid,
            "confidence":  "HIGH" if 0.618<=w2_ret<=0.786 else "MEDIUM",
            "swing_tp_notes": [
                f"W1 top ${w1h:,.4f}",
                f"1.618xW1 (W3 target)",
                f"2.618xW1",
                f"Prior W5 top ${w5h:,.4f}",
            ],
            "sit_applicable": ["fib_golden", "wave_symmetry", "wave_count",
                               "rsi_ok", "stoch_ok", "macd_ok",
                               "vol_dec", "vol_exp", "smi_ok", "candlestick"],
            "sit_na": ["blue_box", "alternation", "wave_c_bottom",
                       "ca_zone", "abc_struct", "wxyxz"],
        }

    return {"type": "UNKNOWN", "label": "Unknown Pattern", "entry_wave": ""}


# ── ENTRY DETECTION (original — unchanged) ───────────────────
def detect_entry(pivots, prices=None, rsi_val=50):
    if len(pivots)<3: return "",0
    w1r=abs(pivots[1]["price"]-pivots[0]["price"])
    if w1r>0:
        w2r=abs(pivots[2]["price"]-pivots[1]["price"])/w1r*100
        if 38<=w2r<=100: return "W2",w2r
    if len(pivots)>=5:
        w3r=abs(pivots[3]["price"]-pivots[2]["price"])
        if w3r>0:
            w4r=abs(pivots[4]["price"]-pivots[3]["price"])/w3r*100
            if 23<=w4r<=38 and pivots[4]["price"]>pivots[1]["price"]:
                return "W4",w4r
    if prices and len(pivots)>=4:
        is_c,_,ret=_detect_wave_c(pivots,prices,rsi_val)
        if is_c: return "Wave C",ret
    return "",0

def _detect_wave_c(pivots, prices, rsi_val):
    if len(pivots)<6: return False,"",0
    n=len(pivots)
    if n>=4:
        last=pivots[n-1]; prev=pivots[n-2]
        prev2=pivots[n-3]; prev3=pivots[n-4]
        is_wc=(last["type"] in ["trough","current"] and
               prev["type"]=="peak" and
               prev2["type"]=="trough" and
               prev3["type"]=="peak")
        if is_wc:
            wa=abs(prev3["price"]-prev2["price"])
            wb=abs(prev["price"]-prev2["price"])
            wc=abs(prev["price"]-last["price"])
            if wa==0: return False,"",0
            b_ret=wb/wa*100
            c_rat=wc/wa*100
            near=(abs(prices[-1]-last["price"])/last["price"]*100)<=8
            if 38<=b_ret<=78 and near and (prices[-1]<=prev2["price"]*1.05 or rsi_val<45):
                return True,"Wave C",b_ret
    return False,"",0

# ── SIGNAL ANALYSIS ───────────────────────────────────────────
def analyze(coin, signal_type="swing"):
    sym=coin["sym"]
    if signal_type=="swing":
        prices,vols=fetch_klines(sym,"1d",730)
        min_move=0.10
        sl_pct=SWING_SL; tp1_pct=SWING_TP1; tp2_pct=SWING_TP2
        tp3_pct=SWING_TP3; tp4_pct=SWING_TP4
        min_score=12; max_score=22
        hold="Days to weeks"
    else:
        prices,vols=fetch_klines(sym,"4h",540)
        min_move=0.05
        sl_pct=SCALP_SL; tp1_pct=SCALP_TP1; tp2_pct=SCALP_TP2
        tp3_pct=SCALP_TP3; tp4_pct=SCALP_TP4
        min_score=7; max_score=13
        hold="1-3 days (4H trade)"

    if len(prices)<50: return None
    current=prices[-1]; ath=max(prices); pct_ath=((current-ath)/ath)*100

    rsi_val=calc_rsi(prices)
    _,_,h_curr,h_prev=calc_macd(prices)
    stoch=calc_stoch(prices); ewo=calc_ewo(prices)
    macd_cross=h_curr>0 and h_prev<=0; macd_turn=h_curr>h_prev

    pivots=detect_pivots(prices,min_move)
    ew_ok,ew_issues=validate_ew(pivots)
    entry,w_ret=detect_entry(pivots,prices,rsi_val)
    alt_ok,alt_note=check_alternation(pivots)
    candle_name,candle_bull=detect_candlestick(prices)
    diagonal=detect_diagonal(pivots,prices) if len(pivots)>=5 else False
    sym_ok,sym_note=check_wave_symmetry(pivots)
    inbox,box_label=calc_blue_box(pivots,current)
    smi=calc_smi(prices)
    trunc,trunc_note=detect_truncated_w5(pivots,prices) if len(pivots)>=6 else (False,"Need W5")
    ca_zone,ca_price,ca_ratio,ca_label=calc_c_equals_a(pivots,current)
    wxyxz_ok,wxyxz_price,wxyxz_ratio,wxyxz_label=detect_wxyxz(pivots,current)
    fib_retrace,fib_valid,fib_label=calc_fib_retrace(pivots)
    w4_fib_ret,w4_fib_valid,w4_fib_label=calc_w4_fib_retrace(pivots)
    fib_entry_ok=fib_valid or w4_fib_valid

    avg_vol=sum(vols[-20:])/20 if len(vols)>=20 else 1
    vol_dec=(sum(vols[-5:])/5)<(sum(vols[-10:-5])/5) if len(vols)>=10 else False
    vol_exp=vols[-1]>avg_vol if vols else False

    ma50=sum(prices[-50:])/50 if len(prices)>=50 else current
    daily_bull=current>ma50 or pct_ath<-50

    # Block bad setups
    if diagonal: return None
    if trunc:    return None

    # ── RECOGNIZE CHART STRUCTURE ─────────────────────────────
    chart = recognize_chart_structure(pivots, prices, current)
    struct_type  = chart.get("type", "UNKNOWN")
    struct_label = chart.get("label", "Unknown")
    sit_applicable = set(chart.get("sit_applicable", []))
    sit_na         = set(chart.get("sit_na", []))

    # Entry is valid if recognized structure matches price position
    # OR original entry detection confirms it
    struct_entry_ok = (
        struct_type != "UNKNOWN" and
        abs(current - chart.get("entry_price", current)) / max(current, 0.0001) < 0.08
    )
    entry_ok = entry != "" or struct_entry_ok

    wave_c_ok  = (struct_type in ("ABC_ZIGZAG","EXPANDED_FLAT","RUNNING_CORRECTION")
                  and struct_entry_ok)
    wave_c_ratio = chart.get("wb_ret_pct", 0)

    # ── BUILD CHECKS ──────────────────────────────────────────
    # REQUIRED (all must pass — same for all structures):
    if signal_type=="swing":
        checks={
            "daily_bull":     daily_bull,
            "ma50":           current>ma50,
            "wave_count":     len(pivots)>=5,
            "ew_valid":       ew_ok or struct_type in ("ABC_ZIGZAG","EXPANDED_FLAT",
                                                        "RUNNING_CORRECTION","WXYXZ"),
            "entry_zone":     entry_ok,
            "fib_w1_retrace": fib_valid,
            "rsi_ok":         rsi_val<45,
            "macd_ok":        macd_cross or macd_turn,
            "no_diagonal":    not diagonal,
            "no_trunc_w5":    not trunc,
            # Situational — scored only when applicable to THIS structure
            "wave_c_bottom":  wave_c_ok if "wave_c_bottom" in sit_applicable else False,
            "fib_golden":     (38.2<=fib_retrace<=78.6) if "fib_golden" in sit_applicable else False,
            "fib_entry":      fib_entry_ok,
            "stoch_ok":       stoch<25 if "stoch_ok" in sit_applicable else False,
            "smi_ok":         smi<-40 if "smi_ok" in sit_applicable else False,
            "macd_extra":     (macd_cross or macd_turn),
            "ewo_ok":         ewo!=0,
            "vol_dec":        vol_dec if "vol_dec" in sit_applicable else False,
            "vol_exp":        vol_exp if "vol_exp" in sit_applicable else False,
            "abc_struct":     (len(pivots)>=6 and struct_type in ("ABC_ZIGZAG","EXPANDED_FLAT","RUNNING_CORRECTION"))
                              if "abc_struct" in sit_applicable else False,
            "alternation":    alt_ok if "alternation" in sit_applicable else False,
            "candlestick":    candle_bull if "candlestick" in sit_applicable else False,
            "no_diagonal":    not diagonal,
            "wave_symmetry":  sym_ok if "wave_symmetry" in sit_applicable else False,
            "blue_box":       inbox if "blue_box" in sit_applicable else False,
            "ca_zone":        ca_zone if "ca_zone" in sit_applicable else False,
            "wxyxz":          wxyxz_ok if "wxyxz" in sit_applicable else False,
        }
        core_required=[
            checks["daily_bull"], checks["ma50"], checks["wave_count"],
            checks["ew_valid"],   checks["entry_zone"], checks["fib_w1_retrace"],
            checks["rsi_ok"],     checks["macd_ok"],
            checks["no_diagonal"],checks["no_trunc_w5"],
        ]
    else:
        wave_c_entry=entry=="Wave C" or wave_c_ok
        checks={
            "daily_bull":     daily_bull,
            "wave_count":     len(pivots)>=4,
            "ew_valid":       ew_ok or wave_c_entry or struct_type!="UNKNOWN",
            "entry_zone":     entry_ok,
            "wave_c_bottom":  wave_c_entry if "wave_c_bottom" in sit_applicable else False,
            "ca_zone":        ca_zone if "ca_zone" in sit_applicable else False,
            "wxyxz":          wxyxz_ok if "wxyxz" in sit_applicable else False,
            "fib_entry":      fib_entry_ok,
            "fib_valid":      fib_valid,
            "rsi_ok":         rsi_val<50,
            "stoch_ok":       stoch<30 if "stoch_ok" in sit_applicable else False,
            "macd_ok":        macd_cross or macd_turn,
            "vol_exp":        vol_exp if "vol_exp" in sit_applicable else False,
            "candlestick":    candle_bull if "candlestick" in sit_applicable else False,
            "alternation":    alt_ok if "alternation" in sit_applicable else False,
            "no_diagonal":    not diagonal,
            "not_overbought": rsi_val<70,
        }
        core_required=[
            checks["daily_bull"], checks["wave_count"],
            checks["entry_zone"], checks["fib_entry"] or checks["fib_valid"],
            checks["rsi_ok"],     checks["macd_ok"],
            checks["no_diagonal"],checks["not_overbought"],
        ]

    score=sum(1 for v in checks.values() if v)
    all_required_pass=all(core_required)
    watch_min=max(4,int(min_score*0.60))

    # WATCH alert
    if watch_min<=score<min_score:
        missing=[]
        if not checks.get("rsi_ok"):     missing.append("RSI not oversold")
        if not checks.get("stoch_ok"):   missing.append("Stoch not oversold")
        if not checks.get("macd_ok"):    missing.append("MACD not bullish")
        if not checks.get("entry_zone"): missing.append("No entry zone")
        if not checks.get("daily_bull"): missing.append("Daily not bullish")
        if signal_type=="swing" and not checks.get("fib_w1_retrace"):
            missing.append(f"W2 Fib not hit ({fib_retrace:.0f}%)")
        reason="|".join(missing[:3]) if missing else "Setup developing"
        return {
            "watch":True,"type":signal_type.upper(),"sym":sym,
            "current":current,"score":score,"max":min_score,
            "rsi":rsi_val,"stoch":stoch,"entry":entry,
            "checks":checks,"reason":reason,
            "struct_label":struct_label,"struct_type":struct_type,
        }

    if not all_required_pass: return None
    if score<min_score:        return None

    # Levels
    sl=current*(1-sl_pct); t1=current*(1+tp1_pct)
    t2=current*(1+tp2_pct); t3=current*(1+tp3_pct); t4=current*(1+tp4_pct)

    if wxyxz_ok and score>=int(max_score*0.55):
        conf="WXYXZ X1=X2 - HIGHEST CONFIDENCE"
    elif score>=int(max_score*0.85): conf="HIGH"
    elif score>=int(max_score*0.70): conf="MEDIUM-HIGH"
    else:                            conf="MEDIUM"

    return {
        "type":sym_ok,"type":signal_type.upper(),"sym":sym,"tier":coin["tier"],
        "current":current,"ath":ath,"pct_ath":pct_ath,
        "entry":entry,"w_ret":w_ret,"score":score,"max":max_score,
        "conf":conf,"rsi":rsi_val,"stoch":stoch,"macd_cross":macd_cross,
        "candle":candle_name,"alt":alt_note,"hold":hold,
        "sl":sl,"tp1":t1,"tp2":t2,"tp3":t3,"tp4":t4,
        # Structure info for Telegram
        "struct_type":  struct_type,
        "struct_label": struct_label,
        "struct_chart": chart,
        "sit_na":       sit_na,
        "ca_label":     ca_label,
        "wxyxz_label":  wxyxz_label,
        "fib_label":    fib_label,
    }

# ── FORMAT ────────────────────────────────────────────────────
def fp(p):
    if not p and p!=0: return "N/A"
    if p>=1000: return f"${p:,.0f}"
    if p>=1:    return f"${p:.4f}"
    if p>=0.01: return f"${p:.5f}"
    return f"${p:.7f}"

STRUCT_ICONS = {
    "WXYXZ":            "WXYXZ X1=X2",
    "EXPANDED_FLAT":    "Expanded Flat",
    "RUNNING_CORRECTION":"Running Correction",
    "ABC_ZIGZAG":       "ABC Zigzag",
    "EW_W4":            "EW W4 Entry",
    "EW_W2":            "EW W2 Entry",
    "UNKNOWN":          "Unknown Pattern",
}

def build_struct_lines(chart):
    """Build structure-specific detail lines for Telegram."""
    t = chart.get("type","UNKNOWN")
    lines = []
    if t in ("ABC_ZIGZAG","EXPANDED_FLAT","RUNNING_CORRECTION"):
        if chart.get("w5_top"):  lines.append(f"W5 top: {fp(chart['w5_top'])}")
        if chart.get("wa_bot"):  lines.append(f"Wave A: {fp(chart['wa_bot'])}")
        if chart.get("wb_top"):  lines.append(f"Wave B: {fp(chart['wb_top'])} ({chart.get('wb_ret_pct',0):.0f}% retrace)")
        if chart.get("wc_bot"):  lines.append(f"Wave C: {fp(chart['wc_bot'])} <- ENTRY")
        if t == "ABC_ZIGZAG" and chart.get("c_eq_a_tgt"):
            conf = "C=A CONFIRMED" if chart.get("c_confirmed") else f"C=A target: {fp(chart['c_eq_a_tgt'])} ({chart.get('c_progress',0):.0f}% done)"
            lines.append(conf)
        if t == "EXPANDED_FLAT":
            lines.append(f"B > W5 top - Expanded")
            lines.append(f"C target: {fp(chart.get('c_t1236',0))} - {fp(chart.get('c_t1618',0))}")
        if t == "RUNNING_CORRECTION":
            lines.append(f"Higher low - C above A bottom")
            lines.append(f"Very bullish - market too strong")
    elif t in ("EW_W4","EW_W2"):
        if chart.get("w1h"): lines.append(f"W1 top: {fp(chart['w1h'])}")
        if chart.get("w2l"): lines.append(f"W2 bot: {fp(chart['w2l'])} [{chart.get('fib_label','')}]")
        if chart.get("w3h"): lines.append(f"W3 top: {fp(chart['w3h'])}")
        if t == "EW_W4" and chart.get("w4l"):
            lines.append(f"W4 bot: {fp(chart['w4l'])} <- ENTRY")
            lines.append(f"W4 retrace: {chart.get('w4_ret',0)*100:.1f}% of W3")
        if t == "EW_W2" and chart.get("w5h"):
            lines.append(f"W5 top: {fp(chart['w5h'])}")
            lines.append(f"W2 bottom: {fp(chart.get('w2l',0))} <- ENTRY")
    elif t == "WXYXZ":
        lines.append("X1=X2 Price+Time Confirmed")
        lines.append(f"Z bottom entry zone")
    return "\n".join(lines)

def build_watch_msg(sym,sig_type,current,score,max_score,checks,rsi,stoch,entry,reason,struct_label=""):
    SEP="\u2501"*19
    icon="\u26a1" if sig_type=="SCALP" else "\U0001f4c8"
    passing=sum(1 for v in checks.values() if v)
    failing=sum(1 for v in checks.values() if not v)
    struct_line=f"\nPattern: {struct_label}" if struct_label else ""
    return (
        f"\U0001f7e1 <b>WATCH - {sym}/USDT</b>\n{SEP}\n"
        f"{icon} {sig_type} Setup Developing{struct_line}\n"
        f"\U0001f4b0 Price: {fp(current)}\n"
        f"\U0001f4ca Score: {score}/{max_score}\n"
        f"{SEP}\n"
        f"\u2705 Passing: {passing} | \u274c Missing: {failing}\n"
        f"\U0001f4c9 RSI:{rsi:.0f} | Stoch:{stoch:.0f}\n"
        f"{'\U0001f3af Entry: '+entry+chr(10) if entry else ''}"
        f"\u26a0\ufe0f {reason}\n{SEP}\n"
        f"<i>Not a signal yet. Monitor closely.</i>"
    )

def build_msg(sig):
    icon  = "\u26a1" if sig["type"]=="SCALP" else "\U0001f4c8"
    is_sc = sig["type"]=="SCALP"
    tp_l  = ["(+3%)","(+5%)","(+8%)","(+12%)"] if is_sc else ["(+5%)","(+10%)","(+15%)","(+20%)"]
    sl_l  = "(-3%)" if is_sc else "(-5%)"

    # Structure detail
    chart = sig.get("struct_chart", {})
    struct_type  = sig.get("struct_type","UNKNOWN")
    struct_label = sig.get("struct_label","")
    struct_lines = build_struct_lines(chart)

    # N/A situational checks (shown as ■ not failure)
    sit_na = sig.get("sit_na", set())
    na_str = ""
    if sit_na:
        na_items = ", ".join(list(sit_na)[:4])
        na_str = f"\n■ N/A checks: {na_items}"

    # Extra info based on structure
    extra = ""
    if struct_type == "WXYXZ":
        extra = f"\nWXYXZ: {sig.get('wxyxz_label','')}"
    elif struct_type in ("ABC_ZIGZAG","EXPANDED_FLAT","RUNNING_CORRECTION"):
        extra = f"\nC=A: {sig.get('ca_label','')}"
    elif struct_type in ("EW_W4","EW_W2"):
        extra = f"\nFib: {sig.get('fib_label','')}"

    return (
        f"{icon} <b>{sig['type']} - {sig['sym']}/USDT</b>\n"
        f"Pattern: {struct_label}\n"
        f"{'━'*19}\n"
        f"{struct_lines}\n"
        f"{'━'*19}\n"
        f"\U0001f7e2 <b>Entry:</b>  {fp(sig['current']*0.99)} - {fp(sig['current']*1.01)}\n"
        f"{'━'*19}\n"
        f"\U0001f3af <b>TP1:</b>    {fp(sig['tp1'])}  {tp_l[0]}\n"
        f"\U0001f3af <b>TP2:</b>    {fp(sig['tp2'])}  {tp_l[1]}\n"
        f"\U0001f3af <b>TP3:</b>    {fp(sig['tp3'])}  {tp_l[2]}\n"
        f"\U0001f3af <b>TP4:</b>    {fp(sig['tp4'])}  {tp_l[3]}\n"
        f"{'━'*19}\n"
        f"\U0001f534 <b>SL:</b>     {fp(sig['sl'])}  {sl_l}\n"
        f"{'━'*19}\n"
        f"\U0001f4ca {sig['score']}/{sig['max']} | {sig['conf']}\n"
        f"\U0001f4c9 RSI:{sig['rsi']:.0f} Stoch:{sig['stoch']:.0f} | {sig['candle']}\n"
        f"{extra}{na_str}\n"
        f"\u23f1 Hold: {sig['hold']}\n"
        f"\U0001f550 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"<i>Spot - Halal - Not financial advice</i>"
    )

# ── MONITOR ───────────────────────────────────────────────────
def monitor_watch_coins():
    if not sent_watches: return
    now=time.time()
    for key,watch_time in list(sent_watches.items()):
        if now-watch_time>21600: continue
        parts=key.replace("_watch_","_").split("_")
        if len(parts)<2: continue
        sym=parts[0]
        sig_type="scalp" if "scalp" in key else "swing"
        coin=next((c for c in HALAL_WATCHLIST if c["sym"]==sym),None)
        if not coin: continue
        try:
            result=analyze(coin,sig_type)
            if not result: continue
            if not result.get("watch"):
                signal_key=sym+"_"+sig_type
                last_sig=sent_signals.get(signal_key,0)
                if now-last_sig<(14400 if sig_type=="swing" else 7200): continue
                print(f"  WATCH->SIGNAL: {sym} {sig_type.upper()} {result['score']}/{result['max']}")
                send_msg(build_msg(result))
                sent_signals[signal_key]=now
                trade_key=sym+"_"+sig_type
                active_trades[trade_key]={
                    "sym":sym,"type":sig_type.upper(),
                    "entry":result["current"],"sl":result["sl"],
                    "tp1":result["tp1"],"tp2":result["tp2"],
                    "tp3":result["tp3"],"tp4":result["tp4"],
                    "hit_tp1":False,"hit_tp2":False,
                    "hit_tp3":False,"hit_tp4":False,
                    "closed":False,"time":now
                }
        except Exception as e:
            print(f"  Watch monitor error {sym}: {e}")
        time.sleep(2)

def check_price_alerts():
    if not active_trades: return
    SEP="\u2501"*19
    for key,trade in list(active_trades.items()):
        if trade.get("closed"): continue
        sym=trade["sym"]; sig_type=trade["type"]
        icon="\u26a1" if sig_type=="SCALP" else "\U0001f4c8"
        try:
            prices,_=fetch_klines(sym,"1m",2)
            if not prices: continue
            current=prices[-1]
        except: continue
        entry=trade["entry"]; sl=trade["sl"]
        tp1=trade["tp1"]; tp2=trade["tp2"]
        tp3=trade["tp3"]; tp4=trade["tp4"]
        if current<=sl and not trade.get("closed"):
            loss=(current-entry)/entry*100
            send_msg(
                f"\U0001f534 <b>STOP LOSS - {sym}/USDT</b>\n{SEP}\n"
                f"{icon} {sig_type} Closed\n"
                f"\U0001f4c9 Price: {fp(current)} | SL: {fp(sl)}\n"
                f"\U0001f4b8 Loss: {loss:.1f}%\n{SEP}\n"
                f"<i>Exit full position.</i>"
            )
            active_trades[key]["closed"]=True; continue
        if current>=tp1 and not trade.get("hit_tp1"):
            profit=(current-entry)/entry*100
            send_msg(
                f"\U0001f3af <b>TP1 HIT - {sym}/USDT</b>\n{SEP}\n"
                f"Price: {fp(current)} | TP1: {fp(tp1)}\n"
                f"Profit: +{profit:.1f}%\n"
                f"Exit 25% | SL -> entry: {fp(entry)}"
            )
            active_trades[key]["hit_tp1"]=True
            active_trades[key]["sl"]=entry
        if current>=tp2 and not trade.get("hit_tp2"):
            profit=(current-entry)/entry*100
            send_msg(
                f"\U0001f3af <b>TP2 HIT - {sym}/USDT</b>\n{SEP}\n"
                f"Price: {fp(current)} | TP2: {fp(tp2)}\n"
                f"Profit: +{profit:.1f}%\n"
                f"Exit 25% | SL -> TP1: {fp(tp1)}"
            )
            active_trades[key]["hit_tp2"]=True
            active_trades[key]["sl"]=tp1
        if current>=tp3 and not trade.get("hit_tp3"):
            profit=(current-entry)/entry*100
            send_msg(
                f"\U0001f3af <b>TP3 HIT - {sym}/USDT</b>\n{SEP}\n"
                f"Price: {fp(current)} | TP3: {fp(tp3)}\n"
                f"Profit: +{profit:.1f}%\n"
                f"Exit 25% | SL -> TP2: {fp(tp2)}"
            )
            active_trades[key]["hit_tp3"]=True
            active_trades[key]["sl"]=tp2
        if current>=tp4 and not trade.get("hit_tp4"):
            profit=(current-entry)/entry*100
            send_msg(
                f"\U0001f3c6 <b>TP4 HIT - {sym}/USDT</b>\n{SEP}\n"
                f"Price: {fp(current)} | TP4: {fp(tp4)}\n"
                f"Full profit: +{profit:.1f}% | Trade complete!"
            )
            active_trades[key]["hit_tp4"]=True
            active_trades[key]["closed"]=True

# ── MAIN LOOP ─────────────────────────────────────────────────
def main():
    global scan_count
    total=len(HALAL_WATCHLIST)
    t1=[c["sym"] for c in HALAL_WATCHLIST if c["tier"]==1]
    t2=[c["sym"] for c in HALAL_WATCHLIST if c["tier"]==2]
    t3=[c["sym"] for c in HALAL_WATCHLIST if c["tier"]==3]

    print(f"SIGNALSYM Bot - Binance API - {total} halal coins")
    send_msg(
        f"\U0001f552 <b>SIGNALSYM Bot - Active</b>\n"
        f"{'━'*19}\n"
        f"\u2705 Shariah-Compliant Coins Only\n"
        f"\U0001f504 Powered by Binance API\n"
        f"\U0001f4ca {total} coins monitored\n"
        f"\u23f1 Every 15 minutes\n"
        f"\U0001f4c8 Swing + \u26a1 Scalp signals\n"
        f"{'━'*19}\n"
        f"Structures detected per chart:\n"
        f"- Standard EW W2/W4 entry\n"
        f"- ABC Zigzag correction\n"
        f"- Expanded Flat (B > W5)\n"
        f"- Running Correction\n"
        f"- W-X-Y-X-Z (X1=X2)\n"
        f"{'━'*19}\n"
        f"\u2b50\u2b50\u2b50 T1 ({len(t1)}): {', '.join(t1[:8])}...\n"
        f"\u2b50\u2b50 T2 ({len(t2)}): {', '.join(t2[:8])}...\n"
        f"\u2b50 T3 ({len(t3)}): {', '.join(t3[:8])}..."
    )

    while True:
        scan_count+=1
        now=datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] Scan #{scan_count}")
        signals=0

        for coin in HALAL_WATCHLIST:
            sym=coin["sym"]
            print(f"  {sym}...",end=" ",flush=True)
            try:
                # SWING
                swing_key=sym+"_swing"; watch_key=sym+"_watch_swing"
                sw=analyze(coin,"swing")
                if sw:
                    if sw.get("watch"):
                        last_w=sent_watches.get(watch_key,0)
                        if time.time()-last_w<7200:
                            print("W(cd)",end=" ")
                        else:
                            print(f"W{sw['score']}/{sw['max']}",end=" ")
                            send_msg(build_watch_msg(
                                sym,"SWING",sw["current"],sw["score"],sw["max"],
                                sw["checks"],sw["rsi"],sw["stoch"],sw["entry"],
                                sw["reason"],sw.get("struct_label","")
                            ))
                            sent_watches[watch_key]=time.time()
                    else:
                        last=sent_signals.get(swing_key,0)
                        if time.time()-last<14400:
                            print("S(cd)",end=" ")
                        else:
                            print(f"{sw['score']}/{sw['max']} [{sw.get('struct_type','')}]",end=" ")
                            send_msg(build_msg(sw))
                            sent_signals[swing_key]=time.time()
                            signals+=1
                            active_trades[swing_key]={
                                "sym":sym,"type":"SWING","entry":sw["current"],
                                "sl":sw["sl"],"tp1":sw["tp1"],"tp2":sw["tp2"],
                                "tp3":sw["tp3"],"tp4":sw["tp4"],
                                "hit_tp1":False,"hit_tp2":False,
                                "hit_tp3":False,"hit_tp4":False,
                                "closed":False,"time":time.time()
                            }
                            time.sleep(2)
                else:
                    print("-",end=" ")

                # SCALP
                scalp_key=sym+"_scalp"; watch_key_sc=sym+"_watch_scalp"
                sc=analyze(coin,"scalp")
                if sc:
                    if sc.get("watch"):
                        last_w=sent_watches.get(watch_key_sc,0)
                        if time.time()-last_w<3600:
                            print("WS(cd)")
                        else:
                            print(f"WS{sc['score']}/{sc['max']}")
                            send_msg(build_watch_msg(
                                sym,"SCALP",sc["current"],sc["score"],sc["max"],
                                sc["checks"],sc["rsi"],sc["stoch"],sc["entry"],
                                sc["reason"],sc.get("struct_label","")
                            ))
                            sent_watches[watch_key_sc]=time.time()
                    else:
                        last=sent_signals.get(scalp_key,0)
                        if time.time()-last<7200:
                            print("SC(cd)")
                        else:
                            print(f"{sc['score']}/{sc['max']} [{sc.get('struct_type','')}]")
                            send_msg(build_msg(sc))
                            sent_signals[scalp_key]=time.time()
                            signals+=1
                            active_trades[scalp_key]={
                                "sym":sym,"type":"SCALP","entry":sc["current"],
                                "sl":sc["sl"],"tp1":sc["tp1"],"tp2":sc["tp2"],
                                "tp3":sc["tp3"],"tp4":sc["tp4"],
                                "hit_tp1":False,"hit_tp2":False,
                                "hit_tp3":False,"hit_tp4":False,
                                "closed":False,"time":time.time()
                            }
                            time.sleep(2)
                else:
                    print("-")

                time.sleep(1)

            except Exception as e:
                print(f"err:{e}")
                time.sleep(5)

        print(f"\nScan #{scan_count} - {signals} signal(s) - next in 15min")
        active_count=len([t for t in active_trades.values() if not t.get("closed")])
        print(f"  Active trades: {active_count} | Watch: {len(sent_watches)}")

        for cycle in range(3):
            time.sleep(300)
            check_price_alerts()
            if sent_watches:
                print(f"  Fast-checking {len(sent_watches)} watch coins...")
                monitor_watch_coins()

        if scan_count%96==0:
            send_msg(
                f"\U0001f493 <b>Heartbeat</b>\n"
                f"Scans: {scan_count} | Coins: {total}\n"
                f"Active trades: {active_count}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC"
            )

if __name__=="__main__":
    main()
