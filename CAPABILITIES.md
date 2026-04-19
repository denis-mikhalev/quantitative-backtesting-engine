# Quantitative Backtesting Engine — Capabilities

A rule-based statistical trading system for digital asset markets built on top of **Binance public OHLCV data** (via [ccxt](https://github.com/ccxt/ccxt)). No machine learning, no black-box — every decision is explainable and reproducible.

---

## Table of Contents

1. [Signal Generation](#1-signal-generation)
2. [Signal Filters](#2-signal-filters)
3. [Signal Ranking](#3-signal-ranking)
4. [Multi-Asset Scanner](#4-multi-asset-scanner)
5. [Backtesting Engine](#5-backtesting-engine)
6. [Parameter Sweep](#6-parameter-sweep)
7. [Risk & Edge Metrics](#7-risk--edge-metrics)
8. [Launch Profiles](#8-launch-profiles)
9. [Notifications](#9-notifications)
10. [CLI Reference](#10-cli-reference)
11. [Backtested Results](#11-backtested-results)

---

## 1. Signal Generation

The core engine implements **4 independent setup detectors**. Each candle is evaluated by all active setups; the final signal direction is determined by majority vote.

| Setup | Logic |
|---|---|
| **Breakout** | Price closes above BB upper / below BB lower with a volume spike (≥ 1.5× 20-period average) and a confirmed directional candle |
| **Pullback** | EMA-50 / EMA-200 trend confirmed; RSI has pulled back below `rsi_oversold` (long) or above `rsi_overbought` (short) |
| **Mean Reversion** | Price at or beyond BB±2σ boundary; RSI at extremes (≤ 30 or ≥ 70); fades overextended moves |
| **Volatility Expansion** | ATR in the bottom 20th percentile (BB squeeze); catches the initial expansion burst |

**Confidence score** = votes in winning direction ÷ total active setup votes (0–1 scale).

**Indicators computed on-the-fly:**

- RSI-14
- EMA-fast (default 50) and EMA-slow (default 200)
- Bollinger Bands (period 20, 2σ)
- ATR-14 + rolling ATR percentile (100-period)
- Volume / 20-period volume MA ratio
- ADX-14 (optional, computed only when the filter is enabled)

**Entry / Exit levels** are set automatically from ATR at signal time:
- Stop Loss: `entry ± 1.0 × ATR`
- Take Profit: `entry ± 2.0 × ATR` (configurable multipliers)

---

## 2. Signal Filters

Filters are applied after setup voting and can be combined freely.

| Filter | Parameter | Description |
|---|---|---|
| **Minimum confidence** | `--min-confidence` | Minimum vote ratio to emit a signal (default 0.5 = 2/4 setups) |
| **EMA trend filter** | `--trend-filter` / `--no-trend-filter` | Only trade in the direction of the EMA-fast vs EMA-slow trend |
| **ADX strength filter** | `--require-adx`, `--adx-min`, `--adx-period` | Require ADX ≥ threshold before accepting a trend-aligned signal |
| **Setup selection** | `enabled_setups` in config | Enable/disable individual setups per preset |

---

## 3. Signal Ranking

`SignalRanker` scores every signal on a **composite 0–1 scale** and returns the sorted list:

| Criterion | Default Weight |
|---|---|
| Confidence (vote ratio) | **40%** |
| Risk / Reward ratio | **30%** |
| Number of active setups (1–4) | **20%** |
| Asset quality (volume / liquidity) | **10%** |

Weights are fully configurable at instantiation time.  
`rank_with_scores()` returns raw `(signal, score)` tuples for downstream analysis.

---

## 4. Multi-Asset Scanner

Scans a configurable watchlist and surfaces the best entries across the entire market in one pass.

**Default watchlist — 20 major pairs:**
`BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `SOLUSDT`, `XRPUSDT`, `ADAUSDT`, `DOGEUSDT`, `DOTUSDT`, `LINKUSDT`, `LTCUSDT`, `NEARUSDT`, `UNIUSDT`, `ATOMUSDT`, `AVAXUSDT`, `OPUSDT`, `ARBUSDT`, `SUIUSDT`, `APTUSDT`, `AAVEUSDT`, `INJUSDT`

**Extended watchlist (via `LaunchStatisticalSystem.py`) — 50+ pairs** including `ORDIUSDT`, `PEPEUSDT`, `WIFUSDT`, `HYPEUSDT`, `TAOUSDT`, `XMRUSDT`, and more.

**Operating modes:**

| Mode | Command | Description |
|---|---|---|
| **Single scan** | `--mode scan` | One-shot scan; prints ranked signals and exits |
| **Continuous scan** | `--mode continuous` | Repeats automatically on a configurable interval |

**Configurable scan parameters:**

| Parameter | Default | Description |
|---|---|---|
| `--timeframe` | `30m` | Candle timeframe: `15m`, `30m`, `1h`, `4h`, `12h`, `1d` |
| `--symbols` | (from config) | Override watchlist inline |
| `--max-signals` | `10` | Max signals to display |
| `--interval` | `1800` s | Re-scan interval in continuous mode |

**Output:** ranked signal table printed to console + optional JSON export to `statistical_system/results/`.  
**Sound alert** (Windows): distinctive two-tone beep when at least one signal is found.

---

## 5. Backtesting Engine

Event-driven candle-by-candle simulator that accurately models real trading costs.

### Execution model

- Signals generated fresh at each candle; entry on the next candle's open (no look-ahead)
- **Commission**: 0.1% per side (Binance spot default)
- **Slippage**: 0.05%
- Portfolio-level position management (configurable `--max-positions`)

### Exit strategies

| Exit type | Parameter | Description |
|---|---|---|
| **Take Profit** | `--tp-mult` | Close at `entry ± tp_mult × ATR` |
| **Stop Loss** | `--sl-mult` | Close at `entry ∓ sl_mult × ATR` |
| **Time-based exit** | `--time-exit-candles` | Force-close after N candles if no TP/SL hit |

### Risk controls

| Control | Parameter | Default |
|---|---|---|
| Risk per trade | `--risk-pct` | 2% of capital |
| Max simultaneous positions | `--max-positions` | 5 |
| Max daily loss guard | `max_daily_loss_pct` | 5% |
| Max portfolio drawdown guard | `max_drawdown_pct` | 20% |

### Backtest modes

| Mode | Flag | Description |
|---|---|---|
| **Single asset** | `--mode single` | Deep-dive one symbol |
| **Multi-asset portfolio** | `--mode multi` | Simultaneous positions across a watchlist |
| **Per-setup analysis** | `--analyze-setups` | Runs a separate backtest for each of the 4 setups to measure individual contribution |

### Output metrics

| Category | Metrics |
|---|---|
| Performance | Total return (%), total return (USD), final capital, Sharpe ratio |
| Risk | Max drawdown, daily loss guard hits |
| Trade statistics | Total trades, win rate, profit factor, avg win, avg loss, avg trade |
| Durations | Avg trade duration (candles) |
| Exit breakdown | TP / SL / TIME counts and percentages |
| Per-symbol stats | Return, trades, win rate — sortable top-N |
| Risk profile | ATR mean/median, avg SL distance %, avg TP distance %, RR mean/median |

Results are saved to `statistical_system/results/` as **JSON** (full detail) and optionally as **CSV signal logs** (`--log-signals`).

---

## 6. Parameter Sweep

`run_statistical_param_sweep.py` runs an **automated grid search** over key parameters and produces a ranked summary table.

**Grid dimensions explored:**

| Dimension | Values |
|---|---|
| TP multiplier | 2.0, 2.2, 2.5, 2.8, 3.0, 3.2 |
| SL multiplier | 1.8, 2.0, 2.2 |
| Time-exit candles | 72, 96 |
| ADX filter | on (min=20) |

**CLI:**

```bash
python run_statistical_param_sweep.py --symbol BTC/USDT --timeframe 30m --days 60
python run_statistical_param_sweep.py --symbol ETH/USDT --timeframe 1h --days 90 --limit 12
```

**Output:** console summary table sorted by total return + full results saved to `sweep_results_<symbol>_<timestamp>.json` and `.csv`.

---

## 7. Risk & Edge Metrics

`risk_metrics.py` provides a standalone analytical module for evaluating trade quality **before** entry. Configured via `risk_config.json` with per-symbol overrides.

**Computed metrics:**

| Metric | Description |
|---|---|
| `target_pct` / `stop_pct` | Raw distance to TP and SL as % of price |
| `cost_pct` | Round-trip commission estimate |
| `net_target_pct` / `net_stop_pct` | Distances net of costs |
| `rrr` | Gross Risk : Reward ratio |
| `net_rr` | Net Risk : Reward after costs |
| `p_be` | Break-even hit probability required for positive EV |
| `ev_naive_pct` | Expected value using signal confidence as proxy for win probability |
| `edge_ok` | `net_target_pct >= min_edge_pct` (configurable per symbol) |
| `prob_ok` | `confidence >= p_be` |
| Position sizing | Notional size, risk amount in USD, potential P&L in USD (risk-based or margin-based sizing modes) |

**`risk_config.json` structure:**

```json
{
  "deposit": 1000,
  "risk_pct": 0.01,
  "leverage": 10,
  "default_round_trip_cost_pct": 0.002,
  "min_edge_pct": 0.005,
  "min_net_rr": 1.15,
  "sizing_mode": "risk",
  "symbols": {
    "BTCUSDT": { "min_edge_pct": 0.007, "round_trip_cost_pct": 0.0022 },
    "PEPEUSDT": { "min_edge_pct": 0.006, "round_trip_cost_pct": 0.0025 }
  }
}
```

---

## 8. Launch Profiles

`LaunchStatisticalSystem.py` provides a high-level launcher with pre-tuned configurations based on backtesting results.

```bash
python LaunchStatisticalSystem.py --list           # show all profiles
python LaunchStatisticalSystem.py conservative     # one-shot scan
python LaunchStatisticalSystem.py aggressive       # one-shot scan
python LaunchStatisticalSystem.py conservative --continuous            # live loop
python LaunchStatisticalSystem.py conservative --continuous --telegram # live + alerts
```

| Profile | Timeframe | Preset | Win Rate | Profit Factor | Expected Annual Return |
|---|---|---|---|---|---|
| **Conservative** | 1d | balanced | 52.83% | 1.92 | ~20–25% |
| **Aggressive** | 12h | balanced | 50.98% | 1.72 | ~25–30% |
| **Hybrid** | both simultaneously | — | — | — | combined |

### Signal presets

| Preset | Min Confidence | Trend Filter | ADX Filter | Active Setups |
|---|---|---|---|---|
| `conservative` | 0.75 (3/4 setups) | ✅ EMA required | ✅ ADX ≥ 20 | Pullback + Mean Reversion |
| `balanced` | 0.50 (2/4 setups) | ✅ EMA required | ❌ | All 4 |
| `aggressive` | 0.25 (1/4 setups) | ❌ | ❌ | All 4 |

---

## 9. Notifications

### Telegram

Sends formatted signal alerts via Telegram Bot API when `--telegram` flag is set.

- Configurable via `.env`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `--telegram-high-conf-only`: only sends signals with confidence ≥ 0.75 (avoids noise)
- Sends full signal detail: symbol, direction, entry, SL, TP, confidence, active setups

### Sound alerts (Windows)

Plays a distinct two-tone audio cue (`1400 Hz → 1000 Hz`) when new signals are detected during a continuous scan, requiring no screen monitoring.

---

## 10. CLI Reference

### `run_statistical_scanner.py`

```
--mode          scan | continuous          (default: scan)
--preset        conservative | balanced | aggressive
--min-confidence  float 0–1               (default: 0.5)
--timeframe     15m | 30m | 1h | 4h       (default: 30m)
--symbols       BTCUSDT ETHUSDT ...       (overrides watchlist)
--max-signals   int                       (default: 10)
--interval      int seconds               (default: 1800)
--telegram
--telegram-high-conf-only
--save-results
--verbose
```

### `run_statistical_backtest.py`

```
--symbol        BTCUSDT                   (single mode)
--symbols       BTCUSDT ETHUSDT ...       (multi mode)
--timeframe     15m | 30m | 1h | 4h | 12h | 1d
--days          int                       (default: 180)
--preset        conservative | balanced | aggressive
--min-confidence  float 0–1
--trend-filter  / --no-trend-filter
--require-adx
--adx-min       float                     (default: 20.0)
--adx-period    int                       (default: 14)
--capital       float                     (default: 10000)
--risk-pct      float                     (default: 0.02)
--max-positions int                       (default: 5)
--tp-mult       float                     (default: 2.0)
--sl-mult       float                     (default: 1.0)
--enable-time-exit / --no-time-exit
--time-exit-candles int                   (default: 48)
--mode          single | multi
--save-results
--log-signals
--signals-log-dir path
--analyze-setups
```

### `run_statistical_param_sweep.py`

```
--symbol        BTC/USDT
--timeframe     30m
--days          int                       (default: 60)
--limit         int                       (0 = all configs)
```

---

## 11. Backtested Results

Results from backtests on **Binance public OHLCV data**, no forward-bias (out-of-sample periods).

### Portfolio backtest — 1d timeframe, 365 days, balanced preset

| Symbol | Backtest Return | Win Rate |
|---|---|---|
| DOGEUSDT | +1516% | 83.3% |
| DOTUSDT | +672% | 66.7% |
| BTCUSDT | +394% | 53.8% |
| XRPUSDT | +126% | 50.0% |
| SOLUSDT | +75% | — |

### System-level aggregated metrics

| Config | Return | Win Rate | Profit Factor | Max Drawdown | Trades/Year |
|---|---|---|---|---|---|
| 1d balanced | **+24.26% p.a.** | 52.83% | 1.92 | ~7% | ~50–60 |
| 12h balanced | **+13.93% / 6 mo** (~28% p.a.) | 50.98% | 1.72 | ~8% | ~100 |

> Backtests include 0.1% commission and 0.05% slippage per trade.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data feed | Binance Spot via `ccxt` (public API, no key required) |
| Indicators | `ta` (Technical Analysis library) |
| Data processing | `pandas`, `numpy` |
| Notifications | Telegram Bot API |
| Config | Dataclasses + JSON |
| Output | JSON results, CSV signal logs |
