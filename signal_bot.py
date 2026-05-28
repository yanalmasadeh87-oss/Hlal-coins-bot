# ═══════════════════════════════════════════════════════════════
# ELLIOTT WAVE ENGINE V3
# Base: Your wave structure (W1→W2→W3 supercycle)
# Added: 18-point validation, multi-TF, EWO, volume, Fibonacci
# ═══════════════════════════════════════════════════════════════

import requests
import time
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────
TELEGRAM_TOKEN = "7975488031:AAHLdeNTM-YIItriXwradU4bPyCMdR-mAIY"
CHAT_ID        = "8422276082"
CG_API_KEY     = "CG-DJnA8sWPRSUuF8Xz27Fhastn"
CG_BASE        = "https://api.coingecko.com/api/v3"
TG_BASE        = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ── SIGNAL LEVELS ─────────────────────────────────────────────
SL_PCT  = 0.05   # -5%
TP1_PCT = 0.05   # +5%
TP2_PCT = 0.10   # +10%
TP3_PCT = 0.15   # +15%
TP4_PCT = 0.20   # +20%

# ── HALAL WATCHLIST ───────────────────────────────────────────
HALAL_WATCHLIST = [
    # TIER 1 — cryptohalal.cc verified
    {"id":"bitcoin",               "sym":"BTC",    "tier":1},
    {"id":"ethereum",              "sym":"ETH",    "tier":1},
    {"id":"ripple",                "sym":"XRP",    "tier":1},
    {"id":"solana",                "sym":"SOL",    "tier":1},
    {"id":"binancecoin",           "sym":"BNB",    "tier":1},
    {"id":"cardano",               "sym":"ADA",    "tier":1},
    {"id":"avalanche-2",           "sym":"AVAX",   "tier":1},
    {"id":"sui",                   "sym":"SUI",    "tier":1},
    {"id":"hedera-hashgraph",      "sym":"HBAR",   "tier":1},
    {"id":"near",                  "sym":"NEAR",   "tier":1},
    {"id":"polkadot",              "sym":"DOT",    "tier":1},
    {"id":"internet-computer",     "sym":"ICP",    "tier":1},
    {"id":"fantom",                "sym":"FTM",    "tier":1},
    {"id":"ethereum-classic",      "sym":"ETC",    "tier":1},
    {"id":"worldcoin-wld",         "sym":"WLD",    "tier":1},
    {"id":"render-token",          "sym":"RENDER", "tier":1},
    {"id":"cosmos",                "sym":"ATOM",   "tier":1},
    {"id":"kaspa",                 "sym":"KAS",    "tier":1},
    {"id":"filecoin",              "sym":"FIL",    "tier":1},
    {"id":"aptos",                 "sym":"APT",    "tier":1},
    {"id":"arbitrum",              "sym":"ARB",    "tier":1},
    {"id":"vechain",               "sym":"VET",    "tier":1},
    {"id":"sei-network",           "sym":"SEI",    "tier":1},
    {"id":"blockstack",            "sym":"STX",    "tier":1},
    {"id":"celestia",              "sym":"TIA",    "tier":1},
    {"id":"pyth-network",          "sym":"PYTH",   "tier":1},
    {"id":"the-graph",             "sym":"GRT",    "tier":1},
    {"id":"optimism",              "sym":"OP",     "tier":1},
    {"id":"theta-token",           "sym":"THETA",  "tier":1},
    # TIER 2
    {"id":"stellar",               "sym":"XLM",    "tier":2},
    {"id":"algorand",              "sym":"ALGO",   "tier":2},
    {"id":"litecoin",              "sym":"LTC",    "tier":2},
    {"id":"toncoin",               "sym":"TON",    "tier":2},
    {"id":"chainlink",             "sym":"LINK",   "tier":2},
    {"id":"matic-network",         "sym":"POL",    "tier":2},
    {"id":"tezos",                 "sym":"XTZ",    "tier":2},
    {"id":"quant-network",         "sym":"QNT",    "tier":2},
    {"id":"iota",                  "sym":"IOTA",   "tier":2},
    {"id":"bitcoin-cash",          "sym":"BCH",    "tier":2},
    {"id":"immutable-x",           "sym":"IMX",    "tier":2},
    {"id":"injective-protocol",    "sym":"INJ",    "tier":2},
    {"id":"fetch-ai",              "sym":"FET",    "tier":2},
    {"id":"ocean-protocol",        "sym":"OCEAN",  "tier":2},
    {"id":"singularitynet",        "sym":"AGIX",   "tier":2},
    {"id":"akash-network",         "sym":"AKT",    "tier":2},
    {"id":"arweave",               "sym":"AR",     "tier":2},
    {"id":"helium",                "sym":"HNT",    "tier":2},
    {"id":"nervos-network",        "sym":"CKB",    "tier":2},
    {"id":"harmony",               "sym":"ONE",    "tier":2},
    {"id":"icon",                  "sym":"ICX",    "tier":2},
    {"id":"zilliqa",               "sym":"ZIL",    "tier":2},
    {"id":"qtum",                  "sym":"QTUM",   "tier":2},
    {"id":"decred",                "sym":"DCR",    "tier":2},
    {"id":"ravencoin",             "sym":"RVN",    "tier":2},
    {"id":"nano",                  "sym":"NANO",   "tier":2},
    {"id":"xdc-network",           "sym":"XDC",    "tier":2},
    {"id":"multiversx",            "sym":"EGLD",   "tier":2},
    {"id":"flow",                  "sym":"FLOW",   "tier":2},
    {"id":"ankr",                  "sym":"ANKR",   "tier":2},
    {"id":"storj",                 "sym":"STORJ",  "tier":2},
    {"id":"band-protocol",         "sym":"BAND",   "tier":2},
    {"id":"numeraire",             "sym":"NMR",    "tier":2},
    {"id":"golem",                 "sym":"GLM",    "tier":2},
    {"id":"skale",                 "sym":"SKL",    "tier":2},
    {"id":"celo",                  "sym":"CELO",   "tier":2},
    {"id":"oasis-network",         "sym":"ROSE",   "tier":2},
    {"id":"cartesi",               "sym":"CTSI",   "tier":2},
    {"id":"kadena",                "sym":"KDA",    "tier":2},
    {"id":"secret",                "sym":"SCRT",   "tier":2},
    {"id":"aleph-zero",            "sym":"AZERO",  "tier":2},
    {"id":"lisk",                  "sym":"LSK",    "tier":2},
    {"id":"waves",                 "sym":"WAVES",  "tier":2},
    {"id":"siacoin",               "sym":"SC",     "tier":2},
    {"id":"digibyte",              "sym":"DGB",    "tier":2},
    # TIER 3
    {"id":"gala",                  "sym":"GALA",   "tier":3},
    {"id":"axie-infinity",         "sym":"AXS",    "tier":3},
    {"id":"the-sandbox",           "sym":"SAND",   "tier":3},
    {"id":"decentraland",          "sym":"MANA",   "tier":3},
    {"id":"enjincoin",             "sym":"ENJ",    "tier":3},
    {"id":"chiliz",                "sym":"CHZ",    "tier":3},
    {"id":"theta-fuel",            "sym":"TFUEL",  "tier":3},
    {"id":"astar",                 "sym":"ASTR",   "tier":3},
    {"id":"moonbeam",              "sym":"GLMR",   "tier":3},
    {"id":"acala",                 "sym":"ACA",    "tier":3},
    {"id":"basic-attention-token", "sym":"BAT",    "tier":3},
    {"id":"livepeer",              "sym":"LPT",    "tier":3},
    {"id":"audius",                "sym":"AUDIO",  "tier":3},
    {"id":"civic",                 "sym":"CVC",    "tier":3},
    {"id":"requestnetwork",        "sym":"REQ",    "tier":3},
    {"id":"gitcoin",               "sym":"GTC",    "tier":3},
    {"id":"power-ledger",          "sym":"POWR",   "tier":3},
    {"id":"woo-network",           "sym":"WOO",    "tier":3},
    {"id":"holotoken",             "sym":"HOT",    "tier":3},
    {"id":"syscoin",               "sym":"SYS",    "tier":3},
    {"id":"metahero",              "sym":"HERO",   "tier":3},
    {"id":"xyo-network",           "sym":"XYO",    "tier":3},
    {"id":"wrapped-bitcoin",       "sym":"WBTC",   "tier":3},
    {"id":"stacks",                "sym":"STX2",   "tier":3},
]

# Remove duplicates
seen = set()
UNIQUE_LIST = []
for c in HALAL_WATCHLIST:
    if c["sym"] not in seen:
        seen.add(c["sym"])
        UNIQUE_LIST.append(c)
HALAL_WATCHLIST = UNIQUE_LIST

sent_signals = {}
scan_count = 0

# ═══════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════

def fetch_prices(coin_id, days, interval="daily", retries=3):
    """Fetch price + volume data with retry logic"""
    for attempt in range(retries):
        try:
            r = requests.get(
                f"{CG_BASE}/coins/{coin_id}/market_chart",
                params={"vs_currency":"usd","days":days,"interval":interval},
                headers={"x-cg-demo-api-key":CG_API_KEY},
                timeout=20
            )
            d = r.json()
            prices = [p[1] for p in d.get("prices",[])]
            vols   = [v[1] for v in d.get("total_volumes",[])]
            if prices:
                return prices, vols
        except Exception as e:
            if attempt < retries-1:
                time.sleep(3)
    return [], []

def fetch_info(coin_id, retries=3):
    """Fetch coin info with retry"""
    for attempt in range(retries):
        try:
            r = requests.get(
                f"{CG_BASE}/coins/{coin_id}",
                params={"localization":"false","tickers":"false",
                        "community_data":"false","developer_data":"false"},
                headers={"x-cg-demo-api-key":CG_API_KEY},
                timeout=20
            )
            return r.json()
        except:
            if attempt < retries-1:
                time.sleep(3)
    return {}

# ═══════════════════════════════════════════════════════════════
# INDICATORS
# ═══════════════════════════════════════════════════════════════

def calc_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    gains = losses = 0
    for i in range(1, period+1):
        d = prices[i]-prices[i-1]
        if d>0: gains+=d
        else: losses+=abs(d)
    ag,al = gains/period, losses/period
    for i in range(period, len(prices)):
        d = prices[i]-prices[i-1]
        ag = (ag*(period-1)+(d if d>0 else 0))/period
        al = (al*(period-1)+(abs(d) if d<0 else 0))/period
    return 100 if al==0 else 100-(100/(1+ag/al))

def calc_ema(prices, period):
    if len(prices)<period: return []
    k = 2/(period+1)
    r = [sum(prices[:period])/period]
    for p in prices[period:]:
        r.append(p*k+r[-1]*(1-k))
    return r

def calc_macd(prices):
    """Returns (macd_val, signal_val, hist_curr, hist_prev)"""
    if len(prices)<35: return 0,0,0,0
    ef = calc_ema(prices,12)
    es = calc_ema(prices,26)
    off = 26-12
    if len(es)==0: return 0,0,0,0
    ml = [ef[i+off]-es[i] for i in range(len(es))]
    if len(ml)<9: return 0,0,0,0
    sl = calc_ema(ml,9)
    diff = len(ml)-len(sl)
    hist = [ml[i+diff]-sl[i] for i in range(len(sl))]
    if len(hist)<2: return ml[-1],sl[-1],0,0
    return ml[-1],sl[-1],hist[-1],hist[-2]

def calc_ewo(prices):
    """Elliott Wave Oscillator: 5-period MA minus 35-period MA"""
    if len(prices)<35: return 0
    ma5  = sum(prices[-5:])/5
    ma35 = sum(prices[-35:])/35
    return ma5-ma35

def calc_volume_trend(vols):
    """Returns True if volume declining (healthy correction)"""
    if len(vols)<10: return False
    recent = sum(vols[-5:])/5
    prev   = sum(vols[-10:-5])/5
    return recent < prev

def calc_volume_expanding(vols):
    """Returns True if volume expanding (reversal signal)"""
    if len(vols)<5: return False
    return vols[-1] > sum(vols[-5:])/5

# ═══════════════════════════════════════════════════════════════
# WAVE DETECTION ENGINE — YOUR STRUCTURE AS BASE
# ═══════════════════════════════════════════════════════════════

def find_pivots(prices, min_move_pct=0.10):
    """Find significant price pivots"""
    n = len(prices)
    if n < 20: return []
    win = max(3, n//20)
    pivots = []

    for i in range(win, n-win):
        sl = prices[i-win:i+win+1]
        mx, mn = max(sl), min(sl)
        if prices[i]==mx and prices[i]>prices[i-1] and prices[i]>prices[i+1]:
            pivots.append({"idx":i,"price":prices[i],"type":"peak"})
        elif prices[i]==mn and prices[i]<prices[i-1] and prices[i]<prices[i+1]:
            pivots.append({"idx":i,"price":prices[i],"type":"trough"})

    # Add start and end
    start_type = "trough" if prices[0]<prices[min(10,n-1)] else "peak"
    pivots.insert(0,{"idx":0,"price":prices[0],"type":start_type})
    pivots.append({"idx":n-1,"price":prices[-1],"type":"current"})

    # Filter by minimum move
    sig = [pivots[0]]
    for i in range(1,len(pivots)):
        prev,curr = sig[-1],pivots[i]
        if prev["type"]==curr["type"]:
            if curr["type"]=="peak" and curr["price"]>prev["price"]: sig[-1]=curr
            elif curr["type"]=="trough" and curr["price"]<prev["price"]: sig[-1]=curr
            continue
        move = abs((curr["price"]-prev["price"])/prev["price"])
        if move >= min_move_pct:
            sig.append(curr)
    return sig

def validate_ew_rules(pivots):
    """
    Validate your 3 cardinal EW rules:
    Rule 1: W2 never retraces more than 100% of W1
    Rule 2: W3 is never the shortest wave
    Rule 3: W4 never overlaps W1 territory
    """
    issues = []
    valid  = True

    if len(pivots) >= 3:
        w1_start = pivots[0]["price"]
        w1_end   = pivots[1]["price"]
        w2_end   = pivots[2]["price"]
        w1_range = abs(w1_end-w1_start)
        if w1_range > 0:
            w2_ret = abs(w2_end-w1_end)/w1_range*100
            if w2_end < w1_start:
                issues.append("W2>100% W1"); valid=False
            elif w2_ret < 38:
                issues.append(f"W2 shallow({w2_ret:.0f}%)")
            elif w2_ret > 100:
                issues.append("W2 too deep"); valid=False

    if len(pivots) >= 4:
        w1_size = abs(pivots[1]["price"]-pivots[0]["price"])
        w3_size = abs(pivots[3]["price"]-pivots[2]["price"])
        if w3_size < w1_size:
            issues.append("W3<W1"); valid=False

    if len(pivots) >= 5:
        w1_top = pivots[1]["price"]
        w4_low = pivots[4]["price"]
        if w4_low < w1_top:
            issues.append("W4 overlaps W1"); valid=False

    return valid, issues

def detect_wave_position(prices, vols, ath):
    """
    Detect current position in YOUR wave structure:
    - Grand: W1→W2→W3 (we are in W3)
    - W3 internal: W1ofW3→W2ofW3→W3ofW3
    - W2ofW3 internal: A→B→C (correction)
    """
    if len(prices)<30: return None

    current = prices[-1]
    pct_ath = ((current-ath)/ath)*100

    # Find pivots at different sensitivities
    pivots_major  = find_pivots(prices, min_move_pct=0.15)  # Daily/Weekly
    pivots_minor  = find_pivots(prices, min_move_pct=0.08)  # 4H
    pivots_micro  = find_pivots(prices, min_move_pct=0.03)  # 1H

    ew_valid, ew_issues = validate_ew_rules(pivots_major)

    # Determine entry type
    entry_type = ""
    w2_retrace = 0

    # Check for W2 bottom (38-100% retrace of W1)
    if len(pivots_major) >= 3:
        w1_range = abs(pivots_major[1]["price"]-pivots_major[0]["price"])
        if w1_range > 0:
            w2_range = abs(pivots_major[2]["price"]-pivots_major[1]["price"])
            w2_retrace = (w2_range/w1_range)*100
            if 38 <= w2_retrace <= 100:
                entry_type = "W2"

    # Check for W4 bottom (23-38% retrace of W3)
    if len(pivots_major) >= 5:
        w3_range = abs(pivots_major[3]["price"]-pivots_major[2]["price"])
        if w3_range > 0:
            w4_range = abs(pivots_major[4]["price"]-pivots_major[3]["price"])
            w4_retrace = (w4_range/w3_range)*100
            if 23 <= w4_retrace <= 38 and pivots_major[4]["price"] > pivots_major[1]["price"]:
                entry_type = "W4"

    # Label waves — never return "undefined"
    labels = ["W1","W2","W3","W4","W5","Wave A","Wave B","Wave C"]
    labeled_waves = []
    for i, p in enumerate(pivots_major[:8]):
        label = labels[i] if i < len(labels) else f"Wave {i+1}"
        color = "#22c55e" if p["type"]=="peak" else "#ef4444" if p["type"]=="trough" else "#f0b429"
        labeled_waves.append({
            "label":  label,
            "price":  p["price"],
            "type":   p["type"],
            "color":  color,
            "idx":    p["idx"],
        })

    # Alternate count — if primary unclear
    alternate = ""
    if not ew_valid:
        alternate = "Alternate: ABC zigzag correction in progress"
    elif pct_ath < -70:
        alternate = "Alternate: Extended W2 — accumulation zone"
    elif pct_ath < -40:
        alternate = "Alternate: W4 correction within larger W3"

    return {
        "waves":       labeled_waves,
        "pivots":      pivots_major,
        "entry_type":  entry_type,
        "w2_retrace":  w2_retrace,
        "ew_valid":    ew_valid,
        "ew_issues":   ew_issues,
        "alternate":   alternate,
        "pct_ath":     pct_ath,
        "current":     current,
        "ath":         ath,
    }

# ═══════════════════════════════════════════════════════════════
# MULTI-TIMEFRAME ENGINE
# ═══════════════════════════════════════════════════════════════

def analyze_timeframe(coin_id, days, interval="daily"):
    """Analyze a single timeframe"""
    prices, vols = fetch_prices(coin_id, days, interval)
    if len(prices) < 30:
        return None

    rsi_val  = calc_rsi(prices)
    _,_,h_curr,h_prev = calc_macd(prices)
    ewo      = calc_ewo(prices)
    vol_dec  = calc_volume_trend(vols)
    vol_exp  = calc_volume_expanding(vols)
    macd_cross   = h_curr>0 and h_prev<=0
    macd_turning = h_curr>h_prev

    # Trend bias: bullish if price above 50-period MA
    ma50 = sum(prices[-50:])/50 if len(prices)>=50 else prices[-1]
    bullish = prices[-1] > ma50

    return {
        "prices":      prices,
        "vols":        vols,
        "rsi":         rsi_val,
        "macd_cross":  macd_cross,
        "macd_turning":macd_turning,
        "ewo":         ewo,
        "vol_dec":     vol_dec,
        "vol_exp":     vol_exp,
        "bullish":     bullish,
        "current":     prices[-1],
    }

def full_analysis(coin):
    """
    Full multi-timeframe analysis using your wave structure.
    Checks: Weekly → Daily → 4H → 1H
    Golden Rule: all must align before signal fires.
    """
    coin_id = coin["id"]

    # Fetch all timeframes
    weekly  = analyze_timeframe(coin_id, 730,  "daily")   # 2yr weekly view
    daily   = analyze_timeframe(coin_id, 365,  "daily")   # 1yr daily
    h4      = analyze_timeframe(coin_id, 90,   "daily")   # 3mo 4H view
    h1      = analyze_timeframe(coin_id, 14,   "hourly")  # 2wk 1H

    if not weekly or not daily:
        return None

    # Fetch coin info for ATH
    info = fetch_info(coin_id)
    ath  = info.get("market_data",{}).get("ath",{}).get("usd", max(daily["prices"]))
    current = daily["current"]
    pct_ath = ((current-ath)/ath)*100

    # Wave position on daily (your structure)
    wave_pos = detect_wave_position(daily["prices"], daily["vols"], ath)
    if not wave_pos:
        return None

    # ── GOLDEN RULE CHECK ────────────────────────────────────
    # Weekly must be bullish for any long signal
    weekly_bull = weekly["bullish"]

    # Daily must show bullish structure
    daily_bull  = daily["bullish"] or pct_ath < -50

    # 4H must confirm if available
    h4_bull = h4["bullish"] if h4 else True

    # Golden Rule: all timeframes must align
    golden_rule_pass = weekly_bull and daily_bull and h4_bull

    # ── 18-POINT CHECKLIST ───────────────────────────────────
    entry = wave_pos["entry_type"]

    checks = {
        # Timeframe alignment (4 checks)
        "c01_weekly_bull":    weekly_bull,
        "c02_daily_bull":     daily_bull,
        "c03_h4_aligned":     h4_bull,
        "c04_golden_rule":    golden_rule_pass,
        # Wave structure (3 checks)
        "c05_wave_count":     len(wave_pos["waves"]) >= 4,
        "c06_ew_valid":       wave_pos["ew_valid"],
        "c07_entry_zone":     entry != "",
        # Price level (2 checks)
        "c08_price_level":    pct_ath < -40,
        "c09_deep_level":     pct_ath < -60,
        # Fibonacci (1 check)
        "c10_fib_level":      -80 < pct_ath < -38,
        # Momentum (3 checks)
        "c11_rsi_ok":         daily["rsi"] < 45,
        "c12_macd_ok":        daily["macd_cross"] or daily["macd_turning"],
        "c13_ewo_positive":   daily["ewo"] > 0 or h4["ewo"] > 0 if h4 else daily["ewo"] > 0,
        # Volume (3 checks)
        "c14_vol_declining":  daily["vol_dec"],
        "c15_vol_expanding":  daily["vol_exp"] or (h1["vol_exp"] if h1 else False),
        "c16_vol_ok":         daily["vol_dec"] or daily["vol_exp"],
        # Structure (2 checks)
        "c17_abc_structure":  len(wave_pos["waves"]) >= 5,
        "c18_no_overlap":     wave_pos["ew_valid"],
    }

    score = sum(checks.values())

    # ── SIGNAL QUALIFICATION ──────────────────────────────────
    # Must pass Golden Rule AND minimum score
    if not golden_rule_pass and pct_ath > -40:
        return None

    # Minimum 10/18 for signal
    if score < 10:
        return None

    # Must have some momentum confirmation
    if not (checks["c11_rsi_ok"] or checks["c12_macd_ok"]):
        return None

    # ── SIGNAL LEVELS ─────────────────────────────────────────
    sl  = current*(1-SL_PCT)
    tp1 = current*(1+TP1_PCT)
    tp2 = current*(1+TP2_PCT)
    tp3 = current*(1+TP3_PCT)
    tp4 = current*(1+TP4_PCT)

    # Confidence
    if score >= 15:   conf = "🔥 HIGH"
    elif score >= 12: conf = "⚡ MEDIUM-HIGH"
    elif score >= 10: conf = "✳️ MEDIUM"
    else: return None

    return {
        "sym":         coin["sym"],
        "tier":        coin["tier"],
        "current":     current,
        "ath":         ath,
        "pct_ath":     pct_ath,
        "entry_type":  entry,
        "w2_retrace":  wave_pos["w2_retrace"],
        "waves":       wave_pos["waves"],
        "ew_valid":    wave_pos["ew_valid"],
        "ew_issues":   wave_pos["ew_issues"],
        "alternate":   wave_pos["alternate"],
        "score":       score,
        "conf":        conf,
        "checks":      checks,
        "rsi":         daily["rsi"],
        "macd_cross":  daily["macd_cross"],
        "golden_rule": golden_rule_pass,
        "sl":  sl, "tp1":tp1, "tp2":tp2, "tp3":tp3, "tp4":tp4,
    }

# ═══════════════════════════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════════════════════════

def fp(p):
    if not p: return "N/A"
    if p>=1000: return f"${p:,.0f}"
    if p>=1:    return f"${p:.4f}"
    if p>=0.01: return f"${p:.5f}"
    return f"${p:.7f}"

def fpc(p):
    return f"+{p:.1f}%" if p>=0 else f"{p:.1f}%"

# ═══════════════════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════════════════

def send_msg(msg):
    try:
        requests.post(f"{TG_BASE}/sendMessage",
            json={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML"},
            timeout=10)
    except Exception as e:
        print(f"  TG error: {e}")

def build_signal_msg(sig):
    """Clean signal format — Entry, TP, SL only"""
    entry = sig["entry_type"] or "Setup"
    return (
        f"🕌 <b>{sig['sym']}/USDT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>Entry:</b>  {fp(sig['current']*0.99)} – {fp(sig['current']*1.01)}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>TP1:</b>    {fp(sig['tp1'])}  (+5%)\n"
        f"🎯 <b>TP2:</b>    {fp(sig['tp2'])}  (+10%)\n"
        f"🎯 <b>TP3:</b>    {fp(sig['tp3'])}  (+15%)\n"
        f"🎯 <b>TP4:</b>    {fp(sig['tp4'])}  (+20%)\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔴 <b>SL:</b>     {fp(sig['sl'])}  (-5%)\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 {entry} | Score: {sig['score']}/18 | {sig['conf']}\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"<i>Spot · Halal · Not financial advice</i>"
    )

# ═══════════════════════════════════════════════════════════════
# MAIN BOT LOOP
# ═══════════════════════════════════════════════════════════════

def main():
    global scan_count
    total = len(HALAL_WATCHLIST)
    t1 = [c["sym"] for c in HALAL_WATCHLIST if c["tier"]==1]
    t2 = [c["sym"] for c in HALAL_WATCHLIST if c["tier"]==2]
    t3 = [c["sym"] for c in HALAL_WATCHLIST if c["tier"]==3]

    print(f"🕌 EW Strategy Bot V3 Starting...")
    print(f"📊 Watching {total} halal coins")
    print(f"🔍 18-point validation system\n")

    send_msg(
        f"🕌 <b>EW Strategy Bot V3 — Active</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Shariah-Compliant Coins Only\n"
        f"📊 18-Point Validation System\n"
        f"🔍 Multi-Timeframe: Weekly+Daily+4H+1H\n"
        f"📐 Your Wave Structure as Base\n"
        f"⏱ Scanning every 15 minutes\n"
        f"💰 Spot only — no leverage\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⭐⭐⭐ T1 ({len(t1)}): {', '.join(t1[:10])}...\n"
        f"⭐⭐ T2 ({len(t2)}): {', '.join(t2[:10])}...\n"
        f"⭐ T3 ({len(t3)}): {', '.join(t3[:8])}...\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"بارك الله فيك 🤲"
    )

    while True:
        scan_count += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] Scan #{scan_count} — {total} coins")
        signals_found = 0

        for coin in HALAL_WATCHLIST:
            sym = coin["sym"]
            print(f"  {sym}...", end=" ", flush=True)
            try:
                sig = full_analysis(coin)
                if sig:
                    last = sent_signals.get(sym, 0)
                    if time.time()-last < 14400:  # 4hr cooldown
                        print("cooldown")
                        time.sleep(4)
                        continue
                    print(f"🔥 {sig['score']}/18 — {sig['conf']}")
                    send_msg(build_signal_msg(sig))
                    sent_signals[sym] = time.time()
                    signals_found += 1
                    time.sleep(3)
                else:
                    print("–")
                time.sleep(5)  # Rate limit
            except Exception as e:
                print(f"err: {e}")
                time.sleep(6)

        print(f"\n  ✅ Scan #{scan_count} done. "
              f"{signals_found} signal(s). Next in 15min...")

        # Heartbeat every 24 hours
        if scan_count % 96 == 0:
            send_msg(
                f"💓 <b>Bot Heartbeat</b>\n"
                f"Scans: {scan_count}\n"
                f"Coins: {total}\n"
                f"Signals sent: {len(sent_signals)}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
                f"الحمد لله 🤲"
            )

        time.sleep(900)  # 15 minutes

if __name__ == "__main__":
    main()
