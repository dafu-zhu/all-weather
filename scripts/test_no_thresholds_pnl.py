#!/usr/bin/env python3
"""
Test PnL performance of v2.0 strategy WITHOUT asymmetric thresholds.

Compares symmetric 3% drift threshold vs the old asymmetric 3%/10% setup.
Backtest period: 2025-01-01 to latest available data.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategy_v2 import AllWeatherV2

# Use 6-ETF subset (same as live trading)
TRADABLE_ETFS = [
    '510300.SH',  # CSI 300
    '510500.SH',  # CSI 500
    '513500.SH',  # S&P 500
    '511260.SH',  # 10Y Treasury
    '518880.SH',  # Gold
    '513100.SH',  # Nasdaq-100
]

START_DATE = '2025-01-01'
INITIAL_CAPITAL = 1_000_000


def load_prices():
    """Load prices from local CSV."""
    prices = pd.read_csv(
        'data/etf_prices_7etf.csv',
        index_col=0,
        parse_dates=True
    )
    # Filter to tradable ETFs only
    return prices[TRADABLE_ETFS]


def run_backtest(prices, drift_threshold, label):
    """Run a backtest with given drift threshold."""
    strategy = AllWeatherV2(
        prices=prices,
        initial_capital=INITIAL_CAPITAL,
        lookback=252,
        commission_rate=0.0003,
        drift_threshold=drift_threshold,
        use_shrinkage=True,
    )

    results = strategy.run_backtest(
        start_date=START_DATE,
        verbose=False,
    )

    return results


def print_results(label, results):
    """Print formatted results."""
    metrics = results['metrics']
    equity = results['equity_curve']

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Period: {equity.index[0].date()} to {equity.index[-1].date()}")
    print(f"  Final Value:        ¥{results['final_value']:,.0f}")
    print(f"  Total Return:       {results['total_return']*100:+.2f}%")
    print(f"  Annual Return:      {metrics.get('annual_return', 0)*100:+.2f}%")
    print(f"  Sharpe Ratio:       {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"  Sortino Ratio:      {metrics.get('sortino_ratio', 0):.2f}")
    print(f"  Max Drawdown:       {metrics.get('max_drawdown', 0)*100:.2f}%")
    print(f"  Calmar Ratio:       {metrics.get('calmar_ratio', 0):.2f}")
    print(f"  Win Rate:           {metrics.get('win_rate', 0)*100:.1f}%")
    print(f"  Weekly Updates:     {results['weekly_rebalance_count']}")
    print(f"  Daily Rebalances:   {results['daily_rebalance_count']}")
    print(f"  Total Daily Trades: {len(results['daily_trades'])}")


def main():
    print("Loading prices...")
    prices = load_prices()
    print(f"Data: {prices.index[0].date()} to {prices.index[-1].date()}")
    print(f"ETFs: {list(prices.columns)}")

    # Test thresholds from 1% to 3% in 0.5% steps
    thresholds = [0.01, 0.015, 0.02, 0.025, 0.03]
    labels = ['1.0%', '1.5%', '2.0%', '2.5%', '3.0%']
    all_results = []

    for threshold, label in zip(thresholds, labels):
        print(f"Running backtest: {label} threshold...")
        r = run_backtest(prices, drift_threshold=threshold, label=label)
        all_results.append(r)

    # Print individual results
    for label, r in zip(labels, all_results):
        print_results(f"{label} Drift Threshold", r)

    # Comparison table
    header = f"{'Metric':<22}" + "".join(f"{l:>14}" for l in labels)
    print(f"\n{'='*len(header)}")
    print(f"  COMPARISON TABLE (starting {START_DATE})")
    print(f"{'='*len(header)}")
    print(header)
    print(f"{'-'*len(header)}")

    rows = [
        ("Final Value", "¥{:,.0f}", 'final_value', None),
        ("Total Return", "{:+.2f}%", 'total_return', 100),
        ("Annual Return", "{:+.2f}%", 'annual_return', 100),
        ("Sharpe Ratio", "{:.2f}", 'sharpe_ratio', None),
        ("Sortino Ratio", "{:.2f}", 'sortino_ratio', None),
        ("Max Drawdown", "{:.2f}%", 'max_drawdown', 100),
        ("Win Rate", "{:.1f}%", 'win_rate', 100),
    ]

    for row_label, fmt, key, mult in rows:
        vals = []
        for r in all_results:
            if key in ('final_value', 'total_return'):
                v = r[key]
            else:
                v = r['metrics'].get(key, 0)
            if mult:
                v = v * mult
            vals.append(fmt.format(v))
        print(f"{row_label:<22}" + "".join(f"{v:>14}" for v in vals))

    # Rebalance counts
    print(f"{'Daily Rebalances':<22}" + "".join(f"{r['daily_rebalance_count']:>14}" for r in all_results))
    print(f"{'Total Trades':<22}" + "".join(f"{len(r['daily_trades']):>14}" for r in all_results))


if __name__ == '__main__':
    main()
