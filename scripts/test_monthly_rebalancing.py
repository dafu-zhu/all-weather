"""
Test Monthly Rebalancing vs Weekly

Simple comparison to isolate the effect of rebalancing frequency.
"""

import sys
sys.path.append('.')

import pandas as pd
from src.data_loader import load_prices
from src.strategy import AllWeatherV1
from src.metrics import format_metrics

START_DATE = '2018-01-01'

def test_rebalancing_frequency():
    """Test weekly vs monthly rebalancing."""

    print("=" * 80)
    print("Rebalancing Frequency Test: Weekly vs Monthly")
    print("=" * 80)

    prices = load_prices('data/etf_prices_7etf.csv')
    print(f"\nLoaded {len(prices.columns)} ETFs")

    # Weekly rebalancing (original)
    print("\n" + "-" * 80)
    print("WEEKLY REBALANCING")
    print("-" * 80)

    weekly = AllWeatherV1(
        prices=prices,
        initial_capital=1_000_000,
        rebalance_freq='W-MON',
        lookback=100,
        commission_rate=0.0003,
        target_volatility=None  # No vol targeting
    )

    weekly_results = weekly.run_backtest(start_date=START_DATE, verbose=True)
    weekly_metrics = weekly_results['metrics']

    print("\nWeekly Results:")
    print(format_metrics(weekly_metrics))
    print(f"Final Value: ¥{weekly_results['final_value']:,.0f}")
    print(f"Total Return: {weekly_results['total_return']:.2%}")

    # Monthly rebalancing
    print("\n" + "-" * 80)
    print("MONTHLY REBALANCING")
    print("-" * 80)

    monthly = AllWeatherV1(
        prices=prices,
        initial_capital=1_000_000,
        rebalance_freq='MS',
        lookback=100,
        commission_rate=0.0003,
        target_volatility=None  # No vol targeting
    )

    monthly_results = monthly.run_backtest(start_date=START_DATE, verbose=True)
    monthly_metrics = monthly_results['metrics']

    print("\nMonthly Results:")
    print(format_metrics(monthly_metrics))
    print(f"Final Value: ¥{monthly_results['final_value']:,.0f}")
    print(f"Total Return: {monthly_results['total_return']:.2%}")

    # Comparison
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)

    print(f"\nAnnual Return:    Weekly {weekly_metrics['annual_return']:.2%}  →  Monthly {monthly_metrics['annual_return']:.2%}  (Δ {monthly_metrics['annual_return']-weekly_metrics['annual_return']:.2%})")
    print(f"Sharpe Ratio:     Weekly {weekly_metrics['sharpe_ratio']:.2f}  →  Monthly {monthly_metrics['sharpe_ratio']:.2f}  (Δ {monthly_metrics['sharpe_ratio']-weekly_metrics['sharpe_ratio']:.2f})")
    print(f"Max Drawdown:     Weekly {weekly_metrics['max_drawdown']:.2%}  →  Monthly {monthly_metrics['max_drawdown']:.2%}  (Δ {monthly_metrics['max_drawdown']-weekly_metrics['max_drawdown']:.2%})")
    print(f"Final Value:      Weekly ¥{weekly_results['final_value']:,.0f}  →  Monthly ¥{monthly_results['final_value']:,.0f}  (Δ ¥{monthly_results['final_value']-weekly_results['final_value']:,.0f})")

    improvement = (monthly_results['final_value'] - weekly_results['final_value']) / weekly_results['final_value']
    print(f"\nMonthly rebalancing improvement: {improvement:.2%}")
    print("=" * 80)

if __name__ == '__main__':
    test_rebalancing_frequency()
