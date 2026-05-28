import requests
import time
from datetime import datetime

# ── CONFIGURATION ─────────────────────────────────────────────
TELEGRAM_TOKEN = "7975488031:AAHLdeNTM-YIItriXwradU4bPyCMdR-mAIY"
CHAT_ID = "8422276082"
CG_API_KEY = "CG-DJnA8sWPRSUuF8Xz27Fhastn"
CG_BASE = "https://api.coingecko.com/api/v3"
TG_BASE = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ── HALAL WATCHLIST ───────────────────────────────────────────
# Sources: cryptohalal.cc (your screenshots) + CryptoUmmah +
#          HalalSignalz (Mufti Faraz Adam) + CoinRanking halal list
# SPOT TRADING ONLY — no leverage, no margin, no futures
# Excluded: memecoins, riba-based DeFi, gambling, alcohol

HALAL_WATCHLIST = [

    # ══ TIER 1 — cryptohalal.cc + Mufti Faraz Adam verified ══
    {"id": "bitcoin",                "sym": "BTC",    "tier": 1},
    {"id": "ethereum",               "sym": "ETH",    "tier": 1},
    {"id": "ripple",                 "sym": "XRP",    "tier": 1},
    {"id": "solana",                 "sym": "SOL",    "tier": 1},
    {"id": "binancecoin",            "sym": "BNB",    "tier": 1},
    {"id": "cardano",                "sym": "ADA",    "tier": 1},
    {"id": "avalanche-2",            "sym": "AVAX",   "tier": 1},
    {"id": "sui",                    "sym": "SUI",    "tier": 1},
    {"id": "hedera-hashgraph",       "sym": "HBAR",   "tier": 1},
    {"id": "near",                   "sym": "NEAR",   "tier": 1},
    {"id": "polkadot",               "sym": "DOT",    "tier": 1},
    {"id": "internet-computer",      "sym": "ICP",    "tier": 1},
    {"id": "fantom",                 "sym": "FTM",    "tier": 1},
    {"id": "ethereum-classic",       "sym": "ETC",    "tier": 1},
    {"id": "worldcoin-wld",          "sym": "WLD",    "tier": 1},
    {"id": "render-token",           "sym": "RENDER", "tier": 1},
    {"id": "cosmos",                 "sym": "ATOM",   "tier": 1},
    {"id": "kaspa",                  "sym": "KAS",    "tier": 1},
    {"id": "filecoin",               "sym": "FIL",    "tier": 1},
    {"id": "aptos",                  "sym": "APT",    "tier": 1},
    {"id": "arbitrum",               "sym": "ARB",    "tier": 1},
    {"id": "vechain",                "sym": "VET",    "tier": 1},
    {"id": "sei-network",            "sym": "SEI",    "tier": 1},
    {"id": "blockstack",             "sym": "STX",    "tier": 1},
    {"id": "celestia",               "sym": "TIA",    "tier": 1},
    {"id": "pyth-network",           "sym": "PYTH",   "tier": 1},
    {"id": "the-graph",              "sym": "GRT",    "tier": 1},
    {"id": "optimism",               "sym": "OP",     "tier": 1},
    {"id": "theta-token",            "sym": "THETA",  "tier": 1},

    # ══ TIER 2 — CryptoUmmah + CoinRanking + HalalSignalz ════
    {"id": "stellar",                "sym": "XLM",    "tier": 2},
    {"id": "algorand",               "sym": "ALGO",   "tier": 2},
    {"id": "litecoin",               "sym": "LTC",    "tier": 2},
    {"id": "toncoin",                "sym": "TON",    "tier": 2},
    {"id": "chainlink",              "sym": "LINK",   "tier": 2},
    {"id": "matic-network",          "sym": "POL",    "tier": 2},
    {"id": "tezos",                  "sym": "XTZ",    "tier": 2},
    {"id": "quant-network",          "sym": "QNT",    "tier": 2},
    {"id": "iota",                   "sym": "IOTA",   "tier": 2},
    {"id": "bitcoin-cash",           "sym": "BCH",    "tier": 2},
    {"id": "immutable-x",            "sym": "IMX",    "tier": 2},
    {"id": "injective-protocol",     "sym": "INJ",    "tier": 2},
    {"id": "mantra-dao",             "sym": "OM",     "tier": 2},
    {"id": "fetch-ai",               "sym": "FET",    "tier": 2},
    {"id": "ocean-protocol",         "sym": "OCEAN",  "tier": 2},
    {"id": "singularitynet",         "sym": "AGIX",   "tier": 2},
    {"id": "akash-network",          "sym": "AKT",    "tier": 2},
    {"id": "arweave",                "sym": "AR",     "tier": 2},
    {"id": "helium",                 "sym": "HNT",    "tier": 2},
    {"id": "nervos-network",         "sym": "CKB",    "tier": 2},
    {"id": "harmony",                "sym": "ONE",    "tier": 2},
    {"id": "icon",                   "sym": "ICX",    "tier": 2},
    {"id": "zilliqa",                "sym": "ZIL",    "tier": 2},
    {"id": "qtum",                   "sym": "QTUM",   "tier": 2},
    {"id": "decred",                 "sym": "DCR",    "tier": 2},
    {"id": "ravencoin",              "sym": "RVN",    "tier": 2},
    {"id": "nano",                   "sym": "NANO",   "tier": 2},
    {"id": "xdc-network",            "sym": "XDC",    "tier": 2},
    {"id": "multiversx",             "sym": "EGLD",   "tier": 2},
    {"id": "flow",                   "sym": "FLOW",   "tier": 2},
    {"id": "ankr",                   "sym": "ANKR",   "tier": 2},
    {"id": "storj",                  "sym": "STORJ",  "tier": 2},
    {"id": "band-protocol",          "sym": "BAND",   "tier": 2},
    {"id": "numeraire",              "sym": "NMR",    "tier": 2},
    {"id": "golem",                  "sym": "GLM",    "tier": 2},
    {"id": "skale",                  "sym": "SKL",    "tier": 2},
    {"id": "celo",                   "sym": "CELO",   "tier": 2},
    {"id": "oasis-network",          "sym": "ROSE",   "tier": 2},
    {"id": "cartesi",                "sym": "CTSI",   "tier": 2},
    {"id": "dusk-network",           "sym": "DUSK",   "tier": 2},
    {"id": "orion-protocol",         "sym": "ORN",    "tier": 2},
    {"id": "phala",                  "sym": "PHA",    "tier": 2},
    {"id": "truefi",                 "sym": "TRU",    "tier": 2},
    {"id": "origintrail",            "sym": "TRAC",   "tier": 2},
    {"id": "kava",                   "sym": "KAVA",   "tier": 2},

    # ══ TIER 3 — Broadly accepted halal utility tokens ════════
    {"id": "gala",                   "sym": "GALA",   "tier": 3},
    {"id": "axie-infinity",          "sym": "AXS",    "tier": 3},
    {"id": "the-sandbox",            "sym": "SAND",   "tier": 3},
    {"id": "decentraland",           "sym": "MANA",   "tier": 3},
    {"id": "enjincoin",              "sym": "ENJ",    "tier": 3},
    {"id": "chiliz",                 "sym": "CHZ",    "tier": 3},
    {"id": "theta-fuel",             "sym": "TFUEL",  "tier": 3},
    {"id": "wax",                    "sym": "WAXP",   "tier": 3},
    {"id": "ultra",                  "sym": "UOS",    "tier": 3},
    {"id": "myneighboralice",        "sym": "ALICE",  "tier": 3},
    {"id": "vulcan-forged",          "sym": "PYR",    "tier": 3},
    {"id": "astar",                  "sym": "ASTR",   "tier": 3},
    {"id": "moonbeam",               "sym": "GLMR",   "tier": 3},
    {"id": "moonriver",              "sym": "MOVR",   "tier": 3},
    {"id": "acala",                  "sym": "ACA",    "tier": 3},
    {"id": "bifrost-native-coin",    "sym": "BNC",    "tier": 3},
    {"id": "subsocial",              "sym": "SUB",    "tier": 3},
    {"id": "phala",                  "sym": "PHA",    "tier": 3},
    {"id": "reef",                   "sym": "REEF",   "tier": 3},
    {"id": "concordium",             "sym": "CCD",    "tier": 3},
    {"id": "cudos",                  "sym": "CUDOS",  "tier": 3},
    {"id": "medibloc",               "sym": "MED",    "tier": 3},
    {"id": "holotoken",              "sym": "HOT",    "tier": 3},
    {"id": "basic-attention-token",  "sym": "BAT",    "tier": 3},
    {"id": "livepeer",               "sym": "LPT",    "tier": 3},
    {"id": "audius",                 "sym": "AUDIO",  "tier": 3},
    {"id": "civic",                  "sym": "CVC",    "tier": 3},
    {"id": "requestnetwork",         "sym": "REQ",    "tier": 3},
    {"id": "gitcoin",                "sym": "GTC",    "tier": 3},
    {"id": "radicle",                "sym": "RAD",    "tier": 3},
    {"id": "power-ledger",           "sym": "POWR",   "tier": 3},
    {"id": "woo-network",            "sym": "WOO",    "tier": 3},
    {"id": "truebit-protocol",       "sym": "TRU",    "tier": 3},
    {"id": "lisk",                   "sym": "LSK",    "tier": 3},
    {"id": "waves",                  "sym": "WAVES",  "tier": 3},
    {"id": "siacoin",                "sym": "SC",     "tier": 3},
    {"id": "digibyte",               "sym": "DGB",    "tier": 3},
    {"id": "vertcoin",               "sym": "VTC",    "tier": 3},
    {"id": "groestlcoin",            "sym": "GRS",    "tier": 3},
    {"id": "syscoin",                "sym": "SYS",    "tier": 3},
    {"id": "komodo",                 "sym": "KMD",    "tier": 3},
    {"id": "stratis",                "sym": "STRAX",  "tier": 3},
    {"id": "metahero",               "sym": "HERO",   "tier": 3},
    {"id": "xyo-network",            "sym": "XYO",    "tier": 3},
    {"id": "measurable-data-token",  "sym": "MDT",    "tier": 3},
    {"id": "self-key",               "sym": "KEY",    "tier": 3},
    {"id": "wrapped-bitcoin",        "sym": "WBTC",   "tier": 3},
    {"id": "kadena",                 "sym": "KDA",    "tier": 3},
    {"id": "secret",                 "sym": "SCRT",   "tier": 3},
    {"id": "stacks",                 "sym": "STX",    "tier": 3},
    {"id": "aleph-zero",             "sym": "AZERO",  "tier": 3},
]

# Remove duplicates by sym
seen = set()
UNIQUE_WATCHLIST = []
for c in HALAL_WATCHLIST:
    if c["sym"] not in seen:
        seen.add(c["sym"])
        UNIQUE_WATCHLIST.append(c)
HALAL_WATCHLIST = UNIQUE_WATCHLIST

# Track sent signals — 4hr cooldown per coin
sent_signals = {}
scan_count = 0

# ── TELEGRAM ──────────────────────────────────────────────────
def send_msg(msg):
    try:
        requests.post(f"{TG_BASE}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print(f"  Telegram error: {e}")

# ── COINGECKO DATA ────────────────────────────────────────────
def get_data(coin_id, days=365):
    try:
        r = requests.get(
            f"{CG_BASE}/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": days, "interval": "daily"},
            headers={"x-cg-demo-api-key": CG_API_KEY},
            timeout=15
        )
        d = r.json()
        prices = [p[1] for p in d.get("prices", [])]
        vols   = [v[1] for v in d.get("total_volumes", [])]
        return prices, vols
    except:
        return [], []

def get_info(coin_id):
    try:
        r = requests.get(
            f"{CG_BASE}/coins/{coin_id}",
            params={"localization":"false","tickers":"false",
                    "community_data":"false","developer_data":"false"},
            headers={"x-cg-demo-api-key": CG_API_KEY},
            timeout=15
        )
        return r.json()
    except:
        return {}

# ── RSI ───────────────────────────────────────────────────────
def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return None
    gains = losses = 0
    for i in range(1, period + 1):
        d = prices[i] - prices[i-1]
        if d > 0: gains += d
        else:     losses += abs(d)
    ag, al = gains/period, losses/period
    for i in range(period, len(prices)):
        d = prices[i] - prices[i-1]
        ag = (ag*(period-1) + (d if d>0 else 0)) / period
        al = (al*(period-1) + (abs(d) if d<0 else 0)) / period
    return 100 if al == 0 else 100 - (100/(1+ag/al))

# ── EMA + MACD ────────────────────────────────────────────────
def ema(prices, period):
    if len(prices) < period: return []
    k = 2/(period+1)
    r = [sum(prices[:period])/period]
    for p in prices[period:]:
        r.append(p*k + r[-1]*(1-k))
    return r

def calc_macd(prices):
    if len(prices) < 35: return None,None,None,None
    ef = ema(prices, 12)
    es = ema(prices, 26)
    off = 26-12
    ml = [ef[i+off]-es[i] for i in range(len(es))]
    if len(ml) < 9: return None,None,None,None
    sl = ema(ml, 9)
    diff = len(ml)-len(sl)
    hist = [ml[i+diff]-sl[i] for i in range(len(sl))]
    if len(hist) < 2: return None,None,None,None
    return ml[-1], sl[-1], hist[-1], hist[-2]

# ── WAVE DETECTION ────────────────────────────────────────────
def detect_waves(prices):
    if len(prices) < 20: return []
    n = len(prices)
    win = max(3, n//20)
    pivots = []
    for i in range(win, n-win):
        sl = prices[i-win:i+win+1]
        mx, mn = max(sl), min(sl)
        if prices[i]==mx and prices[i]>prices[i-1] and prices[i]>prices[i+1]:
            pivots.append({"idx":i,"price":prices[i],"type":"peak"})
        elif prices[i]==mn and prices[i]<prices[i-1] and prices[i]<prices[i+1]:
            pivots.append({"idx":i,"price":prices[i],"type":"trough"})
    ftype = "trough" if prices[0]<prices[n//4] else "peak"
    pivots.insert(0,{"idx":0,"price":prices[0],"type":ftype})
    pivots.append({"idx":n-1,"price":prices[-1],"type":"current"})
    sig = [pivots[0]]
    for i in range(1,len(pivots)):
        prev,curr = sig[-1],pivots[i]
        if prev["type"]==curr["type"]:
            if curr["type"]=="peak" and curr["price"]>prev["price"]: sig[-1]=curr
            elif curr["type"]=="trough" and curr["price"]<prev["price"]: sig[-1]=curr
            continue
        if abs((curr["price"]-prev["price"])/prev["price"])>0.10:
            sig.append(curr)
    return sig

# ── EW VALIDATION ─────────────────────────────────────────────
def validate_ew(pivots):
    issues = []
    if len(pivots)<3: return False,["Not enough data"]
    if len(pivots)>=3:
        w1s,w1e,w2e = pivots[0]["price"],pivots[1]["price"],pivots[2]["price"]
        w1r = abs(w1e-w1s)
        if w1r==0: return False,["Invalid W1"]
        w2ret = abs(w2e-w1e)/w1r*100
        if w2e<w1s: issues.append("W2>100% W1")
        elif w2ret<38: issues.append(f"W2 shallow({w2ret:.0f}%)")
    if len(pivots)>=4:
        w1sz = abs(pivots[1]["price"]-pivots[0]["price"])
        w3sz = abs(pivots[3]["price"]-pivots[2]["price"])
        if w3sz<w1sz: issues.append("W3<W1")
    if len(pivots)>=5:
        if pivots[4]["price"]<pivots[1]["price"]: issues.append("W4 overlaps W1")
    return len(issues)==0, issues

# ── SIGNAL CHECK ──────────────────────────────────────────────
def check_signal(coin):
    prices, vols = get_data(coin["id"])
    if len(prices)<50: return None
    info = get_info(coin["id"])
    ath = info.get("market_data",{}).get("ath",{}).get("usd", max(prices))
    current = prices[-1]
    pct_ath = ((current-ath)/ath)*100

    rsi_val = calc_rsi(prices)
    if rsi_val is None: return None

    m_val,s_val,h_curr,h_prev = calc_macd(prices)
    if m_val is None: return None

    macd_cross   = h_curr>0 and h_prev<=0
    macd_turning = h_curr>h_prev

    waves = detect_waves(prices)
    ew_ok,ew_issues = validate_ew(waves)

    entry_type = ""
    w2_ret = 0
    if len(waves)>=3:
        w1r = abs(waves[1]["price"]-waves[0]["price"])
        if w1r>0:
            w2r = abs(waves[2]["price"]-waves[1]["price"])
            w2_ret = (w2r/w1r)*100
            if 38<=w2_ret<=100: entry_type="W2"
    if len(waves)>=5:
        w3r = abs(waves[3]["price"]-waves[2]["price"])
        if w3r>0:
            w4r = abs(waves[4]["price"]-waves[3]["price"])
            w4ret = (w4r/w3r)*100
            if 23<=w4ret<=38 and waves[4]["price"]>waves[1]["price"]:
                entry_type="W4"

    checks = {
        "wave_count":  len(waves)>=5,
        "abc_correct": len(waves)>=6,
        "entry_zone":  entry_type!="",
        "price_level": pct_ath<-50,
        "rsi_ok":      rsi_val<45,
        "macd_ok":     macd_cross or macd_turning,
    }
    score = sum(checks.values())

    if score<4: return None
    if pct_ath>-25: return None
    if not (checks["rsi_ok"] or checks["macd_ok"]): return None

    sl      = current*0.87
    hard_sl = current*0.79
    tp1     = current*1.30
    tp2     = current*1.80
    tp3     = current*2.60
    tp4     = ath*1.05

    if score==6:   conf="🔥 HIGH — Full position"
    elif score==5: conf="⚡ MEDIUM-HIGH — 75% position"
    else:          conf="✳️ MEDIUM — 50% position"

    return {
        "sym":coin["sym"], "tier":coin["tier"],
        "price":current, "ath":ath, "pct_ath":pct_ath,
        "rsi":rsi_val, "macd_cross":macd_cross,
        "macd_turning":macd_turning, "entry_type":entry_type,
        "w2_ret":w2_ret, "score":score, "conf":conf,
        "sl":sl, "hard_sl":hard_sl,
        "tp1":tp1, "tp2":tp2, "tp3":tp3, "tp4":tp4,
        "checks":checks, "ew_ok":ew_ok, "ew_issues":ew_issues,
    }

# ── FORMAT ────────────────────────────────────────────────────
def fp(p):
    if p>=1000:  return f"${p:,.0f}"
    if p>=1:     return f"${p:.4f}"
    if p>=0.01:  return f"${p:.5f}"
    return f"${p:.7f}"

def fpc(p):
    return f"+{p:.1f}%" if p>=0 else f"{p:.1f}%"

# ── BUILD MESSAGE ─────────────────────────────────────────────
def build_msg(sig):
    c = sig["checks"]
    entry = sig["entry_type"] or "Correction"
    tp1p = ((sig["tp1"]-sig["price"])/sig["price"])*100
    tp2p = ((sig["tp2"]-sig["price"])/sig["price"])*100
    tp3p = ((sig["tp3"]-sig["price"])/sig["price"])*100
    slp  = ((sig["sl"] -sig["price"])/sig["price"])*100
    rr1  = abs(tp1p/slp) if slp!=0 else 0
    rr2  = abs(tp2p/slp) if slp!=0 else 0
    ew   = "✅ EW Rules Valid" if sig["ew_ok"] else f"⚠️ {', '.join(sig['ew_issues'])}"
    stars= "⭐"*sig["tier"]

    cl = (
        f"{'✅' if c['wave_count']  else '❌'} 5-Wave Impulse Complete\n"
        f"{'✅' if c['abc_correct'] else '❌'} ABC Correction Identified\n"
        f"{'✅' if c['entry_zone']  else '❌'} {entry} Zone ({sig['w2_ret']:.0f}% retrace)\n"
        f"{'✅' if c['price_level'] else '❌'} Price 50%+ Below ATH\n"
        f"{'✅' if c['rsi_ok']      else '❌'} RSI Oversold ({sig['rsi']:.1f})\n"
        f"{'✅' if c['macd_ok']     else '❌'} MACD {'Crossed' if sig['macd_cross'] else 'Turning'} Bullish"
    )
    return (
        f"🕌 <b>HALAL SIGNAL — {sig['sym']}/USDT</b> {stars}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Shariah Compliant | Spot Only\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>{entry} Bottom Detected</b>\n"
        f"📊 Score: <b>{sig['score']}/6</b> — {sig['conf']}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Price: {fp(sig['price'])}\n"
        f"🏆 ATH: {fp(sig['ath'])}\n"
        f"📉 From ATH: {fpc(sig['pct_ath'])}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>Entry:</b> {fp(sig['price']*0.97)} – {fp(sig['price']*1.02)}\n"
        f"🔴 <b>Stop Loss:</b> {fp(sig['sl'])} ({fpc(slp)})\n"
        f"🔴 <b>Hard SL:</b> {fp(sig['hard_sl'])}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 TP1: {fp(sig['tp1'])} (+{tp1p:.1f}%) — Exit 25%\n"
        f"🎯 TP2: {fp(sig['tp2'])} (+{tp2p:.1f}%) — Exit 25%\n"
        f"🎯 TP3: {fp(sig['tp3'])} (+{tp3p:.1f}%) — Trail\n"
        f"🎯 TP4: {fp(sig['tp4'])} — ATH Target\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📐 R:R — 1:{rr1:.1f} (TP1) | 1:{rr2:.1f} (TP2)\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"CHECKLIST:\n{cl}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{ew}\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <i>Spot only. Not financial advice.</i>\n"
        f"<i>Consult a scholar for personal rulings.</i>"
    )

# ── MAIN LOOP ─────────────────────────────────────────────────
def main():
    global scan_count
    total = len(HALAL_WATCHLIST)
    syms  = ", ".join([c["sym"] for c in HALAL_WATCHLIST])
    t1    = [c["sym"] for c in HALAL_WATCHLIST if c["tier"]==1]
    t2    = [c["sym"] for c in HALAL_WATCHLIST if c["tier"]==2]
    t3    = [c["sym"] for c in HALAL_WATCHLIST if c["tier"]==3]

    print(f"🕌 SIGNALSYM Halal Bot Starting...")
    print(f"📊 Watching {total} halal coins\n")

    send_msg(
        f"🕌 <b>SIGNALSYM Halal Bot Active</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Shariah-Compliant Coins Only\n"
        f"📊 {total} coins monitored\n"
        f"🚫 Riba, memecoins & gambling excluded\n"
        f"⏱ Scanning every 15 minutes\n"
        f"💰 Spot trading only — no leverage\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⭐⭐⭐ Tier 1 ({len(t1)}): {', '.join(t1)}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⭐⭐ Tier 2 ({len(t2)}): {', '.join(t2)}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Tier 3 ({len(t3)}): {', '.join(t3)}\n"
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
                sig = check_signal(coin)
                if sig:
                    last = sent_signals.get(sym, 0)
                    if time.time()-last < 14400:
                        print("cooldown")
                        time.sleep(3)
                        continue
                    print(f"🔥 {sig['score']}/6")
                    send_msg(build_msg(sig))
                    sent_signals[sym] = time.time()
                    signals_found += 1
                    time.sleep(3)
                else:
                    print("–")
                time.sleep(4)
            except Exception as e:
                print(f"err: {e}")
                time.sleep(5)

        print(f"\n  ✅ Scan #{scan_count} done. {signals_found} signal(s). Next in 15min...")

        if scan_count % 96 == 0:
            send_msg(
                f"💓 <b>Bot Heartbeat</b>\n"
                f"Scans: {scan_count}\n"
                f"Coins watched: {total}\n"
                f"Signals sent: {len(sent_signals)}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
                f"الحمد لله 🤲"
            )

        time.sleep(900)

if __name__ == "__main__":
    main()
