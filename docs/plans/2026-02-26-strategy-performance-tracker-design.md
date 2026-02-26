# All-Weather Strategy Performance Tracker Design

**Date**: 2026-02-26
**Status**: Approved

## Overview

Add an auto-updating, interactive performance tracker for the All-Weather strategy starting from 2026. Displays simulated strategy returns with automatic rebalancing.

## Requirements

- **Tracking mode**: Simulated strategy with auto-rebalancing when drift > 5%
- **Update frequency**: Daily via GitHub Actions
- **Display**: Percentage returns only (no absolute values)
- **Chart**: Interactive with hover, zoom, rebalance markers
- **Non-trading days**: Excluded from x-axis (trading days only)
- **Location**: Embedded in portfolio site (dafu-zhu.github.io)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        all-weather repo                         │
├─────────────────────────────────────────────────────────────────┤
│  GitHub Action (daily 16:00 Beijing)                            │
│       │                                                         │
│       ▼                                                         │
│  scripts/generate_tracker_data.py                               │
│       │  - Uses Portfolio class                                 │
│       │  - Fetches prices via yfinance                          │
│       │  - Simulates rebalancing at 5% drift                    │
│       │  - 0.03% commission per trade                           │
│       ▼                                                         │
│  data/pnl_tracker.json                                          │
│       │                                                         │
└───────┼─────────────────────────────────────────────────────────┘
        │
        │ raw.githubusercontent.com
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    dafu-zhu.github.io repo                      │
├─────────────────────────────────────────────────────────────────┤
│  projects/all-weather/index.html                                │
│       │                                                         │
│       ▼                                                         │
│  projects/all-weather/tracker.js                                │
│       │  - Fetches JSON at page load                            │
│       │  - Renders Lightweight Charts                           │
│       ▼                                                         │
│  [Interactive PnL Chart]                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Data Pipeline

### Simulation Script

**Location**: `scripts/generate_tracker_data.py`

**Logic**:
1. Calculate initial risk parity weights from historical data
2. Start with hypothetical allocation on 2026-01-02 (first trading day)
3. For each trading day:
   - Fetch prices from yfinance
   - Calculate current weights and drift
   - If drift > 5%, simulate rebalance trades (with 0.03% commission)
   - Record daily PnL %
4. Output JSON with PnL series, rebalance events, and summary metrics

### GitHub Action

**Location**: `.github/workflows/update-tracker.yml`

**Schedule**: Daily at 16:00 Beijing time (08:00 UTC)

**Steps**:
1. Checkout repo
2. Setup Python with dependencies
3. Run `scripts/generate_tracker_data.py`
4. Commit and push `data/pnl_tracker.json` if changed

### JSON Schema

```json
{
  "last_updated": "2026-02-26T16:00:00+08:00",
  "start_date": "2026-01-02",
  "pnl": [
    {"date": "2026-01-02", "value": 0.0},
    {"date": "2026-01-03", "value": 0.12}
  ],
  "rebalances": [
    {"date": "2026-02-15", "drift": 0.062}
  ],
  "metrics": {
    "total_return": 2.45,
    "sharpe": 1.2,
    "max_drawdown": -3.1,
    "win_rate": 54.5
  }
}
```

## Frontend Component

### Chart Library

**Lightweight Charts** (TradingView): 50KB, finance-focused, built-in interactivity

### Features

- Area chart with gradient fill (green profit, red loss)
- Crosshair with date + PnL % on hover
- Zoom via mouse wheel or pinch
- Rebalance events marked as dots on chart
- Responsive design for mobile

### Layout

```
┌─────────────────────────────────────────────────────┐
│  All-Weather Strategy Performance (2026)            │
│  Last updated: Feb 26, 2026                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Interactive PnL % Chart]                          │
│   ▲                                                 │
│   │    ╱╲    ╱╲___╱╲                               │
│   │___╱  ╲__╱        ╲___                          │
│   └─────────────────────────────────────────────── │
│   Jan        Feb        Mar                         │
│                                                     │
├─────────────────────────────────────────────────────┤
│  Return: +2.45%  │  Sharpe: 1.2  │  Max DD: -3.1%  │
└─────────────────────────────────────────────────────┘
```

### File Structure

```
dafu-zhu.github.io/
└── projects/
    └── all-weather/
        ├── index.html      # Page with chart container
        └── tracker.js      # Fetch JSON + render chart
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| yfinance API down | Action retries 3x, skips update (keeps previous data) |
| Market holiday | No data point for that day (excluded from series) |
| First run | Initialize with Day 1 = 0% return |
| Raw GitHub fetch fails | Show "Data temporarily unavailable" message |

## Dependencies

### all-weather repo
- Python 3.x
- yfinance
- pandas, numpy
- Existing `src/portfolio_tracker.py`, `src/optimizer.py`, `src/metrics.py`

### portfolio site
- Lightweight Charts (CDN or bundled)
- No build step required (vanilla JS)

## Security Considerations

- No PAT required (all-weather Action commits to own repo)
- Public JSON data contains only simulated returns (no sensitive info)
- yfinance public API (no API keys)

## Future Enhancements (Out of Scope)

- Benchmark comparison (CSI 300, S&P 500)
- Multiple strategy variants
- Downloadable CSV export
