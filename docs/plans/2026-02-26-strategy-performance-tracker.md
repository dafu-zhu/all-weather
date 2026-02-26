# Strategy Performance Tracker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an auto-updating interactive PnL chart to the portfolio site showing simulated All-Weather strategy returns from 2026.

**Architecture:** Python script in all-weather repo simulates strategy with auto-rebalancing, outputs JSON. GitHub Action runs daily. Portfolio site fetches JSON from raw.githubusercontent.com and renders with Lightweight Charts.

**Tech Stack:** Python (yfinance, pandas), GitHub Actions, JavaScript (Lightweight Charts), Jekyll

---

## Task 1: Create Strategy Simulator

**Files:**
- Create: `scripts/generate_tracker_data.py`
- Reference: `src/portfolio_tracker.py`, `src/optimizer.py`, `src/metrics.py`

**Step 1: Create the simulator script**

```python
#!/usr/bin/env python3
"""
Generate strategy performance data for the live tracker.

Simulates the All-Weather strategy from 2026-01-02 with:
- Risk parity initial weights (Ledoit-Wolf shrinkage)
- Auto-rebalancing when drift > 5%
- 0.03% commission per trade

Outputs JSON for the portfolio site tracker.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.optimizer import optimize_weights
from src.metrics import calculate_all_metrics

# Strategy configuration
TRADABLE_ETFS = [
    '510300.SH',  # CSI 300
    '510500.SH',  # CSI 500
    '513500.SH',  # S&P 500
    '511260.SH',  # 10Y Treasury
    '518880.SH',  # Gold
    '513100.SH',  # Nasdaq-100
]
START_DATE = '2026-01-02'
COMMISSION_RATE = 0.0003  # 0.03%
REBALANCE_THRESHOLD = 0.05  # 5% drift
LOOKBACK = 252


def fetch_prices(tickers: list[str], start: str = '2015-01-01') -> pd.DataFrame:
    """Fetch historical prices from yfinance."""
    data = {}
    for ticker in tickers:
        yf_ticker = ticker.replace('.SH', '.SS')
        hist = yf.Ticker(yf_ticker).history(start=start, auto_adjust=True)
        if hist.empty:
            raise ValueError(f"No data for {ticker}")
        data[ticker] = hist['Close']

    prices = pd.DataFrame(data)
    prices.index = prices.index.tz_localize(None)
    return prices.dropna()


def calculate_weights(prices: pd.DataFrame, lookback: int = 252) -> np.ndarray:
    """Calculate risk parity weights using Ledoit-Wolf shrinkage."""
    returns = prices.iloc[-lookback:].pct_change().dropna()
    return optimize_weights(returns, use_shrinkage=True)


def simulate_strategy(prices: pd.DataFrame) -> dict:
    """
    Simulate the All-Weather strategy with auto-rebalancing.

    Returns dict with pnl series, rebalance events, and metrics.
    """
    # Get tracking period (from START_DATE onwards)
    tracking_prices = prices.loc[START_DATE:]
    if tracking_prices.empty:
        raise ValueError(f"No data available from {START_DATE}")

    # Calculate initial weights using data before start date
    pre_start_prices = prices.loc[:START_DATE].iloc[:-1]
    if len(pre_start_prices) < LOOKBACK:
        raise ValueError(f"Insufficient historical data for lookback period")

    weights = calculate_weights(pre_start_prices, LOOKBACK)

    # Initialize tracking
    pnl_series = []
    rebalances = []
    initial_value = 1.0  # Normalized
    portfolio_value = initial_value

    # Track positions (normalized)
    positions = {etf: weights[i] for i, etf in enumerate(TRADABLE_ETFS)}
    prev_prices = tracking_prices.iloc[0]

    for date, current_prices in tracking_prices.iterrows():
        # Update portfolio value based on price changes
        if date != tracking_prices.index[0]:
            returns = (current_prices - prev_prices) / prev_prices
            for i, etf in enumerate(TRADABLE_ETFS):
                positions[etf] *= (1 + returns[etf])

        # Calculate current portfolio value and weights
        portfolio_value = sum(positions.values())
        current_weights = {etf: pos / portfolio_value for etf, pos in positions.items()}

        # Check for rebalancing
        target_weights = dict(zip(TRADABLE_ETFS, weights))
        max_drift = max(abs(current_weights[etf] - target_weights[etf]) for etf in TRADABLE_ETFS)

        if max_drift > REBALANCE_THRESHOLD:
            # Recalculate target weights with current data
            hist_prices = prices.loc[:date]
            if len(hist_prices) >= LOOKBACK:
                weights = calculate_weights(hist_prices, LOOKBACK)
                target_weights = dict(zip(TRADABLE_ETFS, weights))

            # Simulate rebalancing with commission
            turnover = sum(abs(current_weights[etf] - target_weights[etf]) for etf in TRADABLE_ETFS) / 2
            commission_cost = turnover * COMMISSION_RATE * portfolio_value
            portfolio_value -= commission_cost

            # Reset positions to target weights
            positions = {etf: target_weights[etf] * portfolio_value for etf in TRADABLE_ETFS}

            rebalances.append({
                'date': date.strftime('%Y-%m-%d'),
                'drift': round(max_drift * 100, 2)
            })

        # Record PnL
        pnl_pct = (portfolio_value - initial_value) / initial_value * 100
        pnl_series.append({
            'date': date.strftime('%Y-%m-%d'),
            'value': round(pnl_pct, 2)
        })

        prev_prices = current_prices

    # Calculate performance metrics
    pnl_values = [p['value'] for p in pnl_series]
    daily_returns = pd.Series(pnl_values).diff().dropna() / 100
    equity_curve = pd.Series([1 + p['value']/100 for p in pnl_series])

    metrics_raw = calculate_all_metrics(daily_returns, equity_curve)

    return {
        'last_updated': datetime.now().isoformat(),
        'start_date': START_DATE,
        'pnl': pnl_series,
        'rebalances': rebalances,
        'metrics': {
            'total_return': round(pnl_series[-1]['value'], 2),
            'sharpe': round(metrics_raw.get('sharpe_ratio', 0), 2),
            'max_drawdown': round(metrics_raw.get('max_drawdown', 0) * 100, 2),
            'win_rate': round(metrics_raw.get('win_rate', 0) * 100, 1)
        }
    }


def main():
    """Generate tracker data and save to JSON."""
    print("Fetching prices...")
    prices = fetch_prices(TRADABLE_ETFS)

    print("Simulating strategy...")
    result = simulate_strategy(prices)

    # Save to data directory
    output_path = Path(__file__).parent.parent / 'data' / 'pnl_tracker.json'
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Saved to {output_path}")
    print(f"Total return: {result['metrics']['total_return']}%")
    print(f"Rebalances: {len(result['rebalances'])}")


if __name__ == '__main__':
    main()
```

**Step 2: Run the script to verify it works**

Run: `cd /Users/zdf/Documents/GitHub/all-weather && uv run python scripts/generate_tracker_data.py`

Expected: Script outputs JSON file to `data/pnl_tracker.json` with PnL series

**Step 3: Verify JSON output structure**

Run: `cat /Users/zdf/Documents/GitHub/all-weather/data/pnl_tracker.json | head -50`

Expected: JSON with `last_updated`, `start_date`, `pnl` array, `rebalances` array, `metrics` object

**Step 4: Commit**

```bash
cd /Users/zdf/Documents/GitHub/all-weather
git add scripts/generate_tracker_data.py data/pnl_tracker.json
git commit -m "feat: add strategy performance tracker data generator"
```

---

## Task 2: Create GitHub Action Workflow

**Files:**
- Create: `.github/workflows/update-tracker.yml`

**Step 1: Create the workflow file**

```yaml
name: Update Strategy Tracker

on:
  schedule:
    # Run at 16:00 Beijing time (08:00 UTC) on weekdays
    - cron: '0 8 * * 1-5'
  workflow_dispatch:  # Allow manual trigger

jobs:
  update-tracker:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync

      - name: Generate tracker data
        run: uv run python scripts/generate_tracker_data.py
        continue-on-error: true
        id: generate

      - name: Retry on failure
        if: steps.generate.outcome == 'failure'
        run: |
          sleep 60
          uv run python scripts/generate_tracker_data.py
        continue-on-error: true

      - name: Commit and push if changed
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add data/pnl_tracker.json
          git diff --staged --quiet || git commit -m "chore: update tracker data $(date +%Y-%m-%d)"
          git push
```

**Step 2: Commit the workflow**

```bash
cd /Users/zdf/Documents/GitHub/all-weather
git add .github/workflows/update-tracker.yml
git commit -m "feat: add GitHub Action for daily tracker updates"
```

**Step 3: Trigger manually to test**

Run: `cd /Users/zdf/Documents/GitHub/all-weather && gh workflow run update-tracker.yml`

Expected: Workflow runs successfully (check with `gh run list`)

---

## Task 3: Add Tracker Section to Portfolio Site

**Files:**
- Modify: `_projects/all-weather.md`
- Create: `assets/js/strategy-tracker.js`

**Step 1: Create the JavaScript file for the chart**

```javascript
/**
 * Strategy Performance Tracker
 * Fetches PnL data and renders interactive chart using Lightweight Charts
 */

const DATA_URL = 'https://raw.githubusercontent.com/dafu-zhu/all-weather/main/data/pnl_tracker.json';

async function initStrategyTracker() {
  const container = document.getElementById('strategy-tracker-chart');
  const metricsContainer = document.getElementById('strategy-tracker-metrics');
  const statusEl = document.getElementById('strategy-tracker-status');

  if (!container) return;

  try {
    // Fetch data
    statusEl.textContent = 'Loading...';
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error('Failed to fetch data');
    const data = await response.json();

    // Update status
    const lastUpdated = new Date(data.last_updated).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric'
    });
    statusEl.textContent = `Last updated: ${lastUpdated}`;

    // Render metrics
    const metrics = data.metrics;
    const returnClass = metrics.total_return >= 0 ? 'positive' : 'negative';
    metricsContainer.innerHTML = `
      <div class="metric">
        <span class="label">Return</span>
        <span class="value ${returnClass}">${metrics.total_return >= 0 ? '+' : ''}${metrics.total_return}%</span>
      </div>
      <div class="metric">
        <span class="label">Sharpe</span>
        <span class="value">${metrics.sharpe}</span>
      </div>
      <div class="metric">
        <span class="label">Max DD</span>
        <span class="value negative">${metrics.max_drawdown}%</span>
      </div>
      <div class="metric">
        <span class="label">Win Rate</span>
        <span class="value">${metrics.win_rate}%</span>
      </div>
    `;

    // Create chart
    const chart = LightweightCharts.createChart(container, {
      width: container.clientWidth,
      height: 300,
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#eee' },
        horzLines: { color: '#eee' },
      },
      crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: '#ccc',
      },
      timeScale: {
        borderColor: '#ccc',
        timeVisible: false,
      },
    });

    // Add area series
    const areaSeries = chart.addAreaSeries({
      topColor: 'rgba(76, 175, 80, 0.4)',
      bottomColor: 'rgba(76, 175, 80, 0.0)',
      lineColor: 'rgba(76, 175, 80, 1)',
      lineWidth: 2,
    });

    // Transform data for chart
    const chartData = data.pnl.map(point => ({
      time: point.date,
      value: point.value,
    }));

    areaSeries.setData(chartData);

    // Add rebalance markers
    if (data.rebalances && data.rebalances.length > 0) {
      const markers = data.rebalances.map(r => ({
        time: r.date,
        position: 'aboveBar',
        color: '#2196F3',
        shape: 'circle',
        text: `R ${r.drift}%`,
      }));
      areaSeries.setMarkers(markers);
    }

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const resizeObserver = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth });
    });
    resizeObserver.observe(container);

  } catch (error) {
    console.error('Strategy tracker error:', error);
    statusEl.textContent = 'Data temporarily unavailable';
    container.innerHTML = '<p style="text-align: center; color: #999; padding: 50px;">Unable to load tracker data</p>';
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initStrategyTracker);
} else {
  initStrategyTracker();
}
```

**Step 2: Add tracker section to the project page**

Edit `/Users/zdf/Documents/GitHub/dafu-zhu.github.io/_projects/all-weather.md` to add after the Tech Stack section:

```markdown
---

## Live Strategy Tracker (2026)

<p id="strategy-tracker-status" style="color: #666; font-size: 0.9em;">Loading...</p>

<div id="strategy-tracker-metrics" style="display: flex; gap: 20px; margin-bottom: 15px; flex-wrap: wrap;">
</div>

<div id="strategy-tracker-chart" style="width: 100%; height: 300px; border: 1px solid #eee; border-radius: 4px;">
</div>

<style>
  #strategy-tracker-metrics .metric {
    display: flex;
    flex-direction: column;
    padding: 8px 16px;
    background: #f8f9fa;
    border-radius: 4px;
  }
  #strategy-tracker-metrics .label {
    font-size: 0.8em;
    color: #666;
  }
  #strategy-tracker-metrics .value {
    font-size: 1.2em;
    font-weight: 600;
  }
  #strategy-tracker-metrics .positive { color: #4caf50; }
  #strategy-tracker-metrics .negative { color: #f44336; }
</style>

<script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
<script src="/assets/js/strategy-tracker.js"></script>
```

**Step 3: Commit the changes**

```bash
cd /Users/zdf/Documents/GitHub/dafu-zhu.github.io
git add assets/js/strategy-tracker.js _projects/all-weather.md
git commit -m "feat: add live strategy performance tracker"
```

---

## Task 4: Test End-to-End

**Step 1: Push all-weather changes**

```bash
cd /Users/zdf/Documents/GitHub/all-weather
git push
```

**Step 2: Verify JSON is accessible**

Run: `curl -s https://raw.githubusercontent.com/dafu-zhu/all-weather/main/data/pnl_tracker.json | head -20`

Expected: JSON data is returned

**Step 3: Test portfolio site locally**

```bash
cd /Users/zdf/Documents/GitHub/dafu-zhu.github.io
bundle exec jekyll serve
```

Open: `http://localhost:4000/projects/all-weather/`

Expected: Interactive chart loads with PnL data and metrics

**Step 4: Push portfolio site changes**

```bash
cd /Users/zdf/Documents/GitHub/dafu-zhu.github.io
git push
```

**Step 5: Verify production**

Open: `https://dafu-zhu.github.io/projects/all-weather/`

Expected: Tracker section displays with chart and metrics

---

## Summary

| Task | Files | Purpose |
|------|-------|---------|
| 1 | `scripts/generate_tracker_data.py` | Simulate strategy, output JSON |
| 2 | `.github/workflows/update-tracker.yml` | Daily auto-update |
| 3 | `assets/js/strategy-tracker.js`, `_projects/all-weather.md` | Frontend chart |
| 4 | - | End-to-end testing |
