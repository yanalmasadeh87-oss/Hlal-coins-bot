import requests
import time
import math
import os
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)
import functools
import builtins
print = functools.partial(builtins.print, flush=True)

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

API_PORT = int(os.getenv("PORT", 8080))

def start_api_server():
    class APIHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            if self.path == '/api/status':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                active_sigs = [t for t in active_trades.values() if not t.get("closed")]
                watches = list(sent_watches.keys())
                response = {
                    "version": "V8",
                    "scan_count": scan_count,
                    "timestamp": datetime.now().isoformat(),
                    "market_ctx": market_ctx,
                    "active_signals": len(active_sigs),
                    "active_trades": active_sigs,
                    "watch_list": watches,
                    "sent_signals_count": len(sent_signals),
                    "sent_watches_count": len(sent_watches),
                    "engine_data": {
                        "multi_degree": "Weekly+Monthly validation active",
                        "liquidity": "BOS/CHoCH detection active",
                        "mtf": "1D->4H->1H alignment active",
                        "triangle": "ABCDE detection active",
                        "extended_wave": "W3/W5 extended detection active",
                        "candlestick": "Pattern confirmation active",
                        "market_data": "100% Binance - no CoinGecko dependency"
                    }
                }
                self.wfile.write(json.dumps(response, indent=2).encode())
            elif self.path == '/api/signals':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                signals_data = {
                    "signals": [t for t in active_trades.values() if not t.get("closed")],
                    "watches": [{"sym": k.split("_")[0], "type": k.split("_")[-1]} for k in sent_watches.keys()],
                    "stats": {
                        "scans": scan_count,
                        "signals": len(sent_signals),
                        "watches": len(sent_watches),
                        "trades": len([t for t in active_trades.values() if not t.get("closed")])
                    }
                }
                self.wfile.write(json.dumps(signals_data, indent=2).encode())
            else:
                self.send_response(404)
                self.end_headers()

    server = HTTPServer(('0.0.0.0', API_PORT), APIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print("  [API] Dashboard server running on port " + str(API_PORT))

# ================================================================
# CONFIGURATION
# ================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7975488031:AAHLdeNTM-YIItriXwradU4bPyCMdR-mAIY")
CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID", "8422276082")
BN_BASE        = "https://api.binance.us/api/v3"
TG_BASE        = None

# ================================================================
# HALAL WATCHLIST
# ================================================================
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

# ================================================================
# GLOBAL STATE
# ================================================================
sent_signals   = {}
sent_watches   = {}
scan_count     = 0
active_trades  = {}
market_ctx     = None
_ctx_history   = []
_structure_memory = {}

# ================================================================
# STATE PERSISTENCE
# Try multiple paths in order — use the first writable one.
# /opt/render/project/src/ persists across Render deploys.
# Falls back to /tmp if running locally or path not available.
# ================================================================
def _get_state_path():
    """Find the best persistent path available."""
    candidates = [
        "/opt/render/project/src/signalsym_state.json",
        "/app/signalsym_state.json",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "signalsym_state.json"),
        "/tmp/signalsym_state.json",
    ]
    for path in candidates:
        try:
            dir_ = os.path.dirname(path)
            if os.access(dir_, os.W_OK):
                return path
        except:
            pass
    return "/tmp/signalsym_state.json"

STATE_FILE = _get_state_path()

def save_state():
    """Persist cooldowns to disk."""
    try:
        state = {"sent_signals": sent_signals, "saved_at": time.time()}
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print("  [STATE] Save failed: " + str(e))

def load_state():
    """Load cooldowns from disk on startup."""
    global sent_signals
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        age = time.time() - state.get("saved_at", 0)
        if age < 86400:
            now = time.time()
            for key, ts in state.get("sent_signals", {}).items():
                cooldown = 28800 if "swing" in key else 14400
                if now - ts < cooldown:
                    sent_signals[key] = ts
            print("  [STATE] Restored " + str(len(sent_signals)) +
                  " cooldowns from " + STATE_FILE +
                  " (age=" + str(round(age/60)) + "min)")
        else:
            print("  [STATE] State too old — starting fresh")
    except FileNotFoundError:
        print("  [STATE] No state file — starting fresh (" + STATE_FILE + ")")
    except Exception as e:
        print("  [STATE] Load error: " + str(e))



# ================================================================
# TELEGRAM
# ================================================================
def init_telegram():
    global TG_BASE
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("WARNING: Using placeholder token.")
        return False
    TG_BASE = "https://api.telegram.org/bot" + TELEGRAM_TOKEN
    return True

def send_msg(msg):
    if not TG_BASE:
        print("[NO TG] " + msg[:80])
        return
    try:
        requests.post(TG_BASE + "/sendMessage",
            json={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML","disable_web_page_preview":True},
            timeout=10)
    except Exception as e:
        print("  TG error: " + str(e))

# ================================================================
# DATA FETCH
# ================================================================
def fetch_klines_full(sym, interval="1d", limit=365):
    for attempt in range(3):
        try:
            if attempt > 0:
                wait = 2 ** attempt
                print("  Retry " + sym + " " + interval + " attempt " + str(attempt+1) + " wait " + str(wait) + "s")
                time.sleep(wait)
            r = requests.get(BN_BASE + "/klines",
                params={"symbol":sym+"USDT","interval":interval,"limit":limit},
                timeout=20)
            if r.status_code == 429:
                print("  RATE LIMITED — waiting 30s")
                time.sleep(30)
                continue
            if r.status_code == 418:
                print("  IP BANNED — waiting 60s")
                time.sleep(60)
                continue
            data = r.json()
            if not data or isinstance(data, dict):
                if attempt == 2:
                    print("  Fetch empty " + sym + " " + interval + " status=" + str(r.status_code))
                continue
            prices=[float(k[4]) for k in data]
            highs=[float(k[2]) for k in data]
            lows=[float(k[3]) for k in data]
            vols=[float(k[5]) for k in data]
            opens=[float(k[1]) for k in data]
            return prices,highs,lows,vols,opens
        except Exception as e:
            print("  Fetch error " + sym + " " + interval + " attempt " + str(attempt+1) + ": " + str(e)[:60])
    return [],[],[],[],[]

def fetch_global_ath(sym):
    try:
        r = requests.get(BN_BASE + "/klines",
            params={"symbol":sym+"USDT","interval":"1w","limit":200}, timeout=15)
        data = r.json()
        if not data or isinstance(data, dict):
            return 0
        return max(float(k[2]) for k in data)
    except:
        return 0

# ================================================================
# MARKET CONTEXT — CoinGecko for BTC.D/TOTAL/TOTAL3 (exact real data)
# Retries up to 3 times per scan. Never falls back to fake 50%.
# If all retries fail, skips the scan rather than use wrong data.
# ================================================================
_cg_last_success = 0
_cg_cached = None

def fetch_market_context():
    """
    Fetches BTC.D, TOTAL, TOTAL3 from CoinGecko /v3/global.
    This is the ONLY source — no calculations, no estimates.
    Retries 3 times with backoff. Uses last successful value if
    within 2 hours. Beyond 2 hours stale = return None (skip scan).
    Fear & Greed from alternative.me separately.
    """
    global _ctx_history, _cg_last_success, _cg_cached

    # --- CoinGecko: up to 3 attempts ---
    cg_data = None
    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(5 * attempt)
                print("  [CTX] CoinGecko retry " + str(attempt + 1))
            r = requests.get(
                "https://api.coingecko.com/api/v3/global",
                timeout=15,
                headers={"User-Agent": "SIGNALSYM/8.0", "Accept": "application/json", "x-cg-demo-api-key": "CG-FPGBHDZ1DTNv1Uj1Uowe4pZ7"}
            )
            if r.status_code == 200:
                gdata = r.json().get("data", {})
                btc_dom = float(gdata["market_cap_percentage"]["btc"])
                eth_dom = float(gdata["market_cap_percentage"].get("eth", 10))
                total   = float(gdata["total_market_cap"]["usd"])
                btc_mcap = total * btc_dom / 100
                eth_mcap = total * eth_dom / 100
                total3   = total - btc_mcap - eth_mcap
                cg_data  = {
                    "btc_dom": round(btc_dom, 2),
                    "total":   total,
                    "total3":  total3,
                    "btc_mcap": btc_mcap,
                    "eth_mcap": eth_mcap,
                }
                _cg_last_success = time.time()
                _cg_cached = cg_data
                print("  [CTX] CoinGecko OK: BTC.D=" + str(round(btc_dom, 2)) +
                      "% TOTAL=$" + str(round(total / 1e12, 2)) + "T")
                break
            elif r.status_code == 429:
                wait = 20 * (attempt + 1)
                print("  [CTX] CoinGecko rate limit — waiting " + str(wait) + "s")
                time.sleep(wait)
            else:
                print("  [CTX] CoinGecko status=" + str(r.status_code))
        except Exception as e:
            print("  [CTX] CoinGecko error attempt " + str(attempt + 1) + ": " + str(e)[:60])

    # If CoinGecko failed, use cache if within 2 hours
    if cg_data is None:
        if _cg_cached and (time.time() - _cg_last_success) < 7200:
            age_min = round((time.time() - _cg_last_success) / 60)
            print("  [CTX] Using cached data (" + str(age_min) + "min old) — still valid")
            cg_data = _cg_cached
        else:
            # Cache too old or no cache — return None to skip this scan
            age = "no cache" if not _cg_cached else str(round((time.time() - _cg_last_success)/60)) + "min old"
            print("  [CTX] CoinGecko unavailable (" + age + ") — scan will skip market filters")
            return None

    # --- Fear & Greed ---
    fg_now = 50; fg_7d = 50
    try:
        r3 = requests.get("https://api.alternative.me/fng/?limit=7", timeout=10)
        fng = r3.json().get("data", [])
        fg_now = int(fng[0]["value"]) if fng else 50
        fg_7d  = int(fng[-1]["value"]) if len(fng) >= 7 else fg_now
    except:
        print("  [CTX] FNG failed — using neutral 50")

    if fg_now <= 20:   fg_zone = "EXTREME_FEAR"
    elif fg_now <= 40: fg_zone = "FEAR"
    elif fg_now <= 60: fg_zone = "NEUTRAL"
    elif fg_now <= 80: fg_zone = "GREED"
    else:              fg_zone = "EXTREME_GREED"

    fg_trend = "RISING" if fg_now > fg_7d + 3 else "FALLING" if fg_now < fg_7d - 3 else "NEUTRAL"

    ctx = {
        "btc_dom":  cg_data["btc_dom"],
        "total":    cg_data["total"],
        "total3":   cg_data["total3"],
        "btc_mcap": cg_data["btc_mcap"],
        "eth_mcap": cg_data["eth_mcap"],
        "fg_now":   fg_now,
        "fg_zone":  fg_zone,
        "fg_trend": fg_trend,
        "source":   "coingecko_live"
    }

    _ctx_history.append({
        "btc_dom": cg_data["btc_dom"],
        "total":   cg_data["total"],
        "total3":  cg_data["total3"],
        "ts":      time.time()
    })
    if len(_ctx_history) > 96:
        _ctx_history.pop(0)

    def get_trend(key):
        if len(_ctx_history) < 4: return "NEUTRAL"
        old = _ctx_history[0][key]; new = _ctx_history[-1][key]
        if old == 0: return "NEUTRAL"
        chg = (new - old) / old * 100
        return "RISING" if chg > 3.0 else "FALLING" if chg < -3.0 else "NEUTRAL"

    ctx["btc_dom_trend"] = get_trend("btc_dom")
    ctx["total_trend"]   = get_trend("total")
    ctx["total3_trend"]  = get_trend("total3")
    ctx["history_len"]   = len(_ctx_history)

    print("  CTX: BTC.D=" + str(ctx["btc_dom"]) + "% FG=" + str(fg_now) +
          "(" + fg_zone + ") TOTAL=$" + str(round(ctx["total"]/1e12, 2)) + "T [CoinGecko LIVE]")
    return ctx

# _build_fallback_ctx removed in V8 — CoinGecko with retry is the only source

def context_adjustment(sym, ctx):
    if not ctx: return 0
    adj = 0
    fg = ctx.get("fg_now", 50)
    if fg <= 20:   adj -= 15
    elif fg <= 35: adj -= 8
    elif fg >= 80: adj -= 3
    elif fg >= 60: adj += 5

    total_trend = ctx.get("total_trend", "NEUTRAL")
    if total_trend == "FALLING": adj -= 10
    elif total_trend == "RISING": adj += 5

    if sym not in ("BTC", "ETH"):
        btc_dom = ctx.get("btc_dom", 50)
        btc_dom_trend = ctx.get("btc_dom_trend", "NEUTRAL")
        total3_trend  = ctx.get("total3_trend", "NEUTRAL")
        if btc_dom > 55 and btc_dom_trend == "RISING": adj -= 8
        elif btc_dom < 45 and btc_dom_trend == "FALLING": adj += 5
        if total3_trend == "FALLING": adj -= 5
        elif total3_trend == "RISING": adj += 5

    return max(-20, min(+15, adj))

# ================================================================
# HARD MARKET FILTERS
# ================================================================
def hard_market_filter(sym, ctx):
    if not ctx:
        return True, "No market context"

    fg            = ctx.get("fg_now", 50)
    fg_zone       = ctx.get("fg_zone", "NEUTRAL")
    total_trend   = ctx.get("total_trend", "NEUTRAL")
    btc_dom       = ctx.get("btc_dom", 50)
    btc_dom_trend = ctx.get("btc_dom_trend", "NEUTRAL")
    total3_trend  = ctx.get("total3_trend", "NEUTRAL")
    history_len   = ctx.get("history_len", 0)

    enough_history = history_len >= 8  # V8: lowered from 96 to 8 — trend signals faster

    if fg <= 20 and fg_zone == "EXTREME_FEAR":
        return False, "HARD FILTER: Extreme Fear (FG=" + str(fg) + ") — no entries"

    if enough_history and total_trend == "FALLING" and sym not in ("BTC", "ETH"):
        return False, "HARD FILTER: TOTAL falling — " + sym + " blocked"

    if btc_dom > 58 and btc_dom_trend == "RISING" and sym not in ("BTC", "ETH"):
        return False, "HARD FILTER: BTC.D=" + str(round(btc_dom,1)) + "% rising — " + sym + " blocked"

    if enough_history and total3_trend == "FALLING" and btc_dom_trend == "RISING" and sym != "BTC":
        return False, "HARD FILTER: TOTAL3 falling + BTC.D rising — only BTC allowed"

    return True, "Market OK — BTC.D=" + str(round(btc_dom,1)) + "% FG=" + str(fg) + " [" + ctx.get("source","?") + "]"

# ================================================================
# INDICATORS
# ================================================================
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
    rsi_now  = calc_rsi(prices[-period:])
    rsi_prev = calc_rsi(prices[-period * 2:-period]) if len(prices) >= period * 2 else rsi_now
    bullish  = prices[-1] < prices[-period] * 0.99 and rsi_now > rsi_prev * 1.02
    bearish  = prices[-1] > prices[-period] * 1.01 and rsi_now < rsi_prev * 0.98
    return {"bullish": bullish, "bearish": bearish}

# ================================================================
# V8: CANDLESTICK ENGINE
# ================================================================
def detect_candlestick_patterns(opens, highs, lows, closes):
    if len(closes) < 5 or len(opens) < 5:
        return {"patterns": [], "bullish_score": 0, "bearish_score": 0}

    patterns = []; bullish_score = 0; bearish_score = 0

    for i in range(max(0, len(closes) - 5), len(closes)):
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]
        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        total_range = h - l if h != l else 0.0001

        if body / total_range < 0.3:
            if lower_wick > body * 2 and c > o:
                patterns.append("HAMMER"); bullish_score += 3
            elif upper_wick > body * 2 and c < o:
                patterns.append("SHOOTING_STAR"); bearish_score += 3

        if i > 0:
            prev_o, prev_c = opens[i-1], closes[i-1]
            prev_body = abs(prev_c - prev_o)
            if body > prev_body * 1.5:
                if c > o and prev_c < prev_o and c > prev_o and o < prev_c:
                    patterns.append("BULL_ENGULFING"); bullish_score += 4
                elif c < o and prev_c > prev_o and c < prev_o and o > prev_c:
                    patterns.append("BEAR_ENGULFING"); bearish_score += 4

        if body / total_range < 0.1:
            patterns.append("DOJI")
            if i == len(closes) - 1:
                avg = sum(closes[-10:]) / min(len(closes), 10)
                if closes[i] < avg:
                    bullish_score += 1

        if i >= 2:
            c1, c2, c3 = closes[i-2], closes[i-1], closes[i]
            o1, o2, o3 = opens[i-2], opens[i-1], opens[i]
            if c1 < o1 and abs(c2 - o2) < abs(c1 - o1) * 0.5 and c3 > o3 and c3 > (o1 + c1) / 2:
                patterns.append("MORNING_STAR"); bullish_score += 5
            if c1 > o1 and abs(c2 - o2) < abs(c1 - o1) * 0.5 and c3 < o3 and c3 < (o1 + c1) / 2:
                patterns.append("EVENING_STAR"); bearish_score += 5

    return {
        "patterns": list(set(patterns)),
        "bullish_score": min(bullish_score, 15),
        "bearish_score": min(bearish_score, 15)
    }

# ================================================================
# LIQUIDITY ENGINE
# ================================================================
def detect_liquidity_levels(prices, highs, lows, pivots, lookback=20):
    if len(prices) < lookback * 2:
        return {"bos": False, "choch": False, "bos_level": None, "choch_level": None, "direction": "neutral"}

    swing_highs = []; swing_lows = []
    for i in range(lookback, len(prices) - lookback):
        if highs[i] == max(highs[i-lookback:i+lookback+1]):
            swing_highs.append({"idx": i, "price": highs[i]})
        if lows[i] == min(lows[i-lookback:i+lookback+1]):
            swing_lows.append({"idx": i, "price": lows[i]})

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {"bos": False, "choch": False, "bos_level": None, "choch_level": None, "direction": "neutral"}

    last_sh = swing_highs[-1]; prev_sh = swing_highs[-2]
    last_sl = swing_lows[-1];  prev_sl = swing_lows[-2]
    current = prices[-1]

    bos = False; bos_level = None; bos_direction = "neutral"
    if current > last_sh["price"] * 1.005:
        bos = True; bos_level = last_sh["price"]; bos_direction = "bullish"
    elif current < last_sl["price"] * 0.995:
        bos = True; bos_level = last_sl["price"]; bos_direction = "bearish"

    choch = False; choch_level = None; choch_direction = "neutral"
    if len(swing_lows) >= 3:
        sl1, sl2, sl3 = swing_lows[-3], swing_lows[-2], swing_lows[-1]
        if sl1["price"] > sl2["price"] and sl3["price"] > sl2["price"]:
            choch = True; choch_level = sl3["price"]; choch_direction = "bullish"
    if len(swing_highs) >= 3:
        sh1, sh2, sh3 = swing_highs[-3], swing_highs[-2], swing_highs[-1]
        if sh1["price"] < sh2["price"] and sh3["price"] < sh2["price"]:
            choch = True; choch_level = sh3["price"]; choch_direction = "bearish"

    return {
        "bos": bos, "choch": choch, "bos_level": bos_level, "choch_level": choch_level,
        "direction": bos_direction if bos else choch_direction,
        "swing_highs": swing_highs[-5:], "swing_lows": swing_lows[-5:]
    }

# ================================================================
# TRIANGLE ENGINE
# ================================================================
def detect_triangle(prices, highs, lows, pivots):
    if len(pivots) < 6: return None
    peaks   = [p for p in pivots if p["type"] == "peak"]
    troughs = [p for p in pivots if p["type"] == "trough"]
    if len(peaks) < 3 or len(troughs) < 3: return None

    recent_peaks   = peaks[-3:]
    recent_troughs = troughs[-3:]

    contracting_highs = (recent_peaks[-1]["price"]   < recent_peaks[-2]["price"]   < recent_peaks[-3]["price"])
    contracting_lows  = (recent_troughs[-1]["price"] > recent_troughs[-2]["price"] > recent_troughs[-3]["price"])

    if contracting_highs and contracting_lows:
        high_slope = (recent_peaks[-1]["price"]   - recent_peaks[-3]["price"])   / max(recent_peaks[-1]["idx"]   - recent_peaks[-3]["idx"],   1)
        low_slope  = (recent_troughs[-1]["price"] - recent_troughs[-3]["price"]) / max(recent_troughs[-1]["idx"] - recent_troughs[-3]["idx"], 1)
        if (high_slope - low_slope) != 0:
            raw_apex = recent_peaks[-1]["idx"] + int(
                (recent_troughs[-1]["price"] - recent_peaks[-1]["price"]) / (high_slope - low_slope))
            apex_idx = max(0, min(raw_apex, len(prices) * 3))
        else:
            apex_idx = 0

        current = prices[-1]
        triangle_range = recent_peaks[-1]["price"] - recent_troughs[-1]["price"]
        breakout_threshold = triangle_range * 0.3
        near_apex    = abs(current - (recent_peaks[-1]["price"] + recent_troughs[-1]["price"]) / 2) < breakout_threshold
        breakout_up  = current > recent_peaks[-1]["price"] * 1.01

        if near_apex or breakout_up:
            return {
                "type": "CONTRACTING_TRIANGLE",
                "label": "Contracting Triangle (ABCDE) - Bullish Breakout",
                "score": 65, "entry_wave": "Wave E / Breakout", "entry_price": current,
                "target": recent_peaks[-3]["price"], "resistance": recent_peaks[-1]["price"],
                "support": recent_troughs[-1]["price"], "apex_idx": apex_idx,
                "breakout": breakout_up, "sub_type": "TRIANGLE_BULL"
            }

    expanding_highs = (recent_peaks[-1]["price"]   > recent_peaks[-2]["price"]   > recent_peaks[-3]["price"])
    expanding_lows  = (recent_troughs[-1]["price"] < recent_troughs[-2]["price"] < recent_troughs[-3]["price"])
    if expanding_highs and expanding_lows:
        return {"type": "EXPANDING_TRIANGLE", "label": "Expanding Triangle - High Volatility",
                "score": 40, "entry_wave": "Avoid", "entry_price": prices[-1], "sub_type": "TRIANGLE_EXPAND"}
    return None

# ================================================================
# EXTENDED WAVE DETECTION
# ================================================================
def detect_extended_wave(pivots, current):
    if len(pivots) < 6:
        return {"extended": False, "wave": None, "extension_ratio": 0, "tp_multiplier": 1.0}
    for i in range(len(pivots) - 6, -1, -1):
        if i + 5 >= len(pivots): continue
        p = pivots[i:i + 6]
        types = [x["type"] for x in p]
        if types != ["trough", "peak", "trough", "peak", "trough", "peak"]: continue
        w0 = p[0]["price"]; w1h = p[1]["price"]; w2l = p[2]["price"]
        w3h = p[3]["price"]; w4l = p[4]["price"]; w5h = p[5]["price"]
        w1 = w1h - w0; w3 = w3h - w2l; w5 = w5h - w4l
        if w1 <= 0: continue
        if w3 >= w1 * 1.618:
            return {"extended": True, "wave": "W3_EXTENDED", "extension_ratio": round(w3/w1,2),
                    "tp_multiplier": 1.618, "w1": w1, "w3": w3, "w5": w5,
                    "label": "Extended W3 (" + str(round(w3/w1,2)) + "x W1)"}
        if w5 >= w1 * 1.618 and w5 > w3 * 0.8:
            return {"extended": True, "wave": "W5_EXTENDED", "extension_ratio": round(w5/w1,2),
                    "tp_multiplier": 2.0, "w1": w1, "w3": w3, "w5": w5,
                    "label": "Extended W5 (" + str(round(w5/w1,2)) + "x W1)"}
        if abs(w5 - w1) / w1 < 0.15 and w3 > w1 * 1.0:
            return {"extended": False, "wave": "W1_W5_EQUALITY", "extension_ratio": 1.0,
                    "tp_multiplier": 1.0, "label": "W1=W5 Equality"}
    return {"extended": False, "wave": None, "extension_ratio": 0, "tp_multiplier": 1.0}

# ================================================================
# MTF ALIGNMENT
# ================================================================
def check_mtf_alignment(mtf_data):
    alignment = {"1d": "neutral", "4h": "neutral", "1h": "neutral", "score": 0, "details": []}
    for tf in ["1d", "4h", "1h"]:
        data   = mtf_data[tf]
        prices = data["prices"]
        if len(prices) < 50:
            alignment[tf] = "insufficient_data"; continue
        ma20   = sum(prices[-20:]) / 20
        ma50   = sum(prices[-50:]) / 50 if len(prices) >= 50 else ma20
        current = prices[-1]
        if current > ma20 and ma20 > ma50:            alignment[tf] = "bullish"
        elif current < ma20 and ma20 < ma50:          alignment[tf] = "bearish"
        elif current > ma20:                          alignment[tf] = "weak_bullish"
        elif current < ma20:                          alignment[tf] = "weak_bearish"
        else:                                         alignment[tf] = "neutral"

    bullish_count = sum(1 for tf in ["1d","4h","1h"] if alignment[tf] in ["bullish","weak_bullish"])
    bearish_count = sum(1 for tf in ["1d","4h","1h"] if alignment[tf] in ["bearish","weak_bearish"])

    if bullish_count == 3:
        alignment["score"] = 15; alignment["details"].append("Full bullish alignment 1D->4H->1H")
    elif bullish_count == 2:
        alignment["score"] = 8;  alignment["details"].append("Partial bullish alignment")
    elif bearish_count >= 2:
        alignment["score"] = -10; alignment["details"].append("Bearish alignment detected")

    if alignment["1d"] in ["bullish","weak_bullish"]:
        alignment["score"] += 5; alignment["details"].append("1D trend supportive")
    return alignment

# ================================================================
# VOLATILITY REGIME
# ================================================================
def detect_volatility_regime(prices, highs, lows):
    if len(prices) < 50:
        return {"type": "normal", "label": "Normal", "multiplier": 1.0, "atr": 0, "atr_pct": 0.04}
    atr     = calc_atr(highs, lows, prices, 14)
    avg_p   = sum(prices) / len(prices)
    atr_pct = atr / avg_p if avg_p > 0 else 0
    returns = [abs((prices[i]-prices[i-1])/prices[i-1]) for i in range(1,len(prices))]
    avg_ret = sum(returns)/len(returns) if returns else 0
    var     = sum((r-avg_ret)**2 for r in returns)/len(returns) if returns else 0
    std_dev = math.sqrt(var)
    if atr_pct > 0.08 or std_dev > 0.06:
        return {"type":"high","label":"High Volatility","multiplier":1.5,"atr":atr,"atr_pct":atr_pct}
    if atr_pct < 0.02 or std_dev < 0.015:
        return {"type":"low","label":"Low Volatility","multiplier":0.7,"atr":atr,"atr_pct":atr_pct}
    return {"type":"normal","label":"Normal Volatility","multiplier":1.0,"atr":atr,"atr_pct":atr_pct}

# ================================================================
# ADAPTIVE PIVOTS
# ================================================================
def detect_pivots_adaptive(prices, highs, lows, regime, mode="swing"):
    n       = len(prices)
    atr_pct = regime.get("atr_pct", 0.04)
    base_win = 5 if mode == "scalp" else max(3, min(15, int(n / (30 + atr_pct * 100))))
    win      = max(3, round(base_win * regime["multiplier"]))
    base_min = 0.05 if mode == "scalp" else 0.10
    min_move = base_min * regime["multiplier"]

    pivots = []
    for i in range(win, n - win):
        sl = prices[i - win:i + win + 1]
        mx = max(sl); mn = min(sl)
        if prices[i] == mx and prices[i] > prices[i-1] and prices[i] > prices[i+1]:
            s = abs(prices[i]-prices[i-win])/prices[i-win] if prices[i-win] > 0 else 0
            pivots.append({"idx":i,"price":prices[i],"type":"peak","strength":s})
        elif prices[i] == mn and prices[i] < prices[i-1] and prices[i] < prices[i+1]:
            s = abs(prices[i]-prices[i-win])/prices[i-win] if prices[i-win] > 0 else 0
            pivots.append({"idx":i,"price":prices[i],"type":"trough","strength":s})

    st = "trough" if prices[0] < prices[min(10,n-1)] else "peak"
    pivots.insert(0, {"idx":0,"price":prices[0],"type":st,"strength":0})
    pivots.append({"idx":n-1,"price":prices[-1],"type":"current","strength":0})

    sig = [pivots[0]]
    for p in pivots[1:]:
        prev = sig[-1]
        if prev["type"] == p["type"]:
            if p["type"] == "peak" and p["price"] > prev["price"]: sig[-1] = p
            elif p["type"] == "trough" and p["price"] < prev["price"]: sig[-1] = p
            continue
        move = abs((p["price"]-prev["price"])/prev["price"]) if prev["price"] > 0 else 0
        if move >= min_move: sig.append(p)

    # W1 size filter — adaptive based on ATR not fixed %
    # Removes structures where the first wave is smaller than
    # the coin's normal daily noise (ATR-based threshold)
    if len(sig) >= 2:
        w1_size = abs(sig[1]["price"] - sig[0]["price"])
        # Use ATR-based minimum: at least 1.5x ATR to be meaningful
        # For swing: atr from regime, for scalp same
        atr_val = regime.get("atr", 0)
        if atr_val > 0:
            min_w1 = atr_val * 1.5
        else:
            # Fallback: 3% of current price (half the old 6% — less aggressive)
            min_w1 = prices[-1] * 0.03
        if w1_size < min_w1:
            sig = sig[:1] + [sig[-1]]

    return sig, win, min_move

# ================================================================
# TREND ANALYSIS
# ================================================================
def analyze_trend(prices, weekly_prices, current):
    ma20  = sum(prices[-20:]) / 20 if len(prices) >= 20 else current
    ma50  = sum(prices[-50:]) / 50 if len(prices) >= 50 else current
    if len(weekly_prices) >= 200:   ma200 = sum(weekly_prices[-200:]) / 200
    elif len(prices) >= 200:        ma200 = sum(prices[-200:]) / 200
    else:                           ma200 = ma50

    e12  = calc_ema(prices, 12); e26 = calc_ema(prices, 26)
    ema12 = e12[-1] if e12 else current
    ema26 = e26[-1] if e26 else current
    momentum = (prices[-1]-prices[-10])/prices[-10]*100 if len(prices) >= 10 else 0

    score = 0
    if current > ma20:  score += 20
    if current > ma50:  score += 20
    if current > ma200: score += 25
    if ema12 > ema26:   score += 15
    if momentum > 0:    score += 10
    if len(prices) >= 25:
        slope = (ma20 - prices[-25]) / prices[-25] * 100
        if slope > 0: score += 10

    if score >= 85:    label = "STRONG_UPTREND"
    elif score >= 60:  label = "UPTREND"
    elif score <= 15:  label = "STRONG_DOWNTREND"
    elif score <= 40:  label = "DOWNTREND"
    else:              label = "NEUTRAL"

    return {"score":score,"label":label,"ma20":ma20,"ma50":ma50,"ma200":ma200,
            "momentum":momentum,"bullish":score>=60,"bearish":score<=40}

# ================================================================
# MARKET PHASE
# ================================================================
def read_market_phase(prices, highs, lows, pivots, current, pct_ath):
    if len(prices) < 50: return "UNKNOWN"
    ma20  = sum(prices[-20:]) / 20
    ma50  = sum(prices[-50:]) / 50
    ma200 = sum(prices[-200:]) / 200 if len(prices) >= 200 else ma50

    peaks   = [p for p in pivots if p["type"] == "peak"][-3:]
    troughs = [p for p in pivots if p["type"] == "trough"][-3:]

    hh = len(peaks)   >= 2 and peaks[-1]["price"]   > peaks[-2]["price"]
    hl = len(troughs) >= 2 and troughs[-1]["price"] > troughs[-2]["price"]
    lh = len(peaks)   >= 2 and peaks[-1]["price"]   < peaks[-2]["price"]
    ll = len(troughs) >= 2 and troughs[-1]["price"] < troughs[-2]["price"]

    in_correction = pct_ath < -20
    momentum = (prices[-1]-prices[-10])/prices[-10]*100 if len(prices) >= 10 else 0

    if len(prices) >= 20:
        rh = max(prices[-20:]); rl = min(prices[-20:])
        in_range = (rh-rl)/rl*100 < 12 if rl > 0 else False
    else:
        in_range = False

    if lh and ll and current < ma50:             return "DOWNTREND"
    if hh and hl and current > ma50 and current > ma200 and momentum > 5: return "IMPULSING"
    if hh and hl and current > ma50:             return "TRENDING_UP"
    if in_correction and (hh or hl):             return "CORRECTING_WITHIN_UPTREND"
    if in_correction:                            return "CORRECTING"
    if in_range and not in_correction:           return "RANGING"
    if current > ma50 and momentum > 5:          return "TRENDING_UP"
    if current < ma50 and momentum < -5:         return "TRENDING_DOWN"
    return "NEUTRAL"

# ================================================================
# HTF VALIDATION
# ================================================================
def htf_validation(sym):
    try:
        w_prices, _, _, _, _ = fetch_klines_full(sym, "1w", 52)
        if len(w_prices) < 20: return True, "HTF: No weekly data"
        w_ma20 = sum(w_prices[-20:]) / 20
        w_ma50 = sum(w_prices[-50:]) / 50 if len(w_prices) >= 50 else w_ma20
        w_cur  = w_prices[-1]
        w_mom  = (w_prices[-1]-w_prices[-4])/w_prices[-4]*100 if len(w_prices) >= 4 else 0
        # Only block truly bearish coins — deep below both MAs
        # Coins correcting near MA20/MA50 are normal buy zones
        if w_cur < w_ma20 * 0.85 and w_cur < w_ma50 * 0.80:
            return False, "HTF BLOCKED: Weekly deeply bearish (>15% below MA20)"
        if w_mom < -30:
            return False, "HTF BLOCKED: Weekly momentum < -30%"
        trend = "bull" if w_cur > w_ma20 else "neutral" if w_cur > w_ma50 else "bear"
        return True, "HTF OK: Weekly " + trend
    except:
        return True, "HTF: Error - passing"

# ================================================================
# MULTI-DEGREE VALIDATION
# ================================================================
def multi_degree_validation(sym, current, struct_type, pivots, htf_prices, htf_highs=None, htf_lows=None):
    if len(htf_prices) < 100:
        return True, "No weekly data", 0

    w_highs  = htf_highs if htf_highs else htf_prices
    w_lows   = htf_lows  if htf_lows  else htf_prices
    w_regime = detect_volatility_regime(htf_prices, w_highs, w_lows)
    w_pivots, _, _ = detect_pivots_adaptive(htf_prices, w_highs, w_lows, w_regime, "swing")

    if len(w_pivots) < 4:
        return True, "Weekly structure unclear", 0

    w_peaks   = [p for p in w_pivots if p["type"] == "peak"]
    w_troughs = [p for p in w_pivots if p["type"] == "trough"]
    if len(w_peaks) < 2 or len(w_troughs) < 2:
        return True, "Weekly pivots insufficient", 0

    w_hh = w_peaks[-1]["price"]   > w_peaks[-2]["price"]   if len(w_peaks)   >= 2 else False
    w_hl = w_troughs[-1]["price"] > w_troughs[-2]["price"] if len(w_troughs) >= 2 else False
    w_lh = w_peaks[-1]["price"]   < w_peaks[-2]["price"]   if len(w_peaks)   >= 2 else False
    w_ll = w_troughs[-1]["price"] < w_troughs[-2]["price"] if len(w_troughs) >= 2 else False

    weekly_degree = "UNKNOWN"; bonus = 0
    if w_hh and w_hl:
        if len(w_peaks) >= 3 and w_peaks[-1]["price"] > w_peaks[-2]["price"] > w_peaks[-3]["price"]:
            weekly_degree = "W3_EXTENDED_WEEKLY"; bonus = 15
        else:
            weekly_degree = "W1_OR_W5_WEEKLY"; bonus = 8
    elif w_lh and w_ll:
        weekly_degree = "W2_OR_W4_WEEKLY"; bonus = 0
    elif w_hh and w_ll:
        weekly_degree = "CORRECTING_WEEKLY"; bonus = 0
    else:
        weekly_degree = "NEUTRAL_WEEKLY"; bonus = 0

    monthly_degree = "UNKNOWN"; monthly_bonus = 0
    if len(htf_prices) >= 200:
        monthly_prices = htf_prices[::4]
        if len(monthly_prices) >= 50:
            m_regime = detect_volatility_regime(monthly_prices, monthly_prices, monthly_prices)
            m_pivots, _, _ = detect_pivots_adaptive(monthly_prices, monthly_prices, monthly_prices, m_regime, "swing")
            m_peaks   = [p for p in m_pivots if p["type"] == "peak"]
            m_troughs = [p for p in m_pivots if p["type"] == "trough"]
            if len(m_peaks) >= 2 and len(m_troughs) >= 2:
                m_hh = m_peaks[-1]["price"]   > m_peaks[-2]["price"]
                m_hl = m_troughs[-1]["price"] > m_troughs[-2]["price"]
                if m_hh and m_hl:
                    monthly_degree = "MONTHLY_BULLISH"; monthly_bonus = 10
                elif not m_hh and not m_hl:
                    monthly_degree = "MONTHLY_BEARISH"; monthly_bonus = -5

    if struct_type in ("EW_W2","EW_W4"):
        if weekly_degree in ("W3_EXTENDED_WEEKLY","W1_OR_W5_WEEKLY"):
            if monthly_degree == "MONTHLY_BULLISH":
                return True, "Monthly+Weekly Bullish | Daily " + struct_type + " perfect alignment", bonus+monthly_bonus
            return True, "Weekly " + weekly_degree + " | Daily " + struct_type + " aligned", bonus
        elif weekly_degree == "W2_OR_W4_WEEKLY":
            return True, "Weekly correction | Daily " + struct_type + " caution", -5

    elif struct_type in ("ABC_ZIGZAG","EXPANDED_FLAT","RUNNING_CORRECTION","CONTRACTING_TRIANGLE"):
        if weekly_degree in ("W2_OR_W4_WEEKLY","CORRECTING_WEEKLY"):
            if monthly_degree == "MONTHLY_BULLISH":
                return True, "Monthly Bullish | Weekly correction | Daily correction nested", bonus+monthly_bonus
            return True, "Weekly correction | Daily correction nested", bonus
        elif weekly_degree in ("W3_EXTENDED_WEEKLY","W1_OR_W5_WEEKLY"):
            return True, "Weekly impulse | Daily correction normal", bonus

    elif struct_type == "TREND_CONTINUATION":
        if weekly_degree in ("W3_EXTENDED_WEEKLY","W1_OR_W5_WEEKLY"):
            if monthly_degree == "MONTHLY_BULLISH":
                return True, "Monthly+Weekly Bullish | Daily trend aligned", bonus+monthly_bonus
            return True, "Weekly trend | Daily trend aligned", bonus
        else:
            return False, "HARD FILTER: Trend against weekly correction", 0

    return True, "Weekly " + weekly_degree + " | Monthly " + monthly_degree, bonus+monthly_bonus

# ================================================================
# FIBONACCI & PATTERN TOOLS
# ================================================================
def calc_fib_retrace(pivots):
    if len(pivots) < 3: return 0, False, "No data"
    w1r = abs(pivots[1]["price"] - pivots[0]["price"])
    if w1r == 0: return 0, False, "Invalid W1"
    w2r = abs(pivots[2]["price"] - pivots[1]["price"])
    ret = w2r / w1r * 100; valid = 38.2 <= ret <= 100
    if ret < 38.2:       lbl = "Shallow"
    elif ret <= 50:      lbl = "0.382 Fib"
    elif ret <= 61.8:    lbl = "0.500 Fib"
    elif ret <= 78.6:    lbl = "0.618 Golden"
    elif ret <= 100:     lbl = "0.786 Deep"
    else:                lbl = "W2>W1 Invalid"
    return ret, valid, lbl

def calc_c_equals_a(pivots, current):
    if len(pivots) < 4: return False, 0, 0, "Need more data"
    for i in range(len(pivots)-4,-1,-1):
        p0=pivots[i]; p1=pivots[i+1]; p2=pivots[i+2]; p3=pivots[i+3]
        if not (p0["type"]=="peak" and p1["type"]=="trough" and p2["type"]=="peak" and p3["type"]=="trough"):
            continue
        wa = abs(p0["price"]-p1["price"])
        if wa == 0: continue
        ct = p2["price"]; cat = ct-wa; ratio = (ct-current)/wa*100
        prox = abs(current-cat)/max(abs(cat),0.0001)*100
        at = p1["idx"]-p0["idx"]; ctt = p3["idx"]-p2["idx"]
        tr = ctt/at*100 if at > 0 else 0; te = 80 <= tr <= 120
        if prox <= 5 and te:   return True, cat, ratio, "C=A Price+Time"
        if prox <= 5:          return True, cat, ratio, "C=A Price"
        if 80 <= ratio <= 120: return True, cat, ratio, "Near C=A (" + str(round(ratio)) + "%)"
        return False, cat, ratio, "C=A at " + str(cat)
    return False, 0, 0, "No ABC found"

# ================================================================
# CLASSICAL PATTERNS
# ================================================================
def detect_classical_patterns(prices, pivots, current):
    if len(prices) < 30 or len(pivots) < 4: return None
    peaks   = [p for p in pivots if p["type"] == "peak"]
    troughs = [p for p in pivots if p["type"] == "trough"]

    if len(troughs) >= 2:
        t1 = troughs[-2]; t2 = troughs[-1]
        if abs(t1["price"]-t2["price"])/t1["price"] < 0.03:
            mid = [p for p in peaks if t1["idx"] < p["idx"] < t2["idx"]]
            if mid and current >= t2["price"]*0.97:
                nk = mid[-1]["price"]
                return {"type":"DOUBLE_BOTTOM","label":"Double Bottom",
                        "entry_price":t2["price"],"target":nk+(nk-t2["price"]),"score":70}

    # V8 FIX: DOUBLE_TOP returns watch data instead of hard block signal
    if len(peaks) >= 2:
        p1 = peaks[-2]; p2 = peaks[-1]
        if abs(p1["price"]-p2["price"])/p1["price"] < 0.03:
            return {"type":"DOUBLE_TOP","label":"Double Top — Watch for breakdown",
                    "score":0, "watch_note":"Double Top detected — monitoring for resolution"}

    if len(peaks) >= 3 and len(troughs) >= 3:
        ph = [peaks[-3]["price"],peaks[-2]["price"],peaks[-1]["price"]]
        tl = [troughs[-3]["price"],troughs[-2]["price"],troughs[-1]["price"]]
        hf  = ph[0] > ph[1] > ph[2]; lf = tl[0] > tl[1] > tl[2]
        conv = (ph[-1]-tl[-1]) < (ph[0]-tl[0])*0.7
        if hf and lf and conv:
            return {"type":"FALLING_WEDGE","label":"Falling Wedge (Bullish)",
                    "entry_price":current,"target":ph[0],"score":65}
    return None

# ================================================================
# WXYXZ DETECTION
# ================================================================
def detect_wxyxz(pivots, current):
    if len(pivots) < 6: return False, 0, 0, ""
    best = None
    for i in range(len(pivots)-6,-1,-1):
        if i+5 >= len(pivots): continue
        p = pivots[i:i+6]
        types = [x["type"] for x in p]
        if types != ["peak","trough","peak","trough","peak","trough"]: continue
        x1p = abs(p[2]["price"]-p[1]["price"]); x1t = p[2]["idx"]-p[1]["idx"]
        x2p = abs(p[4]["price"]-p[3]["price"]); x2t = p[4]["idx"]-p[3]["idx"]
        if x1p==0 or x1t==0: continue
        if x1p/p[1]["price"]*100 < 5 or x2p/p[3]["price"]*100 < 5: continue
        ws = abs(p[1]["price"]-p[0]["price"]); ys = abs(p[3]["price"]-p[2]["price"])
        if x1p >= ws*0.8 or x2p >= ys*0.8: continue
        pr = x2p/x1p*100; tr = x2t/x1t*100 if x1t > 0 else 100
        if 85 <= pr <= 115 and 85 <= tr <= 115:
            z = p[5]["price"]; near = abs(current-z)/z*100 <= 8
            best = (True, z, pr, "WXYXZ X1=X2 (" + str(round(pr)) + "%|" + str(round(tr)) + "%)")
            if near: break
    return best if best else (False, 0, 0, "")

# ================================================================
# TREND CONTINUATION
# ================================================================
def detect_trend_continuation(prices, highs, lows, pivots, current, trend, htf_prices):
    if len(prices) < 30: return None
    htf_bullish = False
    if len(htf_prices) >= 20:
        htf_ma20 = sum(htf_prices[-20:]) / 20
        htf_bullish = htf_prices[-1] > htf_ma20
    if not htf_bullish: return None

    recent_peaks   = [p for p in pivots if p["type"]=="peak"   and p["idx"] > len(prices)*0.2]
    recent_troughs = [p for p in pivots if p["type"]=="trough" and p["idx"] > len(prices)*0.2]
    if len(recent_peaks) < 2 or len(recent_troughs) < 2: return None

    hh1 = recent_peaks[-1]["price"]   > recent_peaks[-2]["price"]
    hl1 = recent_troughs[-1]["price"] > recent_troughs[-2]["price"]
    # Need at least 2 HH and 2 HL — basic uptrend structure
    if not (hh1 and hl1): return None

    adx = calc_adx(highs, lows, prices, 14)
    if adx["adx"] < 20: return None  # Lowered from 30
    momentum = (prices[-1]-prices[-20])/prices[-20]*100 if len(prices) >= 20 else 0
    if momentum < 2: return None  # Lowered from 5%
    ma50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else current
    if current < ma50*0.95: return None  # Loosened from 0.98

    if len(pivots) >= 5:
        return {"type":"TREND_CONTINUATION","sub_type":"IMPULSE_W3_LIKELY",
                "label":"Trend Continuation (W3/Parabolic) - WATCH","score":50,
                "entry_wave":"W3 or Pullback","entry_price":current,"htf_confirmed":htf_bullish,
                "watch_only":True,
                "reason":"3xHH+HL, ADX=" + str(round(adx["adx"])) + ", momentum=" + str(round(momentum,1)) + "%"}
    else:
        return {"type":"TREND_CONTINUATION","sub_type":"EARLY_TREND",
                "label":"Early Trend Continuation - WATCH","score":45,
                "entry_wave":"Pullback to MA20","entry_price":sum(prices[-20:])/20,
                "htf_confirmed":htf_bullish,"watch_only":True,
                "reason":"3xHH+HL forming, ADX=" + str(round(adx["adx"])) + ", momentum=" + str(round(momentum,1)) + "%"}

# ================================================================
# STRUCTURE MEMORY
# ================================================================
def check_structure_memory(sym, sig_type, current, pivots):
    key = sym + "_" + sig_type
    mem = _structure_memory.get(key)
    if not mem: return None
    if time.time() - mem["since"] > 30*86400: return None
    if mem["type"] == "IMPULSE":
        if mem.get("w0_origin") and current < mem["w0_origin"]*0.99: return None
        if mem.get("w1_top")    and current < mem["w1_top"]*0.99:    return None
        if mem.get("last_trough") and current < mem["last_trough"]*0.97: return None
    return {"type":mem["type"],"sub_type":mem["sub_type"],"label":mem["label"],
            "score":min(mem["score"]+5,85),"entry_wave":mem["entry_wave"],
            "entry_price":mem["entry_price"],"locked":True,
            "reason":"Locked structure from " + mem["date"] + ": " + mem["label"]}

def update_structure_memory(sym, sig_type, structure, pivots):
    key = sym + "_" + sig_type
    if structure["score"] >= 70 and structure["type"] in ("IMPULSE","TREND_CONTINUATION"):
        mem = {"type":structure["type"],"sub_type":structure.get("sub_type",""),
               "label":structure["label"],"score":structure["score"],
               "entry_wave":structure.get("entry_wave",""),"entry_price":structure.get("entry_price",0),
               "since":time.time(),"date":datetime.now().strftime("%Y-%m-%d")}
        if len(pivots) >= 3: mem["w0_origin"] = pivots[0]["price"]
        if len(pivots) >= 2:
            peaks = [p for p in pivots if p["type"]=="peak"]
            if peaks: mem["w1_top"] = peaks[0]["price"]
        troughs = [p for p in pivots if p["type"]=="trough"]
        if troughs: mem["last_trough"] = troughs[-1]["price"]
        _structure_memory[key] = mem

# ================================================================
# V8: MAIN STRUCTURE RECOGNIZER
# KEY FIX: DOUBLE_TOP → WATCH (not hard block)
# KEY FIX: Scalp DOWNTREND → check daily before blocking
# ================================================================
def recognize_chart_structure(prices, highs, lows, opens, pivots, current, pct_ath,
                               rsi_val, macd_bull, vol_dec, vol_exp, stoch,
                               trend, regime, phase, htf_prices, sym, sig_type,
                               liquidity_info, mtf_alignment, candlestick_info, extended_wave):

    if len(pivots) < 4:
        return {"type":"UNKNOWN","label":"Insufficient data","confidence_score":0,
                "sit_applicable":[],"sit_na":[],"phase":phase}

    mem = check_structure_memory(sym, sig_type, current, pivots)
    candidates = []

    def add_candidate(s):
        if not s or s.get("type") == "UNKNOWN": return
        s["confidence_score"] = score_structure_v7(s, rsi_val, macd_bull, vol_dec, vol_exp, stoch, trend,
                                                    liquidity_info, mtf_alignment, candlestick_info, extended_wave)
        candidates.append(s)

    # CANDIDATE 1: Trend Continuation
    trend_cont = detect_trend_continuation(prices, highs, lows, pivots, current, trend, htf_prices)
    if trend_cont:
        if trend_cont["score"] > 55: trend_cont["score"] = 55
        add_candidate(trend_cont)

    # CANDIDATE 2: Classical Patterns
    classical = detect_classical_patterns(prices, pivots, current)
    if classical:
        if classical.get("type") == "DOUBLE_TOP":
            # V8 FIX: Don't hard-block DOUBLE_TOP — send to watch instead
            # Return a low-score watch candidate rather than a full block
            return {
                "type": "DOUBLE_TOP_WATCH",
                "label": "Double Top — Watch only",
                "confidence_score": 15,   # below any min_score threshold → becomes watch
                "watch_note": classical.get("watch_note", "Double Top detected"),
                "sit_applicable": [], "sit_na": [], "phase": phase
            }
        add_candidate({
            "type":classical["type"],"label":classical["label"],
            "entry_wave":"Pattern completion","entry_price":classical["entry_price"],
            "target":classical.get("target"),"score":classical["score"],
            "sit_applicable":["rsi_ok","macd_ok","vol_exp"],
            "sit_na":["fib_golden","alternation","wave_symmetry","blue_box","abc_struct"]
        })

    # CANDIDATE 3: WXYXZ
    wx_ok, wx_price, wx_ratio, wx_label = detect_wxyxz(pivots, current)
    if wx_ok:
        add_candidate({"type":"WXYXZ","label":"W-X-Y-X-Z Triple Combination",
                       "entry_wave":"Wave Z","entry_price":wx_price,
                       "sit_applicable":["rsi_ok","macd_ok","vol_exp"],
                       "sit_na":["fib_golden","alternation","wave_symmetry","blue_box","abc_struct","ca_zone"]})

    # CANDIDATE 4: Triangle
    triangle = detect_triangle(prices, highs, lows, pivots)
    if triangle and triangle.get("sub_type") != "TRIANGLE_EXPAND":
        add_candidate(triangle)

    # CANDIDATE 4.5: IMPULSING phase pullback entry
    # When coin is in strong uptrend (IMPULSING/TRENDING_UP),
    # look for the most recent higher low as a W4 pullback entry
    if phase in ("IMPULSING", "TRENDING_UP"):
        recent_troughs = [p for p in pivots if p["type"] == "trough"]
        recent_peaks   = [p for p in pivots if p["type"] == "peak"]
        if len(recent_troughs) >= 2 and len(recent_peaks) >= 2:
            last_trough = recent_troughs[-1]
            last_peak   = recent_peaks[-1]
            prev_trough = recent_troughs[-2]
            # Higher low = valid pullback in uptrend
            if (last_trough["price"] > prev_trough["price"] and
                last_peak["price"] > prev_trough["price"] and
                abs(current - last_trough["price"]) / last_trough["price"] < 0.15):
                w3_range = last_peak["price"] - prev_trough["price"]
                w4_ret   = (last_peak["price"] - last_trough["price"]) / w3_range if w3_range > 0 else 0
                bb_lo = last_peak["price"] - w3_range * 0.786
                bb_hi = last_peak["price"] - w3_range * 0.382
                in_bb = bb_lo <= current <= bb_hi
                score = 55 + (10 if 0.236 <= w4_ret <= 0.5 else 5) + (5 if in_bb else 0)
                add_candidate({
                    "type": "EW_W4",
                    "label": "Impulse Pullback — W4 Entry (" + phase + ")",
                    "entry_wave": "W4 pullback",
                    "entry_price": last_trough["price"],
                    "w1h": recent_peaks[-2]["price"] if len(recent_peaks) >= 2 else last_peak["price"],
                    "w2l": prev_trough["price"],
                    "w3h": last_peak["price"],
                    "w4l": last_trough["price"],
                    "w1": last_peak["price"] - prev_trough["price"],
                    "w3": w3_range,
                    "w2_ret": 0.5,
                    "w4_ret": w4_ret,
                    "fib_label": "W4 pullback",
                    "fib_valid": True,
                    "in_blue_box": in_bb,
                    "score": score,
                    "sit_applicable": ["rsi_ok", "macd_ok", "vol_dec", "vol_exp"],
                    "sit_na": ["fib_golden", "blue_box", "alternation", "wave_symmetry", "wxyxz"],
                    "recency": 0.0
                })

    # CANDIDATES 5-7: EW Structures
    n = len(pivots)
    best_w2 = None; best_w4 = None

    for i in range(n-6,-1,-1):
        if i+5 >= n: continue
        p = pivots[i:i+6]
        types = [x["type"] for x in p]

        if types == ["trough","peak","trough","peak","trough","peak"]:
            w0=p[0]["price"]; w1h=p[1]["price"]; w2l=p[2]["price"]
            w3h=p[3]["price"]; w4l=p[4]["price"]; w5h=p[5]["price"]
            w1 = w1h - w0
            if w1 <= 0 or w2l <= w0: continue
            w2_ret = (w1h-w2l)/w1
            if abs(current-w2l)/w2l > 0.15: continue
            _, fib_valid, fib_label = calc_fib_retrace(p[:3])
            score = 60 + (10 if 0.5<=w2_ret<=0.786 else 5 if w2_ret>=0.382 else 0)
            cand = {"type":"EW_W2","label":"Standard EW - W2 Entry",
                    "entry_wave":"W2","entry_price":w2l,
                    "w1h":w1h,"w2l":w2l,"w3h":w3h,"w4l":w4l,"w5h":w5h,
                    "w1":w1,"w2_ret":w2_ret,"fib_label":fib_label,"fib_valid":fib_valid,
                    "score":score,
                    "sit_applicable":["fib_golden","wave_symmetry","rsi_ok","macd_ok","vol_dec","vol_exp","candlestick"],
                    "sit_na":["blue_box","alternation","wave_c_bottom","ca_zone","abc_struct","wxyxz"],
                    "recency":(n-p[2]["idx"])/n}
            if not best_w2 or cand["recency"] < best_w2["recency"]: best_w2 = cand

        if i+4 < n and types[:5] == ["trough","peak","trough","peak","trough"]:
            p5 = pivots[i:i+5]
            w0=p5[0]["price"]; w1h=p5[1]["price"]; w2l=p5[2]["price"]
            w3h=p5[3]["price"]; w4l=p5[4]["price"]
            w1=w1h-w0; w3=w3h-w2l
            if w1<=0 or w3<=0 or w2l<=w0 or w3<w1 or w4l<=w1h: continue
            w2_ret=(w1h-w2l)/w1; w4_ret=(w3h-w4l)/w3
            if abs(current-w4l)/w4l > 0.15: continue
            _, fib_valid, fib_label = calc_fib_retrace(p5[:3])
            bb_lo=w3h-w3*0.786; bb_hi=w3h-w3*0.618; in_bb=bb_lo<=current<=bb_hi
            score=55+(10 if 0.236<=w4_ret<=0.382 else 5 if w4_ret<=0.5 else 0)+(5 if in_bb else 0)
            cand = {"type":"EW_W4","label":"Standard EW - W4 Entry",
                    "entry_wave":"W4","entry_price":w4l,
                    "w1h":w1h,"w2l":w2l,"w3h":w3h,"w4l":w4l,
                    "w1":w1,"w3":w3,"w2_ret":w2_ret,"w4_ret":w4_ret,
                    "fib_label":fib_label,"fib_valid":fib_valid,"in_blue_box":in_bb,
                    "score":score,
                    "sit_applicable":["fib_golden","blue_box","alternation","wave_symmetry","rsi_ok","macd_ok","vol_dec","vol_exp","candlestick"],
                    "sit_na":["wave_c_bottom","ca_zone","abc_struct","wxyxz"],
                    "recency":(n-p5[4]["idx"])/n}
            if not best_w4 or cand["recency"] < best_w4["recency"]: best_w4 = cand

    if best_w2: add_candidate(best_w2)
    if best_w4: add_candidate(best_w4)

    # CANDIDATES 8-10: Correction patterns
    for i in range(n-6,-1,-1):
        if i+5 >= n: continue
        p = pivots[i:i+6]
        types = [x["type"] for x in p]
        if types != ["trough","peak","trough","peak","trough","peak"]: continue
        w0=p[0]["price"]; w1h=p[1]["price"]; w2l=p[2]["price"]
        w3h=p[3]["price"]; w4l=p[4]["price"]; w5h=p[5]["price"]
        w1=w1h-w0
        if w1<=0 or w2l<=w0: continue
        w3=w3h-w2l; w5=w5h-w4l
        if w3<=0 or (w3<w1 and w3<w5) or w4l<=w1h or w5h<=w3h: continue
        w5_top = w5h
        post  = [pv for pv in pivots if pv["idx"] > p[5]["idx"]]
        if not post: continue
        aP = next((pv for pv in post if pv["type"]=="trough"), None)
        if not aP: continue
        wa_bot=aP["price"]; wa_range=w5h-wa_bot
        if wa_range <= 0: continue
        postA = [pv for pv in post if pv["idx"] > aP["idx"]]
        bP = next((pv for pv in postA if pv["type"]=="peak"), None)
        if not bP: continue
        wb_top=bP["price"]; wb_ret=(wb_top-wa_bot)/wa_range
        postB = [pv for pv in post if pv["idx"] > bP["idx"]]
        cP = next((pv for pv in postB if pv["type"]=="trough"), None)
        wc_bot=cP["price"] if cP else current
        wc_range=wb_top-wc_bot; c_vs_a=wc_range/wa_range if wa_range > 0 else 0

        if wb_top > w5_top and c_vs_a >= 0.6:
            score=55+(10 if c_vs_a>=0.8 else 5)
            add_candidate({"type":"EXPANDED_FLAT","label":"Expanded Flat Correction",
                           "entry_wave":"Wave C","entry_price":wc_bot,
                           "wa_bot":wa_bot,"wb_top":wb_top,"wc_bot":wc_bot,"w5_top":w5_top,"wa_range":wa_range,
                           "c_progress":min(c_vs_a/1.236*100,100),"score":score,
                           "sit_applicable":["wave_c_bottom","ca_zone","abc_struct","rsi_ok","macd_ok","vol_dec","vol_exp"],
                           "sit_na":["fib_golden","blue_box","alternation","wave_symmetry","wxyxz"]})

        if 0.38<=wb_ret<=0.78 and wc_bot>wa_bot and c_vs_a>=0.38:
            score=50+(10 if c_vs_a>=0.6 else 5)
            add_candidate({"type":"RUNNING_CORRECTION","label":"Running Correction (Bullish)",
                           "entry_wave":"Wave C (Higher Low)","entry_price":wc_bot,
                           "wa_bot":wa_bot,"wb_top":wb_top,"wc_bot":wc_bot,"w5_top":w5_top,"wa_range":wa_range,
                           "score":score,
                           "sit_applicable":["wave_c_bottom","abc_struct","rsi_ok","macd_ok","vol_dec","vol_exp"],
                           "sit_na":["fib_golden","blue_box","ca_zone","alternation","wxyxz"]})

        if 0.38<=wb_ret<=0.78 and c_vs_a>=0.6:
            c_eq_a=wb_top-wa_range; c_conf=abs(wc_bot-c_eq_a)/max(abs(c_eq_a),0.0001) < 0.05
            score=50+(15 if c_conf else 8 if c_vs_a>=0.8 else 5)
            add_candidate({"type":"ABC_ZIGZAG","label":"ABC Zigzag Correction",
                           "entry_wave":"Wave C","entry_price":wc_bot,
                           "wa_bot":wa_bot,"wb_top":wb_top,"wc_bot":wc_bot,"w5_top":w5_top,"wa_range":wa_range,
                           "c_progress":c_vs_a*100,"c_eq_a_tgt":c_eq_a,"c_confirmed":c_conf,"score":score,
                           "sit_applicable":["wave_c_bottom","ca_zone","abc_struct","rsi_ok","macd_ok","vol_dec","vol_exp"],
                           "sit_na":["fib_golden","blue_box","alternation","wave_symmetry","wxyxz"]})
        break

    if mem and mem["type"] in ("IMPULSE","TREND_CONTINUATION"):
        mem["confidence_score"] = score_structure_v7(mem, rsi_val, macd_bull, vol_dec, vol_exp, stoch, trend,
                                                      liquidity_info, mtf_alignment, candlestick_info, extended_wave)
        if candidates:
            winner = max(candidates, key=lambda x: x.get("confidence_score",0))
            if mem["confidence_score"] >= winner.get("confidence_score",0)*0.85:
                candidates.insert(0, mem)
        else:
            candidates.append(mem)

    if not candidates:
        print("  [debug] " + sym + " " + sig_type + " no candidates — pivots=" + str(len(pivots)) + " phase=" + phase)
        return {"type":"UNKNOWN","label":"No valid structure found","confidence_score":0,
                "sit_applicable":[],"sit_na":[],"phase":phase}

    candidates.sort(key=lambda x: x.get("confidence_score",0), reverse=True)
    winner = candidates[0]
    runner = candidates[1] if len(candidates) > 1 else None

    if runner:
        gap = winner.get("confidence_score",0) - runner.get("confidence_score",0)
        if gap < 8:
            winner["confidence_score"] = int(winner.get("confidence_score",0)*0.85)
            winner["ambiguous"] = True
            winner["alternate"] = runner.get("label","")

    if runner and not winner.get("alternate"):
        winner["alternate"] = runner.get("label","")

    winner["phase"] = phase
    winner["all_candidates"] = [(c.get("type",""), c.get("confidence_score",0)) for c in candidates]

    if winner["type"] in ("IMPULSE","TREND_CONTINUATION") and winner.get("score",0) >= 65:
        update_structure_memory(sym, sig_type, winner, pivots)

    return winner

# ================================================================
# SCORING ENGINE (unchanged from V7)
# ================================================================
def score_structure_v7(struct, rsi_val, macd_bull, vol_dec, vol_exp, stoch, trend,
                        liquidity_info, mtf_alignment, candlestick_info, extended_wave):
    if not struct or struct.get("type","UNKNOWN") == "UNKNOWN": return 0
    t   = struct.get("type","UNKNOWN")
    sub = struct.get("sub_type","")

    if t == "TREND_CONTINUATION":
        max_score = 55 if sub == "IMPULSE_W3_LIKELY" else 50 if sub == "EARLY_TREND" else 55
    elif t == "WXYXZ":            max_score = 95
    elif t == "EXPANDED_FLAT":    max_score = 90
    elif t == "RUNNING_CORRECTION":max_score = 85
    elif t == "CONTRACTING_TRIANGLE": max_score = 85
    elif t == "DOUBLE_BOTTOM":    max_score = 80
    elif t == "FALLING_WEDGE":    max_score = 75
    elif t in ("ABC_ZIGZAG","EW_W4","EW_W2"): max_score = 100
    else:                         max_score = 70

    base = 0
    if t == "TREND_CONTINUATION":
        base = 20 + (10 if sub=="IMPULSE_W3_LIKELY" else 5 if sub=="EARLY_TREND" else 8)
        if struct.get("htf_confirmed"): base += 5
    elif t == "CONTRACTING_TRIANGLE":
        base = 22 + (8 if struct.get("breakout") else 5 if struct.get("near_apex") else 0)
    elif t == "WXYXZ":
        base = 22; wx_ratio = struct.get("wx_ratio",0)
        base += 8 if 90<=wx_ratio<=110 else 4 if 80<=wx_ratio<=120 else 0
    elif t in ("EXPANDED_FLAT","RUNNING_CORRECTION"):
        base = 18; cp = struct.get("c_progress",0)
        base += 8 if cp>=90 else 5 if cp>=70 else 2 if cp>=50 else 0
    elif t == "ABC_ZIGZAG":
        base = 18; cp = struct.get("c_progress",0)
        base += 10 if cp>=90 else 6 if cp>=70 else 3 if cp>=50 else 0
        if struct.get("c_confirmed"): base += 5
    elif t == "EW_W4":
        base = 20; w4r = struct.get("w4_ret",0)
        base += 10 if 0.236<=w4r<=0.382 else 6 if w4r<=0.50 else 2 if w4r<=0.618 else 0
        if struct.get("in_blue_box"): base += 5
    elif t == "EW_W2":
        base = 20; w2r = struct.get("w2_ret",0)
        base += 10 if 0.618<=w2r<=0.786 else 6 if w2r>=0.50 else 2 if w2r>=0.382 else 0
    elif t == "DOUBLE_BOTTOM":
        base = 18 + (5 if struct.get("target") else 0)
    elif t == "FALLING_WEDGE": base = 15
    else: base = 15

    ew = 0
    if t in ("EW_W4","EW_W2"):
        w1=struct.get("w1",0); w3=struct.get("w3",0)
        ew += 12 if w3>=w1*1.0 else 6 if w3>=w1*0.8 else 0
        w2r=struct.get("w2_ret",0); w4r=struct.get("w4_ret",0)
        if t=="EW_W4" and w2r>0 and w4r>0:
            ew += 8 if w2r>w4r*1.5 or w4r>w2r*1.5 else 4 if abs(w2r-w4r)/max(w2r,w4r)>0.3 else 0
        ew += 5
    elif t=="ABC_ZIGZAG":
        cp=struct.get("c_progress",0)
        ew += 15 if cp>=100 else 10 if cp>=80 else 5 if cp>=60 else 0
        if struct.get("c_confirmed"): ew += 10
    elif t=="WXYXZ":
        ew += 10
        if 90<=struct.get("wx_ratio",0)<=110: ew += 10
    elif t=="CONTRACTING_TRIANGLE":
        ew += 12 + (8 if struct.get("breakout") else 0)
    elif t=="TREND_CONTINUATION": ew += 0
    elif t in ("EXPANDED_FLAT","RUNNING_CORRECTION"):
        ew += 12
        if t=="EXPANDED_FLAT" and struct.get("wb_top",0)>struct.get("w5_top",0): ew += 6
    elif t in ("DOUBLE_BOTTOM","FALLING_WEDGE"): ew += 8
    else: ew += 5

    fib = 0
    if t=="EW_W2":
        r=struct.get("w2_ret",0)
        fib = 15 if 0.618<=r<=0.786 else 10 if r>=0.50 else 5 if r>=0.382 else 0
    elif t=="EW_W4":
        r=struct.get("w4_ret",0)
        fib = 15 if 0.236<=r<=0.382 else 10 if r<=0.50 else 5 if r<=0.618 else 0
        if struct.get("in_blue_box"): fib += 5
    elif t=="ABC_ZIGZAG":
        fib = 15 if struct.get("c_confirmed") else 8
        c_eq=struct.get("c_eq_a_tgt",0); wc=struct.get("wc_bot",0)
        if c_eq and wc and abs(wc-c_eq)/max(abs(c_eq),0.0001)<0.03: fib += 5
    elif t=="WXYXZ":
        fib=12; wx=struct.get("wx_ratio",0)
        if 85<=wx<=115: fib += 8
    elif t=="CONTRACTING_TRIANGLE":
        fib=10+(5 if struct.get("breakout") else 0)
    elif t=="TREND_CONTINUATION": fib=0
    elif t=="EXPANDED_FLAT":
        fib=10+(5 if struct.get("c_progress",0)>=123.6 else 0)
    elif t=="RUNNING_CORRECTION": fib=8
    elif t=="DOUBLE_BOTTOM": fib=8
    elif t=="FALLING_WEDGE": fib=5
    else: fib=5

    vol=0
    if vol_dec: vol += 5
    if vol_exp: vol += 5

    mom=0
    if rsi_val<35: mom += 5
    elif rsi_val<45: mom += 3
    if macd_bull: mom += 5
    elif stoch<20: mom += 3

    trend_adj=0
    if trend["score"]>=75: trend_adj=10
    elif trend["score"]>=60: trend_adj=5
    elif trend["score"]<=30: trend_adj=-10
    elif trend["score"]<=40: trend_adj=-5

    candle_bonus=0
    if candlestick_info:
        if t in ("EW_W2","EW_W4","ABC_ZIGZAG","EXPANDED_FLAT","RUNNING_CORRECTION","CONTRACTING_TRIANGLE"):
            candle_bonus=min(candlestick_info.get("bullish_score",0),3)
        elif t in ("DOUBLE_BOTTOM","FALLING_WEDGE"):
            candle_bonus=min(candlestick_info.get("bullish_score",0),5)

    liquidity_bonus=0
    if liquidity_info:
        if liquidity_info.get("choch") and liquidity_info.get("direction")=="bullish": liquidity_bonus=5
        elif liquidity_info.get("bos") and liquidity_info.get("direction")=="bullish": liquidity_bonus=3

    mtf_bonus=0
    if mtf_alignment: mtf_bonus=mtf_alignment.get("score",0)

    ext_bonus=0
    if extended_wave and extended_wave.get("extended"):
        if t in ("EW_W2","EW_W4","ABC_ZIGZAG","EXPANDED_FLAT","RUNNING_CORRECTION","CONTRACTING_TRIANGLE"):
            ext_bonus=5

    raw_score = base+ew+fib+vol+mom+trend_adj+candle_bonus+liquidity_bonus+mtf_bonus+ext_bonus
    score = min(raw_score, max_score)

    struct["_max_ceiling"]=max_score; struct["_raw_score"]=raw_score
    struct["_base"]=base; struct["_ew"]=ew; struct["_fib"]=fib
    struct["_vol"]=vol; struct["_mom"]=mom; struct["_trend_adj"]=trend_adj
    struct["_candle_bonus"]=candle_bonus; struct["_liquidity_bonus"]=liquidity_bonus
    struct["_mtf_bonus"]=mtf_bonus; struct["_ext_bonus"]=ext_bonus

    return max(0, score)

# ================================================================
# ADAPTIVE RISK
# ================================================================
def calculate_adaptive_risk(struct_type, sub_type, pivots, current, regime, atr,
                             sl_pct, tp1_pct, tp2_pct, tp3_pct, tp4_pct, extended_wave=None):
    atr_mult = 2.5 if regime["type"]=="high" else 1.5 if regime["type"]=="low" else 2.0
    max_sl   = 0.08 if regime["type"]=="high" else 0.05
    sl=tp1=tp2=tp3=tp4=0; sl_reason=""
    ext_mult = extended_wave.get("tp_multiplier",1.0) if extended_wave else 1.0

    if struct_type=="TREND_CONTINUATION":
        troughs=[p for p in pivots if p["type"]=="trough"]
        if len(troughs)>=2:
            sl=troughs[-2]["price"]*0.98
            tp1=current+(current-sl)*1.5*ext_mult; tp2=current+(current-sl)*2.5*ext_mult
            tp3=current+(current-sl)*4.0*ext_mult; tp4=current+(current-sl)*6.0*ext_mult
            sl_reason="Below last significant trough"
        else:
            sl=current-atr*atr_mult*1.5
            tp1=current+atr*atr_mult*2.0*ext_mult; tp2=current+atr*atr_mult*3.5*ext_mult
            tp3=current+atr*atr_mult*5.0*ext_mult; tp4=current+atr*atr_mult*7.0*ext_mult
            sl_reason="ATR-based trend SL"

    elif struct_type=="EW_W4" and len(pivots)>=5:
        # Use actual EW peaks/troughs not arbitrary pivot indices
        peaks_w4   = [p for p in pivots if p["type"]=="peak"]
        troughs_w4 = [p for p in pivots if p["type"]=="trough"]
        if len(peaks_w4) >= 2 and len(troughs_w4) >= 2:
            w1h = peaks_w4[-2]["price"] if len(peaks_w4) >= 2 else peaks_w4[-1]["price"]
            w3h = peaks_w4[-1]["price"]
            w4l = troughs_w4[-1]["price"]
            w3r = w3h - (troughs_w4[-2]["price"] if len(troughs_w4) >= 2 else troughs_w4[-1]["price"])
            # SL below W1 top — EW rule W4 cannot overlap W1
            sl  = min(w1h * 0.99, current * (1 - sl_pct))
            tp1 = w3h
            tp2 = w3h + w3r * 0.618 * ext_mult
            tp3 = w3h + w3r * 1.0 * ext_mult
            tp4 = w3h + w3r * 1.618 * ext_mult
            sl_reason = "Below W1 Top (W4 overlap rule)"
        else:
            sl  = current * (1 - sl_pct)
            tp1 = current * (1 + tp1_pct)
            tp2 = current * (1 + tp2_pct * ext_mult)
            tp3 = current * (1 + tp3_pct * ext_mult)
            tp4 = current * (1 + tp4_pct * ext_mult)
            sl_reason = "Fixed % fallback (W4)"

    elif struct_type in ("ABC_ZIGZAG","EXPANDED_FLAT","RUNNING_CORRECTION"):
        troughs=[p for p in pivots if p["type"]=="trough"]
        peaks=[p for p in pivots if p["type"]=="peak"]
        if len(troughs)>=2 and peaks:
            # Wave A bottom = lowest trough in correction sequence
            a_bot = min(troughs, key=lambda x: x["price"])["price"]
            b_top = peaks[-1]["price"]
            wa_rng = abs(b_top - a_bot)
            # SL below Wave A bottom with 1.5% buffer
            sl = a_bot * 0.985
            tp1 = b_top
            tp2 = b_top + wa_rng * 0.618 * ext_mult
            tp3 = b_top + wa_rng * 1.0 * ext_mult
            tp4 = b_top + wa_rng * 1.618 * ext_mult
            sl_reason = "Below Wave A Bottom"
        else:
            sl=current*(1-sl_pct); tp1=current*(1+tp1_pct*ext_mult)
            tp2=current*(1+tp2_pct*ext_mult); tp3=current*(1+tp3_pct*ext_mult)
            tp4=current*(1+tp4_pct*ext_mult); sl_reason="Fixed % (fallback)"

    elif struct_type=="EW_W2" and len(pivots)>=3:
        # Find the actual wave origin trough (lowest trough before first peak)
        troughs_ew = [p for p in pivots if p["type"]=="trough"]
        peaks_ew   = [p for p in pivots if p["type"]=="peak"]
        if troughs_ew and peaks_ew:
            # W0 = lowest trough before first peak
            first_peak_idx = peaks_ew[0]["idx"]
            pre_peak_troughs = [p for p in troughs_ew if p["idx"] < first_peak_idx]
            w0_price = pre_peak_troughs[-1]["price"] if pre_peak_troughs else troughs_ew[0]["price"]
            w1h = peaks_ew[0]["price"]
            w1r = w1h - w0_price
            # SL = below W0 origin with 1% buffer — MUST be below current
            sl = w0_price * 0.99
            tp1 = w1h
            tp2 = w1h + w1r * 0.618 * ext_mult
            tp3 = w1h + w1r * 1.0 * ext_mult
            tp4 = w1h + w1r * 1.618 * ext_mult
            sl_reason = "Below W0 Origin (W2 rule)"
        else:
            sl = current * (1 - sl_pct)
            tp1 = current * (1 + tp1_pct)
            tp2 = current * (1 + tp2_pct * ext_mult)
            tp3 = current * (1 + tp3_pct * ext_mult)
            tp4 = current * (1 + tp4_pct * ext_mult)
            sl_reason = "Fixed % fallback (no pivots)"

    elif struct_type=="WXYXZ" and len(pivots)>=4:
        troughs=[p for p in pivots if p["type"]=="trough"]
        peaks=[p for p in pivots if p["type"]=="peak"]
        sl=troughs[-1]["price"]*0.98 if troughs else current*(1-max_sl)
        tp1=peaks[-1]["price"] if peaks else current*(1+tp1_pct*ext_mult)
        rng=tp1-sl
        tp2=tp1+rng*0.618*ext_mult; tp3=tp1+rng*1.0*ext_mult; tp4=tp1+rng*1.618*ext_mult
        sl_reason="Below Z-wave bottom"

    elif struct_type=="CONTRACTING_TRIANGLE":
        peaks=[p for p in pivots if p["type"]=="peak"]
        troughs=[p for p in pivots if p["type"]=="trough"]
        if len(peaks)>=3 and len(troughs)>=3:
            triangle_height=peaks[-3]["price"]-troughs[-3]["price"]
            sl=troughs[-1]["price"]*0.98
            tp1=current+triangle_height*0.5*ext_mult; tp2=current+triangle_height*1.0*ext_mult
            tp3=current+triangle_height*1.618*ext_mult; tp4=current+triangle_height*2.618*ext_mult
            sl_reason="Below triangle support"
        else:
            sl=current-atr*atr_mult; tp1=current+atr*atr_mult*1.5*ext_mult
            tp2=current+atr*atr_mult*2.5*ext_mult; tp3=current+atr*atr_mult*4.0*ext_mult
            tp4=current+atr*atr_mult*6.0*ext_mult; sl_reason="ATR-based triangle SL"

    else:
        sl=current-atr*atr_mult; tp1=current+atr*atr_mult*1.5*ext_mult
        tp2=current+atr*atr_mult*2.5*ext_mult; tp3=current+atr*atr_mult*4.0*ext_mult
        tp4=current+atr*atr_mult*6.0*ext_mult; sl_reason="ATR-based (" + str(round(atr_mult,1)) + "x)"

    if sl>0 and (current-sl)/current>max_sl:
        sl=current*(1-max_sl); sl_reason+=" (capped " + str(round(max_sl*100)) + "%)"

    # ── SANITY CHECKS ──────────────────────────────────────────
    # SL must be BELOW entry (we only take long signals)
    if sl >= current:
        sl = current * (1 - sl_pct)
        sl_reason += " [SL fixed: was above entry]"

    # SL must not be more than max_sl below entry
    if sl > 0 and (current - sl) / current > max_sl:
        sl = current * (1 - max_sl)
        sl_reason += " (capped " + str(round(max_sl * 100)) + "%)"

    # TPs must be above entry and strictly ascending
    if tp1 <= current: tp1 = current * (1 + tp1_pct)
    if tp2 <= tp1:     tp2 = tp1 * (1 + tp2_pct)
    if tp3 <= tp2:     tp3 = tp2 * (1 + tp3_pct)
    if tp4 <= tp3:     tp4 = tp3 * (1 + tp4_pct)

    return sl, tp1, tp2, tp3, tp4, sl_reason

# ================================================================
# POSITION SIZING
# ================================================================
def calculate_position_size(score, regime, trend_label, is_mem_locked=False):
    base = 100 if score>=85 else 75 if score>=75 else 50 if score>=65 else 25 if score>=55 else 10
    if regime["type"]=="high": base=int(base*0.7)
    elif regime["type"]=="low": base=int(base*1.1)
    if trend_label=="STRONG_UPTREND": base=int(base*1.15)
    elif trend_label=="DOWNTREND": base=int(base*0.5)
    if is_mem_locked: base=int(base*1.1)
    return min(base,100)

# ================================================================
# V8: MAIN ANALYSIS — KEY FIXES:
# 1. DOUBLE_TOP_WATCH → send watch alert, don't block
# 2. Scalp DOWNTREND → only block if DAILY also bearish
# ================================================================
def analyze(coin, signal_type="swing"):
    sym = coin["sym"]

    if signal_type=="swing":
        prices,highs,lows,vols,opens = fetch_klines_full(sym,"1d",730)
        sl_pct=0.05; tp1_pct=0.05; tp2_pct=0.10; tp3_pct=0.15; tp4_pct=0.20
        min_score=75; hold="Days to weeks"
    else:
        prices,highs,lows,vols,opens = fetch_klines_full(sym,"4h",540)
        sl_pct=0.03; tp1_pct=0.03; tp2_pct=0.05; tp3_pct=0.08; tp4_pct=0.12
        min_score=75; hold="1-3 days"

    if len(prices) < 50:
        print("  [" + signal_type + "] " + sym + " BLOCKED: only " + str(len(prices)) + " candles")
        return None

    current    = prices[-1]
    global_ath = fetch_global_ath(sym)
    ath        = global_ath if global_ath > 0 else max(prices)
    pct_ath    = (current-ath)/ath*100

    regime  = detect_volatility_regime(prices, highs, lows)
    atr     = regime.get("atr", calc_atr(highs, lows, prices))
    pivots, win, min_move = detect_pivots_adaptive(prices, highs, lows, regime, signal_type)
    phase   = read_market_phase(prices, highs, lows, pivots, current, pct_ath)
    print("  [" + signal_type + "] " + sym + " phase=" + phase)

    # V8 FIX #2: Scalp DOWNTREND — check daily before hard blocking
    if phase == "DOWNTREND":
        if signal_type == "scalp":
            # For scalp, check daily timeframe. If daily is bullish/correcting, allow it
            d_prices, _, _, _, _ = fetch_klines_full(sym, "1d", 100)
            if len(d_prices) >= 20:
                d_ma20  = sum(d_prices[-20:]) / 20
                d_ma50  = sum(d_prices[-50:]) / 50 if len(d_prices) >= 50 else d_ma20
                d_cur   = d_prices[-1]
                d_pct_ath = (d_cur - max(d_prices)) / max(d_prices) * 100
                daily_in_correction = d_pct_ath < -20
                daily_above_ma20    = d_cur > d_ma20

                if daily_in_correction or daily_above_ma20:
                    print("    [scalp] " + sym + " 4H=DOWNTREND but daily is bullish/correcting — continuing as watch")
                    # Don't block — let it run as a low-score watch candidate
                else:
                    print("    [scalp] " + sym + " BLOCKED: 4H=DOWNTREND + daily also bearish")
                    return None
            else:
                print("    [scalp] " + sym + " BLOCKED: DOWNTREND phase (no daily data)")
                return None
        else:
            print("    [swing] " + sym + " BLOCKED: DOWNTREND phase")
            return None

    rsi_val = calc_rsi(prices)
    _, _, h_curr, h_prev = calc_macd(prices)
    macd_bull = (h_curr>0 and h_prev<=0) or h_curr>h_prev
    stoch = calc_stoch(prices)
    smi   = calc_smi(prices)
    div   = calc_divergence(prices)

    if phase=="CORRECTING":          rsi_oversold=35
    elif phase=="IMPULSING":         rsi_oversold=40
    elif regime["type"]=="high":     rsi_oversold=25
    elif regime["type"]=="low":      rsi_oversold=35
    else:                            rsi_oversold=40

    avg_vol = sum(vols[-20:])/20 if len(vols)>=20 else 1
    vol_dec = (sum(vols[-5:])/5) < (sum(vols[-10:-5])/5) if len(vols)>=10 else False
    vol_exp = vols[-1]>avg_vol if vols else False

    weekly_prices,weekly_highs,weekly_lows,_,_ = fetch_klines_full(sym,"1w",52)
    trend = analyze_trend(prices, weekly_prices, current)

    in_correction = pct_ath < -20
    ma50 = sum(prices[-50:])/50 if len(prices)>=50 else current
    daily_bull = current>ma50 or in_correction
    if not daily_bull:
        print("    [" + signal_type + "] " + sym + " BLOCKED: not daily bullish MA50=" + str(round(ma50,2)) + " cur=" + str(round(current,2)))
        return None

    candlestick_info = detect_candlestick_patterns(opens, highs, lows, prices)
    liquidity_info   = detect_liquidity_levels(prices, highs, lows, pivots)
    extended_wave    = detect_extended_wave(pivots, current)

    chart = recognize_chart_structure(
        prices, highs, lows, opens, pivots, current, pct_ath,
        rsi_val, macd_bull, vol_dec, vol_exp, stoch,
        trend, regime, phase, weekly_prices, sym, signal_type,
        liquidity_info, None, candlestick_info, extended_wave
    )

    struct_type  = chart.get("type","UNKNOWN")
    struct_label = chart.get("label","Unknown")
    sub_type     = chart.get("sub_type","")
    conf_score   = chart.get("confidence_score",0)

    # V8 FIX #1: DOUBLE_TOP_WATCH → send watch alert with 6hr cooldown
    if struct_type == "DOUBLE_TOP_WATCH":
        # Only alert once per 6 hours per coin — not every scan
        dt_key = sym + "_dt_" + signal_type
        if time.time() - sent_watches.get(dt_key, 0) < 21600:
            print("    [" + signal_type + "] " + sym + " DOUBLE_TOP watch cooldown — skip")
            return None
        print("    [" + signal_type + "] " + sym + " DOUBLE_TOP — sending watch alert")
        sent_watches[dt_key] = time.time()
        return {
            "watch": True, "type": signal_type.upper(), "sym": sym,
            "current": current, "score": 20, "rsi": rsi_val, "stoch": stoch,
            "struct_label": "Double Top — Watch for resolution",
            "struct_type": "DOUBLE_TOP_WATCH",
            "position_size": 0,
            "reason": "Double Top pattern — waiting for breakdown or breakout confirmation",
            "market_ctx": market_ctx,
            "degree_info": "Double Top watch",
            "degree_bonus": 0,
            "_mtf_alignment": None,
            "_candlestick_patterns": candlestick_info.get("patterns",[]),
            "_liquidity_info": liquidity_info,
            "_extended_wave": extended_wave
        }

    if struct_type in ("DOWNTREND","DOUBLE_TOP","UNKNOWN"):
        print("    [" + signal_type + "] " + sym + " BLOCKED: struct=" + struct_type + " score=" + str(conf_score))
        return None

    # HARD FILTERS
    market_passed, market_reason = hard_market_filter(sym, market_ctx)
    if not market_passed:
        print("    " + market_reason)
        return None

    htf_ok, htf_note = htf_validation(sym)
    if not htf_ok:
        print("    " + htf_note)
        return None

    degree_passed, degree_info, degree_bonus = multi_degree_validation(
        sym, current, struct_type, pivots, weekly_prices, weekly_highs, weekly_lows
    )
    if not degree_passed:
        print("    " + degree_info)
        return None

    # MTF lazy load
    mtf_alignment = None
    if struct_type not in ("TREND_CONTINUATION",) or conf_score >= 50:
        h1_prices,h1_highs,h1_lows,h1_vols,h1_opens = fetch_klines_full(sym,"1h",500)
        if len(h1_prices) >= 50:
            if signal_type=="swing":
                h4_p,h4_h,h4_l,h4_v,h4_o = fetch_klines_full(sym,"4h",500)
                mtf_data = {
                    "1d":{"prices":prices,"highs":highs,"lows":lows,"vols":vols,"opens":opens},
                    "4h":{"prices":h4_p,"highs":h4_h,"lows":h4_l,"vols":h4_v,"opens":h4_o},
                    "1h":{"prices":h1_prices,"highs":h1_highs,"lows":h1_lows,"vols":h1_vols,"opens":h1_opens}
                }
            else:
                d1_p,d1_h,d1_l,d1_v,d1_o = fetch_klines_full(sym,"1d",200)
                mtf_data = {
                    "1d":{"prices":d1_p,"highs":d1_h,"lows":d1_l,"vols":d1_v,"opens":d1_o},
                    "4h":{"prices":prices,"highs":highs,"lows":lows,"vols":vols,"opens":opens},
                    "1h":{"prices":h1_prices,"highs":h1_highs,"lows":h1_lows,"vols":h1_vols,"opens":h1_opens}
                }
            mtf_alignment = check_mtf_alignment(mtf_data)

    if mtf_alignment:
        chart["confidence_score"] = score_structure_v7(
            chart, rsi_val, macd_bull, vol_dec, vol_exp, stoch, trend,
            liquidity_info, mtf_alignment, candlestick_info, extended_wave
        )
        conf_score = chart.get("confidence_score",0)

    ctx_adj     = context_adjustment(sym, market_ctx)
    final_score = max(0, min(100, conf_score + ctx_adj + degree_bonus))

    print("    [" + signal_type + "] " + sym + " score=" + str(final_score) +
          " (raw=" + str(conf_score) + ") struct=" + struct_type + " phase=" + phase)

    # Gate 1: Raw structure score must be at least 45 before any bonuses
    # Prevents degree_bonus from inflating a weak structure to 60+
    if conf_score < 55:
        print("    [" + signal_type + "] " + sym + " BLOCKED: raw score <55, final score=" + str(conf_score))
        return None

    # Gate 2: Final score (with bonuses) must be at least 25 to even watch
    if final_score < 25:
        print("    [" + signal_type + "] " + sym + " BLOCKED: final score too low=" + str(final_score))
        return None

    if rsi_val > 75:
        print("    [" + signal_type + "] " + sym + " BLOCKED: RSI overbought=" + str(round(rsi_val,1)))
        return None

    sl,tp1,tp2,tp3,tp4,sl_reason = calculate_adaptive_risk(
        struct_type, sub_type, pivots, current, regime, atr,
        sl_pct, tp1_pct, tp2_pct, tp3_pct, tp4_pct, extended_wave
    )

    is_locked = chart.get("locked",False)
    position_size = calculate_position_size(final_score, regime, trend["label"], is_locked)

    if final_score>=90:    conf="HIGH — STRONG BUY"
    elif final_score>=85:  conf="HIGH — STRONG BUY"
    elif final_score>=80:  conf="MEDIUM-HIGH — STRONG BUY"
    elif final_score>=75:  conf="MEDIUM — BUY"
    else:                  conf="WATCH"

    if final_score < min_score:
        # Only send watch if score >= 40, otherwise skip entirely
        if final_score < 55:
            print("    [" + signal_type + "] " + sym + " SKIPPED: watch score too low=" + str(final_score))
            return None
        return {
            "watch":True,"type":signal_type.upper(),"sym":sym,
            "current":current,"score":final_score,"rsi":rsi_val,"stoch":stoch,
            "struct_label":struct_label,"struct_type":struct_type,
            "position_size":position_size,
            "reason":"Developing - " + struct_label + " (score " + str(final_score) + "/100)",
            "market_ctx":market_ctx,"degree_info":degree_info,"degree_bonus":degree_bonus,
            "_mtf_alignment":mtf_alignment,"_candlestick_patterns":candlestick_info.get("patterns",[]),
            "_liquidity_info":liquidity_info,"_extended_wave":extended_wave
        }

    return {
        "type":signal_type.upper(),"sym":sym,"tier":coin["tier"],
        "current":current,"ath":ath,"pct_ath":pct_ath,
        "score":final_score,"conf_score":conf_score,"ctx_adj":ctx_adj,
        "conf":conf,"rsi":rsi_val,"stoch":stoch,"hold":hold,
        "sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"tp4":tp4,
        "sl_reason":sl_reason,"struct_type":struct_type,"struct_label":struct_label,
        "sub_type":sub_type,"regime":regime["label"],"phase":phase,"trend":trend["label"],
        "divergence":div["bullish"],"position_size":position_size,"is_locked":is_locked,
        "market_ctx":market_ctx,"degree_info":degree_info,"degree_bonus":degree_bonus,
        "mtf_alignment":mtf_alignment,"candlestick_patterns":candlestick_info.get("patterns",[]),
        "liquidity_info":liquidity_info,"extended_wave":extended_wave
    }

# ================================================================
# FORMATTING
# ================================================================
def fp(p):
    if not p and p != 0: return "N/A"
    if p >= 1000:   return "$" + "{:,}".format(round(p))
    if p >= 1:      return "$" + "{:.4f}".format(p)
    if p >= 0.01:   return "$" + "{:.5f}".format(p)
    return "$" + "{:.7f}".format(p)

def build_msg(sig):
    is_sc  = sig["type"]=="SCALP"
    icon   = "⚡" if is_sc else "📈"
    entry  = sig["current"]

    def pct(tp):
        if not tp or not entry or entry==0: return ""
        return "(" + ("+" if tp>entry else "") + str(round((tp-entry)/entry*100,1)) + "%)"

    def sl_pct():
        sl=sig.get("sl",0)
        if not sl or not entry or entry==0: return ""
        return "(" + str(round((sl-entry)/entry*100,1)) + "%)"

    rr=""
    sl=sig.get("sl",0); tp2=sig.get("tp2",0)
    if sl and tp2 and entry and sl!=entry:
        risk=abs(entry-sl); reward=abs(tp2-entry)
        if risk>0: rr=" | R:R 1:" + str(round(reward/risk,1))

    msg  = icon + " <b>" + sig["type"] + " — " + sig["sym"] + "/USDT</b>\n\n"
    msg += "💵 Entry:  " + fp(entry*0.99) + " – " + fp(entry*1.01) + "\n"
    msg += "🛑 SL:     " + fp(sig["sl"]) + "  " + sl_pct() + rr + "\n\n"
    msg += "🎯 TP1:   " + fp(sig["tp1"]) + "  " + pct(sig["tp1"]) + "\n"
    msg += "🎯 TP2:   " + fp(sig["tp2"]) + "  " + pct(sig["tp2"]) + "\n"
    msg += "🎯 TP3:   " + fp(sig["tp3"]) + "  " + pct(sig["tp3"]) + "\n"
    msg += "🎯 TP4:   " + fp(sig["tp4"]) + "  " + pct(sig["tp4"]) + "\n\n"
    msg += "⏱ Hold: " + sig["hold"] + "\n"
    msg += "⚡ Score: " + str(sig["score"]) + "/100\n"
    msg += "📊 Situation: " + sig["conf"]
    return msg

def build_watch_msg(sym, sig_type, current, score, rsi, struct_label, reason, position_size=0, extra_info=None):
    msg  = "[WATCH] " + sym + "/USDT (" + sig_type + ")\n\n"
    msg += "Pattern: " + struct_label + "\n"
    msg += "Price: " + fp(current) + " | RSI: " + str(round(rsi)) + "\n"
    msg += "Score: " + str(score) + "/100\n"
    msg += "Status: " + reason + "\n\n"
    msg += "Monitoring — not a signal yet"
    return msg

# ================================================================
# PRICE ALERTS
# ================================================================
def check_price_alerts():
    if not active_trades: return
    for key, trade in list(active_trades.items()):
        if trade.get("closed"): continue
        sym=trade["sym"]; sig_type=trade["type"]
        icon="[SCALP]" if sig_type=="SCALP" else "[SWING]"
        try:
            prices,_,_,_,_ = fetch_klines_full(sym,"15m",2)
            if not prices: continue
            current=prices[-1]
        except: continue

        entry=trade["entry"]; sl=trade["sl"]
        tp1=trade["tp1"]; tp2=trade["tp2"]; tp3=trade["tp3"]; tp4=trade["tp4"]

        if current<=sl and not trade.get("closed"):
            loss=(current-entry)/entry*100
            send_msg("[STOP LOSS] " + sym + "/USDT\n" + icon + " Closed\nPrice: " + fp(current) + " | SL: " + fp(sl) + "\nLoss: " + str(round(loss,1)) + "%\nExit full position.")
            active_trades[key]["closed"]=True; continue

        if current>=tp1 and not trade.get("hit_tp1"):
            profit=(current-entry)/entry*100
            send_msg("[TP1 HIT] " + sym + "/USDT\nPrice: " + fp(current) + "\nProfit: +" + str(round(profit,1)) + "%\nExit 25% | SL -> entry: " + fp(entry))
            active_trades[key]["hit_tp1"]=True; active_trades[key]["sl"]=entry

        if current>=tp2 and not trade.get("hit_tp2"):
            profit=(current-entry)/entry*100
            send_msg("[TP2 HIT] " + sym + "/USDT\nPrice: " + fp(current) + "\nProfit: +" + str(round(profit,1)) + "%\nExit 25% | SL -> TP1: " + fp(tp1))
            active_trades[key]["hit_tp2"]=True; active_trades[key]["sl"]=tp1

        if current>=tp3 and not trade.get("hit_tp3"):
            profit=(current-entry)/entry*100
            send_msg("[TP3 HIT] " + sym + "/USDT\nPrice: " + fp(current) + "\nProfit: +" + str(round(profit,1)) + "%\nExit 25% | SL -> TP2: " + fp(tp2))
            active_trades[key]["hit_tp3"]=True; active_trades[key]["sl"]=tp2

        if current>=tp4 and not trade.get("hit_tp4"):
            profit=(current-entry)/entry*100
            send_msg("[TP4 HIT] " + sym + "/USDT\nPrice: " + fp(current) + "\nFull profit: +" + str(round(profit,1)) + "%! Trade complete!")
            active_trades[key]["hit_tp4"]=True; active_trades[key]["closed"]=True

# ================================================================
# WATCH MONITOR
# ================================================================
def monitor_watch_coins():
    return  # Watch alerts disabled — signals only
    if not sent_watches: return
    now=time.time()
    for key, watch_time in list(sent_watches.items()):
        if now-watch_time > 21600: continue
        sym=key.split("_")[0]; sig_type="scalp" if "scalp" in key else "swing"
        coin=next((c for c in HALAL_WATCHLIST if c["sym"]==sym), None)
        if not coin: continue
        try:
            result=analyze(coin,sig_type)
            if not result or result.get("watch"): continue
            signal_key=sym+"_"+sig_type; cooldown=14400 if sig_type=="swing" else 7200
            if time.time()-sent_signals.get(signal_key,0)<cooldown: continue
            print("  WATCH->SIGNAL: " + sym + " " + sig_type.upper() + " " + str(result["score"]) + "/100")
            send_msg(build_msg(result))
            sent_signals[signal_key]=now
            active_trades[signal_key]={"sym":sym,"type":sig_type.upper(),"entry":result["current"],
                "sl":result["sl"],"tp1":result["tp1"],"tp2":result["tp2"],
                "tp3":result["tp3"],"tp4":result["tp4"],
                "hit_tp1":False,"hit_tp2":False,"hit_tp3":False,"hit_tp4":False,
                "closed":False,"time":now}
        except Exception as e:
            print("  Watch error " + sym + ": " + str(e))
        time.sleep(1)

# ================================================================
# MAIN LOOP
# ================================================================
def main():
    global scan_count, market_ctx

    start_api_server()
    tg_ok = init_telegram()
    load_state()  # Restore cooldowns from disk

    total=len(HALAL_WATCHLIST)
    t1=[c["sym"] for c in HALAL_WATCHLIST if c["tier"]==1]
    t2=[c["sym"] for c in HALAL_WATCHLIST if c["tier"]==2]
    t3=[c["sym"] for c in HALAL_WATCHLIST if c["tier"]==3]

    print("=" * 60)
    print("EW STRATEGY V8 — SIGNALSYM")
    print("Fixes: Live BTC.D | DOUBLE_TOP Watch | Scalp DOWNTREND Fix")
    print(str(total) + " coins | 100% Binance data | No CoinGecko")
    print("=" * 60)

    if tg_ok:
        msg  = "[BOT V8 STARTED] SIGNALSYM\n"
        msg += "================================\n"
        msg += "Signals only: 75/100 minimum\n"
        msg += "V8.3 — signals only, no watch spam\n"
        msg += "60-69: Developing — Monitoring\n"
        msg += "70-79: Medium — Monitoring\n"
        msg += "80+: Strong Buy\n"
        msg += "================================\n"
        msg += "MARKET: CoinGecko Live | PRICE: Binance\n"
        msg += "================================\n"
        msg += "T1 (" + str(len(t1)) + "): " + ", ".join(t1[:8]) + "...\n"
        msg += "T2 (" + str(len(t2)) + "): " + ", ".join(t2[:8]) + "...\n"
        msg += "T3 (" + str(len(t3)) + "): " + ", ".join(t3[:8]) + "..."
        send_msg(msg)
    else:
        print("Telegram not configured.")

    while True:
        scan_count += 1
        now=datetime.now().strftime("%H:%M:%S")
        print("\n[" + now + "] Scan #" + str(scan_count))

        market_ctx = fetch_market_context()
        signals=0; watches=0

        try:
            test=requests.get(BN_BASE+"/ping",timeout=10)
            if test.status_code==451:
                print("  Binance geo-blocked (451) — check BN_BASE URL")
                time.sleep(300); continue
            elif test.status_code!=200:
                print("  Binance not responding (status=" + str(test.status_code) + ") — waiting 60s")
                time.sleep(60); continue
            print("  Binance ping OK")
        except Exception as e:
            print("  Binance unreachable: " + str(e) + " — waiting 60s")
            time.sleep(60); continue

        for coin in HALAL_WATCHLIST:
            sym=coin["sym"]
            print("  " + sym + "...", flush=True)

            try:
                now = time.time()

                # ── SWING ──────────────────────────────────────
                swing_key = sym + "_swing"
                sw_cd = now - sent_signals.get(swing_key, 0)
                if sw_cd < 28800:
                    print("  " + sym + " swing: cooldown " + str(round((28800-sw_cd)/3600,1)) + "hr left")
                else:
                    sw = analyze(coin, "swing")
                    if sw and not sw.get("watch"):
                        # Final cooldown check (state may have been updated mid-scan)
                        if time.time() - sent_signals.get(swing_key, 0) < 28800:
                            print("  " + sym + " swing: cooldown (late check)")
                        else:
                            print(sym + " SWING " + str(sw["score"]) + "/100 SENDING")
                            send_msg(build_msg(sw))
                            sent_signals[swing_key] = time.time()
                            signals += 1
                            save_state()
                            active_trades[swing_key] = {
                                "sym":sym,"type":"SWING","entry":sw["current"],
                                "sl":sw["sl"],"tp1":sw["tp1"],"tp2":sw["tp2"],
                                "tp3":sw["tp3"],"tp4":sw["tp4"],
                                "hit_tp1":False,"hit_tp2":False,"hit_tp3":False,"hit_tp4":False,
                                "closed":False,"time":time.time()
                            }
                            time.sleep(3)
                    elif sw and sw.get("watch"):
                        print("  " + sym + " swing: score=" + str(sw.get("score",0)) + " below 75")
                    else:
                        print("  " + sym + " swing: NO SIGNAL")

                # ── SCALP ──────────────────────────────────────
                scalp_key = sym + "_scalp"
                sc_cd = now - sent_signals.get(scalp_key, 0)
                if sc_cd < 14400:
                    print("  " + sym + " scalp: cooldown " + str(round((14400-sc_cd)/3600,1)) + "hr left")
                else:
                    sc = analyze(coin, "scalp")
                    if sc and not sc.get("watch"):
                        # Final cooldown check
                        if time.time() - sent_signals.get(scalp_key, 0) < 14400:
                            print("  " + sym + " scalp: cooldown (late check)")
                        else:
                            print(sym + " SCALP " + str(sc["score"]) + "/100 SENDING")
                            send_msg(build_msg(sc))
                            sent_signals[scalp_key] = time.time()
                            signals += 1
                            save_state()
                            active_trades[scalp_key] = {
                                "sym":sym,"type":"SCALP","entry":sc["current"],
                                "sl":sc["sl"],"tp1":sc["tp1"],"tp2":sc["tp2"],
                                "tp3":sc["tp3"],"tp4":sc["tp4"],
                                "hit_tp1":False,"hit_tp2":False,"hit_tp3":False,"hit_tp4":False,
                                "closed":False,"time":time.time()
                            }
                            time.sleep(3)
                    elif sc and sc.get("watch"):
                        print("  " + sym + " scalp: score=" + str(sc.get("score",0)) + " below 75")
                    else:
                        print("  " + sym + " scalp: NO SIGNAL")

                time.sleep(1)

            except Exception as e:
                import traceback
                print("  " + sym + " CRASH: " + str(e))
                print("  " + traceback.format_exc()[-300:])
                time.sleep(2)

        print("\nScan #" + str(scan_count) + " - " + str(signals) + " signal(s), " + str(watches) + " watch(es) - next in 15min")
        active_count=len([t for t in active_trades.values() if not t.get("closed")])
        print("  Active trades: " + str(active_count) + " | Watch list: " + str(len(sent_watches)))

        for _ in range(3):
            time.sleep(300)
            check_price_alerts()
            if sent_watches: monitor_watch_coins()

        if scan_count%96==0:
            msg  = "[HEARTBEAT]\n"
            msg += "Scans: " + str(scan_count) + " | Coins: " + str(total) + "\n"
            msg += "Active: " + str(active_count) + "\n"
            msg += datetime.now().strftime("%Y-%m-%d %H:%M") + " UTC"
            send_msg(msg)

if __name__=="__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped.")
    except Exception as e:
        print("\nFatal error: " + str(e))
        import traceback
        traceback.print_exc()
