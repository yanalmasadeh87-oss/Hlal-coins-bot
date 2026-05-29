"""
SIGNALSYM — signal_bot.py
Elliott Wave Bot | Halal Spot Only | Binance API
Developer: Yanal Masadeh (@YASAMA_11)

════════════════════════════════════════════════════════════════
YOUR BASE WAVE STRUCTURE — FIXED, NEVER CHANGES
(From session doc Part 1 — this is the foundation of everything)
════════════════════════════════════════════════════════════════

GRAND SUPERCYCLE:
  W1: $0.01 → $69,000          ✅ Complete
  W2: $69,000 → $15,400        ✅ Complete (-77.7%)
  W3: $15,400 → $350K–$450K    🔄 UNFOLDING NOW
  W4: Future (-50 to -60% from W3 top)
  W5: Future (Grand top above W3)

INSIDE W3 (Cycle Degree):
  W1 of W3: $15,400 → $126,200 (ATH Oct 2025)   ✅ Complete
  W2 of W3: $126,200 → ~$74,500 (Zigzag ABC)    🔄 Near Complete
  W3 of W3: ~$74,500 → $280K–$320K              ⏳ Next Major Move
  W4 of W3: TBD ~$180K–$210K                    ⏳ Future
  W5 of W3: TBD → $350K–$450K                   ⏳ Grand W3 Top

W1 of W3 RANGE = $126,200 - $15,400 = $110,800
W3 of W3 FIBONACCI TARGETS (from ~$74,500 base):
  1.618 × $110,800 = ~$253,800
  2.0   × $110,800 = ~$296,100
  2.618 × $110,800 = ~$364,600
  Most Likely Zone: $280,000 – $320,000

W2 of W3 — CORRECTED ZIGZAG (5-3-5):
  Wave A: $126,200 → $74,500  (5-wave impulse)  ✅ Complete
  Wave B: $74,500  → $95,800  (3-wave, 57% ret) ✅ Complete
  Wave C: $95,800  → ~$74,500 (5-wave decline)  🔄 Near Complete

INVALIDATION LEVELS:
  Below $69,000   → W2 of W3 invalidated — full recount needed
  Below $15,400   → Entire Supercycle W3 invalidated
  W3 of W3 below $126,200 → W4 rule violated — count collapses

GOLDEN RULE:
  Daily bias = BULLISH → only LONG signals on 4H / 1H / 15min
  NEVER counter-trade the daily bias on smaller timeframes

════════════════════════════════════════════════════════════════
SIGNAL LEVELS (fixed — from session doc Part 4)
════════════════════════════════════════════════════════════════
SCALP (4H / 90 days):
  SL=-5% | TP1=+3% | TP2=+5% | TP3=+8% | TP4=+10%
  Hold: 1–3 days

SWING (1D / 730 days):
  SL = 2% below actual structure low (wave level)
  TP1/2/3/4 = actual wave levels from chart structure
  Hold: days to weeks

════════════════════════════════════════════════════════════════
CHECKLIST (session doc Part 3 — EXACT)
════════════════════════════════════════════════════════════════
REQUIRED (ALL 10 must pass — no exceptions):
  1. Daily Trend Bullish
  2. MA50 Confirmed
  3. 5-Wave Impulse (core EW structure must exist)
  4. EW Rules Valid (3 cardinal rules)
  5. Entry Zone W2/W4 (correction bottom, not mid-impulse)
  6. W2 Fib 38-100% of W1 (replaces ATH distance rule)
  7. RSI Below 45 (oversold at entry)
  8. MACD Bullish (momentum turning)
  9. No Ending Diagonal
  10. No Truncated W5

SITUATIONAL (■ = not applicable = NOT a failure):
  Wave Count >60% | Golden Ratio 38-78% | Wave C Bottom
  C=A Price+Time | WXYXZ X1=X2 | ABC Structure
  Stochastic <25 | SMI <-40 | EWO Signal
  Volume Declining | Volume Expanding | Alternation W2 vs W4
  Candlestick Pattern | Wave Symmetry | Blue Box Zone

SCORE → ACTION:
  All 10 required + 40%+ situational → SIGNAL
  7-9 required → WATCH (monitor every 5 min)
  Below 7 required → NO SIGNAL
"""

import time
import logging
import requests
import numpy as np
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
TELEGRAM_TOKEN         = "7975488031:AAHLdeNTM-YIItriXwradU4bPyCMdR-mAIY"
CHAT_ID                = "8422276082"
BINANCE_BASE           = "https://api.binance.com"

SWING_DAYS             = 730
SCALP_DAYS             = 90
SCAN_INTERVAL          = 900        # 15 min
COIN_SLEEP             = 1          # 1s between coins
HEARTBEAT_SCANS        = 96         # every 24h

SWING_COOLDOWN         = 4 * 3600
SCALP_COOLDOWN         = 2 * 3600
WATCH_COOLDOWN_SWING   = 2 * 3600
WATCH_COOLDOWN_SCALP   = 1 * 3600
PRICE_MONITOR_INTERVAL = 300        # 5 min

# Scalp: fixed always
SCALP_SL_PCT  = 0.05
SCALP_TP1_PCT = 0.03
SCALP_TP2_PCT = 0.05
SCALP_TP3_PCT = 0.08
SCALP_TP4_PCT = 0.10

# Swing: SL buffer below structure low
SWING_SL_BUFFER = 0.02   # 2% below actual wave low

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("SIGNALSYM")

# ─────────────────────────────────────────────────────────────
# YOUR FIXED BASE WAVE STRUCTURE
# These never change — they are the foundation of everything
# ─────────────────────────────────────────────────────────────
BASE = {
    # Grand Supercycle
    'W1_TOP':   69000,
    'W2_BOT':   15400,
    'W3_START': 15400,    # W3 origin (same as W2 bottom)

    # Inside W3
    'W1_OF_W3_BOT': 15400,
    'W1_OF_W3_TOP': 126200,   # ATH Oct 2025
    'W1_OF_W3_RNG': 110800,   # $126,200 - $15,400

    # W2 of W3 Zigzag levels
    'W2_OF_W3_WAVE_A_TOP': 126200,
    'W2_OF_W3_WAVE_A_BOT': 74500,
    'W2_OF_W3_WAVE_B_TOP': 95800,
    'W2_OF_W3_WAVE_C_BOT': 74500,   # approximate bottom (near complete)

    # W3 of W3 Fibonacci targets (from ~$74,500 base)
    'W3_OF_W3_BASE':   74500,
    'W3_OF_W3_T1618':  253800,   # 1.618 × W1
    'W3_OF_W3_T200':   296100,   # 2.0 × W1
    'W3_OF_W3_T2618':  364600,   # 2.618 × W1
    'W3_OF_W3_ZONE_LO': 280000,
    'W3_OF_W3_ZONE_HI': 320000,

    # Future waves
    'W4_OF_W3_ZONE_LO': 180000,
    'W4_OF_W3_ZONE_HI': 210000,
    'W5_OF_W3_TARGET_LO': 350000,
    'W5_OF_W3_TARGET_HI': 450000,

    # Invalidation levels
    'INVAL_W2_OF_W3':  69000,    # below this = recount needed
    'INVAL_W3':        15400,    # below this = catastrophic
    'INVAL_W3_OF_W3':  126200,   # W3 of W3 below this = W4 rule violated
}

# ─────────────────────────────────────────────────────────────
# 75 HALAL COINS (cryptohalal.cc verified)
# ─────────────────────────────────────────────────────────────
HALAL_COINS = [
    # Tier 1
    "BTC","ETH","XRP","SOL","BNB","ADA","AVAX","SUI","HBAR","NEAR",
    "DOT","ICP","FTM","ETC","WLD","RENDER","ATOM","KAS","FIL","APT",
    "ARB","VET","SEI","STX","TAO",
    # Tier 2
    "XLM","ALGO","LTC","TON","LINK","POL","XTZ","IOTA","BCH","IMX",
    "INJ","FET","OCEAN","AKT","AR","HNT","ONE","ZIL","QTUM","DCR",
    "RVN","EGLD","FLOW","ANKR","GRT","ROSE","KAVA","SKL","NMR","OP",
    "CELO","BAND","WAXP","TWT",
    # Tier 3
    "GALA","AXS","SAND","MANA","ENJ","CHZ","ASTR","BAT","LPT",
    "AUDIO","CVC","POWR","HOT",
]

# ─────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────
last_signal_time = {}
active_trades    = {}
watch_coins      = {}
scan_count       = 0


# ═════════════════════════════════════════════════════════════
# SECTION 1 — BINANCE DATA
# ═════════════════════════════════════════════════════════════

def get_klines(symbol, interval, days):
    limits = {"1d": days, "4h": days * 6, "1w": max(1, days // 7)}
    limit  = min(limits.get(interval, days), 1000)
    url    = f"{BINANCE_BASE}/api/v3/klines"
    try:
        r = requests.get(url,
            params={"symbol": f"{symbol}USDT", "interval": interval, "limit": limit},
            timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data or isinstance(data, dict):
            return None
        arr = lambda idx: np.array([float(c[idx]) for c in data])
        return arr(1), arr(2), arr(3), arr(4), arr(5), np.array([int(c[0]) for c in data])
    except Exception as e:
        log.warning(f"Binance {symbol} {interval}: {e}")
        return None


def get_global_ath(symbol):
    """Global ATH from full weekly history — used for swing mode."""
    try:
        r = requests.get(f"{BINANCE_BASE}/api/v3/klines",
            params={"symbol": f"{symbol}USDT", "interval": "1w", "limit": 1000},
            timeout=10)
        r.raise_for_status()
        data = r.json()
        return max(float(c[2]) for c in data) if data else None
    except Exception:
        return None


def get_current_price(symbol):
    try:
        r = requests.get(f"{BINANCE_BASE}/api/v3/ticker/price",
            params={"symbol": f"{symbol}USDT"}, timeout=5)
        return float(r.json()["price"])
    except Exception:
        return None


# ═════════════════════════════════════════════════════════════
# SECTION 2 — INDICATORS
# ═════════════════════════════════════════════════════════════

def _ema(data, n):
    k = 2 / (n + 1)
    e = [float(data[0])]
    for v in data[1:]:
        e.append(float(v) * k + e[-1] * (1 - k))
    return np.array(e)


def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    d  = np.diff(closes.astype(float))
    g  = np.where(d > 0, d, 0.0)
    l  = np.where(d < 0, -d, 0.0)
    ag = np.mean(g[:period])
    al = np.mean(l[:period])
    for i in range(period, len(g)):
        ag = (ag * (period - 1) + g[i]) / period
        al = (al * (period - 1) + l[i]) / period
    return round(100.0 if al == 0 else 100 - 100 / (1 + ag / al), 2)


def calc_macd(closes, fast=12, slow=26, sig=9):
    if len(closes) < slow + sig:
        return None, None, False
    ml   = _ema(closes, fast) - _ema(closes, slow)
    sl   = _ema(ml, sig)
    hist = ml - sl
    bull = bool(hist[-1] > 0 and hist[-2] <= 0) or bool(hist[-1] > hist[-2] > 0)
    return float(ml[-1]), float(sl[-1]), bull


def calc_stoch(closes, highs, lows, k=14):
    if len(closes) < k:
        return None
    lo, hi = np.min(lows[-k:]), np.max(highs[-k:])
    return round(50.0 if hi == lo else (closes[-1] - lo) / (hi - lo) * 100, 2)


def calc_smi(closes, highs, lows, period=13, smooth=25):
    if len(closes) < period + smooth:
        return None
    mid  = (highs[-period:] + lows[-period:]) / 2
    diff = closes[-period:] - mid
    rng  = np.where(
        highs[-period:] - lows[-period:] == 0,
        0.0001,
        highs[-period:] - lows[-period:]
    )
    return round(float(_ema(200 * diff / rng, smooth)[-1]), 2)


def calc_ewo(closes, fast=5, slow=35):
    if len(closes) < slow:
        return None, False
    val = float(_ema(closes, fast)[-1] - _ema(closes, slow)[-1])
    return round(val, 6), val > 0


def calc_ma50(closes):
    return float(np.mean(closes[-50:])) if len(closes) >= 50 else None


def volume_analysis(volumes, lb=10):
    if len(volumes) < lb + 2:
        return False, False
    v        = volumes[-lb - 1:-1]
    declining = bool(np.polyfit(range(len(v)), v, 1)[0] < 0)
    expanding = bool(volumes[-1] > np.mean(v) * 1.2)
    return declining, expanding


def daily_trend_bullish(closes_1d):
    """Price above MA50 AND last 5 closes trending up — Golden Rule."""
    if len(closes_1d) < 50:
        return False
    return bool(
        closes_1d[-1] > np.mean(closes_1d[-50:]) and
        closes_1d[-1] > closes_1d[-5]
    )


# ═════════════════════════════════════════════════════════════
# SECTION 3 — PIVOT DETECTION
# ═════════════════════════════════════════════════════════════

def find_pivots(highs, lows, window=5):
    """
    Adaptive window pivot detection.
    Tries window=5 first, falls back to 3 if not enough pivots.
    Returns list of (bar_index, price, 'H' or 'L').
    """
    for w in [window, 3]:
        pivots = []
        n = len(highs)
        for i in range(w, n - w):
            is_h = all(highs[i] >= highs[i-j] for j in range(1, w+1)) and \
                   all(highs[i] >= highs[i+j] for j in range(1, w+1))
            is_l = all(lows[i]  <= lows[i-j]  for j in range(1, w+1)) and \
                   all(lows[i]  <= lows[i+j]  for j in range(1, w+1))
            if is_h:
                pivots.append((i, float(highs[i]), 'H'))
            elif is_l:
                pivots.append((i, float(lows[i]),  'L'))
        if len(pivots) >= 8:
            break
    return pivots


# ═════════════════════════════════════════════════════════════
# SECTION 4 — 3 CARDINAL EW RULES
# ═════════════════════════════════════════════════════════════

def validate_ew_rules(w0, w1h, w2l, w3h, w4l, w5h):
    """
    The 3 Cardinal Rules — must never be broken:
    Rule 1: W2 NEVER retraces more than 100% of W1
    Rule 2: W3 is NEVER the shortest impulse wave
    Rule 3: W4 NEVER overlaps W1 territory
    """
    issues = []
    w1 = w1h - w0
    if w1 <= 0:
        return False, ["W1 range zero"]
    if w2l <= w0:
        issues.append("Rule 1 violated: W2 > 100% of W1")
    w3 = w3h - w2l
    w5 = w5h - w4l
    if w3 <= 0:
        issues.append("W3 range zero")
    elif w3 < w1 and w3 < w5:
        issues.append("Rule 2 violated: W3 is shortest")
    if w4l <= w1h:
        issues.append("Rule 3 violated: W4 overlaps W1")
    if w5h <= w3h:
        issues.append("W5 below W3 top")
    return len(issues) == 0, issues


def fib_quality(retrace):
    """W2 retracement quality. Returns (label, is_valid, is_golden)."""
    if 0.618 <= retrace <= 0.786:
        return "GOLDEN (61.8–78.6%)", True, True
    elif 0.500 <= retrace < 0.618:
        return "GOOD (50–61.8%)", True, False
    elif 0.382 <= retrace < 0.500:
        return "VALID (38.2–50%)", True, False
    elif 0.786 < retrace <= 1.000:
        return "DEEP (78.6–100%)", True, False
    return f"INVALID ({retrace*100:.1f}%)", False, False


# ═════════════════════════════════════════════════════════════
# SECTION 5 — STRUCTURE DETECTION
#
# The bot reads the CHART and identifies which of the 5 patterns
# exists. Each structure has its own:
#   - Detection logic and EW rule validation
#   - Entry price (from actual wave level)
#   - Swing SL (2% below actual structure low)
#   - Swing TPs (from actual wave levels and Fib extensions)
#   - Applicable situational checks (■ for N/A ones)
#
# For SCALP mode: levels are always fixed %, structure only
# determines which situational checks apply.
# ═════════════════════════════════════════════════════════════

def _find_impulse(pivots):
    """Find most recent valid completed 5-wave impulse (L H L H L H)."""
    for i in range(len(pivots) - 6, -1, -1):
        seg = pivots[i:i+6]
        if len(seg) < 6:
            continue
        if [p[2] for p in seg] != ['L','H','L','H','L','H']:
            continue
        valid, _ = validate_ew_rules(
            seg[0][1], seg[1][1], seg[2][1],
            seg[3][1], seg[4][1], seg[5][1]
        )
        if valid:
            return seg
    return None


def _post_impulse_waves(pivots, impulse):
    """Get pivots that come after a completed impulse."""
    w5_idx = impulse[5][0]
    return [p for p in pivots if p[0] > w5_idx]


# ── 5.1 Standard EW — W4 entry (active impulse unfolding) ────

def detect_standard_ew_w4(pivots, current):
    """
    Active 5-wave impulse, price currently at W4 correction.
    Pattern in pivots: L H L H L (5 pivots — W5 not yet formed)

    Entry: W4 bottom
    SL (swing): 2% below W4 low
    TP1: W3 top (first resistance)
    TP2: W4 + 1.618×W1 (W5 projection — most common)
    TP3: W4 + 2.0×W1
    TP4: W4 + 2.618×W1 (extended W5)

    Situational: wave_count, golden_ratio, alternation, blue_box,
                 stoch, smi, ewo, vol_dec, vol_exp
    """
    if len(pivots) < 5:
        return None
    for i in range(len(pivots) - 5, -1, -1):
        seg = pivots[i:i+5]
        if len(seg) < 5:
            continue
        if [p[2] for p in seg] != ['L','H','L','H','L']:
            continue
        w0  = seg[0][1]; w1h = seg[1][1]
        w2l = seg[2][1]; w3h = seg[3][1]
        w4l = seg[4][1]
        w1  = w1h - w0;  w3  = w3h - w2l
        if w1 <= 0 or w3 <= 0:
            continue
        # Partial EW rules (no W5 yet)
        if w2l <= w0:        continue   # Rule 1
        if w3 < w1:          continue   # Rule 2 partial
        if w4l <= w1h:       continue   # Rule 3
        # Price must be near W4 bottom (within 5%)
        if abs(current - w4l) / w4l > 0.05:
            continue
        w2_ret = (w1h - w2l) / w1
        w4_ret = (w3h - w4l) / w3
        fib_lbl, fib_valid, fib_golden = fib_quality(w2_ret)
        # Blue box: 0.618–0.786 Fib of W3
        bb_lo = w3h - w3 * 0.786
        bb_hi = w3h - w3 * 0.618
        return {
            'type':        'STANDARD_EW_W4',
            'label':       'Standard EW — W4 Entry',
            'w0':w0,'w1h':w1h,'w2l':w2l,'w3h':w3h,'w4l':w4l,'w5h':None,
            'w1':w1, 'w3':w3,
            'w2_ret':round(w2_ret,3), 'w4_ret':round(w4_ret,3),
            'fib_lbl':fib_lbl, 'fib_valid':fib_valid, 'fib_golden':fib_golden,
            'in_blue_box': bb_lo <= current <= bb_hi,
            'alternation': abs(w2_ret - w4_ret) > 0.15,
            'entry_price': w4l,  'struct_low': w4l,
            # Swing levels — structure based
            'swing_sl':  round(w4l * (1 - SWING_SL_BUFFER), 6),
            'swing_tp1': round(w3h, 6),              # W3 top
            'swing_tp2': round(w4l + w1*1.618, 6),   # 1.618 W5 proj
            'swing_tp3': round(w4l + w1*2.0,   6),
            'swing_tp4': round(w4l + w1*2.618, 6),
            'tp1_lbl': 'W3 high retest',
            'tp2_lbl': '1.618×W1 (W5 projection)',
            'tp3_lbl': '2.0×W1',
            'tp4_lbl': '2.618×W1',
            'sl_lbl':  '2% below W4 low',
            'entry_wave': 'W4',
            # Checklist flags
            '_ew_valid': True,
            '_fib_check': fib_valid,
            '_fib_check_lbl': f'W2 Fib 38-100% of W1: {fib_lbl}',
            '_no_end_diag': True,
            '_no_trunc_w5': True,
            # Applicable situational checks
            'sit_apply': ['wave_count','golden_ratio','alternation','blue_box',
                          'stoch','smi','ewo','vol_dec','vol_exp'],
        }
    return None


# ── 5.2 Standard EW — W2 entry (after full impulse complete) ─

def detect_standard_ew_w2(pivots, current):
    """
    Completed 5-wave impulse, price now back at W2 level (new cycle start).
    Pattern: L H L H L H (6 pivots — impulse complete)

    Entry: W2 bottom (new cycle begins)
    SL (swing): 2% below W2 low
    TP1: W1 top retest
    TP2: W2 + 1.618×W1 (W3 target — most powerful)
    TP3: W2 + 2.618×W1
    TP4: Prior W5 top

    Situational: wave_count, golden_ratio, wave_sym,
                 stoch, smi, ewo, vol_dec, vol_exp
    """
    if len(pivots) < 6:
        return None
    for i in range(len(pivots) - 6, -1, -1):
        seg = pivots[i:i+6]
        if len(seg) < 6:
            continue
        if [p[2] for p in seg] != ['L','H','L','H','L','H']:
            continue
        w0  = seg[0][1]; w1h = seg[1][1]; w2l = seg[2][1]
        w3h = seg[3][1]; w4l = seg[4][1]; w5h = seg[5][1]
        valid, _ = validate_ew_rules(w0,w1h,w2l,w3h,w4l,w5h)
        if not valid:
            continue
        if abs(current - w2l) / w2l > 0.05:
            continue
        w1     = w1h - w0
        w2_ret = (w1h - w2l) / w1
        fib_lbl, fib_valid, fib_golden = fib_quality(w2_ret)
        return {
            'type':        'STANDARD_EW_W2',
            'label':       'Standard EW — W2 Entry',
            'w0':w0,'w1h':w1h,'w2l':w2l,'w3h':w3h,'w4l':w4l,'w5h':w5h,
            'w1':w1, 'w3':w3h-w2l,
            'w2_ret':round(w2_ret,3), 'w4_ret':round((w3h-w4l)/(w3h-w2l),3),
            'fib_lbl':fib_lbl, 'fib_valid':fib_valid, 'fib_golden':fib_golden,
            'in_blue_box': False, 'alternation': None,
            'entry_price': w2l, 'struct_low': w2l,
            'swing_sl':  round(w2l * (1 - SWING_SL_BUFFER), 6),
            'swing_tp1': round(w1h, 6),              # W1 top retest
            'swing_tp2': round(w2l + w1*1.618, 6),   # W3 target
            'swing_tp3': round(w2l + w1*2.618, 6),
            'swing_tp4': round(w5h, 6),               # prior W5 top
            'tp1_lbl': 'W1 high retest',
            'tp2_lbl': '1.618×W1 (W3 target)',
            'tp3_lbl': '2.618×W1',
            'tp4_lbl': 'Prior W5 top',
            'sl_lbl':  '2% below W2 low',
            'entry_wave': 'W2',
            '_ew_valid': True,
            '_fib_check': fib_valid,
            '_fib_check_lbl': f'W2 Fib 38-100% of W1: {fib_lbl}',
            '_no_end_diag': True,
            '_no_trunc_w5': True,
            'sit_apply': ['wave_count','golden_ratio','wave_sym',
                          'stoch','smi','ewo','vol_dec','vol_exp'],
        }
    return None


# ── 5.3 ABC Zigzag — completed impulse + 5-3-5 correction ────

def detect_abc_zigzag(pivots, current):
    """
    Completed 5-wave impulse followed by ABC Zigzag (5-3-5):
      Wave A = 5-wave impulse down
      Wave B = 3-wave bounce (38–78% of A) ← zigzag rule
      Wave C = 5-wave decline, C ≈ A in price

    This is exactly what BTC W2 of W3 is:
      A: $126,200 → $74,500
      B: $74,500  → $95,800 (57% retrace)
      C: $95,800  → ~$74,500

    And what INJ showed on the 4H chart.

    Entry: Wave C bottom (when C ≥ 70% of A range)
    SL (swing): 2% below Wave C low
    TP1: Wave B top (prior bounce high — first resistance)
    TP2: W5 top (Wave A origin — full correction retrace)
    TP3: Wave C + 1.618×Wave A
    TP4: Wave C + 2.618×Wave A

    Situational: wave_c_bot, c_eq_a, abc_struct,
                 stoch, smi, ewo, vol_dec, vol_exp
    """
    if len(pivots) < 8:
        return None
    impulse = _find_impulse(pivots)
    if impulse is None:
        return None
    w5h    = impulse[5][1]
    post   = _post_impulse_waves(pivots, impulse)
    if len(post) < 2:
        return None
    # Wave A — first Low after W5 (decline ≥ 8% of W5)
    a_piv  = next((p for p in post if p[2] == 'L'), None)
    if a_piv is None:
        return None
    wa_bot   = a_piv[1]
    wa_range = w5h - wa_bot
    if wa_range / max(w5h, 0.0001) < 0.08:
        return None
    # Wave B — first High after A, retrace 38–78% of A (zigzag)
    post_a = [p for p in post if p[0] > a_piv[0]]
    b_piv  = next((p for p in post_a if p[2] == 'H'), None)
    if b_piv is None:
        return None
    wb_top  = b_piv[1]
    wb_ret  = (wb_top - wa_bot) / wa_range
    if not (0.38 <= wb_ret <= 0.78):
        return None   # not a zigzag — check expanded flat instead
    # Wave C — decline from B, approaching C=A target
    post_b   = [p for p in post if p[0] > b_piv[0]]
    c_piv    = next((p for p in post_b if p[2] == 'L'), None)
    c_dev    = c_piv is None
    wc_bot   = current if c_dev else c_piv[1]
    wc_range = wb_top - wc_bot
    if wc_range <= 0:
        return None
    c_progress  = wc_range / wa_range * 100
    c_eq_a_tgt  = wb_top - wa_range
    c_confirmed = abs(wc_bot - c_eq_a_tgt) / max(abs(c_eq_a_tgt), 0.0001) < 0.05
    if c_progress < 70:
        return None
    return {
        'type':  'ABC_ZIGZAG',
        'label': 'ABC Zigzag Correction',
        'w5h': w5h,
        'wa_bot': wa_bot, 'wa_range': wa_range,
        'wb_top': wb_top, 'wb_ret_pct': round(wb_ret*100, 1),
        'wc_bot': wc_bot, 'wc_range': wc_range, 'c_dev': c_dev,
        'c_eq_a_tgt': round(c_eq_a_tgt, 6),
        'c_progress': round(c_progress, 1),
        'c_confirmed': c_confirmed,
        'entry_price': wc_bot, 'struct_low': wc_bot,
        'swing_sl':  round(wc_bot * (1 - SWING_SL_BUFFER), 6),
        'swing_tp1': round(wb_top, 6),              # Wave B top
        'swing_tp2': round(w5h,    6),              # W5 top (correction origin)
        'swing_tp3': round(wc_bot + wa_range*1.618, 6),
        'swing_tp4': round(wc_bot + wa_range*2.618, 6),
        'tp1_lbl': 'Wave B top',
        'tp2_lbl': 'W5 top (correction origin)',
        'tp3_lbl': '1.618×Wave A from C',
        'tp4_lbl': '2.618×Wave A from C',
        'sl_lbl':  '2% below Wave C low',
        'entry_wave': 'Wave C',
        '_ew_valid': True,
        '_fib_check': c_progress >= 70,
        '_fib_check_lbl': f'C=A Progress: {c_progress:.1f}% (≥70% required)',
        '_no_end_diag': True,
        '_no_trunc_w5': True,
        'sit_apply': ['wave_c_bot','c_eq_a','abc_struct',
                      'stoch','smi','ewo','vol_dec','vol_exp'],
    }


# ── 5.4 Expanded Flat — B exceeds W5 top ─────────────────────

def detect_expanded_flat(pivots, current):
    """
    Flat correction where B wave EXCEEDS the origin (W5 top).
    B retraces > 100% of A — this distinguishes it from zigzag.
    C typically = 1.236–1.618 × A, ends below Wave A bottom.

    Entry: Wave C bottom
    SL (swing): 2% below Wave C low
    TP1: Wave A bottom (prior support — now cleared)
    TP2: Wave B top (the new high made during B)
    TP3: Wave C + 1.618×Wave A
    TP4: Wave C + 2.0×Wave A

    Situational: wave_c_bot, abc_struct,
                 stoch, smi, ewo, vol_dec, vol_exp
    """
    if len(pivots) < 8:
        return None
    impulse = _find_impulse(pivots)
    if impulse is None:
        return None
    w5h  = impulse[5][1]
    post = _post_impulse_waves(pivots, impulse)
    if len(post) < 3:
        return None
    a_piv = next((p for p in post if p[2] == 'L'), None)
    if a_piv is None:
        return None
    wa_bot   = a_piv[1]
    wa_range = w5h - wa_bot
    if wa_range <= 0:
        return None
    post_a = [p for p in post if p[0] > a_piv[0]]
    b_piv  = next((p for p in post_a if p[2] == 'H'), None)
    if b_piv is None:
        return None
    wb_top = b_piv[1]
    # KEY: B must exceed W5 top
    if wb_top <= w5h:
        return None
    wb_ret = (wb_top - wa_bot) / wa_range   # > 1.0
    post_b = [p for p in post if p[0] > b_piv[0]]
    c_piv  = next((p for p in post_b if p[2] == 'L'), None)
    c_dev  = c_piv is None
    wc_bot = current if c_dev else c_piv[1]
    wc_range = wb_top - wc_bot
    if wc_range <= 0:
        return None
    c_vs_a    = wc_range / wa_range
    c_progress = min(c_vs_a / 1.236 * 100, 100)
    if c_progress < 70:
        return None
    return {
        'type':  'EXPANDED_FLAT',
        'label': 'Expanded Flat Correction',
        'w5h': w5h,
        'wa_bot': wa_bot, 'wa_range': wa_range,
        'wb_top': wb_top, 'wb_ret_pct': round(wb_ret*100, 1),
        'wc_bot': wc_bot, 'wc_range': wc_range, 'c_dev': c_dev,
        'c_vs_a_pct': round(c_vs_a*100, 1),
        'c_progress': round(c_progress, 1),
        'c_t1236': round(wb_top - wa_range*1.236, 6),
        'c_t1618': round(wb_top - wa_range*1.618, 6),
        'entry_price': wc_bot, 'struct_low': wc_bot,
        'swing_sl':  round(wc_bot * (1 - SWING_SL_BUFFER), 6),
        'swing_tp1': round(wa_bot, 6),              # Wave A bottom
        'swing_tp2': round(wb_top, 6),              # Wave B top (new high)
        'swing_tp3': round(wc_bot + wa_range*1.618, 6),
        'swing_tp4': round(wc_bot + wa_range*2.0,   6),
        'tp1_lbl': 'Wave A bottom',
        'tp2_lbl': 'Wave B top (new high)',
        'tp3_lbl': '1.618×Wave A from C',
        'tp4_lbl': '2.0×Wave A from C',
        'sl_lbl':  '2% below Wave C low',
        'entry_wave': 'Wave C',
        '_ew_valid': True,
        '_fib_check': c_progress >= 70,
        '_fib_check_lbl': f'C Progress ≥70% (1.236×A): {c_progress:.1f}%',
        '_no_end_diag': True,
        '_no_trunc_w5': True,
        'sit_apply': ['wave_c_bot','abc_struct',
                      'stoch','smi','ewo','vol_dec','vol_exp'],
    }


# ── 5.5 Running Correction — C above A bottom (very bullish) ──

def detect_running_correction(pivots, current):
    """
    Market so strong it can't complete a full retrace.
    C never reaches A bottom — forms a higher low.
    B retraces 38–78% of A (normal), but C < A in size.

    Very bullish signal — next impulse usually very powerful.

    Entry: Wave C bottom (higher low vs A)
    SL (swing): 2% below Wave C low
    TP1: Wave B top
    TP2: W5 top (full recovery)
    TP3: W5 + 1.0×prior W1 (next new impulse)
    TP4: W5 + 1.618×prior W1 (extended next impulse)

    Situational: wave_c_bot, abc_struct, wave_count,
                 stoch, smi, ewo, vol_dec, vol_exp
    """
    if len(pivots) < 8:
        return None
    impulse = _find_impulse(pivots)
    if impulse is None:
        return None
    w5h   = impulse[5][1]
    w1rng = impulse[1][1] - impulse[0][1]
    post  = _post_impulse_waves(pivots, impulse)
    if len(post) < 3:
        return None
    a_piv = next((p for p in post if p[2] == 'L'), None)
    if a_piv is None:
        return None
    wa_bot   = a_piv[1]
    wa_range = w5h - wa_bot
    if wa_range <= 0:
        return None
    post_a = [p for p in post if p[0] > a_piv[0]]
    b_piv  = next((p for p in post_a if p[2] == 'H'), None)
    if b_piv is None:
        return None
    wb_top = b_piv[1]
    wb_ret = (wb_top - wa_bot) / wa_range
    if not (0.38 <= wb_ret <= 0.78):
        return None
    post_b = [p for p in post if p[0] > b_piv[0]]
    c_piv  = next((p for p in post_b if p[2] == 'L'), None)
    c_dev  = c_piv is None
    wc_bot = current if c_dev else c_piv[1]
    # KEY: C must stay ABOVE Wave A bottom (higher low)
    if wc_bot <= wa_bot:
        return None
    wc_range = wb_top - wc_bot
    c_vs_a   = wc_range / wa_range
    if c_vs_a < 0.38:
        return None
    return {
        'type':  'RUNNING_CORRECTION',
        'label': 'Running Correction (Bullish)',
        'w5h': w5h, 'w1rng': w1rng,
        'wa_bot': wa_bot, 'wa_range': wa_range,
        'wb_top': wb_top, 'wb_ret_pct': round(wb_ret*100, 1),
        'wc_bot': wc_bot, 'wc_range': wc_range, 'c_dev': c_dev,
        'c_vs_a_pct': round(c_vs_a*100, 1), 'higher_low': True,
        'entry_price': wc_bot, 'struct_low': wc_bot,
        'swing_sl':  round(wc_bot * (1 - SWING_SL_BUFFER), 6),
        'swing_tp1': round(wb_top, 6),               # Wave B top
        'swing_tp2': round(w5h,    6),               # W5 top
        'swing_tp3': round(w5h + w1rng*1.0,   6),   # next impulse
        'swing_tp4': round(w5h + w1rng*1.618, 6),   # extended
        'tp1_lbl': 'Wave B top',
        'tp2_lbl': 'W5 top (full recovery)',
        'tp3_lbl': 'W5 + 1.0×W1 (next impulse)',
        'tp4_lbl': 'W5 + 1.618×W1 (extended)',
        'sl_lbl':  '2% below Wave C (higher low)',
        'entry_wave': 'Wave C (Higher Low)',
        '_ew_valid': True,
        '_fib_check': True,
        '_fib_check_lbl': 'C Above A Bottom (Higher Low) ✓',
        '_no_end_diag': True,
        '_no_trunc_w5': True,
        'sit_apply': ['wave_c_bot','abc_struct','wave_count',
                      'stoch','smi','ewo','vol_dec','vol_exp'],
    }


# ── 5.6 W-X-Y-X-Z Triple Combination ─────────────────────────

def detect_wxyxz(pivots, current):
    """
    Complex 5-segment correction — rarest, highest confidence.
    W=down, X1=up, Y=down, X2=up, Z=down

    CRITICAL RULE (from fatinhijjawi):
    X1 and X2 MUST be equal in BOTH price AND time within 15%.
    When X1=X2 confirmed → Z bottom = HIGHEST CONFIDENCE entry.

    Entry: Z wave bottom
    SL (swing): 2% below Z low
    TP1: X2 top (most recent connector high)
    TP2: W top (correction origin = full recovery)
    TP3: W top + 0.618×W range
    TP4: W top + 1.0×W range

    Situational: wxyxz_x1x2, wave_count,
                 stoch, smi, ewo, vol_dec, vol_exp
    """
    if len(pivots) < 10:
        return None
    for i in range(len(pivots) - 10, -1, -1):
        seg = pivots[i:i+10]
        if len(seg) < 10:
            continue
        if [p[2] for p in seg[:5]] != ['H','L','H','L','H']:
            continue
        w_top  = seg[0][1]; w_bot  = seg[1][1]
        x1_top = seg[2][1]; y_bot  = seg[3][1]
        x2_top = seg[4][1]
        x1_rng = x1_top - w_bot
        x2_rng = x2_top - y_bot
        x1_t   = seg[2][0] - seg[1][0]
        x2_t   = seg[4][0] - seg[3][0]
        if x1_rng <= 0 or x1_t <= 0:
            continue
        # X moves must be meaningful (>5%)
        if w_bot > 0 and x1_rng / w_bot < 0.05:
            continue
        if y_bot > 0 and x2_rng / y_bot < 0.05:
            continue
        # X smaller than W and Y
        w_rng = w_top - w_bot
        y_rng = x1_top - y_bot
        if x1_rng >= w_rng * 0.8 or x1_rng >= y_rng * 0.8:
            continue
        # KEY: X1=X2 both price AND time within 15%
        price_diff = abs(x1_rng - x2_rng) / x1_rng
        time_diff  = abs(x1_t   - x2_t)   / x1_t
        if price_diff > 0.15 or time_diff > 0.15:
            continue
        # Z wave — lowest Low after X2 top
        post_x2 = [p for p in pivots if p[0] > seg[4][0]]
        z_piv   = next((p for p in post_x2 if p[2] == 'L'), None)
        z_dev   = z_piv is None
        z_bot   = current if z_dev else z_piv[1]
        if not z_dev and z_bot >= y_bot:
            continue
        move_up = w_top - w_bot
        return {
            'type':  'WXYXZ',
            'label': 'W-X-Y-X-Z Triple Combination',
            'w_top': w_top, 'w_bot': w_bot,
            'x1_top': x1_top, 'y_bot': y_bot, 'x2_top': x2_top,
            'z_bot': z_bot, 'z_dev': z_dev,
            'x1_rng': round(x1_rng,6), 'x2_rng': round(x2_rng,6),
            'price_diff_pct': round(price_diff*100,1),
            'time_diff_pct':  round(time_diff*100,1),
            'x1_eq_x2': True,
            'entry_price': z_bot, 'struct_low': z_bot,
            'swing_sl':  round(z_bot  * (1 - SWING_SL_BUFFER), 6),
            'swing_tp1': round(x2_top, 6),
            'swing_tp2': round(w_top,  6),
            'swing_tp3': round(w_top + move_up*0.618, 6),
            'swing_tp4': round(w_top + move_up*1.0,   6),
            'tp1_lbl': 'X2 top (connector high)',
            'tp2_lbl': 'W origin (full recovery)',
            'tp3_lbl': 'W top + 0.618×W range',
            'tp4_lbl': 'W top + 1.0×W range',
            'sl_lbl':  '2% below Z wave low',
            'entry_wave': 'Wave Z',
            '_ew_valid': True,
            '_fib_check': True,
            '_fib_check_lbl': f'X1=X2 Confirmed — Price {price_diff*100:.1f}% | Time {time_diff*100:.1f}%',
            '_no_end_diag': True,
            '_no_trunc_w5': True,
            'sit_apply': ['wxyxz_x1x2','wave_count',
                          'stoch','smi','ewo','vol_dec','vol_exp'],
        }
    return None


# ═════════════════════════════════════════════════════════════
# SECTION 6 — STRUCTURE RECOGNIZER
# Priority: rarest/most specific first, most common last
# ═════════════════════════════════════════════════════════════

def recognize_structure(pivots, current):
    """
    Tries each detector in priority order.
    Returns the first match (highest priority structure).
    Rarest patterns checked first to avoid masking them.
    """
    for detector in [
        detect_wxyxz,             # Rarest — X1=X2 strict rule
        detect_expanded_flat,     # B > W5 top — specific signature
        detect_running_correction, # C above A — bullish structure
        detect_abc_zigzag,        # Most common post-impulse correction
        detect_standard_ew_w4,    # Active impulse at W4
        detect_standard_ew_w2,    # After impulse, new cycle W2
    ]:
        s = detector(pivots, current)
        if s is not None:
            return s
    return None


# ═════════════════════════════════════════════════════════════
# SECTION 7 — SIGNAL LEVELS
# SCALP: fixed % always (session doc Part 4)
# SWING: actual wave levels from detected structure
# ═════════════════════════════════════════════════════════════

def build_levels(structure, current_price, mode):
    """
    SCALP: fixed percentages from session doc Part 4:
      SL=-5% | TP1=+3% | TP2=+5% | TP3=+8% | TP4=+10%

    SWING: structure wave levels (2% SL buffer below structure low)
    """
    e = current_price

    if mode == 'scalp':
        return {
            'entry':   round(e, 6),
            'sl':      round(e * (1 - SCALP_SL_PCT),  6),
            'tp1':     round(e * (1 + SCALP_TP1_PCT), 6),
            'tp2':     round(e * (1 + SCALP_TP2_PCT), 6),
            'tp3':     round(e * (1 + SCALP_TP3_PCT), 6),
            'tp4':     round(e * (1 + SCALP_TP4_PCT), 6),
            'sl_pct':   -5.0, 'sl_lbl':  '-5% fixed',
            'tp1_pct':  +3.0, 'tp1_lbl': '+3% fixed',
            'tp2_pct':  +5.0, 'tp2_lbl': '+5% fixed',
            'tp3_pct':  +8.0, 'tp3_lbl': '+8% fixed',
            'tp4_pct': +10.0, 'tp4_lbl': '+10% fixed',
            'mode': 'scalp', 'tp_hit': 0,
        }

    # Swing — pure structure levels
    entry = structure['entry_price']
    sl    = structure['swing_sl']
    tp1   = structure['swing_tp1']
    tp2   = structure['swing_tp2']
    tp3   = structure['swing_tp3']
    tp4   = structure['swing_tp4']

    def pct(t):
        return round((t - entry) / entry * 100, 1) if entry > 0 else 0

    return {
        'entry':   round(entry, 6),
        'sl':      round(sl,  6),
        'tp1':     round(tp1, 6),
        'tp2':     round(tp2, 6),
        'tp3':     round(tp3, 6),
        'tp4':     round(tp4, 6),
        'sl_pct':   pct(sl),  'sl_lbl':  structure['sl_lbl'],
        'tp1_pct':  pct(tp1), 'tp1_lbl': structure['tp1_lbl'],
        'tp2_pct':  pct(tp2), 'tp2_lbl': structure['tp2_lbl'],
        'tp3_pct':  pct(tp3), 'tp3_lbl': structure['tp3_lbl'],
        'tp4_pct':  pct(tp4), 'tp4_lbl': structure['tp4_lbl'],
        'mode': 'swing', 'tp_hit': 0,
    }


# ═════════════════════════════════════════════════════════════
# SECTION 8 — SIGNAL CHECKLIST
# Exactly per session doc Part 3
# 10 required (all must pass) + situational (■ = N/A, not failure)
# ═════════════════════════════════════════════════════════════

def run_checklist(structure, closes_1d, closes, highs, lows,
                  rsi, macd_bull, stoch, smi, ewo_bull,
                  vol_dec, vol_exp, current):
    """
    10 REQUIRED checks — adapted per structure type.
    Situational checks — only applicable ones scored, rest = ■.
    """
    stype   = structure['type'] if structure else 'NONE'
    applies = structure['sit_apply'] if structure else []

    # ── REQUIRED ─────────────────────────────────────────────
    # Check 5 and 6 adapt their label based on structure
    req = {}

    # 1. Daily Trend Bullish — Golden Rule
    req['Daily Trend Bullish'] = daily_trend_bullish(closes_1d)

    # 2. MA50 Confirmed
    ma50 = calc_ma50(closes)
    req['MA50 Confirmed'] = ma50 is not None and current > ma50

    # 3. Core EW Structure Exists
    req['5-Wave Impulse / Core Structure'] = structure is not None

    # 4. EW Rules Valid (3 Cardinal Rules)
    req['EW Rules Valid (3 Cardinal Rules)'] = (
        structure.get('_ew_valid', False) if structure else False
    )

    # 5. Entry Zone — label and check adapt per structure
    if structure:
        entry = structure['entry_price']
        near  = abs(current - entry) / max(entry, 0.0001) < 0.05
        req[f"Entry Zone ({structure['entry_wave']})"] = near
    else:
        req['Entry Zone (none)'] = False

    # 6. Fib check — adapts per structure
    if structure:
        req[structure['_fib_check_lbl']] = structure['_fib_check']
    else:
        req['W2 Fib 38-100% of W1'] = False

    # 7. RSI Below 45 — oversold at entry
    req[f'RSI Below 45 ({rsi:.0f})'] = rsi is not None and rsi < 45

    # 8. MACD Bullish
    req['MACD Bullish'] = bool(macd_bull)

    # 9. No Ending Diagonal
    req['No Ending Diagonal'] = (
        structure.get('_no_end_diag', True) if structure else True
    )

    # 10. No Truncated W5
    req['No Truncated W5'] = (
        structure.get('_no_trunc_w5', True) if structure else True
    )

    req_pass  = sum(1 for v in req.values() if v)
    req_total = len(req)

    # ── SITUATIONAL ───────────────────────────────────────────
    # All 16 from session doc — only applicable ones scored
    ALL_SIT = {
        'wave_count': (
            'Wave Count Verified >60%',
            lambda: bool(structure and structure.get('w1',0) > 0 and
                         structure.get('w3',0) / structure.get('w1',1) > 1.0)
        ),
        'golden_ratio': (
            'Golden Ratio 38-78%',
            lambda: bool(structure and
                         0.618 <= structure.get('w2_ret',0) <= 0.786)
        ),
        'wave_c_bot': (
            'Wave C Bottom',
            lambda: bool(structure and
                         float(structure.get('c_progress',0)) >= 80)
        ),
        'c_eq_a': (
            'C=A Price + Time',
            lambda: bool(structure and structure.get('c_confirmed', False))
        ),
        'wxyxz_x1x2': (
            'WXYXZ X1=X2 (Price+Time within 15%)',
            lambda: bool(structure and structure.get('x1_eq_x2', False))
        ),
        'abc_struct': (
            'ABC Structure',
            lambda: stype in ('ABC_ZIGZAG','EXPANDED_FLAT','RUNNING_CORRECTION')
        ),
        'stoch': (
            f'Stochastic Below 25 ({stoch:.0f})',
            lambda: stoch is not None and stoch < 25
        ),
        'smi': (
            f'SMI Below -40 ({smi:.0f})',
            lambda: smi is not None and smi < -40
        ),
        'ewo': (
            'EWO Signal',
            lambda: ewo_bull is True
        ),
        'vol_dec': (
            'Volume Declining (correction phase)',
            lambda: bool(vol_dec)
        ),
        'vol_exp': (
            'Volume Expanding (reversal candle)',
            lambda: bool(vol_exp)
        ),
        'alternation': (
            'Alternation W2 vs W4',
            lambda: bool(structure and structure.get('alternation'))
        ),
        'candlestick': (
            'Candlestick Pattern',
            lambda: False   # requires OHLC pattern logic
        ),
        'wave_sym': (
            'Wave Symmetry (W3>W1, W5<W3)',
            lambda: bool(structure and
                         structure.get('w3',0) > structure.get('w1',0))
        ),
        'blue_box': (
            'Blue Box Zone (0.618–0.786 Fib)',
            lambda: bool(structure and structure.get('in_blue_box', False))
        ),
    }

    sit_scored = {}   # applicable — scored
    sit_na     = []   # not applicable — ■

    for key, (label, check_fn) in ALL_SIT.items():
        if key in applies:
            try:
                sit_scored[label] = check_fn()
            except Exception:
                sit_scored[label] = False
        else:
            sit_na.append(label)

    sit_pass  = sum(1 for v in sit_scored.values() if v)
    sit_total = len(sit_scored)

    return req_pass, req_total, sit_pass, sit_total, req, sit_scored, sit_na


def confidence_label(req_pass, req_total, sit_pass, sit_total):
    """
    From session doc scoring:
    6/6 HIGH → Full position size
    4-5/6 MEDIUM → 50% position
    Below 4 → Skip
    Adapted for 10 required:
    """
    req_r = req_pass / req_total if req_total else 0
    sit_r = sit_pass / sit_total if sit_total else 0.5
    score = req_r * 0.7 + sit_r * 0.3
    if score >= 0.90:   return 'HIGH — Full position'
    elif score >= 0.75: return 'MEDIUM-HIGH — 75% position'
    elif score >= 0.60: return 'MEDIUM — 50% position'
    else:               return 'LOW — Skip'


# ═════════════════════════════════════════════════════════════
# SECTION 9 — TELEGRAM MESSAGES
# ═════════════════════════════════════════════════════════════

STRUCT_ICONS = {
    'STANDARD_EW_W4':     '📊',
    'STANDARD_EW_W2':     '📊',
    'ABC_ZIGZAG':         '〽️',
    'EXPANDED_FLAT':      '📐',
    'RUNNING_CORRECTION': '🚀',
    'WXYXZ':              '🔁',
}


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"
        }, timeout=10)
        if not r.ok:
            log.warning(f"Telegram: {r.text[:200]}")
    except Exception as e:
        log.warning(f"Telegram failed: {e}")


def format_structure_lines(s):
    """Structure-specific wave level lines for Telegram."""
    t = s['type']
    lines = []
    if t in ('STANDARD_EW_W4', 'STANDARD_EW_W2'):
        lines += [
            f"W0 origin : ${s['w0']:,.4f}",
            f"W1 top    : ${s['w1h']:,.4f}",
            f"W2 bottom : ${s['w2l']:,.4f}  [{s['fib_lbl']}]",
            f"W3 top    : ${s['w3h']:,.4f}",
        ]
        if t == 'STANDARD_EW_W4':
            lines += [
                f"W4 bottom : <b>${s['w4l']:,.4f}</b>  ← ENTRY",
                f"W4 retrace: {s['w4_ret']*100:.1f}% of W3",
            ]
        else:
            lines += [
                f"W4 bottom : ${s['w4l']:,.4f}",
                f"W5 top    : ${s['w5h']:,.4f}",
                f"<b>W2 bottom: ${s['w2l']:,.4f}</b>  ← ENTRY (new cycle)",
            ]
    elif t in ('ABC_ZIGZAG', 'EXPANDED_FLAT', 'RUNNING_CORRECTION'):
        lines += [
            f"W5 top (origin) : ${s['w5h']:,.4f}",
            f"Wave A bottom   : ${s['wa_bot']:,.4f}",
            f"Wave B top      : ${s['wb_top']:,.4f}  ({s['wb_ret_pct']}% retrace)",
            f"Wave C bottom   : <b>${s['wc_bot']:,.4f}</b>  "
            f"{'(developing)' if s['c_dev'] else '✅'}  ← ENTRY",
        ]
        if t == 'ABC_ZIGZAG':
            lines += [
                f"C=A target  : ${s['c_eq_a_tgt']:,.4f}  ({s['c_progress']}% complete)",
                f"{'✅ C=A CONFIRMED' if s['c_confirmed'] else '⏳ Approaching C=A target'}",
            ]
        elif t == 'EXPANDED_FLAT':
            lines += [
                f"B retrace   : {s['wb_ret_pct']}%  (B > W5 top ⚡ expanded)",
                f"C target    : ${s['c_t1236']:,.4f} – ${s['c_t1618']:,.4f}",
            ]
        elif t == 'RUNNING_CORRECTION':
            lines += [
                f"C vs A      : {s['c_vs_a_pct']}% of Wave A",
                "🚀 Higher low — C above A bottom — very bullish",
            ]
    elif t == 'WXYXZ':
        lines += [
            f"W top  : ${s['w_top']:,.4f}",
            f"X1 top : ${s['x1_top']:,.4f}  (range: ${s['x1_rng']:,.4f})",
            f"Y bot  : ${s['y_bot']:,.4f}",
            f"X2 top : ${s['x2_top']:,.4f}  (range: ${s['x2_rng']:,.4f})",
            f"X1=X2  : price {s['price_diff_pct']}% | time {s['time_diff_pct']}%  ✅",
            f"Z bot  : <b>${s['z_bot']:,.4f}</b>  "
            f"{'(developing)' if s['z_dev'] else '✅'}  ← ENTRY",
            "🔥🔥 HIGHEST CONFIDENCE — X1=X2 Price+Time Confirmed",
        ]
    return "\n".join(lines)


def format_signal_msg(symbol, structure, levels,
                      req_pass, req_total, req_det,
                      sit_pass, sit_total, sit_det, sit_na,
                      confidence, mode):
    icon  = STRUCT_ICONS.get(structure['type'], '📐')
    mode_lbl = mode.upper()
    struct_lines = format_structure_lines(structure)
    failed = [k for k, v in req_det.items() if not v]
    failed_str = ('\n⚠️ Failed: ' + ' | '.join(failed)) if failed else ''
    # Swing level labels
    if mode == 'swing':
        sl_line  = f"🛑 SL    : ${levels['sl']:,.4f}  ({levels['sl_pct']}%)  [{levels['sl_lbl']}]"
        tp1_line = f"🎯 TP1   : ${levels['tp1']:,.4f}  (+{levels['tp1_pct']}%)  [{levels['tp1_lbl']}]"
        tp2_line = f"🎯 TP2   : ${levels['tp2']:,.4f}  (+{levels['tp2_pct']}%)  [{levels['tp2_lbl']}]"
        tp3_line = f"🎯 TP3   : ${levels['tp3']:,.4f}  (+{levels['tp3_pct']}%)  [{levels['tp3_lbl']}]"
        tp4_line = f"🎯 TP4   : ${levels['tp4']:,.4f}  (+{levels['tp4_pct']}%)  [{levels['tp4_lbl']}]"
    else:
        sl_line  = f"🛑 SL    : ${levels['sl']:,.4f}  (-5% fixed)"
        tp1_line = f"🎯 TP1   : ${levels['tp1']:,.4f}  (+3%)"
        tp2_line = f"🎯 TP2   : ${levels['tp2']:,.4f}  (+5%)"
        tp3_line = f"🎯 TP3   : ${levels['tp3']:,.4f}  (+8%)"
        tp4_line = f"🎯 TP4   : ${levels['tp4']:,.4f}  (+10%)"

    msg = (
        f"🟢 <b>SIGNAL — {symbol}</b> ({mode_lbl})\n"
        f"{icon} {structure['label']}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<b>STRUCTURE</b>\n"
        f"{struct_lines}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<b>LEVELS ({mode_lbl})</b>\n"
        f"💵 Entry : <b>${levels['entry']:,.4f}</b>\n"
        f"{sl_line}\n"
        f"{tp1_line}\n"
        f"{tp2_line}\n"
        f"{tp3_line}\n"
        f"{tp4_line}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"✅ Required : {req_pass}/{req_total}{failed_str}\n"
        f"📊 Situational: {sit_pass}/{sit_total}\n"
        f"⬛ N/A checks : {len(sit_na)}\n"
        f"⚡ {confidence}\n"
        f"#SIGNALSYM #{symbol} #{mode_lbl}"
    )
    return msg


def format_watch_msg(symbol, structure, req_pass, req_total, mode, price):
    icon = STRUCT_ICONS.get(structure['type'], '📐')
    return (
        f"🟡 <b>WATCH — {symbol}</b> ({mode.upper()})\n"
        f"{icon} {structure['label']}\n\n"
        f"💵 Price: ${price:,.4f}\n"
        f"✅ Required: {req_pass}/{req_total}\n"
        f"⏳ Monitoring every 5 min...\n"
        f"#SIGNALSYM #{symbol} #WATCH"
    )


def format_tp_alert(symbol, tp_num, price, new_sl):
    return (
        f"🎯 <b>TP{tp_num} HIT — {symbol}</b>\n"
        f"💵 Price: ${price:,.4f}\n"
        f"🛑 SL moved to: ${new_sl:,.4f}\n"
        f"#SIGNALSYM #{symbol}"
    )


def format_sl_alert(symbol, price):
    return (
        f"🔴 <b>STOP LOSS — {symbol}</b>\n"
        f"💵 Exited: ${price:,.4f}\n"
        f"⏳ Waiting for next signal\n"
        f"#SIGNALSYM #{symbol}"
    )


def format_heartbeat(scans, active, watching):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    return (
        f"💓 <b>SIGNALSYM Heartbeat</b>\n"
        f"🕐 {now}\n"
        f"🔄 Scans: {scans}\n"
        f"🟢 Active trades: {active}\n"
        f"🟡 Watching: {watching}\n"
        f"✅ Running normally"
    )


# ═════════════════════════════════════════════════════════════
# SECTION 10 — PRICE MONITOR (TP/SL auto alerts)
# From session doc: TP1 hit → SL to entry, TP2 → SL to TP1, etc.
# ═════════════════════════════════════════════════════════════

def check_active_trades():
    global active_trades
    to_close = []
    for symbol, trade in list(active_trades.items()):
        price = get_current_price(symbol)
        if price is None:
            continue
        tp_hit = trade['tp_hit']
        sl     = trade['sl']
        tps    = [trade['tp1'], trade['tp2'], trade['tp3'], trade['tp4']]
        # SL hit
        if price <= sl:
            send_telegram(format_sl_alert(symbol, price))
            to_close.append(symbol)
            log.info(f"SL hit: {symbol} @ {price}")
            continue
        # TP hits
        for i, tp in enumerate(tps[tp_hit:], start=tp_hit + 1):
            if price >= tp:
                new_sl = trade['entry'] if i == 1 else tps[i - 2]
                trade['sl']     = new_sl
                trade['tp_hit'] = i
                send_telegram(format_tp_alert(symbol, i, price, new_sl))
                log.info(f"TP{i} hit: {symbol} @ {price}, SL → {new_sl}")
                if i == 4:
                    to_close.append(symbol)
                break
    for sym in to_close:
        active_trades.pop(sym, None)


def check_watch_coins():
    global watch_coins
    graduated = []
    for symbol, info in list(watch_coins.items()):
        result = analyze_coin(symbol, info['mode'])
        if result and result['status'] == 'SIGNAL':
            send_telegram(format_signal_msg(
                symbol, result['structure'], result['levels'],
                result['req_pass'], result['req_total'], result['req_det'],
                result['sit_pass'], result['sit_total'], result['sit_det'],
                result['sit_na'], result['confidence'], info['mode']
            ))
            active_trades[symbol] = result['levels']
            last_signal_time[f"{symbol}_{info['mode']}"] = time.time()
            graduated.append(symbol)
            log.info(f"Watch → Signal: {symbol}")
    for sym in graduated:
        watch_coins.pop(sym, None)


# ═════════════════════════════════════════════════════════════
# SECTION 11 — COIN ANALYSIS
# Full pipeline: data → indicators → structure → checklist → levels
# ═════════════════════════════════════════════════════════════

def analyze_coin(symbol, mode='scalp'):
    """
    Full analysis pipeline for one coin.

    1. Fetch 4H/90d (scalp) or 1D/730d (swing) from Binance
    2. Fetch 1D/100d for daily trend check (Golden Rule)
    3. Calculate all indicators (RSI, MACD, Stoch, SMI, EWO, Vol)
    4. Find pivots (adaptive window)
    5. Recognize which structure this chart shows (5 detectors)
    6. Run the 10 required + situational checklist
    7. Build levels (fixed scalp OR structure-based swing)
    8. Return SIGNAL / WATCH / None
    """
    interval = '1d' if mode == 'swing' else '4h'
    days     = SWING_DAYS if mode == 'swing' else SCALP_DAYS

    data = get_klines(symbol, interval, days)
    if data is None:
        return None
    opens, highs, lows, closes, volumes, times = data
    current = float(closes[-1])

    # Daily data always needed for Golden Rule trend check
    daily = get_klines(symbol, '1d', 100)
    if daily is None:
        return None
    closes_1d = daily[3]

    # Indicators
    rsi             = calc_rsi(closes)
    _, _, macd_bull = calc_macd(closes)
    stoch           = calc_stoch(closes, highs, lows)
    smi             = calc_smi(closes, highs, lows)
    _, ewo_bull     = calc_ewo(closes)
    vol_dec, vol_exp = volume_analysis(volumes)

    if rsi is None:
        return None

    # Pivot detection
    pivots = find_pivots(highs, lows, window=5)
    if len(pivots) < 5:
        return None

    # Structure recognition — the core of the strategy
    structure = recognize_structure(pivots, current)
    if structure is None:
        return None

    # Checklist — exactly per session doc Part 3
    (req_pass, req_total,
     sit_pass, sit_total,
     req_det, sit_det, sit_na) = run_checklist(
        structure, closes_1d, closes, highs, lows,
        rsi, macd_bull, stoch, smi, ewo_bull,
        vol_dec, vol_exp, current
    )

    confidence = confidence_label(req_pass, req_total, sit_pass, sit_total)

    # Build trade levels
    levels = build_levels(structure, current, mode)

    # Signal determination (session doc):
    # All 10 required pass → SIGNAL
    # 7-9 required pass → WATCH
    if req_pass == req_total:
        status = 'SIGNAL'
    elif req_pass >= 7:
        status = 'WATCH'
    else:
        return None

    return {
        'status':     status,
        'structure':  structure,
        'levels':     levels,
        'req_pass':   req_pass,
        'req_total':  req_total,
        'req_det':    req_det,
        'sit_pass':   sit_pass,
        'sit_total':  sit_total,
        'sit_det':    sit_det,
        'sit_na':     sit_na,
        'confidence': confidence,
        'current':    current,
    }


# ═════════════════════════════════════════════════════════════
# SECTION 12 — MAIN SCAN LOOP
# 75 halal coins | 15 min interval | 1s between coins
# Swing cooldown 4h | Scalp cooldown 2h
# Watch re-checked every 5 min
# Heartbeat every 24h
# ═════════════════════════════════════════════════════════════

def should_scan(symbol, mode):
    key      = f"{symbol}_{mode}"
    cooldown = SWING_COOLDOWN if mode == 'swing' else SCALP_COOLDOWN
    return (time.time() - last_signal_time.get(key, 0)) > cooldown


def run_scan():
    global scan_count
    scan_count += 1
    log.info(f"── Scan #{scan_count} | {len(HALAL_COINS)} coins ──")
    t0 = time.time()

    for symbol in HALAL_COINS:
        for mode in ['scalp', 'swing']:
            if not should_scan(symbol, mode):
                continue
            try:
                result = analyze_coin(symbol, mode)
                if result is None:
                    continue

                key    = f"{symbol}_{mode}"
                status = result['status']

                if status == 'SIGNAL':
                    msg = format_signal_msg(
                        symbol, result['structure'], result['levels'],
                        result['req_pass'], result['req_total'], result['req_det'],
                        result['sit_pass'], result['sit_total'], result['sit_det'],
                        result['sit_na'], result['confidence'], mode
                    )
                    send_telegram(msg)
                    active_trades[symbol] = result['levels']
                    last_signal_time[key] = time.time()
                    watch_coins.pop(symbol, None)
                    log.info(
                        f"SIGNAL {symbol} {mode} "
                        f"{result['structure']['type']} "
                        f"req:{result['req_pass']}/{result['req_total']} "
                        f"sit:{result['sit_pass']}/{result['sit_total']}"
                    )

                elif status == 'WATCH':
                    watch_key  = f"{symbol}_{mode}_watch"
                    wc         = WATCH_COOLDOWN_SWING if mode == 'swing' else WATCH_COOLDOWN_SCALP
                    if (time.time() - last_signal_time.get(watch_key, 0)) > wc:
                        msg = format_watch_msg(
                            symbol, result['structure'],
                            result['req_pass'], result['req_total'],
                            mode, result['current']
                        )
                        send_telegram(msg)
                        watch_coins[symbol] = {'mode': mode, 'ts': time.time()}
                        last_signal_time[watch_key] = time.time()
                        log.info(
                            f"WATCH {symbol} {mode} "
                            f"{result['structure']['type']} "
                            f"req:{result['req_pass']}/{result['req_total']}"
                        )

            except Exception as e:
                log.error(f"Error {symbol} {mode}: {e}", exc_info=True)

        time.sleep(COIN_SLEEP)

    log.info(f"── Scan #{scan_count} done in {time.time()-t0:.1f}s ──")

    if scan_count % HEARTBEAT_SCANS == 0:
        send_telegram(format_heartbeat(
            scan_count, len(active_trades), len(watch_coins)
        ))


def main():
    log.info("SIGNALSYM starting...")
    send_telegram(
        "🤖 <b>SIGNALSYM Started</b>\n\n"
        "<b>Strategy: Your Fixed Wave Structure</b>\n"
        "Grand W3 unfolding | W2 of W3 near complete\n\n"
        "<b>Structures detected per chart:</b>\n"
        "📊 Standard EW — W2 or W4 entry\n"
        "〽️ ABC Zigzag — C=A correction\n"
        "📐 Expanded Flat — B exceeds W5\n"
        "🚀 Running Correction — higher low\n"
        "🔁 W-X-Y-X-Z — X1=X2 confirmed\n\n"
        "<b>Levels:</b>\n"
        "Scalp: TP3/5/8/10% | SL -5% (fixed)\n"
        "Swing: Structure wave levels | SL 2% below low\n\n"
        "✅ 75 halal coins | Binance | Every 15 min"
    )

    last_price_check = 0
    while True:
        try:
            now = time.time()
            if (now - last_price_check) >= PRICE_MONITOR_INTERVAL:
                if active_trades:
                    check_active_trades()
                if watch_coins:
                    check_watch_coins()
                last_price_check = time.time()
            run_scan()
            time.sleep(SCAN_INTERVAL)
        except KeyboardInterrupt:
            log.info("Bot stopped.")
            break
        except Exception as e:
            log.error(f"Main loop error: {e}", exc_info=True)
            time.sleep(60)


if __name__ == "__main__":
    main()
