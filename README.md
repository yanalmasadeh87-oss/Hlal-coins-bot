# Hal-coins-bot

**Halal-only** Elliott Wave trading strategy bot — V7 Adaptive Structure-Aware.

## Overview

This bot scans 60+ halal-compliant cryptocurrencies across Binance, detecting Elliott Wave structures and market patterns to generate swing and scalp trading signals sent via Telegram.

## V7 Features

### 6 New Engines
- **Multi-Degree Elliott** — Weekly + Monthly degree validation for nested structure alignment
- **Liquidity BOS/CHoCH** — SMC-style break of structure / change of character detection
- **Full MTF Alignment** — 1D → 4H → 1H trend alignment (lazy-loaded only for coins passing filters)
- **Triangle Engine** — Contracting/Expanding triangle (ABCDE) detection
- **Extended Wave Detection** — W3/W5 extended wave identification with TP multipliers
- **Candlestick Engine** — Pattern confirmation (hammer, engulfing, morning star, etc.)

### Performance Optimizations
- **Lazy-loading**: 1H MTF data only fetched for coins that pass structure detection + hard filters
- **Hard filters first**: Market context, HTF validation, and multi-degree checks run BEFORE expensive API calls
- **Dashboard API**: Built-in HTTP server (`:8080`) serves real-time bot data

### Signal Types
| Type | Timeframe | Hold | Min Score |
|------|-----------|------|-----------|
| Swing | 1D | Days to weeks | 50 |
| Scalp | 4H | 1-3 days | 45 |

### Risk Management
- Adaptive SL/TP based on structure type and volatility regime
- Position sizing: 10-100% based on confidence score
- 4 take-profit levels with trailing SL updates
- Structure memory (anti flip-flop)

## Setup

### Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run
```bash
python signal_bot.py
```

### Dashboard
The bot runs an API server on `http://localhost:8080`:
- `GET /api/status` — Bot status, market context, engine data
- `GET /api/signals` — Active signals, watches, stats

## API Response Format

```json
{
  "version": "V7",
  "scan_count": 42,
  "timestamp": "2026-05-31T12:00:00",
  "market_ctx": { "btc_dom": 52.3, "fg_now": 45, ... },
  "active_signals": 3,
  "active_trades": [...],
  "watch_list": ["BTC_watch_swing", ...],
  "engine_data": {
    "multi_degree": "Weekly+Monthly validation active",
    "liquidity": "BOS/CHoCH detection active",
    "mtf": "1D->4H->1H alignment active (lazy-loaded)",
    "triangle": "ABCDE detection active",
    "extended_wave": "W3/W5 extended detection active",
    "candlestick": "Pattern confirmation active"
  }
}
```

## Signal Message Format (V6 Clean)

```
[SWING] SWING - BTC/USDT

Structure: Standard EW - W2 Entry
Trend: UPTREND | Phase: CORRECTING
Position: 75% Position

Entry:  $95,000.00 - $97,000.00
SL:     $92,000.00
   (Below W0 Origin (W2 rule))

TP1:   $100,000.00
TP2:   $105,000.00
TP3:   $110,000.00
TP4:   $120,000.00

Hold: Days to weeks
Score: 78/100 - MEDIUM-HIGH
RSI: 42 | Stoch: 35
Regime: Normal Volatility
Bullish Divergence detected
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Binance API    │────▶│  Structure      │────▶│  Hard Filters   │
│  (1D/4H/1W)     │     │  Detection      │     │  (Market/HTF)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Multi-Degree   │
                                               │  Validation     │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Lazy 1H MTF    │
                                               │  (if passed)    │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Re-score +     │
                                               │  Risk Calc      │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Telegram       │
                                               │  Signal         │
                                               └─────────────────┘
```

## License
MIT
