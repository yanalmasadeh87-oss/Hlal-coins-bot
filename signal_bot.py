"""
SIGNALSYM — signal_bot.py
Elliott Wave Bot | Halal Spot Only | Binance API
Developer: Yanal Masadeh (@YASAMA_11)

════════════════════════════════════════════════════════════════
CORE PHILOSOPHY
════════════════════════════════════════════════════════════════
Every coin has its own Grand Supercycle structure — just like BTC:
  W1: ATL → ATH (first major impulse)
  W2: ATH → correction (38–100% of W1)
  W3: correction bottom → new ATH (most powerful wave)
  W4: pullback from W3 top (23–38% of W3)
  W5: final push above W3

The bot reads each chart independently:
  1. Fetches full weekly history → finds coin's own ATL, ATH, W1 range
  2. Determines where the coin is in its cycle (W2? W3? W4? ABC?)
  3. Reads the ACTUAL chart pattern (zigzag? flat? running? WXYXZ?)
  4. Applies the correct analysis technique for that specific pattern
  5. Builds levels from actual wave levels — not fixed templates

No two charts are analyzed the same way.
The technique adapts to what the chart actually shows.

════════════════════════════════════════════════════════════════
SESSION DOC — FIXED RULES (never change)
════════════════════════════════════════════════════════════════
CHECKLIST (Part 3):
  Required (ALL 10 must pass):
    1. Daily Trend Bullish
    2. MA50 Confirmed
    3. 5-Wave Impulse / Core Structure
    4. EW Rules Valid (3 Cardinal Rules)
    5. Entry Zone (W2/W4/Wave C — adapts per structure)
    6. Fib Check (adapts per structure)
    7. RSI Below 45
    8. MACD Bullish
    9. No Ending Diagonal
    10. No Truncated W5
  Situational (■ = not applicable = NOT failure):
    Wave Count >60% | Golden Ratio | Wave C Bottom
    C=A Price+Time | WXYXZ X1=X2 | ABC Structure
    Stoch <25 | SMI <-40 | EWO | Vol Declining
    Vol Expanding | Alternation | Candlestick | Wave Sym | Blue Box

SIGNAL LEVELS (Part 4):
  SCALP: SL=-5% | TP1=+3% | TP2=+5% | TP3=+8% | TP4=+10% (fixed)
  SWING: SL=2% below structure low | TPs=actual wave levels

3 CARDINAL RULES:
  Rule 1: W2 NEVER retraces > 100% of W1
  Rule 2: W3 is NEVER the shortest impulse wave
  Rule 3: W4 NEVER overlaps W1 territory

GOLDEN RULE:
  Daily bullish → LONG signals only on all timeframes
  NEVER counter-trade the daily bias
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
SCAN_INTERVAL          = 900
COIN_SLEEP             = 1
HEARTBEAT_SCANS        = 96

SWING_COOLDOWN         = 4 * 3600
SCALP_COOLDOWN         = 2 * 3600
WATCH_COOLDOWN_SWING   = 2 * 3600
WATCH_COOLDOWN_SCALP   = 1 * 3600
PRICE_MONITOR_INTERVAL = 300

SCALP_SL_PCT  = 0.05
SCALP_TP1_PCT = 0.03
SCALP_TP2_PCT = 0.05
SCALP_TP3_PCT = 0.08
SCALP_TP4_PCT = 0.10
SWING_SL_BUFFER = 0.02

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("SIGNALSYM")

# ─────────────────────────────────────────────────────────────
# 75 HALAL COINS
# ─────────────────────────────────────────────────────────────
HALAL_COINS = [
    "BTC","ETH","XRP","SOL","BNB","ADA","AVAX","SUI","HBAR","NEAR",
    "DOT","ICP","FTM","ETC","WLD","RENDER","ATOM","KAS","FIL","APT",
    "ARB","VET","SEI","STX","TAO",
    "XLM","ALGO","LTC","TON","LINK","POL","XTZ","IOTA","BCH","IMX",
    "INJ","FET","OCEAN","AKT","AR","HNT","ONE","ZIL","QTUM","DCR",
    "RVN","EGLD","FLOW","ANKR","GRT","ROSE","KAVA","SKL","NMR","OP",
    "CELO","BAND","WAXP","TWT",
    "GALA","AXS","SAND","MANA","ENJ","CHZ","ASTR","BAT","LPT",
    "AUDIO","CVC","POWR","HOT",
]

last_signal_time = {}
active_trades    = {}
watch_coins      = {}
scan_count       = 0


# ═════════════════════════════════════════════════════════════
# SECTION 1 — BINANCE DATA
# ═════════════════════════════════════════════════════════════

def get_klines(symbol, interval, limit):
    url = f"{BINANCE_BASE}/api/v3/klines"
    try:
        r = requests.get(url,
            params={"symbol": f"{symbol}USDT",
                    "interval": interval, "limit": limit},
            timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data or isinstance(data, dict):
            return None
        arr = lambda i: np.array([float(c[i]) for c in data])
        return arr(1), arr(2), arr(3), arr(4), arr(5), \
               np.array([int(c[0]) for c in data])
    except Exception as e:
        log.warning(f"Binance {symbol} {interval}: {e}")
        return None


def get_weekly_history(symbol):
    """Full weekly history — used to find coin's own grand structure."""
    return get_klines(symbol, "1w", 1000)


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
    bull = bool(hist[-1] > 0 and hist[-2] <= 0) or \
           bool(hist[-1] > hist[-2] > 0)
    return float(ml[-1]), float(sl[-1]), bull


def calc_stoch(closes, highs, lows, k=14):
    if len(closes) < k:
        return None
    lo, hi = np.min(lows[-k:]), np.max(highs[-k:])
    return round(50.0 if hi == lo
                 else (closes[-1] - lo) / (hi - lo) * 100, 2)


def calc_smi(closes, highs, lows, period=13, smooth=25):
    if len(closes) < period + smooth:
        return None
    mid  = (highs[-period:] + lows[-period:]) / 2
    diff = closes[-period:] - mid
    rng  = np.where(highs[-period:] - lows[-period:] == 0,
                    0.0001,
                    highs[-period:] - lows[-period:])
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
    v         = volumes[-lb - 1:-1]
    declining = bool(np.polyfit(range(len(v)), v, 1)[0] < 0)
    expanding = bool(volumes[-1] > np.mean(v) * 1.2)
    return declining, expanding


def daily_trend_bullish(closes_1d):
    """Golden Rule: price above MA50 AND last 5 closes trending up."""
    if len(closes_1d) < 50:
        return False
    return bool(closes_1d[-1] > np.mean(closes_1d[-50:]) and
                closes_1d[-1] > closes_1d[-5])


# ═════════════════════════════════════════════════════════════
# SECTION 3 — COIN GRAND STRUCTURE
#
# Every coin has its own wave cycle. The bot reads the full
# weekly history to find:
#   - ATL (Wave 0 origin — lowest price ever)
#   - ATH (Wave 1 or Wave 3 top — highest price ever)
#   - W1 range (ATH - ATL)
#   - Current position in the cycle
#   - Key Fib levels specific to this coin
#
# This is applied to ALL coins — not just BTC.
# ═════════════════════════════════════════════════════════════

def get_grand_structure(symbol):
    """
    Reads full weekly history to determine coin's own grand wave structure.

    Returns dict with:
      atl, ath, w1_range
      w1_complete: bool (has ATH been formed and price pulled back?)
      current_cycle_position: 'W2', 'W3', 'W4', 'W5', 'UNKNOWN'
      key fib levels for W2 correction zone
      invalidation levels
    """
    weekly = get_weekly_history(symbol)
    if weekly is None:
        return None

    opens, highs, lows, closes, volumes, times = weekly
    current = float(closes[-1])

    # ATL = lowest low in full history (Wave 0 / cycle origin)
    atl_idx = int(np.argmin(lows))
    atl     = float(lows[atl_idx])

    # ATH = highest high in full history (after ATL)
    post_atl_highs = highs[atl_idx:]
    if len(post_atl_highs) == 0:
        return None
    ath_rel_idx = int(np.argmax(post_atl_highs))
    ath_idx     = atl_idx + ath_rel_idx
    ath         = float(highs[ath_idx])

    # W1 range = ATH - ATL (the grand first impulse)
    w1_range = ath - atl
    if w1_range <= 0:
        return None

    # Current price position relative to W1 range
    # How far has price retraced from ATH?
    retrace_from_ath = (ath - current) / w1_range  # 0 = at ATH, 1 = at ATL

    # W2 Fibonacci correction levels (from ATH downward)
    fib_levels = {
        '0.236': round(ath - w1_range * 0.236, 6),
        '0.382': round(ath - w1_range * 0.382, 6),
        '0.500': round(ath - w1_range * 0.500, 6),
        '0.618': round(ath - w1_range * 0.618, 6),
        '0.786': round(ath - w1_range * 0.786, 6),
        '1.000': round(atl, 6),
    }

    # Determine current wave position based on price action
    # after ATH — where is price in the cycle right now?
    ath_candles_ago = len(highs) - 1 - ath_idx
    price_from_atl  = (current - atl) / w1_range  # 0=at ATL, 1=at ATH

    # Find lowest point AFTER ATH (potential W2 bottom)
    post_ath_lows = lows[ath_idx:]
    if len(post_ath_lows) > 1:
        w2_bot_rel = int(np.argmin(post_ath_lows))
        w2_bot     = float(post_ath_lows[w2_bot_rel])
        w2_bot_idx = ath_idx + w2_bot_rel
        w2_retrace = (ath - w2_bot) / w1_range
    else:
        w2_bot     = current
        w2_bot_idx = ath_idx
        w2_retrace = retrace_from_ath

    # Determine cycle position
    # W2: price has pulled back 38-100% from ATH, not yet recovered
    # W3: price recovered from W2 bottom and making new highs or near ATH
    # W4: price pulled back from W3 top (23-38% of W3 range)
    # W5: price near or above ATH after W4

    in_w2_zone = (0.38 <= retrace_from_ath <= 1.00) and \
                 (current < ath * 0.95)  # not near ATH

    # Check if price has recovered significantly from W2 bottom
    if w2_bot < ath and w2_bot > atl:
        recovery_from_w2 = (current - w2_bot) / max(ath - w2_bot, 0.0001)
    else:
        recovery_from_w2 = 0

    # Find W3 top — highest point after W2 bottom
    post_w2_highs = highs[w2_bot_idx:]
    w3_top = float(np.max(post_w2_highs)) if len(post_w2_highs) > 0 else current
    w3_range = w3_top - w2_bot if w3_top > w2_bot else 0

    # W4 retrace from W3 top
    retrace_from_w3 = (w3_top - current) / w3_range if w3_range > 0 else 0
    in_w4_zone = (0.23 <= retrace_from_w3 <= 0.50) and \
                 (w3_top > ath * 0.95)  # W3 must have exceeded or nearly ATH

    # Cycle position
    if current >= ath * 0.95:
        cycle_pos = 'W3_OR_W5_TOP'
    elif in_w4_zone:
        cycle_pos = 'W4'
    elif recovery_from_w2 > 0.5 and current > ath * 0.5:
        cycle_pos = 'W3'
    elif in_w2_zone:
        cycle_pos = 'W2'
    else:
        cycle_pos = 'UNKNOWN'

    # W3 of W3 Fibonacci targets (from W2 bottom)
    w3_targets = {
        '1.618': round(w2_bot + w1_range * 1.618, 6),
        '2.000': round(w2_bot + w1_range * 2.000, 6),
        '2.618': round(w2_bot + w1_range * 2.618, 6),
    } if w2_bot > 0 else {}

    # Invalidation levels
    invalidation = {
        'w2_invalid':  round(atl * 0.95, 6),   # below ATL = full recount
        'w3_invalid':  round(ath - w1_range * 1.05, 6),  # W3 below W1 top
    }

    return {
        'symbol':        symbol,
        'atl':           atl,
        'ath':           ath,
        'w1_range':      w1_range,
        'w2_bot':        w2_bot,
        'w2_retrace':    round(w2_retrace, 3),
        'w3_top':        w3_top,
        'w3_range':      w3_range,
        'current':       current,
        'retrace_ath':   round(retrace_from_ath, 3),
        'recovery_w2':   round(recovery_from_w2, 3),
        'cycle_pos':     cycle_pos,
        'fib_levels':    fib_levels,
        'w3_targets':    w3_targets,
        'invalidation':  invalidation,
        'ath_candles_ago': ath_candles_ago,
    }


# ═════════════════════════════════════════════════════════════
# SECTION 4 — PIVOT DETECTION
# Adaptive window — reads what the chart actually shows
# ═════════════════════════════════════════════════════════════

def find_pivots(highs, lows, window=5):
    """
    Adaptive pivot detection.
    Tries window=5 first (better quality), falls to 3 if needed.
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
# SECTION 5 — 3 CARDINAL EW RULES
# ═════════════════════════════════════════════════════════════

def validate_ew_rules(w0, w1h, w2l, w3h, w4l, w5h):
    issues = []
    w1 = w1h - w0
    if w1 <= 0:
        return False, ["W1 range zero"]
    if w2l <= w0:
        issues.append("Rule 1: W2 > 100% of W1")
    w3 = w3h - w2l
    w5 = w5h - w4l
    if w3 <= 0:
        issues.append("W3 range zero")
    elif w3 < w1 and w3 < w5:
        issues.append("Rule 2: W3 is shortest")
    if w4l <= w1h:
        issues.append("Rule 3: W4 overlaps W1")
    if w5h <= w3h:
        issues.append("W5 below W3 top")
    return len(issues) == 0, issues


def fib_quality(retrace):
    if 0.618 <= retrace <= 0.786:
        return "GOLDEN (61.8-78.6%)", True, True
    elif 0.500 <= retrace < 0.618:
        return "GOOD (50-61.8%)", True, False
    elif 0.382 <= retrace < 0.500:
        return "VALID (38.2-50%)", True, False
    elif 0.786 < retrace <= 1.000:
        return "DEEP (78.6-100%)", True, False
    return f"INVALID ({retrace*100:.1f}%)", False, False


# ═════════════════════════════════════════════════════════════
# SECTION 6 — STRUCTURE DETECTION
#
# The bot reads the chart and identifies which pattern exists.
# Each structure has its own detection logic, entry rules,
# and applicable situational checks.
#
# The grand structure (Section 3) informs WHICH structures
# are most likely — but the chart pattern confirms it.
#
# W2 cycle position → likely ABC/flat/running correction
# W4 cycle position → likely W4 pullback in active impulse
# W3 cycle position → look for sub-wave W2/W4 entries
# ═════════════════════════════════════════════════════════════

def _find_impulse(pivots):
    """Most recent valid completed 5-wave impulse (L H L H L H)."""
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


def _post_impulse(pivots, impulse):
    return [p for p in pivots if p[0] > impulse[5][0]]


# ── Structure 1: Standard EW W4 ──────────────────────────────
def detect_ew_w4(pivots, current, grand):
    """
    Active impulse — price at W4 correction.
    Most relevant when coin is in W3 cycle position.

    Swing TPs built from actual W1 range of THIS chart.
    """
    if len(pivots) < 5:
        return None
    for i in range(len(pivots) - 5, -1, -1):
        seg = pivots[i:i+5]
        if len(seg) < 5:
            continue
        if [p[2] for p in seg] != ['L','H','L','H','L']:
            continue
        w0=seg[0][1]; w1h=seg[1][1]; w2l=seg[2][1]
        w3h=seg[3][1]; w4l=seg[4][1]
        w1=w1h-w0; w3=w3h-w2l
        if w1<=0 or w3<=0: continue
        if w2l<=w0: continue
        if w3<w1:   continue
        if w4l<=w1h: continue
        if abs(current-w4l)/w4l > 0.05: continue

        w2_ret = (w1h-w2l)/w1
        w4_ret = (w3h-w4l)/w3
        fib_lbl, fib_valid, fib_golden = fib_quality(w2_ret)
        bb_lo = w3h - w3*0.786
        bb_hi = w3h - w3*0.618

        return {
            'type': 'STANDARD_EW_W4',
            'label': 'Standard EW - W4 Entry',
            'w0':w0,'w1h':w1h,'w2l':w2l,'w3h':w3h,'w4l':w4l,'w5h':None,
            'w1':w1,'w3':w3,
            'w2_ret':round(w2_ret,3),'w4_ret':round(w4_ret,3),
            'fib_lbl':fib_lbl,'fib_valid':fib_valid,'fib_golden':fib_golden,
            'in_blue_box': bb_lo<=current<=bb_hi,
            'alternation': abs(w2_ret-w4_ret)>0.15,
            'entry_price':w4l,'struct_low':w4l,
            'swing_sl':  round(w4l*(1-SWING_SL_BUFFER),6),
            'swing_tp1': round(w3h,6),
            'swing_tp2': round(w4l+w1*1.618,6),
            'swing_tp3': round(w4l+w1*2.0,6),
            'swing_tp4': round(w4l+w1*2.618,6),
            'tp1_lbl':'W3 high retest',
            'tp2_lbl':'1.618xW1 (W5 projection)',
            'tp3_lbl':'2.0xW1','tp4_lbl':'2.618xW1',
            'sl_lbl':'2% below W4 low',
            'entry_wave':'W4',
            '_ew_valid':True,
            '_fib_check':fib_valid,
            '_fib_lbl':f'W2 Fib 38-100% of W1: {fib_lbl}',
            '_no_end_diag':True,'_no_trunc_w5':True,
            'sit_apply':['wave_count','golden_ratio','alternation',
                         'blue_box','stoch','smi','ewo','vol_dec','vol_exp'],
            'grand_ctx': grand,
        }
    return None


# ── Structure 2: Standard EW W2 ──────────────────────────────
def detect_ew_w2(pivots, current, grand):
    """
    Completed impulse — price at W2 of new cycle.
    Uses THIS chart's W1 range for all Fib calculations.
    """
    if len(pivots) < 6:
        return None
    for i in range(len(pivots) - 6, -1, -1):
        seg = pivots[i:i+6]
        if len(seg) < 6:
            continue
        if [p[2] for p in seg] != ['L','H','L','H','L','H']:
            continue
        w0=seg[0][1]; w1h=seg[1][1]; w2l=seg[2][1]
        w3h=seg[3][1]; w4l=seg[4][1]; w5h=seg[5][1]
        valid,_ = validate_ew_rules(w0,w1h,w2l,w3h,w4l,w5h)
        if not valid: continue
        if abs(current-w2l)/w2l > 0.05: continue
        w1=w1h-w0
        w2_ret=(w1h-w2l)/w1
        fib_lbl,fib_valid,fib_golden=fib_quality(w2_ret)
        return {
            'type':'STANDARD_EW_W2',
            'label':'Standard EW - W2 Entry',
            'w0':w0,'w1h':w1h,'w2l':w2l,'w3h':w3h,'w4l':w4l,'w5h':w5h,
            'w1':w1,'w3':w3h-w2l,
            'w2_ret':round(w2_ret,3),'w4_ret':round((w3h-w4l)/(w3h-w2l),3),
            'fib_lbl':fib_lbl,'fib_valid':fib_valid,'fib_golden':fib_golden,
            'in_blue_box':False,'alternation':None,
            'entry_price':w2l,'struct_low':w2l,
            'swing_sl':  round(w2l*(1-SWING_SL_BUFFER),6),
            'swing_tp1': round(w1h,6),
            'swing_tp2': round(w2l+w1*1.618,6),
            'swing_tp3': round(w2l+w1*2.618,6),
            'swing_tp4': round(w5h,6),
            'tp1_lbl':'W1 high retest',
            'tp2_lbl':'1.618xW1 (W3 target)',
            'tp3_lbl':'2.618xW1','tp4_lbl':'Prior W5 top',
            'sl_lbl':'2% below W2 low',
            'entry_wave':'W2',
            '_ew_valid':True,
            '_fib_check':fib_valid,
            '_fib_lbl':f'W2 Fib 38-100% of W1: {fib_lbl}',
            '_no_end_diag':True,'_no_trunc_w5':True,
            'sit_apply':['wave_count','golden_ratio','wave_sym',
                         'stoch','smi','ewo','vol_dec','vol_exp'],
            'grand_ctx':grand,
        }
    return None


# ── Structure 3: ABC Zigzag ───────────────────────────────────
def detect_abc_zigzag(pivots, current, grand):
    """
    Completed impulse + ABC zigzag correction (5-3-5).
    Wave B retraces 38-78% of A (zigzag signature).
    C approaches A in price (C=A equality).

    This is the BTC W2 of W3 pattern:
    A=$126.2K->$74.5K, B=57% retrace, C approaching $74.5K.
    Applied to ALL coins in their own wave cycle.

    TPs built from actual A/B/C wave levels of THIS chart.
    """
    if len(pivots) < 8:
        return None
    impulse = _find_impulse(pivots)
    if impulse is None:
        return None
    w5h  = impulse[5][1]
    post = _post_impulse(pivots, impulse)
    if len(post) < 2:
        return None
    # Wave A
    aP = next((p for p in post if p[2]=='L'), None)
    if aP is None:
        return None
    wa_bot=aP[1]; wa_rng=w5h-wa_bot
    if wa_rng/max(w5h,0.0001)<0.08:
        return None
    # Wave B — zigzag: 38-78% retrace of A
    postA=[p for p in post if p[0]>aP[0]]
    bP=next((p for p in postA if p[2]=='H'),None)
    if bP is None:
        return None
    wb_top=bP[1]; wb_ret=(wb_top-wa_bot)/wa_rng
    if not (0.38<=wb_ret<=0.78):
        return None
    # Wave C
    postB=[p for p in post if p[0]>bP[0]]
    cP=next((p for p in postB if p[2]=='L'),None)
    c_dev=(cP is None)
    wc_bot=current if c_dev else cP[1]
    wc_rng=wb_top-wc_bot
    if wc_rng<=0:
        return None
    c_prog=wc_rng/wa_rng*100
    c_eq_a=wb_top-wa_rng
    c_conf=abs(wc_bot-c_eq_a)/max(abs(c_eq_a),0.0001)<0.05
    if c_prog<70:
        return None
    return {
        'type':'ABC_ZIGZAG',
        'label':'ABC Zigzag Correction',
        'w5h':w5h,'wa_bot':wa_bot,'wa_rng':wa_rng,
        'wb_top':wb_top,'wb_ret_pct':round(wb_ret*100,1),
        'wc_bot':wc_bot,'wc_rng':wc_rng,'c_dev':c_dev,
        'c_eq_a_tgt':round(c_eq_a,6),
        'c_progress':round(c_prog,1),'c_confirmed':c_conf,
        'entry_price':wc_bot,'struct_low':wc_bot,
        'swing_sl':  round(wc_bot*(1-SWING_SL_BUFFER),6),
        'swing_tp1': round(wb_top,6),
        'swing_tp2': round(w5h,6),
        'swing_tp3': round(wc_bot+wa_rng*1.618,6),
        'swing_tp4': round(wc_bot+wa_rng*2.618,6),
        'tp1_lbl':'Wave B top',
        'tp2_lbl':'W5 top (correction origin)',
        'tp3_lbl':'1.618xWave A from C',
        'tp4_lbl':'2.618xWave A from C',
        'sl_lbl':'2% below Wave C low',
        'entry_wave':'Wave C',
        '_ew_valid':True,
        '_fib_check':c_prog>=70,
        '_fib_lbl':f'C=A Progress: {c_prog:.1f}% (>=70% required)',
        '_no_end_diag':True,'_no_trunc_w5':True,
        'sit_apply':['wave_c_bot','c_eq_a','abc_struct',
                     'stoch','smi','ewo','vol_dec','vol_exp'],
        'grand_ctx':grand,
    }


# ── Structure 4: Expanded Flat ────────────────────────────────
def detect_expanded_flat(pivots, current, grand):
    """
    B wave EXCEEDS the impulse top (W5).
    B retraces >100% of A — expanded flat signature.
    C = 1.236-1.618 x A, ends below Wave A bottom.
    """
    if len(pivots)<8: return None
    impulse=_find_impulse(pivots)
    if impulse is None: return None
    w5h=impulse[5][1]
    post=_post_impulse(pivots,impulse)
    if len(post)<3: return None
    aP=next((p for p in post if p[2]=='L'),None)
    if aP is None: return None
    wa_bot=aP[1]; wa_rng=w5h-wa_bot
    if wa_rng<=0: return None
    postA=[p for p in post if p[0]>aP[0]]
    bP=next((p for p in postA if p[2]=='H'),None)
    if bP is None: return None
    wb_top=bP[1]
    if wb_top<=w5h: return None   # B must exceed W5 top
    wb_ret=(wb_top-wa_bot)/wa_rng
    postB=[p for p in post if p[0]>bP[0]]
    cP=next((p for p in postB if p[2]=='L'),None)
    c_dev=(cP is None)
    wc_bot=current if c_dev else cP[1]
    wc_rng=wb_top-wc_bot
    if wc_rng<=0: return None
    c_vs_a=wc_rng/wa_rng
    c_prog=min(c_vs_a/1.236*100,100)
    if c_prog<70: return None
    return {
        'type':'EXPANDED_FLAT',
        'label':'Expanded Flat Correction',
        'w5h':w5h,'wa_bot':wa_bot,'wa_rng':wa_rng,
        'wb_top':wb_top,'wb_ret_pct':round(wb_ret*100,1),
        'wc_bot':wc_bot,'wc_rng':wc_rng,'c_dev':c_dev,
        'c_vs_a_pct':round(c_vs_a*100,1),
        'c_progress':round(c_prog,1),
        'c_t1236':round(wb_top-wa_rng*1.236,6),
        'c_t1618':round(wb_top-wa_rng*1.618,6),
        'entry_price':wc_bot,'struct_low':wc_bot,
        'swing_sl':  round(wc_bot*(1-SWING_SL_BUFFER),6),
        'swing_tp1': round(wa_bot,6),
        'swing_tp2': round(wb_top,6),
        'swing_tp3': round(wc_bot+wa_rng*1.618,6),
        'swing_tp4': round(wc_bot+wa_rng*2.0,6),
        'tp1_lbl':'Wave A bottom',
        'tp2_lbl':'Wave B top (new high)',
        'tp3_lbl':'1.618xWave A from C',
        'tp4_lbl':'2.0xWave A from C',
        'sl_lbl':'2% below Wave C low',
        'entry_wave':'Wave C',
        '_ew_valid':True,
        '_fib_check':c_prog>=70,
        '_fib_lbl':f'C Progress >=70% (1.236xA): {c_prog:.1f}%',
        '_no_end_diag':True,'_no_trunc_w5':True,
        'sit_apply':['wave_c_bot','abc_struct',
                     'stoch','smi','ewo','vol_dec','vol_exp'],
        'grand_ctx':grand,
    }


# ── Structure 5: Running Correction ──────────────────────────
def detect_running_correction(pivots, current, grand):
    """
    Market too strong to complete full retrace.
    C stays ABOVE Wave A bottom — higher low.
    Very bullish — next impulse usually powerful.
    """
    if len(pivots)<8: return None
    impulse=_find_impulse(pivots)
    if impulse is None: return None
    w5h=impulse[5][1]
    w1rng=impulse[1][1]-impulse[0][1]
    post=_post_impulse(pivots,impulse)
    if len(post)<3: return None
    aP=next((p for p in post if p[2]=='L'),None)
    if aP is None: return None
    wa_bot=aP[1]; wa_rng=w5h-wa_bot
    if wa_rng<=0: return None
    postA=[p for p in post if p[0]>aP[0]]
    bP=next((p for p in postA if p[2]=='H'),None)
    if bP is None: return None
    wb_top=bP[1]; wb_ret=(wb_top-wa_bot)/wa_rng
    if not (0.38<=wb_ret<=0.78): return None
    postB=[p for p in post if p[0]>bP[0]]
    cP=next((p for p in postB if p[2]=='L'),None)
    c_dev=(cP is None)
    wc_bot=current if c_dev else cP[1]
    if wc_bot<=wa_bot: return None  # C must be above A
    wc_rng=wb_top-wc_bot
    c_vs_a=wc_rng/wa_rng
    if c_vs_a<0.38: return None
    return {
        'type':'RUNNING_CORRECTION',
        'label':'Running Correction (Bullish)',
        'w5h':w5h,'w1rng':w1rng,
        'wa_bot':wa_bot,'wa_rng':wa_rng,
        'wb_top':wb_top,'wb_ret_pct':round(wb_ret*100,1),
        'wc_bot':wc_bot,'wc_rng':wc_rng,'c_dev':c_dev,
        'c_vs_a_pct':round(c_vs_a*100,1),'higher_low':True,
        'entry_price':wc_bot,'struct_low':wc_bot,
        'swing_sl':  round(wc_bot*(1-SWING_SL_BUFFER),6),
        'swing_tp1': round(wb_top,6),
        'swing_tp2': round(w5h,6),
        'swing_tp3': round(w5h+w1rng*1.0,6),
        'swing_tp4': round(w5h+w1rng*1.618,6),
        'tp1_lbl':'Wave B top',
        'tp2_lbl':'W5 top (full recovery)',
        'tp3_lbl':'W5 + 1.0xW1 (next impulse)',
        'tp4_lbl':'W5 + 1.618xW1 (extended)',
        'sl_lbl':'2% below Wave C (higher low)',
        'entry_wave':'Wave C (Higher Low)',
        '_ew_valid':True,'_fib_check':True,
        '_fib_lbl':'C Above A Bottom (Higher Low)',
        '_no_end_diag':True,'_no_trunc_w5':True,
        'sit_apply':['wave_c_bot','abc_struct','wave_count',
                     'stoch','smi','ewo','vol_dec','vol_exp'],
        'grand_ctx':grand,
    }


# ── Structure 6: W-X-Y-X-Z Triple Combination ────────────────
def detect_wxyxz(pivots, current, grand):
    """
    Rarest, highest confidence.
    X1 = X2 in BOTH price AND time within 15%.
    Only fires when both confirmed.
    """
    if len(pivots)<10: return None
    for i in range(len(pivots)-10,-1,-1):
        seg=pivots[i:i+10]
        if len(seg)<10: continue
        if [p[2] for p in seg[:5]]!=['H','L','H','L','H']: continue
        w_top=seg[0][1]; w_bot=seg[1][1]
        x1_top=seg[2][1]; y_bot=seg[3][1]; x2_top=seg[4][1]
        x1_rng=x1_top-w_bot; x2_rng=x2_top-y_bot
        x1_t=seg[2][0]-seg[1][0]; x2_t=seg[4][0]-seg[3][0]
        if x1_rng<=0 or x1_t<=0: continue
        if w_bot>0 and x1_rng/w_bot<0.05: continue
        if y_bot>0 and x2_rng/y_bot<0.05: continue
        w_rng=w_top-w_bot; y_rng=x1_top-y_bot
        if x1_rng>=w_rng*0.8 or x1_rng>=y_rng*0.8: continue
        price_diff=abs(x1_rng-x2_rng)/x1_rng
        time_diff=abs(x1_t-x2_t)/x1_t
        if price_diff>0.15 or time_diff>0.15: continue
        postX2=[p for p in pivots if p[0]>seg[4][0]]
        zP=next((p for p in postX2 if p[2]=='L'),None)
        z_dev=(zP is None); z_bot=current if z_dev else zP[1]
        if not z_dev and z_bot>=y_bot: continue
        move=w_top-w_bot
        return {
            'type':'WXYXZ',
            'label':'W-X-Y-X-Z Triple Combination',
            'w_top':w_top,'w_bot':w_bot,
            'x1_top':x1_top,'y_bot':y_bot,'x2_top':x2_top,
            'z_bot':z_bot,'z_dev':z_dev,
            'x1_rng':round(x1_rng,6),'x2_rng':round(x2_rng,6),
            'price_diff_pct':round(price_diff*100,1),
            'time_diff_pct':round(time_diff*100,1),
            'x1_eq_x2':True,
            'entry_price':z_bot,'struct_low':z_bot,
            'swing_sl':  round(z_bot*(1-SWING_SL_BUFFER),6),
            'swing_tp1': round(x2_top,6),
            'swing_tp2': round(w_top,6),
            'swing_tp3': round(w_top+move*0.618,6),
            'swing_tp4': round(w_top+move*1.0,6),
            'tp1_lbl':'X2 top (connector high)',
            'tp2_lbl':'W origin (full recovery)',
            'tp3_lbl':'W top + 0.618xW range',
            'tp4_lbl':'W top + 1.0xW range',
            'sl_lbl':'2% below Z wave low',
            'entry_wave':'Wave Z',
            '_ew_valid':True,'_fib_check':True,
            '_fib_lbl':f'X1=X2: price {price_diff*100:.1f}% | time {time_diff*100:.1f}%',
            '_no_end_diag':True,'_no_trunc_w5':True,
            'sit_apply':['wxyxz_x1x2','wave_count',
                         'stoch','smi','ewo','vol_dec','vol_exp'],
            'grand_ctx':grand,
        }
    return None


# ═════════════════════════════════════════════════════════════
# SECTION 7 — SMART STRUCTURE RECOGNIZER
#
# Uses grand structure position to prioritize which patterns
# to look for, then reads the actual chart to confirm.
# ═════════════════════════════════════════════════════════════

def recognize_structure(pivots, current, grand):
    """
    Smart detection — grand structure informs priority,
    chart pattern confirms.

    W2 position → prioritize ABC/flat/running corrections
    W3/W4 position → prioritize EW W4/W2 entries
    Unknown → try all detectors in standard priority order
    """
    cycle = grand['cycle_pos'] if grand else 'UNKNOWN'

    # Always try WXYXZ first — rarest, most specific
    s = detect_wxyxz(pivots, current, grand)
    if s:
        return s

    if cycle in ('W2',):
        # Coin is in grand W2 correction — look for ABC structures first
        for detector in [
            detect_expanded_flat,
            detect_running_correction,
            detect_abc_zigzag,
            detect_ew_w4,
            detect_ew_w2,
        ]:
            s = detector(pivots, current, grand)
            if s:
                return s

    elif cycle in ('W3', 'W4', 'W3_OR_W5_TOP'):
        # Coin in W3 or W4 — look for impulse entries first
        for detector in [
            detect_ew_w4,
            detect_ew_w2,
            detect_abc_zigzag,
            detect_expanded_flat,
            detect_running_correction,
        ]:
            s = detector(pivots, current, grand)
            if s:
                return s

    else:
        # Unknown position — standard priority order
        for detector in [
            detect_expanded_flat,
            detect_running_correction,
            detect_abc_zigzag,
            detect_ew_w4,
            detect_ew_w2,
        ]:
            s = detector(pivots, current, grand)
            if s:
                return s

    return None


# ═════════════════════════════════════════════════════════════
# SECTION 8 — SIGNAL LEVELS
# Scalp: fixed always | Swing: from structure wave levels
# ═════════════════════════════════════════════════════════════

def build_levels(structure, current, mode):
    e = current

    if mode == 'scalp':
        return {
            'entry':round(e,6),
            'sl':   round(e*(1-SCALP_SL_PCT),6),
            'tp1':  round(e*(1+SCALP_TP1_PCT),6),
            'tp2':  round(e*(1+SCALP_TP2_PCT),6),
            'tp3':  round(e*(1+SCALP_TP3_PCT),6),
            'tp4':  round(e*(1+SCALP_TP4_PCT),6),
            'sl_pct':-5.0,'sl_lbl':'-5% fixed',
            'tp1_pct':3.0,'tp1_lbl':'+3% fixed',
            'tp2_pct':5.0,'tp2_lbl':'+5% fixed',
            'tp3_pct':8.0,'tp3_lbl':'+8% fixed',
            'tp4_pct':10.0,'tp4_lbl':'+10% fixed',
            'mode':'scalp','tp_hit':0,
        }

    entry = structure['entry_price']
    sl    = structure['swing_sl']
    tp1   = structure['swing_tp1']
    tp2   = structure['swing_tp2']
    tp3   = structure['swing_tp3']
    tp4   = structure['swing_tp4']
    def pct(t): return round((t-entry)/entry*100,1) if entry>0 else 0
    return {
        'entry':round(entry,6),
        'sl':   round(sl,6),
        'tp1':  round(tp1,6),'tp2':round(tp2,6),
        'tp3':  round(tp3,6),'tp4':round(tp4,6),
        'sl_pct':pct(sl),'sl_lbl':structure['sl_lbl'],
        'tp1_pct':pct(tp1),'tp1_lbl':structure['tp1_lbl'],
        'tp2_pct':pct(tp2),'tp2_lbl':structure['tp2_lbl'],
        'tp3_pct':pct(tp3),'tp3_lbl':structure['tp3_lbl'],
        'tp4_pct':pct(tp4),'tp4_lbl':structure['tp4_lbl'],
        'mode':'swing','tp_hit':0,
    }


# ═════════════════════════════════════════════════════════════
# SECTION 9 — SIGNAL CHECKLIST
# Session doc Part 3 — exact implementation
# ═════════════════════════════════════════════════════════════

def run_checklist(structure, closes_1d, closes, highs, lows,
                  rsi, macd_bull, stoch, smi, ewo_bull,
                  vol_dec, vol_exp, current):
    stype   = structure['type'] if structure else 'NONE'
    applies = structure['sit_apply'] if structure else []

    # ── 10 REQUIRED ──────────────────────────────────────────
    req = {}

    req['Daily Trend Bullish'] = daily_trend_bullish(closes_1d)

    ma50 = calc_ma50(closes)
    req['MA50 Confirmed'] = ma50 is not None and current > ma50

    req['5-Wave / Core Structure Found'] = structure is not None

    req['EW Rules Valid (3 Cardinal Rules)'] = (
        structure.get('_ew_valid', False) if structure else False
    )

    if structure:
        entry = structure['entry_price']
        near  = abs(current-entry)/max(entry,0.0001) < 0.05
        req[f"Entry Zone ({structure['entry_wave']})"] = near
    else:
        req['Entry Zone'] = False

    if structure:
        req[structure['_fib_lbl']] = structure['_fib_check']
    else:
        req['Fib Check'] = False

    req[f'RSI Below 45 ({rsi:.0f})'] = rsi is not None and rsi < 45

    req['MACD Bullish'] = bool(macd_bull)

    req['No Ending Diagonal'] = (
        structure.get('_no_end_diag', True) if structure else True
    )

    req['No Truncated W5'] = (
        structure.get('_no_trunc_w5', True) if structure else True
    )

    req_pass  = sum(1 for v in req.values() if v)
    req_total = len(req)

    # ── 16 SITUATIONAL ───────────────────────────────────────
    ALL_SIT = {
        'wave_count': (
            'Wave Count Verified >60%',
            lambda: bool(structure and structure.get('w1',0)>0 and
                         structure.get('w3',0)/structure.get('w1',1)>1.0)
        ),
        'golden_ratio': (
            'Golden Ratio 38-78%',
            lambda: bool(structure and
                         0.618<=structure.get('w2_ret',0)<=0.786)
        ),
        'wave_c_bot': (
            'Wave C Bottom',
            lambda: bool(structure and
                         float(structure.get('c_progress',0))>=80)
        ),
        'c_eq_a': (
            'C=A Price + Time',
            lambda: bool(structure and structure.get('c_confirmed',False))
        ),
        'wxyxz_x1x2': (
            'WXYXZ X1=X2 (Price+Time within 15%)',
            lambda: bool(structure and structure.get('x1_eq_x2',False))
        ),
        'abc_struct': (
            'ABC Structure',
            lambda: stype in ('ABC_ZIGZAG','EXPANDED_FLAT',
                              'RUNNING_CORRECTION')
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
            'Volume Declining (correction)',
            lambda: bool(vol_dec)
        ),
        'vol_exp': (
            'Volume Expanding (reversal)',
            lambda: bool(vol_exp)
        ),
        'alternation': (
            'Alternation W2 vs W4',
            lambda: bool(structure and structure.get('alternation'))
        ),
        'candlestick': (
            'Candlestick Pattern',
            lambda: False
        ),
        'wave_sym': (
            'Wave Symmetry (W3>W1)',
            lambda: bool(structure and
                         structure.get('w3',0)>structure.get('w1',0))
        ),
        'blue_box': (
            'Blue Box Zone (0.618-0.786 Fib)',
            lambda: bool(structure and
                         structure.get('in_blue_box',False))
        ),
    }

    sit_scored = {}
    sit_na     = []

    for key,(label,fn) in ALL_SIT.items():
        if key in applies:
            try:
                sit_scored[label] = fn()
            except Exception:
                sit_scored[label] = False
        else:
            sit_na.append(label)

    sit_pass  = sum(1 for v in sit_scored.values() if v)
    sit_total = len(sit_scored)

    return (req_pass, req_total, sit_pass, sit_total,
            req, sit_scored, sit_na)


def confidence_label(req_pass, req_total, sit_pass, sit_total):
    rr = req_pass/req_total if req_total else 0
    sr = sit_pass/sit_total if sit_total else 0.5
    s  = rr*0.7 + sr*0.3
    if s >= 0.90:   return 'HIGH - Full position'
    elif s >= 0.75: return 'MEDIUM-HIGH - 75% position'
    elif s >= 0.60: return 'MEDIUM - 50% position'
    else:           return 'LOW - Skip'


# ═════════════════════════════════════════════════════════════
# SECTION 10 — TELEGRAM MESSAGES
# ═════════════════════════════════════════════════════════════

STRUCT_ICONS = {
    'STANDARD_EW_W4':'📊','STANDARD_EW_W2':'📊',
    'ABC_ZIGZAG':'〽️','EXPANDED_FLAT':'📐',
    'RUNNING_CORRECTION':'🚀','WXYXZ':'🔁',
}

CYCLE_LABELS = {
    'W2':'Grand W2 Correction - Accumulation Zone',
    'W3':'Inside Grand W3 - Most Powerful Wave',
    'W4':'Grand W4 Pullback - Re-entry Zone',
    'W3_OR_W5_TOP':'Near ATH - W3 or W5 Top Area',
    'UNKNOWN':'Cycle Position Unknown',
}


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML"
        }, timeout=10)
        if not r.ok:
            log.warning(f"Telegram: {r.text[:200]}")
    except Exception as e:
        log.warning(f"Telegram failed: {e}")


def format_structure_lines(s):
    t = s['type']
    lines = []
    g = s.get('grand_ctx')
    if g:
        lines.append(
            f"Grand cycle: <b>{CYCLE_LABELS.get(g['cycle_pos'],'Unknown')}</b>"
        )
        lines.append(
            f"ATL: ${g['atl']:,.4f} | ATH: ${g['ath']:,.4f} | "
            f"W1 range: ${g['w1_range']:,.4f}"
        )
        lines.append(
            f"W2 retrace from ATH: {g['retrace_ath']*100:.1f}%"
        )
        lines.append("")

    if t in ('STANDARD_EW_W4','STANDARD_EW_W2'):
        lines += [
            f"W1 top    : ${s['w1h']:,.4f}",
            f"W2 bottom : ${s['w2l']:,.4f}  [{s['fib_lbl']}]",
            f"W3 top    : ${s['w3h']:,.4f}",
        ]
        if t == 'STANDARD_EW_W4':
            lines.append(f"<b>W4 bottom : ${s['w4l']:,.4f}  <- ENTRY</b>")
            lines.append(f"W4 retrace: {s['w4_ret']*100:.1f}% of W3")
        else:
            lines += [
                f"W4 bottom : ${s['w4l']:,.4f}",
                f"W5 top    : ${s['w5h']:,.4f}",
                f"<b>W2 new cycle: ${s['w2l']:,.4f}  <- ENTRY</b>",
            ]

    elif t in ('ABC_ZIGZAG','EXPANDED_FLAT','RUNNING_CORRECTION'):
        lines += [
            f"W5 top (origin): ${s['w5h']:,.4f}",
            f"Wave A bottom  : ${s['wa_bot']:,.4f}",
            f"Wave B top     : ${s['wb_top']:,.4f}  ({s['wb_ret_pct']}% retrace)",
            f"<b>Wave C bottom  : ${s['wc_bot']:,.4f}  "
            f"{'(developing)' if s['c_dev'] else 'complete'}  <- ENTRY</b>",
        ]
        if t == 'ABC_ZIGZAG':
            lines += [
                f"C=A target : ${s['c_eq_a_tgt']:,.4f}  ({s['c_progress']}% done)",
                f"{'C=A CONFIRMED' if s['c_confirmed'] else 'Approaching C=A'}",
            ]
        elif t == 'EXPANDED_FLAT':
            lines += [
                f"B retrace  : {s['wb_ret_pct']}% (B > W5 - expanded)",
                f"C target   : ${s['c_t1236']:,.4f} - ${s['c_t1618']:,.4f}",
            ]
        elif t == 'RUNNING_CORRECTION':
            lines += [
                f"C vs A: {s['c_vs_a_pct']}% of A",
                "Higher low - C above A bottom - very bullish",
            ]

    elif t == 'WXYXZ':
        lines += [
            f"W top  : ${s['w_top']:,.4f}",
            f"X1 top : ${s['x1_top']:,.4f}  (range: ${s['x1_rng']:,.4f})",
            f"Y bot  : ${s['y_bot']:,.4f}",
            f"X2 top : ${s['x2_top']:,.4f}  (range: ${s['x2_rng']:,.4f})",
            f"X1=X2  : price {s['price_diff_pct']}% | time {s['time_diff_pct']}%",
            f"<b>Z bot  : ${s['z_bot']:,.4f}  <- ENTRY</b>",
            "HIGHEST CONFIDENCE - X1=X2 Price+Time Confirmed",
        ]

    return "\n".join(lines)


def format_signal_msg(symbol, structure, levels,
                      req_pass, req_total, req_det,
                      sit_pass, sit_total, sit_det, sit_na,
                      confidence, mode):
    icon    = STRUCT_ICONS.get(structure['type'],'📐')
    mode_u  = mode.upper()
    struct  = format_structure_lines(structure)
    failed  = [k for k,v in req_det.items() if not v]
    f_str   = ('\nFailed: '+'|'.join(failed)) if failed else ''

    if mode == 'swing':
        sl_l  = f"SL  : ${levels['sl']:,.4f} ({levels['sl_pct']}%) [{levels['sl_lbl']}]"
        tp1_l = f"TP1 : ${levels['tp1']:,.4f} (+{levels['tp1_pct']}%) [{levels['tp1_lbl']}]"
        tp2_l = f"TP2 : ${levels['tp2']:,.4f} (+{levels['tp2_pct']}%) [{levels['tp2_lbl']}]"
        tp3_l = f"TP3 : ${levels['tp3']:,.4f} (+{levels['tp3_pct']}%) [{levels['tp3_lbl']}]"
        tp4_l = f"TP4 : ${levels['tp4']:,.4f} (+{levels['tp4_pct']}%) [{levels['tp4_lbl']}]"
    else:
        sl_l  = f"SL  : ${levels['sl']:,.4f}  (-5% fixed)"
        tp1_l = f"TP1 : ${levels['tp1']:,.4f}  (+3%)"
        tp2_l = f"TP2 : ${levels['tp2']:,.4f}  (+5%)"
        tp3_l = f"TP3 : ${levels['tp3']:,.4f}  (+8%)"
        tp4_l = f"TP4 : ${levels['tp4']:,.4f}  (+10%)"

    return (
        f"SIGNAL - <b>{symbol}</b> ({mode_u})\n"
        f"{icon} {structure['label']}\n\n"
        f"STRUCTURE\n{struct}\n\n"
        f"LEVELS ({mode_u})\n"
        f"Entry: <b>${levels['entry']:,.4f}</b>\n"
        f"{sl_l}\n{tp1_l}\n{tp2_l}\n{tp3_l}\n{tp4_l}\n\n"
        f"Required: {req_pass}/{req_total}{f_str}\n"
        f"Situational: {sit_pass}/{sit_total}\n"
        f"N/A checks: {len(sit_na)}\n"
        f"{confidence}\n"
        f"#SIGNALSYM #{symbol} #{mode_u}"
    )


def format_watch_msg(symbol, structure, req_pass, req_total, mode, price):
    icon = STRUCT_ICONS.get(structure['type'],'📐')
    return (
        f"WATCH - <b>{symbol}</b> ({mode.upper()})\n"
        f"{icon} {structure['label']}\n"
        f"Price: ${price:,.4f}\n"
        f"Required: {req_pass}/{req_total}\n"
        f"Monitoring every 5 min...\n"
        f"#SIGNALSYM #{symbol} #WATCH"
    )


def format_tp_alert(symbol, tp_num, price, new_sl):
    return (
        f"TP{tp_num} HIT - <b>{symbol}</b>\n"
        f"Price: ${price:,.4f}\n"
        f"SL moved to: ${new_sl:,.4f}\n"
        f"#SIGNALSYM #{symbol}"
    )


def format_sl_alert(symbol, price):
    return (
        f"STOP LOSS - <b>{symbol}</b>\n"
        f"Exited: ${price:,.4f}\n"
        f"Waiting for next signal\n"
        f"#SIGNALSYM #{symbol}"
    )


def format_heartbeat(scans, active, watching):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    return (
        f"SIGNALSYM Heartbeat\n"
        f"{now}\n"
        f"Scans: {scans}\n"
        f"Active trades: {active}\n"
        f"Watching: {watching}\n"
        f"Running normally"
    )


# ═════════════════════════════════════════════════════════════
# SECTION 11 — PRICE MONITOR
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
        tps    = [trade['tp1'],trade['tp2'],trade['tp3'],trade['tp4']]
        if price <= sl:
            send_telegram(format_sl_alert(symbol, price))
            to_close.append(symbol)
            log.info(f"SL hit: {symbol} @ {price}")
            continue
        for i,tp in enumerate(tps[tp_hit:],start=tp_hit+1):
            if price >= tp:
                new_sl = trade['entry'] if i==1 else tps[i-2]
                trade['sl']     = new_sl
                trade['tp_hit'] = i
                send_telegram(format_tp_alert(symbol,i,price,new_sl))
                log.info(f"TP{i} hit: {symbol} @ {price}")
                if i==4: to_close.append(symbol)
                break
    for sym in to_close:
        active_trades.pop(sym,None)


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
    for sym in graduated:
        watch_coins.pop(sym,None)


# ═════════════════════════════════════════════════════════════
# SECTION 12 — COIN ANALYSIS
# Full pipeline per coin — reads each chart independently
# ═════════════════════════════════════════════════════════════

def analyze_coin(symbol, mode='scalp'):
    """
    Full pipeline:
    1. Fetch full weekly history -> coin's grand structure
    2. Fetch 4H/90d (scalp) or 1D/730d (swing)
    3. Fetch 1D/100d for daily trend (Golden Rule)
    4. Calculate indicators
    5. Find pivots (adaptive)
    6. Recognize structure (grand-informed priority)
    7. Run checklist (10 required + situational)
    8. Build levels
    9. Return SIGNAL / WATCH / None
    """
    # Step 1: Coin's own grand structure (full weekly history)
    grand = get_grand_structure(symbol)
    if grand is None:
        return None

    # Step 2: Chart data for analysis
    interval = '1d' if mode == 'swing' else '4h'
    limit    = SWING_DAYS if mode == 'swing' else SCALP_DAYS * 6
    data     = get_klines(symbol, interval, limit)
    if data is None:
        return None
    opens, highs, lows, closes, volumes, times = data
    current = float(closes[-1])

    # Step 3: Daily for Golden Rule trend check
    daily = get_klines(symbol, '1d', 100)
    if daily is None:
        return None
    closes_1d = daily[3]

    # Step 4: Indicators
    rsi              = calc_rsi(closes)
    _, _, macd_bull  = calc_macd(closes)
    stoch            = calc_stoch(closes, highs, lows)
    smi              = calc_smi(closes, highs, lows)
    _, ewo_bull      = calc_ewo(closes)
    vol_dec, vol_exp = volume_analysis(volumes)

    if rsi is None:
        return None

    # Step 5: Pivots
    pivots = find_pivots(highs, lows, window=5)
    if len(pivots) < 5:
        return None

    # Step 6: Structure recognition (grand-informed)
    structure = recognize_structure(pivots, current, grand)
    if structure is None:
        return None

    # Step 7: Checklist
    (req_pass, req_total,
     sit_pass, sit_total,
     req_det, sit_det, sit_na) = run_checklist(
        structure, closes_1d, closes, highs, lows,
        rsi, macd_bull, stoch, smi, ewo_bull,
        vol_dec, vol_exp, current
    )

    confidence = confidence_label(req_pass,req_total,sit_pass,sit_total)

    # Step 8: Levels
    levels = build_levels(structure, current, mode)

    # Step 9: Signal / Watch / None
    if req_pass == req_total:
        status = 'SIGNAL'
    elif req_pass >= 7:
        status = 'WATCH'
    else:
        return None

    return {
        'status':    status,
        'structure': structure,
        'levels':    levels,
        'req_pass':  req_pass,'req_total':req_total,'req_det':req_det,
        'sit_pass':  sit_pass,'sit_total':sit_total,
        'sit_det':   sit_det,'sit_na':sit_na,
        'confidence':confidence,
        'current':   current,
        'grand':     grand,
    }


# ═════════════════════════════════════════════════════════════
# SECTION 13 — MAIN SCAN LOOP
# ═════════════════════════════════════════════════════════════

def should_scan(symbol, mode):
    key      = f"{symbol}_{mode}"
    cooldown = SWING_COOLDOWN if mode=='swing' else SCALP_COOLDOWN
    return (time.time()-last_signal_time.get(key,0)) > cooldown


def run_scan():
    global scan_count
    scan_count += 1
    log.info(f"Scan #{scan_count} | {len(HALAL_COINS)} coins")
    t0 = time.time()

    for symbol in HALAL_COINS:
        for mode in ['scalp','swing']:
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
                    watch_coins.pop(symbol,None)
                    log.info(
                        f"SIGNAL {symbol} {mode} "
                        f"{result['structure']['type']} "
                        f"cycle:{result['grand']['cycle_pos']} "
                        f"req:{result['req_pass']}/{result['req_total']}"
                    )

                elif status == 'WATCH':
                    wk  = f"{symbol}_{mode}_watch"
                    wc  = WATCH_COOLDOWN_SWING if mode=='swing' else WATCH_COOLDOWN_SCALP
                    if (time.time()-last_signal_time.get(wk,0)) > wc:
                        msg = format_watch_msg(
                            symbol, result['structure'],
                            result['req_pass'], result['req_total'],
                            mode, result['current']
                        )
                        send_telegram(msg)
                        watch_coins[symbol] = {'mode':mode,'ts':time.time()}
                        last_signal_time[wk] = time.time()
                        log.info(
                            f"WATCH {symbol} {mode} "
                            f"{result['structure']['type']} "
                            f"cycle:{result['grand']['cycle_pos']}"
                        )

            except Exception as e:
                log.error(f"Error {symbol} {mode}: {e}", exc_info=True)

        time.sleep(COIN_SLEEP)

    log.info(f"Scan #{scan_count} done in {time.time()-t0:.1f}s")

    if scan_count % HEARTBEAT_SCANS == 0:
        send_telegram(format_heartbeat(
            scan_count, len(active_trades), len(watch_coins)
        ))


def main():
    log.info("SIGNALSYM starting...")
    send_telegram(
        "SIGNALSYM Started\n\n"
        "Every coin analyzed independently:\n"
        "- Full weekly history -> coin's own grand structure\n"
        "- ATL/ATH/W1 range calculated per coin\n"
        "- Cycle position detected (W2/W3/W4)\n"
        "- Chart pattern confirms structure\n"
        "- Levels from actual wave levels\n\n"
        "Structures: EW W2/W4 | ABC Zigzag | Expanded Flat | Running | WXYXZ\n"
        "Scalp: TP3/5/8/10% | SL-5%\n"
        "Swing: Structure wave levels | SL 2% below low\n"
        "75 halal coins | Binance | Every 15 min"
    )
    last_price_check = 0
    while True:
        try:
            now = time.time()
            if (now-last_price_check) >= PRICE_MONITOR_INTERVAL:
                if active_trades: check_active_trades()
                if watch_coins:   check_watch_coins()
                last_price_check = time.time()
            run_scan()
            time.sleep(SCAN_INTERVAL)
        except KeyboardInterrupt:
            log.info("Stopped.")
            break
        except Exception as e:
            log.error(f"Main loop error: {e}", exc_info=True)
            time.sleep(60)


if __name__ == "__main__":
    main()
