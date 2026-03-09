#!/usr/bin/env python3
"""
Generate strategy performance data for the live tracker.

Simulates the All-Weather v2.1 strategy from 2026-01-02 with:
- Risk parity weights (Ledoit-Wolf shrinkage)
- Asymmetric thresholds: 3% trim (profit-taking) / 10% buy (buying dips)
- Weekly target weight updates (Mondays)
- 0.03% commission per trade

Outputs JSON for the portfolio site tracker.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategy_v2 import AllWeatherV2

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
DRIFT_THRESHOLD = 0.03  # 3% symmetric drift threshold
COMMISSION_RATE = 0.0003  # 0.03%
LOOKBACK = 252
INITIAL_CAPITAL = 1_000_000
BENCHMARK_TICKER = '510300.SH'  # CSI 300 as benchmark


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


def calculate_benchmark(prices: pd.DataFrame, start_date: str) -> list[dict]:
    """Calculate benchmark (CSI300) returns from start date."""
    benchmark_prices = prices[BENCHMARK_TICKER]
    benchmark_prices = benchmark_prices[benchmark_prices.index >= start_date]

    if benchmark_prices.empty:
        return []

    initial_price = benchmark_prices.iloc[0]
    benchmark_series = []
    for date, price in benchmark_prices.items():
        pnl_pct = (price - initial_price) / initial_price * 100
        benchmark_series.append({
            'date': date.strftime('%Y-%m-%d'),
            'value': round(pnl_pct, 2)
        })

    return benchmark_series


def simulate_strategy(prices: pd.DataFrame) -> dict:
    """
    Simulate the All-Weather v2.0 strategy.

    Returns dict with pnl series, rebalance events, and metrics.
    """
    strategy = AllWeatherV2(
        prices=prices,
        initial_capital=INITIAL_CAPITAL,
        lookback=LOOKBACK,
        commission_rate=COMMISSION_RATE,
        drift_threshold=DRIFT_THRESHOLD,
        use_shrinkage=True,
    )

    results = strategy.run_backtest(
        start_date=START_DATE,
        end_date=None,
        verbose=False,
    )

    # Convert equity curve to PnL percentage series
    equity = results['equity_curve']
    pnl_series = []
    for date, value in equity.items():
        pnl_pct = (value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
        pnl_series.append({
            'date': date.strftime('%Y-%m-%d'),
            'value': round(pnl_pct, 2)
        })

    # Convert daily trades to rebalance events
    rebalances = []
    for trade in results['daily_trades']:
        rebalances.append({
            'date': trade['date'].strftime('%Y-%m-%d'),
            'drift': round(abs(trade['drift']) * 100, 2)
        })

    # Get metrics
    metrics = results['metrics']

    # Calculate benchmark returns
    benchmark_series = calculate_benchmark(prices, START_DATE)

    return {
        'last_updated': datetime.now().isoformat(),
        'start_date': START_DATE,
        'strategy_version': 'v2.0',
        'drift_threshold': f"{DRIFT_THRESHOLD:.0%}",
        'benchmark': 'CSI 300',
        'pnl': pnl_series,
        'benchmark_pnl': benchmark_series,
        'rebalances': rebalances,
        'metrics': {
            'total_return': round(results['total_return'] * 100, 2),
            'sharpe': round(metrics.get('sharpe_ratio', 0), 2),
            'max_drawdown': round(metrics.get('max_drawdown', 0) * 100, 2),
            'win_rate': round(metrics.get('win_rate', 0) * 100, 1)
        }
    }


def _merge_series(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge time series, preserving existing entries and only adding new dates.

    Existing data is treated as the source of truth (it was captured when
    the market data was fresh). New entries are only added for dates not
    already present, so delayed/missing data in yfinance can never erase
    previously recorded values.
    """
    existing_by_date = {entry['date']: entry for entry in existing}
    for entry in new:
        if entry['date'] not in existing_by_date:
            existing_by_date[entry['date']] = entry
    return sorted(existing_by_date.values(), key=lambda e: e['date'])


def _merge_rebalances(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge rebalance events by date (union)."""
    by_date = {entry['date']: entry for entry in existing}
    for entry in new:
        if entry['date'] not in by_date:
            by_date[entry['date']] = entry
    return sorted(by_date.values(), key=lambda e: e['date'])


def main():
    """Generate tracker data and save to JSON."""
    output_path = Path(__file__).parent.parent / 'data' / 'pnl_tracker.json'
    output_path.parent.mkdir(exist_ok=True)

    # Load existing data to preserve previously captured entries
    existing = {}
    if output_path.exists():
        with open(output_path) as f:
            existing = json.load(f)

    print("Fetching prices...")
    prices = fetch_prices(TRADABLE_ETFS)

    print("Simulating strategy...")
    result = simulate_strategy(prices)

    # Merge: preserve existing time series entries, only add new dates
    if existing:
        result['pnl'] = _merge_series(
            existing.get('pnl', []), result['pnl'])
        result['benchmark_pnl'] = _merge_series(
            existing.get('benchmark_pnl', []), result['benchmark_pnl'])
        result['rebalances'] = _merge_rebalances(
            existing.get('rebalances', []), result['rebalances'])

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Saved to {output_path}")
    print(f"Total return: {result['metrics']['total_return']}%")
    print(f"Rebalances: {len(result['rebalances'])}")


if __name__ == '__main__':
    main()
