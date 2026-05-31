# EW Strategy V7 - Adaptive Structure-Aware Trading Bot

A sophisticated cryptocurrency trading signal generator that analyzes each chart based on its own structure and price behavior rather than applying fixed rules. Features 6 new analysis engines in V7 for multi-timeframe, multi-degree Elliott Wave validation with Smart Money Concepts integration.

## Features

### Core V6 Features
- **Adaptive Structure Recognition** - Chart decides the analysis method
- **Volatility Regime Detection** - Adjusts pivot detection and risk dynamically
- **Trend Continuation Detection** - Identifies W3/parabolic moves
- **Structure Memory** - Anti flip-flop protection with locked structures
- **HTF Weekly Validation** - Blocks signals against weekly bearish trends
- **Hard Market Filters** - Extreme fear, BTC dominance, TOTAL3 analysis
- **Position Sizing** - Score and volatility-based sizing
- **Telegram Integration** - Real-time signal delivery
- **Price Alerts** - TP/SL monitoring with auto-updates

### V7 New Engines (6 New Features)

#### 1. Multi-Degree Elliott Wave Validation
Validates signals against **weekly AND monthly** degree wave structures.
- Ensures daily patterns align with higher-degree W1/W3/W5 impulses
- Monthly bullish adds +10 bonus, monthly bearish adds -5 penalty
- Prevents trading W2/W4 corrections against major monthly trends

#### 2. Liquidity Engine (BOS/CHoCH)
Smart Money Concepts integration:
- **Break of Structure (BOS)** - Price breaks above/below previous swing high/low
- **Change of Character (CHoCH)** - Higher low after lower low sequence (bullish reversal)
- Detects liquidity pools at swing highs/lows
- Adds +5 score for bullish CHoCH, +3 for bullish BOS

#### 3. Full MTF Alignment (1D → 4H → 1H)
Checks trend alignment across three timeframes:
- Full bullish alignment (all three): +15 score bonus
- Partial alignment (2/3): +8 bonus
- Bearish alignment (2+ bearish): -10 penalty, may block signal
- 1D trend supportive adds additional +5

#### 4. Triangle Engine
Detects contracting triangle patterns (ABCDE):
- Identifies lower highs + higher lows convergence
- Calculates apex (convergence point)
- Entry at wave E or post-breakout
- Target = height of triangle projected from breakout
- Score: 65 (contracting), 40 (expanding - avoid)

#### 5. Extended Wave Detection
Identifies extended impulse waves (W3 or W5 that are 1.618x+ longer than W1):
- Dramatically adjusts TP calculations (1.618x or 2.0x multiplier)
- W3 Extended: TP multiplier = 1.618x
- W5 Extended: TP multiplier = 2.0x
- W1=W5 Equality: Normal TP calculations

#### 6. Candlestick Engine
Pattern recognition for confirmation:
- **Hammer** - Bullish reversal at support (+3)
- **Bullish Engulfing** - Strong reversal signal (+4)
- **Morning Star** - 3-candle reversal (+5)
- **Doji** - Indecision, context-dependent (+1)
- Max candlestick bonus: 5 points (capped to prevent over-weighting)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA FETCH LAYER                          │
│  Binance API (1D, 4H, 1H, 1W klines + opens for candles)    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   ANALYSIS PIPELINE                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ 1D Analysis │  │ 4H Analysis │  │ 1H Analysis │           │
│  │ (Swing)     │  │ (Scalp)     │  │ (MTF Align)│           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              V7 ENGINE LAYER (Parallel)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Multi-Deg │ │Liquidity │ │  MTF     │ │ Triangle │       │
│  │Elliott   │ │BOS/CHoCH │ │Alignment │ │ Engine   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐                                  │
│  │ Extended │ │ Candle-  │                                  │
│  │ Wave     │ │ stick    │                                  │
│  └──────────┘ └──────────┘                                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              SCORING ENGINE V7                                 │
│  Base + EW + Fib + Vol + Mom + Trend + Candle +               │
│  Liquidity + MTF + Extended = Final Score (capped by type)    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              FILTERS & VALIDATION                              │
│  Hard Market → HTF Weekly → Multi-Degree → MTF Alignment      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              OUTPUT: Signal / Watch / Block                   │
│  Telegram alerts + JSON export + Dashboard                    │
└─────────────────────────────────────────────────────────────┘
```

## Scoring System V7

| Structure | Max Score | EW | Fib | Candle | BOS/CHoCH | MTF | Extended |
|-----------|-----------|-----|-----|--------|-----------|-----|----------|
| EW_W2/W4 | 100 | 25 | 15 | 3 | 5 | 10 | 5 |
| ABC_ZIGZAG | 100 | 25 | 15 | 3 | 5 | 10 | 5 |
| WXYXZ | 95 | 20 | 12 | 3 | 5 | 8 | 5 |
| EXPANDED_FLAT | 90 | 18 | 10 | 3 | 5 | 8 | 5 |
| CONTRACTING_TRIANGLE | 85 | 15 | 10 | 3 | 5 | 10 | 5 |
| RUNNING_CORRECTION | 85 | 15 | 8 | 3 | 5 | 8 | 5 |
| DOUBLE_BOTTOM | 80 | 12 | 8 | 5 | 5 | 8 | 0 |
| FALLING_WEDGE | 75 | 10 | 5 | 3 | 5 | 8 | 0 |
| TREND_CONTINUATION | 55 | 0 | 0 | 0 | 0 | 0 | 0 |
| EARLY_TREND | 50 | 0 | 0 | 0 | 0 | 0 | 0 |

## Setup

### Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### Requirements
```bash
pip install requests
```

### Run
```bash
python bot.py
```

### Dashboard
Open `index.html` in any modern browser. Connects to `/api/status` endpoint for live data.

## Configuration

### Watchlist Tiers
- **Tier 1** (28 coins): BTC, ETH, XRP, SOL, BNB, ADA, AVAX, SUI, HBAR, NEAR, DOT, ICP, FTM, ETC, WLD, RENDER, ATOM, KAS, FIL, APT, ARB, VET, SEI, STX, TIA, GRT, OP, THETA
- **Tier 2** (35 coins): XLM, ALGO, LTC, TON, LINK, POL, XTZ, IOTA, BCH, IMX, INJ, FET, OCEAN, AKT, AR, HNT, ONE, ZIL, QTUM, DCR, RVN, EGLD, FLOW, ANKR, STORJ, BAND, NMR, GLM, SKL, CELO, ROSE, CTSI, WAVES, DGB
- **Tier 3** (13 coins): GALA, AXS, SAND, MANA, ENJ, CHZ, ASTR, BAT, LPT, AUDIO, CVC, POWR, HOT

### Signal Types
- **SWING**: 1D timeframe, 730 candles, min score 50, hold days-weeks
- **SCALP**: 4H timeframe, 540 candles, min score 45, hold 1-3 days

## Risk Management

### Stop Loss Rules
- **EW_W2**: Below W0 Origin
- **EW_W4**: Below W1 Top (overlap rule)
- **ABC/Flat/Running**: Below Wave A Bottom
- **Trend Continuation**: Below last significant trough
- **Triangle**: Below triangle support
- **WXYXZ**: Below Z-wave bottom

### Take Profit Rules (V7: Extended wave multiplier applied)
- TP1: 1.5x risk (or 0.5x triangle height)
- TP2: 2.5x risk (or 1.0x triangle height)
- TP3: 4.0x risk (or 1.618x triangle height)
- TP4: 6.0x risk (or 2.618x triangle height)
- Extended waves: All TPs multiplied by 1.618x or 2.0x

### Position Sizing
| Score | Base Size | High Vol | Low Vol | Strong Uptrend | Downtrend |
|-------|-----------|----------|---------|------------------|-----------|
| 85+ | 100% | 70% | 110% | 115% | 50% |
| 75-84 | 75% | 52% | 82% | 86% | 37% |
| 65-74 | 50% | 35% | 55% | 57% | 25% |
| 55-64 | 25% | 17% | 27% | 28% | 12% |
| <55 | 10% | 7% | 11% | 11% | 5% |

## Market Filters

1. **Extreme Fear (FG ≤20)**: BLOCK all entries
2. **Total Market Falling**: BLOCK all altcoins
3. **BTC.D >55% Rising**: BLOCK all altcoins
4. **TOTAL3 Falling + BTC.D Rising**: BLOCK everything except BTC
5. **Fear Zone (FG 21-40)**: Reduce position, allow with warning

## Telegram Output Format

```
📈 SWING - BTC/USDT

📊 Structure: Standard EW - W2 Entry
📈 Trend: UPTREND | Phase: CORRECTING
📏 Position: 75% Position

💵 Entry:  $67,200 - $68,800
🛑 SL:     $64,500
   (Below W0 Origin (W2 rule))

🎯 TP1:   $72,000
🎯 TP2:   $78,500
🎯 TP3:   $85,000
🎯 TP4:   $92,000

⏱ Hold: Days to weeks
⚡ Score: 92/100 - HIGH
📊 RSI: 38 | Stoch: 22
🌊 Regime: Normal Volatility
📐 Extended: Extended W3 (1.82x W1)
🔄 MTF: 1D=bullish 4H=bullish 1H=bullish
🕯 Patterns: HAMMER, BULL_ENGULFING
💧 CHoCH: Bullish change of character
🌐 Monthly+Weekly Bullish | Daily EW_W2 aligned
🔄 Bullish Divergence detected
```

## API Endpoints (for Dashboard)

```
GET /api/status
{
  "market_status": "FEAR",
  "btc_dom": 52.4,
  "fg_now": 38,
  "fg_zone": "FEAR",
  "active_signals": 2,
  "active_trades": [...],
  "watch_list": [...],
  "scan_count": 1247
}
```

## Changelog

### V7 (Current)
- Added 6 new analysis engines
- Multi-Degree Elliott (weekly + monthly)
- Liquidity BOS/CHoCH (SMC)
- Full MTF Alignment (1D→4H→1H)
- Triangle Engine (ABCDE patterns)
- Extended Wave Detection (1.618x+ W1)
- Candlestick Engine (confirmation patterns)
- Enhanced scoring with 4 new bonus categories
- Extended wave TP multipliers

### V6
- Adaptive structure recognition
- Volatility regime detection
- Trend continuation
- Structure memory locks
- HTF weekly validation
- Hard market filters

### V5
- Base Elliott Wave engine
- Classical patterns (double bottom, falling wedge)
- WXYXZ detection
- ABC zigzag
- Expanded flat / running correction

## Disclaimer

This bot generates trading signals based on technical analysis. It is NOT financial advice. Always do your own research and never risk more than you can afford to lose. Cryptocurrency trading carries significant risk.

## License

MIT License - Use at your own risk.
