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
# Format: {"sym": "BTC", "tier": 1}
# All use BINANCE symbols — free, unlimited, no key needed
HALAL_WATCHLIST = [
    # TIER 1 — cryptohalal.cc verified
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

sent_signals = {}
scan_count = 0

# Track active trades for TP/SL monitoring
# Format: {sym_type: {entry, sl, tp1, tp2, tp3, tp4, hit_tp1, hit_tp2, hit_tp3, hit_tp4, closed}}
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
    """Fetch OHLCV from Binance — FREE, UNLIMITED, NO KEY"""
    url = f"{BN_BASE}/klines"
    params = {"symbol": sym+"USDT", "interval": interval, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if isinstance(data, dict) and data.get("code"):
            return [], []
        prices = [float(k[4]) for k in data]  # close price
        vols   = [float(k[5]) for k in data]  # volume
        return prices, vols
    except Exception as e:
        print(f"  Binance error {sym}: {e}")
        return [], []

def fetch_ticker(sym):
    """Fetch 24hr stats from Binance"""
    try:
        r = requests.get(f"{BN_BASE}/ticker/24hr",
            params={"symbol": sym+"USDT"}, timeout=10)
        return r.json()
    except:
        return {}

# ── INDICATORS ────────────────────────────────────────────────
def calc_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    ag = al = 0
    for i in range(1, period+1):
        d = prices[i]-prices[i-1]
        if d>0: ag+=d
        else: al+=abs(d)
    ag/=period; al/=period
    for i in range(period, len(prices)):
        d = prices[i]-prices[i-1]
        ag = (ag*13+(d if d>0 else 0))/14
        al = (al*13+(abs(d) if d<0 else 0))/14
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
    sl=prices[-period:]
    high=max(sl); low=min(sl)
    if high==low: return 50
    return ((prices[-1]-low)/(high-low))*100

def calc_ewo(prices):
    if len(prices)<35: return 0
    return sum(prices[-5:])/5 - sum(prices[-35:])/35

# ── WAVE DETECTION ────────────────────────────────────────────
def detect_pivots(prices, min_move=0.10):
    n=len(prices)
    if n<20: return []
    win=max(3,n//20)
    pivots=[]
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
            if p["type"]=="peak" and p["price"]>prev["price"]: sig[-1]=p
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
    return len(issues)==0, issues

def detect_entry(pivots):
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
    return "",0

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


# ── WAVE SYMMETRY ─────────────────────────────────────────────
def check_wave_symmetry(pivots):
    if len(pivots) < 5: return False, "Need 5 waves"
    w1 = abs(pivots[1]["price"]-pivots[0]["price"])
    w3 = abs(pivots[3]["price"]-pivots[2]["price"])
    w2 = abs(pivots[2]["price"]-pivots[1]["price"])
    w4 = abs(pivots[4]["price"]-pivots[3]["price"])
    score = 0; total = 0
    if w1 > 0:
        total += 1
        if w3 >= w1: score += 1
    if w2 > 0 and w4 > 0:
        total += 1
        if abs(w2-w4)/max(w2,w4) >= 0.15: score += 1
    if len(pivots) >= 6:
        w5 = abs(pivots[5]["price"]-pivots[4]["price"])
        if w3 > 0:
            total += 1
            if w5 <= w3 * 1.2: score += 1
    pct = score/total*100 if total > 0 else 50
    return pct >= 60, f"Symmetry {pct:.0f}%"

# ── BLUE BOX ──────────────────────────────────────────────────
def calc_blue_box(pivots, current):
    if len(pivots) < 3: return False, "No box"
    w1_range = abs(pivots[1]["price"]-pivots[0]["price"])
    direction = 1 if pivots[1]["price"] > pivots[0]["price"] else -1
    fib618 = pivots[1]["price"] - direction * w1_range * 0.618
    fib786 = pivots[1]["price"] - direction * w1_range * 0.786
    box_top = max(fib618, fib786)
    box_bot = min(fib618, fib786)
    in_w2_box = box_bot <= current <= box_top
    in_w4_box = False
    if len(pivots) >= 5:
        w3_range = abs(pivots[3]["price"]-pivots[2]["price"])
        dir3 = 1 if pivots[3]["price"] > pivots[2]["price"] else -1
        f382 = pivots[3]["price"] - dir3 * w3_range * 0.382
        f618 = pivots[3]["price"] - dir3 * w3_range * 0.618
        in_w4_box = min(f382,f618) <= current <= max(f382,f618)
    in_box = in_w2_box or in_w4_box
    label = "W2 Blue Box ✓" if in_w2_box else "W4 Blue Box ✓" if in_w4_box else "Outside Blue Box"
    return in_box, label

# ── SMI ───────────────────────────────────────────────────────
def calc_smi(prices, period=14):
    if len(prices) < period: return 0
    sl = prices[-period:]
    high = max(sl); low = min(sl)
    mid = (high+low)/2
    rng = high-low
    if rng == 0: return 0
    raw = ((prices[-1]-mid)/(rng/2))*100
    return raw

# ── TRUNCATED W5 ──────────────────────────────────────────────
def detect_truncated_w5(pivots, prices):
    if len(pivots) < 6: return False, "Need W5"
    w3_high = pivots[3]["price"]
    w5_high = pivots[5]["price"]
    truncated = w5_high < w3_high and w5_high > pivots[4]["price"]
    if truncated:
        return True, "⚠️ Truncated W5 — Reversal imminent — DO NOT ENTER"
    return False, "No truncation"

# ── SIGNAL ANALYSIS ───────────────────────────────────────────
def analyze(coin, signal_type="swing"):
    sym = coin["sym"]

    if signal_type=="swing":
        prices,vols = fetch_klines(sym,"1d",730)
        min_move=0.10
        sl_pct=SWING_SL; tp1=SWING_TP1; tp2=SWING_TP2; tp3=SWING_TP3; tp4=SWING_TP4
        min_score=12; max_score=22
        hold="Days to weeks"
    else:
        # Scalp: use 4h data for better wave detection
        prices,vols = fetch_klines(sym,"4h",168)  # 28 days of 4h
        min_move=0.04
        sl_pct=SCALP_SL; tp1=SCALP_TP1; tp2=SCALP_TP2; tp3=SCALP_TP3; tp4=SCALP_TP4
        min_score=8; max_score=12
        hold="4-8 hours max"

    if len(prices)<50: return None

    current=prices[-1]
    ath=max(prices)
    pct_ath=((current-ath)/ath)*100

    # Indicators
    rsi_val=calc_rsi(prices)
    _,_,h_curr,h_prev=calc_macd(prices)
    stoch=calc_stoch(prices)
    ewo=calc_ewo(prices)
    macd_cross=h_curr>0 and h_prev<=0
    macd_turn=h_curr>h_prev

    # Waves
    pivots=detect_pivots(prices,min_move)
    ew_ok,ew_issues=validate_ew(pivots)
    entry,w_ret=detect_entry(pivots)
    alt_ok,alt_note=check_alternation(pivots)
    candle_name,candle_bull=detect_candlestick(prices)
    diagonal=detect_diagonal(pivots,prices) if len(pivots)>=5 else False
    sym_ok,sym_note=check_wave_symmetry(pivots)
    inbox,box_label=calc_blue_box(pivots,current)
    smi=calc_smi(prices)
    trunc,trunc_note=detect_truncated_w5(pivots,prices) if len(pivots)>=6 else (False,"Need W5")

    # Volume
    avg_vol=sum(vols[-20:])/20 if len(vols)>=20 else 1
    vol_dec=(sum(vols[-5:])/5)<(sum(vols[-10:-5])/5) if len(vols)>=10 else False
    vol_exp=vols[-1]>avg_vol if vols else False

    # MA50
    ma50=sum(prices[-50:])/50 if len(prices)>=50 else current
    daily_bull=current>ma50 or pct_ath<-50

    if signal_type=="swing":
        checks={
            "daily_bull":    daily_bull,
            "ma50":          current>ma50,
            "wave_count":    len(pivots)>=5,
            "ew_valid":      ew_ok,
            "entry_zone":    entry!="",
            "price_level":   pct_ath<-40,
            "deep_level":    pct_ath<-60,
            "fib_level":     -80<pct_ath<-38,
            "rsi_ok":        rsi_val<45,
            "stoch_ok":      stoch<25,
            "macd_ok":       macd_cross or macd_turn,
            "ewo_ok":        ewo!=0,
            "vol_dec":       vol_dec,
            "vol_exp":       vol_exp,
            "abc_struct":    len(pivots)>=6,
            "alternation":   alt_ok,
            "candlestick":   candle_bull,
            "no_diagonal":   not diagonal,
            "wave_symmetry": sym_ok,
            "blue_box":      inbox,
            "smi_ok":        smi < -40,
            "no_trunc_w5":   not trunc,
        }
    else:
        checks={
            "daily_bull":    daily_bull,
            "wave_count":    len(pivots)>=4,
            "ew_valid":      ew_ok,
            "entry_zone":    entry!="",
            "rsi_ok":        rsi_val<50,
            "stoch_ok":      stoch<30,
            "macd_ok":       macd_cross or macd_turn,
            "vol_exp":       vol_exp,
            "candlestick":   candle_bull,
            "alternation":   alt_ok,
            "no_diagonal":   not diagonal,
            "not_overbought": rsi_val<70,
        }

    score=sum(checks.values())

    # Qualifications
    if score<min_score: return None
    if diagonal: return None
    if trunc: return None  # Never enter on truncated W5
    if not daily_bull and signal_type=="swing": return None
    if not(checks.get("rsi_ok") or checks.get("stoch_ok") or checks.get("macd_ok")):
        return None

    # Levels
    sl  = current*(1-sl_pct)
    t1  = current*(1+tp1)
    t2  = current*(1+tp2)
    t3  = current*(1+tp3)
    t4  = current*(1+tp4)

    if score>=int(max_score*0.85): conf="🔥 HIGH"
    elif score>=int(max_score*0.70): conf="⚡ MEDIUM-HIGH"
    else: conf="✳️ MEDIUM"

    return {
        "type":     signal_type.upper(),
        "sym":      sym,
        "tier":     coin["tier"],
        "current":  current,
        "ath":      ath,
        "pct_ath":  pct_ath,
        "entry":    entry,
        "w_ret":    w_ret,
        "score":    score,
        "max":      max_score,
        "conf":     conf,
        "rsi":      rsi_val,
        "stoch":    stoch,
        "macd_cross": macd_cross,
        "candle":   candle_name,
        "alt":      alt_note,
        "hold":     hold,
        "sl":sl,"tp1":t1,"tp2":t2,"tp3":t3,"tp4":t4,
    }

# ── FORMAT ────────────────────────────────────────────────────
def fp(p):
    if not p and p!=0: return"N/A"
    if p>=1000: return f"${p:,.0f}"
    if p>=1: return f"${p:.4f}"
    if p>=0.01: return f"${p:.5f}"
    return f"${p:.7f}"

def build_msg(sig):
    icon="⚡" if sig["type"]=="SCALP" else "📈"
    tp_labels=["(+3%)","+5%)","+8%)","+12%)"] if sig["type"]=="SCALP" else ["(+5%)","+10%)","+15%)","+20%)"]
    sl_label="(-3%)" if sig["type"]=="SCALP" else "(-5%)"
    return (
        f"{icon} <b>{sig['type']} - {sig['sym']}/USDT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>Entry:</b>  {fp(sig['current']*0.99)} – {fp(sig['current']*1.01)}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>TP1:</b>    {fp(sig['tp1'])}  {tp_labels[0]}\n"
        f"🎯 <b>TP2:</b>    {fp(sig['tp2'])}  ({tp_labels[1]}\n"
        f"🎯 <b>TP3:</b>    {fp(sig['tp3'])}  ({tp_labels[2]}\n"
        f"🎯 <b>TP4:</b>    {fp(sig['tp4'])}  ({tp_labels[3]}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔴 <b>SL:</b>     {fp(sig['sl'])}  {sl_label}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 {sig['entry'] or 'Setup'} | {sig['score']}/{sig['max']} | {sig['conf']}\n"
        f"📉 RSI:{sig['rsi']:.0f} Stoch:{sig['stoch']:.0f} | {sig['candle']}\n"
        f"⏱ Hold: {sig['hold']}\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"<i>Spot · Halal · Not financial advice</i>"
    )

# ── PRICE ALERT MONITOR ──────────────────────────────────────
def check_price_alerts():
    """Check all active trades for TP/SL hits every 5 minutes"""
    if not active_trades:
        return

    SEP = "\u2501" * 19

    for key, trade in list(active_trades.items()):
        if trade.get("closed"):
            continue

        sym = trade["sym"]
        sig_type = trade["type"]
        icon = "\u26a1" if sig_type == "SCALP" else "\U0001f4c8"

        try:
            prices, _ = fetch_klines(sym, "1m", 2)
            if not prices:
                continue
            current = prices[-1]
        except:
            continue

        entry = trade["entry"]
        sl    = trade["sl"]
        tp1   = trade["tp1"]
        tp2   = trade["tp2"]
        tp3   = trade["tp3"]
        tp4   = trade["tp4"]

        # SL hit
        if current <= sl and not trade.get("closed"):
            loss = (current-entry)/entry*100
            msg = (
                "\U0001f534 <b>STOP LOSS HIT - " + sym + "/USDT</b>\n" +
                SEP + "\n" +
                icon + " " + sig_type + " Signal Closed\n" +
                "\U0001f4c9 Price: " + fp(current) + "\n" +
                "\U0001f534 SL: " + fp(sl) + "\n" +
                "\U0001f4ca Entry was: " + fp(entry) + "\n" +
                "\U0001f4b8 Loss: " + f"{loss:.1f}%" + "\n" +
                SEP + "\n" +
                "<i>Exit full position. Wait for next signal.</i>"
            )
            send_msg(msg)
            active_trades[key]["closed"] = True
            continue

        # TP1 hit
        if current >= tp1 and not trade.get("hit_tp1"):
            profit = (current-entry)/entry*100
            msg = (
                "\U0001f3af <b>TP1 HIT - " + sym + "/USDT</b>\n" +
                SEP + "\n" +
                icon + " " + sig_type + " Signal\n" +
                "\U0001f4b0 Price: " + fp(current) + "\n" +
                "\u2705 TP1: " + fp(tp1) + " reached\n" +
                "\U0001f4ca Profit: +" + f"{profit:.1f}%" + "\n" +
                SEP + "\n" +
                "\U0001f449 Exit 25% of position\n" +
                "\U0001f3af Next target: TP2 " + fp(tp2) + "\n" +
                "\U0001f534 Move SL to entry: " + fp(entry)
            )
            send_msg(msg)
            active_trades[key]["hit_tp1"] = True
            active_trades[key]["sl"] = entry

        # TP2 hit
        if current >= tp2 and not trade.get("hit_tp2"):
            profit = (current-entry)/entry*100
            msg = (
                "\U0001f3af <b>TP2 HIT - " + sym + "/USDT</b>\n" +
                SEP + "\n" +
                icon + " " + sig_type + " Signal\n" +
                "\U0001f4b0 Price: " + fp(current) + "\n" +
                "\u2705 TP2: " + fp(tp2) + " reached\n" +
                "\U0001f4ca Profit: +" + f"{profit:.1f}%" + "\n" +
                SEP + "\n" +
                "\U0001f449 Exit 25% of position\n" +
                "\U0001f3af Next target: TP3 " + fp(tp3) + "\n" +
                "\U0001f534 Move SL to TP1: " + fp(tp1)
            )
            send_msg(msg)
            active_trades[key]["hit_tp2"] = True
            active_trades[key]["sl"] = tp1

        # TP3 hit
        if current >= tp3 and not trade.get("hit_tp3"):
            profit = (current-entry)/entry*100
            msg = (
                "\U0001f3af <b>TP3 HIT - " + sym + "/USDT</b>\n" +
                SEP + "\n" +
                icon + " " + sig_type + " Signal\n" +
                "\U0001f4b0 Price: " + fp(current) + "\n" +
                "\u2705 TP3: " + fp(tp3) + " reached\n" +
                "\U0001f4ca Profit: +" + f"{profit:.1f}%" + "\n" +
                SEP + "\n" +
                "\U0001f449 Exit 25% of position\n" +
                "\U0001f3af Final target: TP4 " + fp(tp4) + "\n" +
                "\U0001f534 Move SL to TP2: " + fp(tp2)
            )
            send_msg(msg)
            active_trades[key]["hit_tp3"] = True
            active_trades[key]["sl"] = tp2

        # TP4 hit
        if current >= tp4 and not trade.get("hit_tp4"):
            profit = (current-entry)/entry*100
            msg = (
                "\U0001f3c6 <b>TP4 HIT - " + sym + "/USDT</b>\n" +
                SEP + "\n" +
                icon + " " + sig_type + " Signal COMPLETE\n" +
                "\U0001f4b0 Price: " + fp(current) + "\n" +
                "\u2705 TP4: " + fp(tp4) + " reached\n" +
                "\U0001f4ca Full profit: +" + f"{profit:.1f}%" + "\n" +
                SEP + "\n" +
                "\U0001f449 Exit remaining position\n" +
                "\U0001f389 Trade complete! \u0627\u0644\u062d\u0645\u062f \u0644\u0644\u0647 \U0001f91f"
            )
            send_msg(msg)
            active_trades[key]["hit_tp4"] = True
            active_trades[key]["closed"] = True


# ── MAIN LOOP ─────────────────────────────────────────────────
def main():
    global scan_count
    total=len(HALAL_WATCHLIST)
    t1=[c["sym"] for c in HALAL_WATCHLIST if c["tier"]==1]
    t2=[c["sym"] for c in HALAL_WATCHLIST if c["tier"]==2]
    t3=[c["sym"] for c in HALAL_WATCHLIST if c["tier"]==3]

    print(f"🕌 SIGNALSYM Bot V3 - Binance API")
    print(f"📊 {total} halal coins | FREE & UNLIMITED")

    send_msg(
        f"🕌 <b>SIGNALSYM Bot V3 - Active</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Shariah-Compliant Coins Only\n"
        f"🔄 Powered by Binance API\n"
        f"💰 FREE · UNLIMITED · NO KEY NEEDED\n"
        f"📊 {total} coins monitored\n"
        f"⏱ Scanning every 15 minutes\n"
        f"📈 Swing + ⚡ Scalp signals\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⭐⭐⭐ T1 ({len(t1)}): {', '.join(t1[:8])}...\n"
        f"⭐⭐ T2 ({len(t2)}): {', '.join(t2[:8])}...\n"
        f"⭐ T3 ({len(t3)}): {', '.join(t3[:8])}...\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"بارك الله فيك 🤲"
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
                swing_key=sym+"_swing"
                sw=analyze(coin,"swing")
                if sw:
                    last=sent_signals.get(swing_key,0)
                    if time.time()-last<14400:
                        print("S(cd)",end=" ")
                    else:
                        print(f"📈{sw['score']}/{sw['max']}",end=" ")
                        send_msg(build_msg(sw))
                        sent_signals[swing_key]=time.time()
                        signals+=1
                        # Track trade for TP/SL alerts
                        active_trades[swing_key] = {
                            "sym": sym, "type": "SWING",
                            "entry": sw["current"],
                            "sl": sw["sl"], "tp1": sw["tp1"],
                            "tp2": sw["tp2"], "tp3": sw["tp3"],
                            "tp4": sw["tp4"],
                            "hit_tp1": False, "hit_tp2": False,
                            "hit_tp3": False, "hit_tp4": False,
                            "closed": False,
                            "time": time.time()
                        }
                        time.sleep(2)

                # SCALP
                scalp_key=sym+"_scalp"
                time.sleep(2)
                sc=analyze(coin,"scalp")
                if sc:
                    last=sent_signals.get(scalp_key,0)
                    if time.time()-last<7200:
                        print("SC(cd)")
                    else:
                        print(f"⚡{sc['score']}/{sc['max']}")
                        send_msg(build_msg(sc))
                        sent_signals[scalp_key]=time.time()
                        signals+=1
                        # Track trade for TP/SL alerts
                        active_trades[scalp_key] = {
                            "sym": sym, "type": "SCALP",
                            "entry": sc["current"],
                            "sl": sc["sl"], "tp1": sc["tp1"],
                            "tp2": sc["tp2"], "tp3": sc["tp3"],
                            "tp4": sc["tp4"],
                            "hit_tp1": False, "hit_tp2": False,
                            "hit_tp3": False, "hit_tp4": False,
                            "closed": False,
                            "time": time.time()
                        }
                        time.sleep(2)
                else:
                    print("–")

                time.sleep(3)

            except Exception as e:
                print(f"err:{e}")
                time.sleep(5)

        print(f"\n✅ Scan #{scan_count} - {signals} signal(s) - next in 15min")

        # Monitor active trades every 5 minutes
        print(f"  📊 Monitoring {len([t for t in active_trades.values() if not t.get('closed')])} active trades...")
        for _ in range(3):  # Check 3 times during the 15min wait
            time.sleep(300)  # Wait 5 minutes
            check_price_alerts()
        return  # Skip the sleep below since we already waited

        if scan_count%96==0:
            send_msg(
                f"💓 <b>Heartbeat</b>\n"
                f"Scans: {scan_count}\n"
                f"Coins: {total}\n"
                f"API: Binance (unlimited)\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
                f"الحمد لله 🤲"
            )

        # time.sleep(900) -- handled above in monitor loop

if __name__=="__main__":
    main()
