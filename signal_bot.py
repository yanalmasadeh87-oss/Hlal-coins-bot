import requests
import time
import math
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION — Set via environment variables or edit below
# ═══════════════════════════════════════════════════════════════════
# Option 1: Environment variables (recommended for GitHub/replit)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

# Option 2: Hardcode here (not recommended for public repos)
# TELEGRAM_TOKEN = "7975488031:AAH...your_token"
# CHAT_ID        = "8422276082"

BN_BASE        = "https://api.binance.com/api/v3"
TG_BASE        = None  # Set after token validation

# ═══════════════════════════════════════════════════════════════════
# HALAL WATCHLIST — Tier-based priority
# ═══════════════════════════════════════════════════════════════════
HALAL_WATCHLIST = [
    {"sym":"BTC","tier":1},{"sym":"ETH","tier":1},{"sym":"XRP","tier":1},
    {"sym":"SOL","tier":1},{"sym":"BNB","tier":1},{"sym":"ADA","tier":1},
    {"sym":"AVAX","tier":1},{"sym":"SUI","tier":1},{"sym":"HBAR","tier":1},
    {"sym":"NEAR","tier":1},{"sym":"DOT","tier":1},{"sym":"ICP","tier":1},
    {"sym":"FTM","tier":1},{"sym":"ETC","tier":1},{"sym":"WLD","tier":1},
    {"sym":"RENDER","tier":1},{"sym":"ATOM","tier":1},{"sym":"KAS","tier":1},
    {"sym":"FIL","tier":1},{"sym":"APT","tier":1},{"sym":"ARB","tier":1},
    {"sym":"VET","tier":1},{"sym":"SEI","tier":1},{"sym":"STX","tier":1},
    {"sym":"TIA","tier":1},{"sym":"GRT","tier":1},{"sym":"OP","tier":1},
    {"sym":"THETA","tier":1},
    {"sym":"XLM","tier":2},{"sym":"ALGO","tier":2},{"sym":"LTC","tier":2},
    {"sym":"TON","tier":2},{"sym":"LINK","tier":2},{"sym":"POL","tier":2},
    {"sym":"XTZ","tier":2},{"sym":"IOTA","tier":2},{"sym":"BCH","tier":2},
    {"sym":"IMX","tier":2},{"sym":"INJ","tier":2},{"sym":"FET","tier":2},
    {"sym":"OCEAN","tier":2},{"sym":"AKT","tier":2},{"sym":"AR","tier":2},
    {"sym":"HNT","tier":2},{"sym":"ONE","tier":2},{"sym":"ZIL","tier":2},
    {"sym":"QTUM","tier":2},{"sym":"DCR","tier":2},{"sym":"RVN","tier":2},
    {"sym":"EGLD","tier":2},{"sym":"FLOW","tier":2},{"sym":"ANKR","tier":2},
    {"sym":"STORJ","tier":2},{"sym":"BAND","tier":2},{"sym":"NMR","tier":2},
    {"sym":"GLM","tier":2},{"sym":"SKL","tier":2},{"sym":"CELO","tier":2},
    {"sym":"ROSE","tier":2},{"sym":"CTSI","tier":2},{"sym":"WAVES","tier":2},
    {"sym":"DGB","tier":2},
    {"sym":"GALA","tier":3},{"sym":"AXS","tier":3},{"sym":"SAND","tier":3},
    {"sym":"MANA","tier":3},{"sym":"ENJ","tier":3},{"sym":"CHZ","tier":3},
    {"sym":"ASTR","tier":3},{"sym":"BAT","tier":3},{"sym":"LPT","tier":3},
    {"sym":"AUDIO","tier":3},{"sym":"CVC","tier":3},{"sym":"POWR","tier":3},
    {"sym":"HOT","tier":3},
]

# ═══════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════════
sent_signals   = {}
sent_watches   = {}
scan_count     = 0
active_trades  = {}
market_ctx     = None
_ctx_history   = []
# Structure memory: remembers last structure per symbol to prevent flip-flopping
_structure_memory = {}  # key: "BTC_swing" → {"type":"IMPULSE","w2_low":95000,"since":timestamp}

# ═══════════════════════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════════════════════
def init_telegram():
    global TG_BASE
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("WARNING: Using placeholder Telegram token. Set your real token.")
        return False
    TG_BASE = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    return True

def send_msg(msg):
    if not TG_BASE:
        print(f"[NO TG] {msg[:80]}...")
        return
    try:
        requests.post(f"{TG_BASE}/sendMessage",
            json={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML","disable_web_page_preview":True},
            timeout=10)
    except Exception as e:
        print(f"  TG error: {e}")

# ═══════════════════════════════════════════════════════════════════
# DATA FETCH
# ═══════════════════════════════════════════════════════════════════
def fetch_klines_full(sym, interval="1d", limit=365):
    try:
        r = requests.get(f"{BN_BASE}/klines",
            params={"symbol":sym+"USDT","interval":interval,"limit":limit}, timeout=15)
        data = r.json()
        if not data or isinstance(data, dict):
            return [],[],[],[]
        prices=[float(k[4]) for k in data]
        highs=[float(k[2]) for k in data]
        lows=[float(k[3]) for k in data]
        vols=[float(k[5]) for k in data]
        return prices, highs, lows, vols
    except:
        return [],[],[],[]

def fetch_global_ath(sym):
    try:
        r = requests.get(f"{BN_BASE}/klines",
            params={"symbol":sym+"USDT","interval":"1w","limit":200}, timeout=15)
        data = r.json()
        if not data or isinstance(data, dict):
            return 0
        return max(float(k[2]) for k in data)
    except:
        return 0

# ═══════════════════════════════════════════════════════════════════
# MARKET CONTEXT (Alternative.me)
# ═══════════════════════════════════════════════════════════════════
def fetch_market_context():
    global _ctx_history
    try:
        r1 = requests.get("https://api.alternative.me/v2/global/", timeout=10)
        g = r1.json().get("data", {})
        btc_dom = float(g.get("bitcoin_percentage_of_market_cap", 50))
        total = float(g.get("quotes", {}).get("USD", {}).get("total_market_cap", 0))

        r2 = requests.get("https://api.alternative.me/v2/ticker/?limit=2&structure=array", timeout=10)
        t = r2.json().get("data", [])
        btc_mcap = float(t[0]["quotes"]["USD"]["market_cap"]) if len(t) > 0 else 0
        eth_mcap = float(t[1]["quotes"]["USD"]["market_cap"]) if len(t) > 1 else 0
        total3 = total - btc_mcap - eth_mcap if total > 0 else 0

        r3 = requests.get("https://api.alternative.me/fng/?limit=7", timeout=10)
        fng = r3.json().get("data", [])
        fg_now = int(fng[0]["value"]) if fng else 50
        fg_7d = int(fng[-1]["value"]) if len(fng) >= 7 else fg_now

        if fg_now <= 20: fg_zone = "EXTREME_FEAR"
        elif fg_now <= 40: fg_zone = "FEAR"
        elif fg_now <= 60: fg_zone = "NEUTRAL"
        elif fg_now <= 80: fg_zone = "GREED"
        else: fg_zone = "EXTREME_GREED"

        fg_trend = ("RISING" if fg_now > fg_7d + 3 else
                    "FALLING" if fg_now < fg_7d - 3 else "NEUTRAL")

        ctx = {
            "btc_dom": round(btc_dom, 2), "total": total, "total3": total3,
            "fg_now": fg_now, "fg_zone": fg_zone, "fg_trend": fg_trend
        }
        _ctx_history.append({"btc_dom": btc_dom, "total": total, "total3": total3, "ts": time.time()})
        if len(_ctx_history) > 48: _ctx_history.pop(0)

        def get_trend(key):
            if len(_ctx_history) < 4: return "NEUTRAL"
            old = _ctx_history[0][key]; new = _ctx_history[-1][key]
            if old == 0: return "NEUTRAL"
            chg = (new - old) / old * 100
            return "RISING" if chg > 1.5 else "FALLING" if chg < -1.5 else "NEUTRAL"

        ctx["btc_dom_trend"] = get_trend("btc_dom")
        ctx["total_trend"] = get_trend("total")
        ctx["total3_trend"] = get_trend("total3")
        print(f"  CTX: BTC.D={btc_dom:.1f}% FG={fg_now}({fg_zone}) TOTAL={ctx['total_trend']}")
        return ctx
    except Exception as e:
        print(f"  CTX failed: {e}")
        return None

def context_adjustment(sym, ctx):
    """Reduced penalties — max -20 instead of -40. Context is a filter, not a veto."""
    if not ctx: return 0
    adj = 0
    fg = ctx.get("fg_now", 50)
    # Fear/Greed: mild adjustment
    if fg <= 20: adj -= 15
    elif fg <= 35: adj -= 8
    elif fg >= 80: adj -= 3
    elif fg >= 60: adj += 5

    total_trend = ctx.get("total_trend", "NEUTRAL")
    if total_trend == "FALLING": adj -= 10
    elif total_trend == "RISING": adj += 5

    # Altcoin-specific adjustments
    if sym not in ("BTC", "ETH"):
        btc_dom = ctx.get("btc_dom", 50)
        btc_dom_trend = ctx.get("btc_dom_trend", "NEUTRAL")
        total3_trend = ctx.get("total3_trend", "NEUTRAL")
        if btc_dom > 55 and btc_dom_trend == "RISING": adj -= 8
        elif btc_dom < 45 and btc_dom_trend == "FALLING": adj += 5
        if total3_trend == "FALLING": adj -= 5
        elif total3_trend == "RISING": adj += 5

    return max(-20, min(+15, adj))


# ═══════════════════════════════════════════════════════════════════
# INDICATORS
# ═══════════════════════════════════════════════════════════════════
def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    ag = al = 0
    for i in range(1, period + 1):
        d = prices[i] - prices[i - 1]
        if d > 0: ag += d
        else: al += abs(d)
    ag /= period; al /= period
    for i in range(period, len(prices)):
        d = prices[i] - prices[i - 1]
        ag = (ag * 13 + (d if d > 0 else 0)) / 14
        al = (al * 13 + (abs(d) if d < 0 else 0)) / 14
    return 100 if al == 0 else 100 - (100 / (1 + ag / al))

def calc_ema(prices, period):
    if len(prices) < period: return []
    k = 2 / (period + 1)
    r = [sum(prices[:period]) / period]
    for p in prices[period:]:
        r.append(p * k + r[-1] * (1 - k))
    return r

def calc_macd(prices):
    if len(prices) < 35: return 0, 0, 0, 0
    ef = calc_ema(prices, 12)
    es = calc_ema(prices, 26)
    ml = [ef[i + 14] - es[i] for i in range(len(es))]
    if len(ml) < 9: return 0, 0, 0, 0
    sl = calc_ema(ml, 9)
    diff = len(ml) - len(sl)
    hist = [ml[i + diff] - sl[i] for i in range(len(sl))]
    h = hist[-1] if hist else 0
    ph = hist[-2] if len(hist) >= 2 else 0
    return ml[-1], sl[-1] if sl else 0, h, ph

def calc_stoch(prices, period=14):
    if len(prices) < period: return 50
    sl = prices[-period:]
    high = max(sl); low = min(sl)
    if high == low: return 50
    return (prices[-1] - low) / (high - low) * 100

def calc_smi(prices, period=14):
    if len(prices) < period: return 0
    result = []
    for i in range(period - 1, len(prices)):
        sl = prices[i - period + 1:i + 1]
        high = max(sl); low = min(sl)
        mid = (high + low) / 2
        rng = high - low
        result.append(((prices[i] - mid) / (rng / 2)) * 100 if rng > 0 else 0)
    smoothed = calc_ema(result, 3)
    return smoothed[-1] if smoothed else 0

def calc_atr(highs, lows, closes, period=14):
    if len(highs) < period + 1: return 0
    trs = []
    for i in range(1, len(highs)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        trs.append(tr)
    if len(trs) < period:
        return sum(trs) / len(trs) if trs else 0
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * 13 + trs[i]) / 14
    return atr

def calc_adx(highs, lows, closes, period=14):
    if len(highs) < period * 2:
        return {"adx": 0, "plus_di": 0, "minus_di": 0}
    trs = []; plus_dm = []; minus_dm = []
    for i in range(1, len(highs)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        up = highs[i] - highs[i - 1]
        dn = lows[i - 1] - lows[i]
        trs.append(tr)
        plus_dm.append(up if up > dn and up > 0 else 0)
        minus_dm.append(dn if dn > up and dn > 0 else 0)
    atr = p14 = m14 = 0
    for i in range(period):
        atr += trs[i]; p14 += plus_dm[i]; m14 += minus_dm[i]
    atr /= period; p14 /= period; m14 /= period
    for i in range(period, len(trs)):
        atr = (atr * 13 + trs[i]) / 14
        p14 = (p14 * 13 + plus_dm[i]) / 14
        m14 = (m14 * 13 + minus_dm[i]) / 14
    pd = 100 * p14 / atr if atr > 0 else 0
    md = 100 * m14 / atr if atr > 0 else 0
    dx = abs(pd - md) / (pd + md) * 100 if (pd + md) > 0 else 0
    return {"adx": dx, "plus_di": pd, "minus_di": md}

def calc_divergence(prices, period=30):
    if len(prices) < period: return {"bullish": False, "bearish": False}
    rsi_now = calc_rsi(prices[-period:])
    rsi_prev = calc_rsi(prices[-period * 2:-period]) if len(prices) >= period * 2 else rsi_now
    bullish = prices[-1] < prices[-period] * 0.99 and rsi_now > rsi_prev * 1.02
    bearish = prices[-1] > prices[-period] * 1.01 and rsi_now < rsi_prev * 0.98
    return {"bullish": bullish, "bearish": bearish}

# ═══════════════════════════════════════════════════════════════════
# VOLATILITY REGIME (V5)
# ═══════════════════════════════════════════════════════════════════
def detect_volatility_regime(prices, highs, lows):
    if len(prices) < 50:
        return {"type": "normal", "label": "Normal", "multiplier": 1.0, "atr": 0, "atr_pct": 0.04}
    atr = calc_atr(highs, lows, prices, 14)
    avg_p = sum(prices) / len(prices)
    atr_pct = atr / avg_p if avg_p > 0 else 0
    returns = [abs((prices[i] - prices[i - 1]) / prices[i - 1]) for i in range(1, len(prices))]
    avg_ret = sum(returns) / len(returns) if returns else 0
    var = sum((r - avg_ret) ** 2 for r in returns) / len(returns) if returns else 0
    std_dev = math.sqrt(var)
    if atr_pct > 0.08 or std_dev > 0.06:
        return {"type": "high", "label": "High Volatility", "multiplier": 1.5, "atr": atr, "atr_pct": atr_pct}
    if atr_pct < 0.02 or std_dev < 0.015:
        return {"type": "low", "label": "Low Volatility", "multiplier": 0.7, "atr": atr, "atr_pct": atr_pct}
    return {"type": "normal", "label": "Normal Volatility", "multiplier": 1.0, "atr": atr, "atr_pct": atr_pct}

# ═══════════════════════════════════════════════════════════════════
# ADAPTIVE PIVOTS (V5) — IMPROVED: better consolidation
# ═══════════════════════════════════════════════════════════════════
def detect_pivots_adaptive(prices, highs, lows, regime, mode="swing"):
    n = len(prices)
    atr_pct = regime.get("atr_pct", 0.04)
    # Tighter base window for cleaner pivots
    base_win = 5 if mode == "scalp" else max(3, min(15, int(n / (30 + atr_pct * 100))))
    win = max(3, round(base_win * regime["multiplier"]))
    # Higher min_move to filter noise in bull trends
    base_min = 0.05 if mode == "scalp" else 0.10
    min_move = base_min * regime["multiplier"]

    pivots = []
    for i in range(win, n - win):
        sl = prices[i - win:i + win + 1]
        mx = max(sl); mn = min(sl)
        if prices[i] == mx and prices[i] > prices[i - 1] and prices[i] > prices[i + 1]:
            s = abs(prices[i] - prices[i - win]) / prices[i - win] if prices[i - win] > 0 else 0
            pivots.append({"idx": i, "price": prices[i], "type": "peak", "strength": s})
        elif prices[i] == mn and prices[i] < prices[i - 1] and prices[i] < prices[i + 1]:
            s = abs(prices[i] - prices[i - win]) / prices[i - win] if prices[i - win] > 0 else 0
            pivots.append({"idx": i, "price": prices[i], "type": "trough", "strength": s})

    st = "trough" if prices[0] < prices[min(10, n - 1)] else "peak"
    pivots.insert(0, {"idx": 0, "price": prices[0], "type": st, "strength": 0})
    pivots.append({"idx": n - 1, "price": prices[-1], "type": "current", "strength": 0})

    # Consolidate same-type pivots, keeping the most extreme
    sig = [pivots[0]]
    for p in pivots[1:]:
        prev = sig[-1]
        if prev["type"] == p["type"]:
            if p["type"] == "peak" and p["price"] > prev["price"]:
                sig[-1] = p
            elif p["type"] == "trough" and p["price"] < prev["price"]:
                sig[-1] = p
            continue
        move = abs((p["price"] - prev["price"]) / prev["price"]) if prev["price"] > 0 else 0
        if move >= min_move:
            sig.append(p)

    # Filter tiny first waves (noise)
    if len(sig) >= 2:
        w1_size = abs(sig[1]["price"] - sig[0]["price"])
        if w1_size / prices[-1] * 100 < 6.0:
            sig = sig[:1] + [sig[-1]]

    return sig, win, min_move


# ═══════════════════════════════════════════════════════════════════
# TREND ANALYSIS (V5 enhanced)
# ═══════════════════════════════════════════════════════════════════
def analyze_trend(prices, weekly_prices, current):
    ma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current
    ma50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else current
    if len(weekly_prices) >= 200:
        ma200 = sum(weekly_prices[-200:]) / 200
    elif len(prices) >= 200:
        ma200 = sum(prices[-200:]) / 200
    else:
        ma200 = ma50

    e12 = calc_ema(prices, 12)
    e26 = calc_ema(prices, 26)
    ema12 = e12[-1] if e12 else current
    ema26 = e26[-1] if e26 else current

    momentum = (prices[-1] - prices[-10]) / prices[-10] * 100 if len(prices) >= 10 else 0

    score = 0
    if current > ma20: score += 20
    if current > ma50: score += 20
    if current > ma200: score += 25
    if ema12 > ema26: score += 15
    if momentum > 0: score += 10
    if len(prices) >= 25:
        slope = (ma20 - prices[-25]) / prices[-25] * 100
        if slope > 0: score += 10

    if score >= 85: label = "STRONG_UPTREND"
    elif score >= 60: label = "UPTREND"
    elif score <= 15: label = "STRONG_DOWNTREND"
    elif score <= 40: label = "DOWNTREND"
    else: label = "NEUTRAL"

    return {
        "score": score, "label": label, "ma20": ma20, "ma50": ma50, "ma200": ma200,
        "momentum": momentum, "bullish": score >= 60, "bearish": score <= 40,
        "ema12": ema12, "ema26": ema26
    }

# ═══════════════════════════════════════════════════════════════════
# MARKET PHASE — IMPROVED: clearer definitions
# ═══════════════════════════════════════════════════════════════════
def read_market_phase(prices, highs, lows, pivots, current, pct_ath):
    if len(prices) < 50: return "UNKNOWN"

    ma20 = sum(prices[-20:]) / 20
    ma50 = sum(prices[-50:]) / 50
    ma200 = sum(prices[-200:]) / 200 if len(prices) >= 200 else ma50

    peaks = [p for p in pivots if p["type"] == "peak"][-3:]
    troughs = [p for p in pivots if p["type"] == "trough"][-3:]

    hh = len(peaks) >= 2 and peaks[-1]["price"] > peaks[-2]["price"]
    hl = len(troughs) >= 2 and troughs[-1]["price"] > troughs[-2]["price"]
    lh = len(peaks) >= 2 and peaks[-1]["price"] < peaks[-2]["price"]
    ll = len(troughs) >= 2 and troughs[-1]["price"] < troughs[-2]["price"]

    in_correction = pct_ath < -20
    momentum = (prices[-1] - prices[-10]) / prices[-10] * 100 if len(prices) >= 10 else 0

    # Range detection
    if len(prices) >= 20:
        rh = max(prices[-20:]); rl = min(prices[-20:])
        in_range = (rh - rl) / rl * 100 < 12 if rl > 0 else False
    else:
        in_range = False

    # Priority order matters
    if lh and ll and current < ma50:
        return "DOWNTREND"
    if hh and hl and current > ma50 and current > ma200 and momentum > 5:
        return "IMPULSING"  # Strong uptrend with momentum
    if hh and hl and current > ma50:
        return "TRENDING_UP"  # Uptrend but not explosive
    if in_correction and (hh or hl):
        return "CORRECTING_WITHIN_UPTREND"  # Correction in larger uptrend
    if in_correction:
        return "CORRECTING"
    if in_range and not in_correction:
        return "RANGING"
    if current > ma50 and momentum > 5:
        return "TRENDING_UP"
    if current < ma50 and momentum < -5:
        return "TRENDING_DOWN"
    return "NEUTRAL"

# ═══════════════════════════════════════════════════════════════════
# HTF VALIDATION — IMPROVED: stricter
# ═══════════════════════════════════════════════════════════════════
def htf_validation(sym):
    try:
        w_prices, _, _, _ = fetch_klines_full(sym, "1w", 52)
        if len(w_prices) < 20:
            return True, "HTF: No weekly data"
        w_ma20 = sum(w_prices[-20:]) / 20
        w_ma50 = sum(w_prices[-50:]) / 50 if len(w_prices) >= 50 else w_ma20
        w_cur = w_prices[-1]
        w_mom = (w_prices[-1] - w_prices[-4]) / w_prices[-4] * 100 if len(w_prices) >= 4 else 0

        # Stricter: must be above weekly MA20 AND not deeply below MA50
        if w_cur < w_ma20 and w_cur < w_ma50 * 0.95:
            return False, f"HTF BLOCKED: Weekly bearish (price < MA20 & < MA50)"
        if w_mom < -20:
            return False, f"HTF BLOCKED: Weekly momentum -20%"
        trend = "bull" if w_cur > w_ma20 else "neutral" if w_cur > w_ma50 else "bear"
        return True, f"HTF OK: Weekly {trend}"
    except:
        return True, "HTF: Error — passing"

# ═══════════════════════════════════════════════════════════════════
# FIBONACCI & PATTERN TOOLS
# ═══════════════════════════════════════════════════════════════════
def calc_fib_retrace(pivots):
    if len(pivots) < 3: return 0, False, "No data"
    w1r = abs(pivots[1]["price"] - pivots[0]["price"])
    if w1r == 0: return 0, False, "Invalid W1"
    w2r = abs(pivots[2]["price"] - pivots[1]["price"])
    ret = w2r / w1r * 100
    valid = 38.2 <= ret <= 100
    if ret < 38.2: lbl = "Shallow"
    elif ret <= 50: lbl = "0.382 Fib"
    elif ret <= 61.8: lbl = "0.500 Fib"
    elif ret <= 78.6: lbl = "0.618 Golden"
    elif ret <= 100: lbl = "0.786 Deep"
    else: lbl = "W2>W1 Invalid"
    return ret, valid, lbl

def calc_c_equals_a(pivots, current):
    if len(pivots) < 4: return False, 0, 0, "Need more data"
    for i in range(len(pivots) - 4, -1, -1):
        p0 = pivots[i]; p1 = pivots[i + 1]; p2 = pivots[i + 2]; p3 = pivots[i + 3]
        if not (p0["type"] == "peak" and p1["type"] == "trough" and
                p2["type"] == "peak" and p3["type"] == "trough"):
            continue
        wa = abs(p0["price"] - p1["price"])
        if wa == 0: continue
        ct = p2["price"]; cat = ct - wa; ratio = (ct - current) / wa * 100
        prox = abs(current - cat) / max(abs(cat), 0.0001) * 100
        at = p1["idx"] - p0["idx"]; ctt = p3["idx"] - p2["idx"]
        tr = ctt / at * 100 if at > 0 else 0; te = 80 <= tr <= 120
        if prox <= 5 and te: return True, cat, ratio, "C=A Price+Time"
        if prox <= 5: return True, cat, ratio, "C=A Price"
        if 80 <= ratio <= 120: return True, cat, ratio, f"Near C=A ({ratio:.0f}%)"
        return False, cat, ratio, f"C=A at {cat:.6f}"
    return False, 0, 0, "No ABC found"


# ═══════════════════════════════════════════════════════════════════
# CLASSICAL PATTERNS (Rule 17) — IMPROVED
# ═══════════════════════════════════════════════════════════════════
def detect_classical_patterns(prices, pivots, current):
    if len(prices) < 30 or len(pivots) < 4: return None
    peaks = [p for p in pivots if p["type"] == "peak"]
    troughs = [p for p in pivots if p["type"] == "trough"]

    # Double Bottom — must be recent
    if len(troughs) >= 2:
        t1 = troughs[-2]; t2 = troughs[-1]
        if abs(t1["price"] - t2["price"]) / t1["price"] < 0.03:
            mid = [p for p in peaks if t1["idx"] < p["idx"] < t2["idx"]]
            if mid and current >= t2["price"] * 0.97:
                nk = mid[-1]["price"]
                return {
                    "type": "DOUBLE_BOTTOM", "label": "Double Bottom",
                    "entry_price": t2["price"], "target": nk + (nk - t2["price"]),
                    "score": 70, "recency_days": (len(prices) - t2["idx"]) / len(prices) * 365
                }

    # Double Top
    if len(peaks) >= 2:
        p1 = peaks[-2]; p2 = peaks[-1]
        if abs(p1["price"] - p2["price"]) / p1["price"] < 0.03:
            return {"type": "DOUBLE_TOP", "label": "Double Top", "score": 0}

    # Falling Wedge (bullish)
    if len(peaks) >= 3 and len(troughs) >= 3:
        ph = [peaks[-3]["price"], peaks[-2]["price"], peaks[-1]["price"]]
        tl = [troughs[-3]["price"], troughs[-2]["price"], troughs[-1]["price"]]
        hf = ph[0] > ph[1] > ph[2]
        lf = tl[0] > tl[1] > tl[2]
        conv = (ph[-1] - tl[-1]) < (ph[0] - tl[0]) * 0.7
        if hf and lf and conv:
            return {
                "type": "FALLING_WEDGE", "label": "Falling Wedge (Bullish)",
                "entry_price": current, "target": ph[0], "score": 65
            }

    return None

# ═══════════════════════════════════════════════════════════════════
# WXYXZ DETECTION
# ═══════════════════════════════════════════════════════════════════
def detect_wxyxz(pivots, current):
    if len(pivots) < 6: return False, 0, 0, ""
    best = None
    for i in range(len(pivots) - 6, -1, -1):
        if i + 5 >= len(pivots): continue
        p = pivots[i:i + 6]
        types = [x["type"] for x in p]
        if types != ["peak", "trough", "peak", "trough", "peak", "trough"]:
            continue
        x1p = abs(p[2]["price"] - p[1]["price"]); x1t = p[2]["idx"] - p[1]["idx"]
        x2p = abs(p[4]["price"] - p[3]["price"]); x2t = p[4]["idx"] - p[3]["idx"]
        if x1p == 0 or x1t == 0: continue
        if x1p / p[1]["price"] * 100 < 5 or x2p / p[3]["price"] * 100 < 5: continue
        ws = abs(p[1]["price"] - p[0]["price"]); ys = abs(p[3]["price"] - p[2]["price"])
        if x1p >= ws * 0.8 or x2p >= ys * 0.8: continue
        pr = x2p / x1p * 100; tr = x2t / x1t * 100 if x1t > 0 else 100
        if 85 <= pr <= 115 and 85 <= tr <= 115:
            z = p[5]["price"]; near = abs(current - z) / z * 100 <= 8
            best = (True, z, pr, f"WXYXZ X1=X2 ({pr:.0f}%|{tr:.0f}%)")
            if near: break
    return best if best else (False, 0, 0, "")

# ═══════════════════════════════════════════════════════════════════
# TREND CONTINUATION DETECTION — NEW: catches bull trends without 5 pivots
# ═══════════════════════════════════════════════════════════════════
def detect_trend_continuation(prices, highs, lows, pivots, current, trend, htf_prices):
    """
    Detects when price is in a strong trend continuation (Wave 3, parabolic, etc.)
    even when classic 5-wave impulse structure isn't visible.
    """
    if len(prices) < 30: return None

    # Check higher timeframe
    htf_bullish = False
    if len(htf_prices) >= 20:
        htf_ma20 = sum(htf_prices[-20:]) / 20
        htf_bullish = htf_prices[-1] > htf_ma20

    # Recent higher highs and higher lows
    recent_peaks = [p for p in pivots if p["type"] == "peak" and p["idx"] > len(prices) * 0.3]
    recent_troughs = [p for p in pivots if p["type"] == "trough" and p["idx"] > len(prices) * 0.3]

    if len(recent_peaks) < 2 or len(recent_troughs) < 2:
        return None

    hh = recent_peaks[-1]["price"] > recent_peaks[-2]["price"]
    hl = recent_troughs[-1]["price"] > recent_troughs[-2]["price"]

    if not (hh and hl):
        return None

    # ADX confirmation
    adx = calc_adx(highs, lows, prices, 14)
    if adx["adx"] < 20:
        return None

    # Momentum confirmation
    momentum = (prices[-1] - prices[-20]) / prices[-20] * 100 if len(prices) >= 20 else 0
    if momentum < 5:
        return None

    # Price above key MAs
    ma50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else current
    if current < ma50 * 0.98:
        return None

    # Determine sub-type based on structure
    if len(pivots) >= 5:
        # Could be W3 of impulse
        return {
            "type": "TREND_CONTINUATION",
            "sub_type": "IMPULSE_W3_LIKELY",
            "label": "Trend Continuation (W3/Parabolic)",
            "score": 75,
            "entry_wave": "W3 or Pullback",
            "entry_price": current,
            "htf_confirmed": htf_bullish,
            "reason": f"HH+HL, ADX={adx['adx']:.0f}, momentum={momentum:.1f}%"
        }
    else:
        # Early trend, fewer pivots
        return {
            "type": "TREND_CONTINUATION",
            "sub_type": "EARLY_TREND",
            "label": "Early Trend Continuation",
            "score": 65,
            "entry_wave": "Pullback to MA20",
            "entry_price": sum(prices[-20:]) / 20,
            "htf_confirmed": htf_bullish,
            "reason": f"HH+HL forming, ADX={adx['adx']:.0f}, momentum={momentum:.1f}%"
        }

# ═══════════════════════════════════════════════════════════════════
# STRUCTURE MEMORY — NEW: prevents flip-flopping
# ═══════════════════════════════════════════════════════════════════
def check_structure_memory(sym, sig_type, current, pivots):
    """
    Checks if we previously identified an impulse and price hasn't invalidated it.
    Returns the locked structure if still valid, None otherwise.
    """
    key = f"{sym}_{sig_type}"
    mem = _structure_memory.get(key)
    if not mem: return None

    # Memory expires after 30 days
    if time.time() - mem["since"] > 30 * 86400:
        return None

    # Check invalidation
    if mem["type"] == "IMPULSE":
        # W2 entry: invalidated if price breaks below W0 origin
        if mem.get("w0_origin") and current < mem["w0_origin"] * 0.99:
            return None  # Invalidated
        # W4 entry: invalidated if price breaks below W1 top
        if mem.get("w1_top") and current < mem["w1_top"] * 0.99:
            return None  # Invalidated
        # W3 in progress: invalidated if price breaks below last trough
        if mem.get("last_trough") and current < mem["last_trough"] * 0.97:
            return None  # Invalidated

    # Still valid — return locked structure
    return {
        "type": mem["type"],
        "sub_type": mem["sub_type"],
        "label": mem["label"],
        "score": min(mem["score"] + 5, 85),  # Confidence grows with time
        "entry_wave": mem["entry_wave"],
        "entry_price": mem["entry_price"],
        "locked": True,
        "reason": f"Locked structure from {mem['date']}: {mem['label']}"
    }

def update_structure_memory(sym, sig_type, structure, pivots):
    """Updates memory when a strong structure is detected."""
    key = f"{sym}_{sig_type}"
    if structure["score"] >= 70 and structure["type"] in ("IMPULSE", "TREND_CONTINUATION"):
        mem = {
            "type": structure["type"],
            "sub_type": structure.get("sub_type", ""),
            "label": structure["label"],
            "score": structure["score"],
            "entry_wave": structure.get("entry_wave", ""),
            "entry_price": structure.get("entry_price", 0),
            "since": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        # Store invalidation levels
        if len(pivots) >= 3:
            mem["w0_origin"] = pivots[0]["price"]
        if len(pivots) >= 2:
            peaks = [p for p in pivots if p["type"] == "peak"]
            if peaks: mem["w1_top"] = peaks[0]["price"]
        troughs = [p for p in pivots if p["type"] == "trough"]
        if troughs: mem["last_trough"] = troughs[-1]["price"]

        _structure_memory[key] = mem


# ═══════════════════════════════════════════════════════════════════
# MAIN STRUCTURE RECOGNIZER — FIXED
# Key changes:
# 1. Scans ALL history, finds MOST RECENT valid pattern (not oldest)
# 2. Phase can OVERRIDE structure type
# 3. Trend continuation is a PRIMARY candidate, not fallback
# 4. Structure memory prevents flip-flopping
# 5. All candidates scored, best wins
# ═══════════════════════════════════════════════════════════════════
def recognize_chart_structure(prices, highs, lows, pivots, current, pct_ath,
                                 rsi_val, macd_bull, vol_dec, vol_exp, stoch,
                                 trend, regime, phase, htf_prices, sym, sig_type):

    if len(pivots) < 4:
        return {"type": "UNKNOWN", "label": "Insufficient data", "confidence_score": 0,
                "sit_applicable": [], "sit_na": [], "phase": phase}

    # Check structure memory first
    mem = check_structure_memory(sym, sig_type, current, pivots)

    candidates = []

    def add_candidate(s):
        if not s or s.get("type") == "UNKNOWN":
            return
        # Score the candidate
        s["confidence_score"] = score_structure_v6(s, rsi_val, macd_bull, vol_dec, vol_exp, stoch, trend)
        candidates.append(s)

    # === CANDIDATE 1: Trend Continuation (NEW — primary, not fallback) ===
    trend_cont = detect_trend_continuation(prices, highs, lows, pivots, current, trend, htf_prices)
    if trend_cont:
        add_candidate(trend_cont)

    # === CANDIDATE 2: Classical Patterns ===
    classical = detect_classical_patterns(prices, pivots, current)
    if classical:
        if classical.get("type") == "DOUBLE_TOP":
            return {"type": "DOUBLE_TOP", "label": "Double Top — No Long Signal",
                    "confidence_score": 0, "sit_applicable": [], "sit_na": [], "phase": phase}
        add_candidate({
            "type": classical["type"], "label": classical["label"],
            "entry_wave": "Pattern completion", "entry_price": classical["entry_price"],
            "target": classical.get("target"), "score": classical["score"],
            "sit_applicable": ["rsi_ok", "macd_ok", "vol_exp"],
            "sit_na": ["fib_golden", "alternation", "wave_symmetry", "blue_box", "abc_struct"]
        })

    # === CANDIDATE 3: WXYXZ ===
    wx_ok, wx_price, wx_ratio, wx_label = detect_wxyxz(pivots, current)
    if wx_ok:
        add_candidate({
            "type": "WXYXZ", "label": "W-X-Y-X-Z Triple Combination",
            "entry_wave": "Wave Z", "entry_price": wx_price,
            "sit_applicable": ["rsi_ok", "macd_ok", "vol_exp"],
            "sit_na": ["fib_golden", "alternation", "wave_symmetry", "blue_box", "abc_struct", "ca_zone"]
        })

    # === CANDIDATE 4-6: EW Structures (scan ALL history, pick MOST RECENT) ===
    n = len(pivots)

    # Find most recent valid patterns
    best_w2 = None; best_w4 = None
    best_abc = None; best_flat = None; best_running = None

    for i in range(n - 6, -1, -1):
        if i + 5 >= n: continue
        p = pivots[i:i + 6]
        types = [x["type"] for x in p]

        # IMPULSE W2 (needs 6 pivots: trough,peak,trough,peak,trough,peak)
        if types == ["trough", "peak", "trough", "peak", "trough", "peak"]:
            w0 = p[0]["price"]; w1h = p[1]["price"]; w2l = p[2]["price"]
            w3h = p[3]["price"]; w4l = p[4]["price"]; w5h = p[5]["price"]
            w1 = w1h - w0
            if w1 <= 0 or w2l <= w0: continue
            w2_ret = (w1h - w2l) / w1
            if abs(current - w2l) / w2l > 0.08: continue
            _, fib_valid, fib_label = calc_fib_retrace(p[:3])
            score = 60 + (10 if 0.5 <= w2_ret <= 0.786 else 5 if w2_ret >= 0.382 else 0)
            cand = {
                "type": "EW_W2", "label": "Standard EW - W2 Entry",
                "entry_wave": "W2", "entry_price": w2l,
                "w1h": w1h, "w2l": w2l, "w3h": w3h, "w4l": w4l, "w5h": w5h,
                "w1": w1, "w2_ret": w2_ret, "fib_label": fib_label, "fib_valid": fib_valid,
                "score": score,
                "sit_applicable": ["fib_golden", "wave_symmetry", "rsi_ok", "macd_ok", "vol_dec", "vol_exp", "candlestick"],
                "sit_na": ["blue_box", "alternation", "wave_c_bottom", "ca_zone", "abc_struct", "wxyxz"],
                "recency": (n - p[2]["idx"]) / n  # How recent is the W2?
            }
            if not best_w2 or cand["recency"] < best_w2["recency"]:
                best_w2 = cand

        # IMPULSE W4 (needs 5 pivots: trough,peak,trough,peak,trough)
        if i + 4 < n and types[:5] == ["trough", "peak", "trough", "peak", "trough"]:
            p5 = pivots[i:i + 5]
            w0 = p5[0]["price"]; w1h = p5[1]["price"]; w2l = p5[2]["price"]
            w3h = p5[3]["price"]; w4l = p5[4]["price"]
            w1 = w1h - w0; w3 = w3h - w2l
            if w1 <= 0 or w3 <= 0 or w2l <= w0 or w3 < w1 or w4l <= w1h: continue
            w2_ret = (w1h - w2l) / w1; w4_ret = (w3h - w4l) / w3
            if abs(current - w4l) / w4l > 0.08: continue
            _, fib_valid, fib_label = calc_fib_retrace(p5[:3])
            bb_lo = w3h - w3 * 0.786; bb_hi = w3h - w3 * 0.618
            in_bb = bb_lo <= current <= bb_hi
            score = 55 + (10 if 0.236 <= w4_ret <= 0.382 else 5 if w4_ret <= 0.5 else 0) + (5 if in_bb else 0)
            cand = {
                "type": "EW_W4", "label": "Standard EW - W4 Entry",
                "entry_wave": "W4", "entry_price": w4l,
                "w1h": w1h, "w2l": w2l, "w3h": w3h, "w4l": w4l,
                "w1": w1, "w3": w3, "w2_ret": w2_ret, "w4_ret": w4_ret,
                "fib_label": fib_label, "fib_valid": fib_valid, "in_blue_box": in_bb,
                "score": score,
                "sit_applicable": ["fib_golden", "blue_box", "alternation", "wave_symmetry", "rsi_ok", "macd_ok", "vol_dec", "vol_exp", "candlestick"],
                "sit_na": ["wave_c_bottom", "ca_zone", "abc_struct", "wxyxz"],
                "recency": (n - p5[4]["idx"]) / n
            }
            if not best_w4 or cand["recency"] < best_w4["recency"]:
                best_w4 = cand

    # Add best EW patterns (most recent, not oldest)
    if best_w2: add_candidate(best_w2)
    if best_w4: add_candidate(best_w4)

    # === CANDIDATE 7-9: Correction patterns (scan ALL, pick most recent) ===
    # These require a completed 5-wave impulse BEFORE the correction
    for i in range(n - 6, -1, -1):
        if i + 5 >= n: continue
        p = pivots[i:i + 6]
        types = [x["type"] for x in p]

        if types != ["trough", "peak", "trough", "peak", "trough", "peak"]:
            continue

        w0 = p[0]["price"]; w1h = p[1]["price"]; w2l = p[2]["price"]
        w3h = p[3]["price"]; w4l = p[4]["price"]; w5h = p[5]["price"]
        w1 = w1h - w0
        if w1 <= 0 or w2l <= w0: continue
        w3 = w3h - w2l; w5 = w5h - w4l
        if w3 <= 0 or (w3 < w1 and w3 < w5) or w4l <= w1h or w5h <= w3h: continue

        w5_top = w5h
        post = [pv for pv in pivots if pv["idx"] > p[5]["idx"]]
        if not post: continue

        aP = next((pv for pv in post if pv["type"] == "trough"), None)
        if not aP: continue

        wa_bot = aP["price"]; wa_range = w5h - wa_bot
        if wa_range <= 0: continue

        postA = [pv for pv in post if pv["idx"] > aP["idx"]]
        bP = next((pv for pv in postA if pv["type"] == "peak"), None)
        if not bP: continue

        wb_top = bP["price"]; wb_ret = (wb_top - wa_bot) / wa_range

        postB = [pv for pv in post if pv["idx"] > bP["idx"]]
        cP = next((pv for pv in postB if pv["type"] == "trough"), None)
        wc_bot = cP["price"] if cP else current
        wc_range = wb_top - wc_bot
        c_vs_a = wc_range / wa_range if wa_range > 0 else 0

        # EXPANDED FLAT
        if wb_top > w5_top and c_vs_a >= 0.6:
            score = 55 + (10 if c_vs_a >= 0.8 else 5)
            add_candidate({
                "type": "EXPANDED_FLAT", "label": "Expanded Flat Correction",
                "entry_wave": "Wave C", "entry_price": wc_bot,
                "wa_bot": wa_bot, "wb_top": wb_top, "wc_bot": wc_bot,
                "w5_top": w5_top, "wa_range": wa_range,
                "c_progress": min(c_vs_a / 1.236 * 100, 100),
                "score": score,
                "sit_applicable": ["wave_c_bottom", "ca_zone", "abc_struct", "rsi_ok", "macd_ok", "vol_dec", "vol_exp"],
                "sit_na": ["fib_golden", "blue_box", "alternation", "wave_symmetry", "wxyxz"]
            })

        # RUNNING CORRECTION
        if 0.38 <= wb_ret <= 0.78 and wc_bot > wa_bot and c_vs_a >= 0.38:
            score = 50 + (10 if c_vs_a >= 0.6 else 5)
            add_candidate({
                "type": "RUNNING_CORRECTION", "label": "Running Correction (Bullish)",
                "entry_wave": "Wave C (Higher Low)", "entry_price": wc_bot,
                "wa_bot": wa_bot, "wb_top": wb_top, "wc_bot": wc_bot,
                "w5_top": w5_top, "wa_range": wa_range,
                "score": score,
                "sit_applicable": ["wave_c_bottom", "abc_struct", "rsi_ok", "macd_ok", "vol_dec", "vol_exp"],
                "sit_na": ["fib_golden", "blue_box", "ca_zone", "alternation", "wxyxz"]
            })

        # ABC ZIGZAG
        if 0.38 <= wb_ret <= 0.78 and c_vs_a >= 0.6:
            c_eq_a = wb_top - wa_range
            c_conf = abs(wc_bot - c_eq_a) / max(abs(c_eq_a), 0.0001) < 0.05
            score = 50 + (15 if c_conf else 8 if c_vs_a >= 0.8 else 5)
            add_candidate({
                "type": "ABC_ZIGZAG", "label": "ABC Zigzag Correction",
                "entry_wave": "Wave C", "entry_price": wc_bot,
                "wa_bot": wa_bot, "wb_top": wb_top, "wc_bot": wc_bot,
                "w5_top": w5_top, "wa_range": wa_range,
                "c_progress": c_vs_a * 100, "c_eq_a_tgt": c_eq_a, "c_confirmed": c_conf,
                "score": score,
                "sit_applicable": ["wave_c_bottom", "ca_zone", "abc_struct", "rsi_ok", "macd_ok", "vol_dec", "vol_exp"],
                "sit_na": ["fib_golden", "blue_box", "alternation", "wave_symmetry", "wxyxz"]
            })

        break  # Only process the most recent 5-wave + correction sequence

    # === PHASE OVERRIDE ===
    # If phase says IMPULSING or TRENDING_UP but best candidate is a correction,
    # check if it's really a correction or just a pullback
    if candidates:
        candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
        winner = candidates[0]

        # Override: if we're in a strong uptrend and the "correction" is shallow
        if phase in ("IMPULSING", "TRENDING_UP") and winner["type"] in ("ABC_ZIGZAG", "RUNNING_CORRECTION"):
            total_decline = abs((pivots[0]["price"] - current) / pivots[0]["price"]) if pivots[0]["price"] > 0 else 0
            if total_decline < 0.15:  # Less than 15% from start = not a real correction
                # Replace with trend continuation
                trend_cont = detect_trend_continuation(prices, highs, lows, pivots, current, trend, htf_prices)
                if trend_cont:
                    trend_cont["confidence_score"] = score_structure_v6(trend_cont, rsi_val, macd_bull, vol_dec, vol_exp, stoch, trend)
                    winner = trend_cont
                    candidates.insert(0, winner)

        # Override: if memory says we were in impulse and price hasn't broken invalidation
        if mem and mem["type"] in ("IMPULSE", "TREND_CONTINUATION"):
            mem["confidence_score"] = score_structure_v6(mem, rsi_val, macd_bull, vol_dec, vol_exp, stoch, trend)
            if mem["confidence_score"] >= winner.get("confidence_score", 0) * 0.85:
                winner = mem
                candidates.insert(0, winner)

    # === NO CANDIDATES ===
    if not candidates:
        # Last resort: if trend is strong, return TREND_CONTINUATION
        if trend["score"] >= 60 and phase in ("IMPULSING", "TRENDING_UP"):
            fallback = {
                "type": "TREND_CONTINUATION", "sub_type": "TREND_FALLBACK",
                "label": "Trend Continuation (Fallback)",
                "score": 55, "entry_wave": "Pullback", "entry_price": current,
                "reason": "No EW structure, but strong trend detected"
            }
            fallback["confidence_score"] = score_structure_v6(fallback, rsi_val, macd_bull, vol_dec, vol_exp, stoch, trend)
            return fallback

        return {"type": "UNKNOWN", "label": "No valid structure found", "confidence_score": 0,
                "sit_applicable": [], "sit_na": [], "phase": phase}

    # === PICK WINNER ===
    candidates.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
    winner = candidates[0]
    runner = candidates[1] if len(candidates) > 1 else None

    # Ambiguity check
    if runner:
        gap = winner.get("confidence_score", 0) - runner.get("confidence_score", 0)
        if gap < 8:
            winner["confidence_score"] = int(winner.get("confidence_score", 0) * 0.85)
            winner["ambiguous"] = True
            winner["alternate"] = runner.get("label", "")

    if runner and not winner.get("alternate"):
        winner["alternate"] = runner.get("label", "")

    winner["phase"] = phase
    winner["all_candidates"] = [(c.get("type", ""), c.get("confidence_score", 0)) for c in candidates]

    # Update memory if strong impulse/trend detected
    if winner["type"] in ("IMPULSE", "TREND_CONTINUATION") and winner.get("score", 0) >= 65:
        update_structure_memory(sym, sig_type, winner, pivots)

    return winner


# ═══════════════════════════════════════════════════════════════════
# SCORING ENGINE V6 — IMPROVED: trend continuation gets proper scoring
# ═══════════════════════════════════════════════════════════════════
def score_structure_v6(struct, rsi_val, macd_bull, vol_dec, vol_exp, stoch, trend):
    if not struct or struct.get("type") == "UNKNOWN":
        return 0

    t = struct.get("type", "UNKNOWN")
    score = 0

    # Base score by structure type
    sq = 0
    if t == "TREND_CONTINUATION":
        sq += 20  # High base for trend continuation
        if struct.get("sub_type") == "IMPULSE_W3_LIKELY": sq += 8
        elif struct.get("sub_type") == "EARLY_TREND": sq += 5
    elif t == "WXYXZ": sq += 18
    elif t in ("EXPANDED_FLAT", "RUNNING_CORRECTION"): sq += 14
    elif t in ("ABC_ZIGZAG", "EW_W4", "EW_W2"): sq += 10
    elif t in ("DOUBLE_BOTTOM", "FALLING_WEDGE"): sq += 8

    # Structure-specific bonuses
    if t == "ABC_ZIGZAG":
        cp = struct.get("c_progress", 0)
        sq += 10 if cp >= 90 else 6 if cp >= 70 else 3 if cp >= 50 else 0
    elif t == "EW_W4":
        w4r = struct.get("w4_ret", 0)
        sq += 10 if 0.23 <= w4r <= 0.38 else 6 if w4r <= 0.50 else 2
    elif t == "EW_W2":
        w2r = struct.get("w2_ret", 0)
        sq += 10 if 0.50 <= w2r <= 0.786 else 6 if w2r >= 0.382 else 2
    elif t == "TREND_CONTINUATION":
        if struct.get("htf_confirmed"): sq += 10
        sq += 8  # Trend continuation bonus
    else:
        sq += 8

    score += min(sq, 40)

    # EW rules validation bonus
    ew = 0
    if t in ("EW_W4", "EW_W2"):
        if struct.get("w2_ret", 0) <= 1.0: ew += 8
        if struct.get("w3", 1) >= struct.get("w1", 1): ew += 8
        ew += 9
    elif t == "TREND_CONTINUATION":
        ew += 25  # Trend continuation gets full EW bonus
    else:
        ew += 25
    score += min(ew, 25)

    # Fibonacci bonus
    fib = 0
    if t == "EW_W2":
        r = struct.get("w2_ret", 0)
        fib = 15 if 0.618 <= r <= 0.786 else 10 if r >= 0.5 else 7 if r >= 0.382 else 0
    elif t == "EW_W4":
        r = struct.get("w4_ret", 0)
        fib = 15 if 0.236 <= r <= 0.382 else 10 if r <= 0.5 else 5
    elif t == "ABC_ZIGZAG":
        fib = 15 if struct.get("c_confirmed") else 8
    elif t == "TREND_CONTINUATION":
        fib = 12  # Trend continuation gets fib bonus for momentum
    else:
        fib = 10
    score += min(fib, 15)

    # Volume
    vol = 0
    if vol_dec: vol += 5
    if vol_exp: vol += 5
    score += min(vol, 10)

    # Momentum
    mom = 0
    if rsi_val < 35: mom += 5
    elif rsi_val < 45: mom += 3
    if macd_bull: mom += 5
    elif stoch < 20: mom += 3
    score += min(mom, 10)

    # Trend alignment — IMPROVED: stronger bonus
    if trend["score"] >= 75: score = min(score + 10, 100)
    elif trend["score"] >= 60: score = min(score + 5, 100)
    elif trend["score"] <= 30: score = max(score - 10, 0)

    return min(score, 100)

# ═══════════════════════════════════════════════════════════════════
# ADAPTIVE RISK — IMPROVED: better SL logic for trend continuation
# ═══════════════════════════════════════════════════════════════════
def calculate_adaptive_risk(struct_type, sub_type, pivots, current, regime, atr,
                             sl_pct, tp1_pct, tp2_pct, tp3_pct, tp4_pct):
    atr_mult = 2.5 if regime["type"] == "high" else 1.5 if regime["type"] == "low" else 2.0
    max_sl = 0.08 if regime["type"] == "high" else 0.05
    sl = tp1 = tp2 = tp3 = tp4 = 0
    sl_reason = ""

    if struct_type == "TREND_CONTINUATION":
        # For trend continuation, SL is below the last significant trough or ATR-based
        troughs = [p for p in pivots if p["type"] == "trough"]
        if len(troughs) >= 2:
            sl = troughs[-2]["price"] * 0.98  # Below last significant trough
            tp1 = current + (current - sl) * 1.5
            tp2 = current + (current - sl) * 2.5
            tp3 = current + (current - sl) * 4.0
            tp4 = current + (current - sl) * 6.0
            sl_reason = "Below last significant trough (trend support)"
        else:
            sl = current - atr * atr_mult * 1.5
            tp1 = current + atr * atr_mult * 2.0
            tp2 = current + atr * atr_mult * 3.5
            tp3 = current + atr * atr_mult * 5.0
            tp4 = current + atr * atr_mult * 7.0
            sl_reason = f"ATR-based trend SL ({atr_mult:.1f}x * 1.5)"

    elif struct_type == "EW_W4" and len(pivots) >= 5:
        w1h = pivots[1]["price"]; w3h = pivots[3]["price"]
        w3r = w3h - pivots[2]["price"]
        sl = w1h * 0.99
        tp1 = w3h
        tp2 = w3h + w3r * 0.618
        tp3 = w3h + w3r * 1.0
        tp4 = w3h + w3r * 1.618
        sl_reason = "Below W1 Top (W4 overlap rule)"

    elif struct_type in ("ABC_ZIGZAG", "EXPANDED_FLAT", "RUNNING_CORRECTION"):
        troughs = [p for p in pivots if p["type"] == "trough"]
        peaks = [p for p in pivots if p["type"] == "peak"]
        if len(troughs) >= 2 and peaks:
            a_bot = troughs[-2]["price"]; b_top = peaks[-1]["price"]
            wa_rng = abs(b_top - a_bot)
            sl = a_bot * 0.985
            tp1 = b_top
            tp2 = b_top + wa_rng * 0.618
            tp3 = b_top + wa_rng * 1.0
            tp4 = b_top + wa_rng * 1.618
            sl_reason = "Below Wave A Bottom"
        else:
            sl = current * (1 - sl_pct)
            tp1 = current * (1 + tp1_pct)
            tp2 = current * (1 + tp2_pct)
            tp3 = current * (1 + tp3_pct)
            tp4 = current * (1 + tp4_pct)
            sl_reason = "Fixed % (fallback)"

    elif struct_type == "EW_W2" and len(pivots) >= 3:
        w0 = pivots[0]["price"]; w1h = pivots[1]["price"]
        w1r = w1h - w0
        sl = w0 * 1.01
        tp1 = w1h
        tp2 = w1h + w1r * 0.618
        tp3 = w1h + w1r * 1.0
        tp4 = w1h + w1r * 1.618
        sl_reason = "Below W0 Origin (W2 rule)"

    elif struct_type == "WXYXZ" and len(pivots) >= 4:
        troughs = [p for p in pivots if p["type"] == "trough"]
        peaks = [p for p in pivots if p["type"] == "peak"]
        sl = troughs[-1]["price"] * 0.98 if troughs else current * (1 - max_sl)
        tp1 = peaks[-1]["price"] if peaks else current * (1 + tp1_pct)
        rng = tp1 - sl
        tp2 = tp1 + rng * 0.618
        tp3 = tp1 + rng * 1.0
        tp4 = tp1 + rng * 1.618
        sl_reason = "Below Z-wave bottom"

    else:
        sl = current - atr * atr_mult
        tp1 = current + atr * atr_mult * 1.5
        tp2 = current + atr * atr_mult * 2.5
        tp3 = current + atr * atr_mult * 4.0
        tp4 = current + atr * atr_mult * 6.0
        sl_reason = f"ATR-based ({atr_mult:.1f}x)"

    # Cap SL
    if sl > 0 and (current - sl) / current > max_sl:
        sl = current * (1 - max_sl)
        sl_reason += f" (capped {max_sl * 100:.0f}%)"

    # Ensure TPs are progressive
    if tp1 <= current: tp1 = current * (1 + tp1_pct)
    if tp2 <= tp1: tp2 = current * (1 + tp2_pct)
    if tp3 <= tp2: tp3 = current * (1 + tp3_pct)
    if tp4 <= tp3: tp4 = current * (1 + tp4_pct)

    return sl, tp1, tp2, tp3, tp4, sl_reason

# ═══════════════════════════════════════════════════════════════════
# POSITION SIZING — NEW: based on score and volatility
# ═══════════════════════════════════════════════════════════════════
def calculate_position_size(score, regime, trend_label, is_mem_locked=False):
    """
    Returns position size as percentage of available capital.
    Higher scores + lower volatility = larger positions.
    """
    base = 0
    if score >= 85: base = 100
    elif score >= 75: base = 75
    elif score >= 65: base = 50
    elif score >= 55: base = 25
    else: base = 10

    # Volatility adjustment
    if regime["type"] == "high":
        base = int(base * 0.7)  # Reduce size in high vol
    elif regime["type"] == "low":
        base = int(base * 1.1)  # Slight increase in low vol

    # Trend strength bonus
    if trend_label == "STRONG_UPTREND":
        base = int(base * 1.15)
    elif trend_label == "DOWNTREND":
        base = int(base * 0.5)

    # Memory lock bonus (we've been tracking this structure)
    if is_mem_locked:
        base = int(base * 1.1)

    return min(base, 100)


# ═══════════════════════════════════════════════════════════════════
# MAIN ANALYSIS — IMPROVED
# ═══════════════════════════════════════════════════════════════════
def analyze(coin, signal_type="swing"):
    sym = coin["sym"]

    if signal_type == "swing":
        prices, highs, lows, vols = fetch_klines_full(sym, "1d", 730)
        sl_pct = 0.05; tp1_pct = 0.05; tp2_pct = 0.10; tp3_pct = 0.15; tp4_pct = 0.20
        min_score = 50; hold = "Days to weeks"
    else:
        prices, highs, lows, vols = fetch_klines_full(sym, "4h", 540)
        sl_pct = 0.03; tp1_pct = 0.03; tp2_pct = 0.05; tp3_pct = 0.08; tp4_pct = 0.12
        min_score = 45; hold = "1-3 days"

    if len(prices) < 50:
        return None

    current = prices[-1]
    global_ath = fetch_global_ath(sym)
    ath = global_ath if global_ath > 0 else max(prices)
    pct_ath = (current - ath) / ath * 100

    regime = detect_volatility_regime(prices, highs, lows)
    atr = regime.get("atr", calc_atr(highs, lows, prices))
    pivots, win, min_move = detect_pivots_adaptive(prices, highs, lows, regime, signal_type)
    phase = read_market_phase(prices, highs, lows, pivots, current, pct_ath)

    if phase == "DOWNTREND":
        return None

    rsi_val = calc_rsi(prices)
    _, _, h_curr, h_prev = calc_macd(prices)
    macd_bull = (h_curr > 0 and h_prev <= 0) or h_curr > h_prev
    stoch = calc_stoch(prices)
    smi = calc_smi(prices)
    div = calc_divergence(prices)

    # Adaptive RSI thresholds
    if phase == "CORRECTING":
        rsi_oversold = 35
    elif phase == "IMPULSING":
        rsi_oversold = 40
    elif regime["type"] == "high":
        rsi_oversold = 25
    elif regime["type"] == "low":
        rsi_oversold = 35
    else:
        rsi_oversold = 40

    # Volume analysis
    avg_vol = sum(vols[-20:]) / 20 if len(vols) >= 20 else 1
    vol_dec = (sum(vols[-5:]) / 5) < (sum(vols[-10:-5]) / 5) if len(vols) >= 10 else False
    vol_exp = vols[-1] > avg_vol if vols else False

    # Weekly prices for trend
    weekly_prices, _, _, _ = fetch_klines_full(sym, "1w", 52)
    trend = analyze_trend(prices, weekly_prices, current)

    # Daily bullish check
    in_correction = pct_ath < -20
    daily_bull = current > (sum(prices[-50:]) / 50 if len(prices) >= 50 else current) or in_correction
    if not daily_bull:
        return None

    # Structure recognition
    chart = recognize_chart_structure(
        prices, highs, lows, pivots, current, pct_ath,
        rsi_val, macd_bull, vol_dec, vol_exp, stoch,
        trend, regime, phase, weekly_prices, sym, signal_type
    )

    struct_type = chart.get("type", "UNKNOWN")
    struct_label = chart.get("label", "Unknown")
    sub_type = chart.get("sub_type", "")
    conf_score = chart.get("confidence_score", 0)

    if struct_type in ("DOWNTREND", "DOUBLE_TOP", "UNKNOWN"):
        return None

    # Context adjustment (reduced penalties)
    ctx_adj = context_adjustment(sym, market_ctx)
    final_score = max(0, min(100, conf_score + ctx_adj))

    if final_score < 35:
        return None

    # HTF validation
    htf_ok, htf_note = htf_validation(sym)
    if not htf_ok:
        print(f"    {htf_note}")
        return None

    # RSI filter
    if rsi_val > 75:
        return None

    # Risk calculation
    sl, tp1, tp2, tp3, tp4, sl_reason = calculate_adaptive_risk(
        struct_type, sub_type, pivots, current, regime, atr,
        sl_pct, tp1_pct, tp2_pct, tp3_pct, tp4_pct
    )

    # Position sizing
    is_locked = chart.get("locked", False)
    position_size = calculate_position_size(final_score, regime, trend["label"], is_locked)

    # Confidence label
    if final_score >= 85:
        conf = "HIGH"
    elif final_score >= 70:
        conf = "MEDIUM-HIGH"
    elif final_score >= 55:
        conf = "MEDIUM"
    else:
        conf = "DEVELOPING"

    if final_score < min_score:
        return {
            "watch": True, "type": signal_type.upper(), "sym": sym,
            "current": current, "score": final_score, "rsi": rsi_val, "stoch": stoch,
            "struct_label": struct_label, "struct_type": struct_type,
            "position_size": position_size,
            "reason": f"Developing — {struct_label} (score {final_score}/100)"
        }

    return {
        "type": signal_type.upper(), "sym": sym, "tier": coin["tier"],
        "current": current, "ath": ath, "pct_ath": pct_ath,
        "score": final_score, "conf_score": conf_score, "ctx_adj": ctx_adj,
        "conf": conf, "rsi": rsi_val, "stoch": stoch, "hold": hold,
        "sl": sl, "tp1": tp1, "tp2": tp2, "tp3": tp3, "tp4": tp4,
        "sl_reason": sl_reason, "struct_type": struct_type, "struct_label": struct_label,
        "sub_type": sub_type,
        "regime": regime["label"], "phase": phase, "trend": trend["label"],
        "divergence": div["bullish"],
        "position_size": position_size,
        "is_locked": is_locked
    }

# ═══════════════════════════════════════════════════════════════════
# FORMATTING
# ═══════════════════════════════════════════════════════════════════
def fp(p):
    if not p and p != 0:
        return "N/A"
    if p >= 1000:
        return "$" + f"{round(p):,}"
    if p >= 1:
        return "$" + f"{p:.4f}"
    if p >= 0.01:
        return "$" + f"{p:.5f}"
    return "$" + f"{p:.7f}"

def build_msg(sig):
    is_sc = sig["type"] == "SCALP"
    icon = "⚡" if is_sc else "📈"
    pos = sig.get("position_size", 50)
    pos_str = f"{pos}% Position" if pos < 100 else "Full Position"

    locked = "🔒 " if sig.get("is_locked") else ""

    msg = (
        f"{icon} <b>{locked}{sig['type']} — {sig['sym']}/USDT</b>

"
        f"📊 Structure: {sig['struct_label']}
"
        f"📈 Trend: {sig['trend']} | Phase: {sig['phase']}
"
        f"📏 Position: {pos_str}

"
        f"💵 Entry:  {fp(sig['current'] * 0.99)} – {fp(sig['current'] * 1.01)}
"
        f"🛑 SL:     {fp(sig['sl'])}
"
        f"   ({sig['sl_reason']})

"
        f"🎯 TP1:   {fp(sig['tp1'])}
"
        f"🎯 TP2:   {fp(sig['tp2'])}
"
        f"🎯 TP3:   {fp(sig['tp3'])}
"
        f"🎯 TP4:   {fp(sig['tp4'])}

"
        f"⏱ Hold: {sig['hold']}
"
        f"⚡ Score: {sig['score']}/100 — {sig['conf']}
"
        f"📊 RSI: {sig['rsi']:.0f} | Stoch: {sig['stoch']:.0f}
"
        f"🌊 Regime: {sig['regime']}
"
    )

    if sig.get("divergence"):
        msg += "🔄 Bullish Divergence detected
"

    if sig.get("alternate"):
        msg += f"⚠️ Alternate: {sig['alternate']}
"

    return msg

def build_watch_msg(sym, sig_type, current, score, rsi, struct_label, reason, position_size=0):
    icon = "⚡" if sig_type == "SCALP" else "📈"
    return (
        f"👁 <b>WATCH — {sym}/USDT ({sig_type})</b>

"
        f"Pattern: {struct_label}
"
        f"Price: {fp(current)} | RSI: {rsi:.0f}
"
        f"Score: {score}/100 | Suggested: {position_size}%
"
        f"Status: {reason}

"
        f"<i>Not a signal yet — monitoring</i>"
    )

# ═══════════════════════════════════════════════════════════════════
# PRICE ALERTS
# ═══════════════════════════════════════════════════════════════════
def check_price_alerts():
    if not active_trades:
        return

    for key, trade in list(active_trades.items()):
        if trade.get("closed"):
            continue

        sym = trade["sym"]
        sig_type = trade["type"]
        icon = "⚡" if sig_type == "SCALP" else "📈"

        try:
            prices, _, _, _ = fetch_klines_full(sym, "1m", 2)
            if not prices:
                continue
            current = prices[-1]
        except:
            continue

        entry = trade["entry"]
        sl = trade["sl"]
        tp1 = trade["tp1"]
        tp2 = trade["tp2"]
        tp3 = trade["tp3"]
        tp4 = trade["tp4"]

        # Stop Loss
        if current <= sl and not trade.get("closed"):
            loss = (current - entry) / entry * 100
            send_msg(
                f"🔴 <b>STOP LOSS — {sym}/USDT</b>
"
                f"{icon} {sig_type} Closed
"
                f"Price: {fp(current)} | SL: {fp(sl)}
"
                f"Loss: {loss:.1f}%
"
                f"<i>Exit full position.</i>"
            )
            active_trades[key]["closed"] = True
            continue

        # TP1
        if current >= tp1 and not trade.get("hit_tp1"):
            profit = (current - entry) / entry * 100
            send_msg(
                f"🎯 <b>TP1 HIT — {sym}/USDT</b>
"
                f"Price: {fp(current)}
"
                f"Profit: +{profit:.1f}%
"
                f"Exit 25% | SL → entry: {fp(entry)}"
            )
            active_trades[key]["hit_tp1"] = True
            active_trades[key]["sl"] = entry

        # TP2
        if current >= tp2 and not trade.get("hit_tp2"):
            profit = (current - entry) / entry * 100
            send_msg(
                f"🎯 <b>TP2 HIT — {sym}/USDT</b>
"
                f"Price: {fp(current)}
"
                f"Profit: +{profit:.1f}%
"
                f"Exit 25% | SL → TP1: {fp(tp1)}"
            )
            active_trades[key]["hit_tp2"] = True
            active_trades[key]["sl"] = tp1

        # TP3
        if current >= tp3 and not trade.get("hit_tp3"):
            profit = (current - entry) / entry * 100
            send_msg(
                f"🎯 <b>TP3 HIT — {sym}/USDT</b>
"
                f"Price: {fp(current)}
"
                f"Profit: +{profit:.1f}%
"
                f"Exit 25% | SL → TP2: {fp(tp2)}"
            )
            active_trades[key]["hit_tp3"] = True
            active_trades[key]["sl"] = tp2

        # TP4
        if current >= tp4 and not trade.get("hit_tp4"):
            profit = (current - entry) / entry * 100
            send_msg(
                f"🏆 <b>TP4 HIT — {sym}/USDT</b>
"
                f"Price: {fp(current)}
"
                f"Full profit: +{profit:.1f}%! | Trade complete!"
            )
            active_trades[key]["hit_tp4"] = True
            active_trades[key]["closed"] = True

# ═══════════════════════════════════════════════════════════════════
# WATCH MONITOR
# ═══════════════════════════════════════════════════════════════════
def monitor_watch_coins():
    if not sent_watches:
        return

    now = time.time()
    for key, watch_time in list(sent_watches.items()):
        if now - watch_time > 21600:  # 6 hours
            continue

        sym = key.split("_")[0]
        sig_type = "scalp" if "scalp" in key else "swing"
        coin = next((c for c in HALAL_WATCHLIST if c["sym"] == sym), None)
        if not coin:
            continue

        try:
            result = analyze(coin, sig_type)
            if not result or result.get("watch"):
                continue

            signal_key = sym + "_" + sig_type
            cooldown = 14400 if sig_type == "swing" else 7200
            if time.time() - sent_signals.get(signal_key, 0) < cooldown:
                continue

            print(f"  WATCH→SIGNAL: {sym} {sig_type.upper()} {result['score']}/100")
            send_msg(build_msg(result))
            sent_signals[signal_key] = now
            active_trades[signal_key] = {
                "sym": sym, "type": sig_type.upper(), "entry": result["current"],
                "sl": result["sl"], "tp1": result["tp1"], "tp2": result["tp2"],
                "tp3": result["tp3"], "tp4": result["tp4"],
                "hit_tp1": False, "hit_tp2": False, "hit_tp3": False, "hit_tp4": False,
                "closed": False, "time": now
            }
        except Exception as e:
            print(f"  Watch error {sym}: {e}")

        time.sleep(1)


# ═══════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════
def main():
    global scan_count, market_ctx

    # Initialize Telegram
    tg_ok = init_telegram()

    total = len(HALAL_WATCHLIST)
    t1 = [c["sym"] for c in HALAL_WATCHLIST if c["tier"] == 1]
    t2 = [c["sym"] for c in HALAL_WATCHLIST if c["tier"] == 2]
    t3 = [c["sym"] for c in HALAL_WATCHLIST if c["tier"] == 3]

    print(f"╔══════════════════════════════════════════════════════════════╗")
    print(f"║  EW STRATEGY V6 — ADAPTIVE STRUCTURE-AWARE BOT               ║")
    print(f"║  {total} coins | Trend continuation enabled | Memory locks     ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")

    if tg_ok:
        send_msg(
            f"🕒 <b>EW Strategy V6 — Active</b>
"
            f"━━━━━━━━━━━━━━━━━━━
"
            f"✅ Adaptive — Chart decides the method
"
            f"📊 Volatility regime detection
"
            f"🔄 Trend continuation detection (NEW)
"
            f"🔒 Structure memory (anti flip-flop)
"
            f"📈 HTF weekly validation
"
            f"💰 Position sizing by score & vol
"
            f"━━━━━━━━━━━━━━━━━━━
"
            f"⭐⭐⭐ T1 ({len(t1)}): {', '.join(t1[:8])}...
"
            f"⭐⭐ T2 ({len(t2)}): {', '.join(t2[:8])}...
"
            f"⭐ T3 ({len(t3)}): {', '.join(t3[:8])}..."
        )
    else:
        print("Telegram not configured — running in console-only mode.")

    while True:
        scan_count += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"
[{now}] Scan #{scan_count}")

        market_ctx = fetch_market_context()
        signals = 0
        watches = 0

        for coin in HALAL_WATCHLIST:
            sym = coin["sym"]
            print(f"  {sym}...", end=" ", flush=True)

            try:
                # SWING analysis
                swing_key = sym + "_swing"
                sw = analyze(coin, "swing")

                if sw:
                    if sw.get("watch"):
                        wk = sym + "_watch_swing"
                        if time.time() - sent_watches.get(wk, 0) < 7200:
                            print("W(cd)", end=" ")
                        else:
                            print(f"W{sw['score']}", end=" ")
                            pos = sw.get("position_size", 0)
                            send_msg(build_watch_msg(sym, "SWING", sw["current"], sw["score"], sw["rsi"], sw["struct_label"], sw["reason"], pos))
                            sent_watches[wk] = time.time()
                            watches += 1
                    else:
                        if time.time() - sent_signals.get(swing_key, 0) < 14400:
                            print("S(cd)", end=" ")
                        else:
                            print(f"{sw['score']}/100[{sw.get('struct_type', '')}]", end=" ")
                            send_msg(build_msg(sw))
                            sent_signals[swing_key] = time.time()
                            signals += 1
                            active_trades[swing_key] = {
                                "sym": sym, "type": "SWING", "entry": sw["current"],
                                "sl": sw["sl"], "tp1": sw["tp1"], "tp2": sw["tp2"],
                                "tp3": sw["tp3"], "tp4": sw["tp4"],
                                "hit_tp1": False, "hit_tp2": False, "hit_tp3": False, "hit_tp4": False,
                                "closed": False, "time": time.time()
                            }
                            time.sleep(2)
                else:
                    print("-", end=" ")

                # SCALP analysis
                scalp_key = sym + "_scalp"
                sc = analyze(coin, "scalp")

                if sc:
                    if sc.get("watch"):
                        wk = sym + "_watch_scalp"
                        if time.time() - sent_watches.get(wk, 0) < 3600:
                            print("WS(cd)")
                        else:
                            print(f"WS{sc['score']}")
                            pos = sc.get("position_size", 0)
                            send_msg(build_watch_msg(sym, "SCALP", sc["current"], sc["score"], sc["rsi"], sc["struct_label"], sc["reason"], pos))
                            sent_watches[wk] = time.time()
                            watches += 1
                    else:
                        if time.time() - sent_signals.get(scalp_key, 0) < 7200:
                            print("SC(cd)")
                        else:
                            print(f"{sc['score']}/100[{sc.get('struct_type', '')}]")
                            send_msg(build_msg(sc))
                            sent_signals[scalp_key] = time.time()
                            signals += 1
                            active_trades[scalp_key] = {
                                "sym": sym, "type": "SCALP", "entry": sc["current"],
                                "sl": sc["sl"], "tp1": sc["tp1"], "tp2": sc["tp2"],
                                "tp3": sc["tp3"], "tp4": sc["tp4"],
                                "hit_tp1": False, "hit_tp2": False, "hit_tp3": False, "hit_tp4": False,
                                "closed": False, "time": time.time()
                            }
                            time.sleep(2)
                else:
                    print("-")

                time.sleep(1)

            except Exception as e:
                print(f"err:{e}")
                time.sleep(5)

        print(f"
Scan #{scan_count} — {signals} signal(s), {watches} watch(es) — next in 15min")
        active_count = len([t for t in active_trades.values() if not t.get("closed")])
        print(f"  Active trades: {active_count} | Watch list: {len(sent_watches)}")

        # Price alerts and watch monitoring during the 15-min wait
        for _ in range(3):
            time.sleep(300)  # 5 minutes
            check_price_alerts()
            if sent_watches:
                monitor_watch_coins()

        # Heartbeat every 96 scans (24 hours)
        if scan_count % 96 == 0:
            send_msg(
                f"💓 <b>Heartbeat</b>
"
                f"Scans: {scan_count} | Coins: {total}
"
                f"Active: {active_count}
"
                f"{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC"
            )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("

Bot stopped by user.")
    except Exception as e:
        print(f"

Fatal error: {e}")
        import traceback
        traceback.print_exc()
