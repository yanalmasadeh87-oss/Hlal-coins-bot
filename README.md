# Hlal-coins-bot
Hlal only
# EW Strategy V6 - Halal Crypto Trading Bot

Adaptive structure-aware trading bot for halal cryptocurrency pairs. Analyzes each chart based on its own price behavior and Elliott Wave structure, not fixed rules.

## Features

- **Adaptive Analysis** - Chart decides the method (EW, patterns, trend)
- **Hard Score Ceilings** - Trend signals capped at 55, EW structures up to 100
- **WATCH-Only Trend** - Trend continuation requires 3xHH/HL, ADX>30, HTF bullish
- **No EW/Fib Bonus for Trend** - Reserved for real EW structures only
- **Hard Market Filters** - BTC.D, TOTAL, TOTAL3, Fear & Greed as BLOCKS not score adjustments
- **Volatility Regime Detection** - Adjusts pivots and risk per market conditions
- **Structure Memory** - Anti flip-flop, locks valid structures for 30 days
- **HTF Weekly Validation** - Blocks signals against weekly trend
- **Position Sizing** - By score, volatility, and trend strength
- **Telegram Alerts** - Real-time signals, watches, TP/SL hits
- **JSON Export** - Auto-saves signals.json for dashboard every scan cycle
- **70-Coin Watchlist** - Tier 1-3 halal coins

## Scoring Table (Hard Ceilings)

| Structure | Max Score | EW Bonus | Fib Bonus | Notes |
|-----------|-----------|----------|-----------|-------|
| TREND_CONTINUATION | 55 | 0 | 0 | Trend only, NO EW/Fib |
| IMPULSE_W3_LIKELY | 55 | 0 | 0 | WATCH only, 3xHH/HL, ADX>30 |
| EARLY_TREND | 50 | 0 | 0 | WATCH only, weakest signal |
| EW_W2 / EW_W4 | 100 | 25 | 15 | Full EW validation |
| ABC_ZIGZAG | 100 | 25 | 15 | Full EW validation |
| WXYXZ | 95 | 20 | 12 | Complex but validated |
| EXPANDED_FLAT | 90 | 18 | 10 | Validated correction |
| RUNNING_CORRECTION | 85 | 15 | 8 | Validated correction |
| DOUBLE_BOTTOM | 80 | 12 | 8 | Pattern only |
| FALLING_WEDGE | 75 | 10 | 5 | Pattern only |

## Hard Market Filters (NEW)

These BLOCK signals entirely, not just reduce score:

| Condition | Action | Affected Coins |
|-----------|--------|---------------|
| Fear & Greed <= 20 (Extreme Fear) | **BLOCK everything** | All coins - WATCH only |
| Total market cap FALLING | **BLOCK altcoins** | Altcoins only, BTC/ETH allowed |
| BTC.D > 55% and RISING | **BLOCK altcoins** | Alt bloodbath - BTC dominance crushing |
| TOTAL3 falling + BTC.D rising | **BLOCK everything except BTC** | Only BTC survives |
| Fear zone 21-40 | Allow with warning | Reduced position recommended |

## Setup

### 1. Environment Variables

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python signal_bot.py
```

### 4. Dashboard (Optional)

Upload `signals.json` (auto-exported every scan) to the HTML dashboard at `ew-app` repo, or open `index.html` locally and drag the JSON file.

## File Structure

```
Hal-coin/
├── signal_bot.py      # Main bot (V6 with hard filters)
├── requirements.txt   # Dependencies
└── README.md          # This file

ey-app/
├── index.html         # V6 dashboard with market bar
└── README.md          # Dashboard docs
```

## JSON Export Format

Every signal includes market context:

```json
{
  "sym": "BTC",
  "score": 88,
  "struct_type": "EW_W4",
  "market_ctx": {
    "btc_dom": 52.5,
    "total_trend": "RISING",
    "total3_trend": "RISING",
    "fg_now": 65,
    "fg_zone": "GREED"
  }
}
```

## Security

- Bot token loaded from `os.getenv()` - never hardcoded
- Regenerate token if previously exposed
- No private keys or API secrets in code

## Disclaimer

This is for educational purposes only. Not financial advice. Trade at your own risk.
