"""
Test Optimal Configuration

Combines optimal parameters discovered:
- Weekly rebalancing (better than monthly)
- 252-day lookback (best from optimization)
"""

import sys
sys.path.append('.')

import pandas as pd
from src.data_loader import load_prices
from src.strategy import AllWeatherV1
from src.metrics import format_metrics

START_DATE = '2018-01-01'

def test_optimal_configuration():
    """Test optimal configuration vs baseline."""

    print("=" * 80)
    print("Optimal Configuration Test")
    print("=" * 80)

    prices = load_prices('data/etf_prices_7etf.csv')
    print(f"\nLoaded {len(prices.columns)} ETFs")

    # Baseline (original v1.0)
    print("\n" + "=" * 80)
    print("BASELINE (Original v1.0)")
    print("=" * 80)
    print("Weekly rebalancing, 100-day lookback")

    baseline = AllWeatherV1(
        prices=prices,
        initial_capital=1_000_000,
        rebalance_freq='W-MON',
        lookback=100,
        commission_rate=0.0003,
        target_volatility=None
    )

    baseline_results = baseline.run_backtest(start_date=START_DATE, verbose=False)
    baseline_metrics = baseline_results['metrics']

    print(format_metrics(baseline_metrics))
    print(f"\nFinal Value: ¥{baseline_results['final_value']:,.0f}")
    print(f"Total Return: {baseline_results['total_return']:.2%}")

    # Optimal configuration
    print("\n" + "=" * 80)
    print("OPTIMAL CONFIGURATION")
    print("=" * 80)
    print("Weekly rebalancing, 252-day lookback")

    optimal = AllWeatherV1(
        prices=prices,
        initial_capital=1_000_000,
        rebalance_freq='W-MON',  # Weekly (better than monthly)
        lookback=252,  # 1 year (optimal from testing)
        commission_rate=0.0003,
        target_volatility=None  # No vol targeting
    )

    optimal_results = optimal.run_backtest(start_date=START_DATE, verbose=False)
    optimal_metrics = optimal_results['metrics']

    print(format_metrics(optimal_metrics))
    print(f"\nFinal Value: ¥{optimal_results['final_value']:,.0f}")
    print(f"Total Return: {optimal_results['total_return']:.2%}")

    # Comparison
    print("\n" + "=" * 80)
    print("IMPROVEMENT SUMMARY")
    print("=" * 80)

    comparison = pd.DataFrame({
        'Baseline': [
            f"{baseline_metrics['annual_return']:.2%}",
            f"{baseline_metrics['sharpe_ratio']:.2f}",
            f"{baseline_metrics['max_drawdown']:.2%}",
            f"{baseline_metrics['calmar_ratio']:.2f}",
            f"¥{baseline_results['final_value']:,.0f}"
        ],
        'Optimal': [
            f"{optimal_metrics['annual_return']:.2%}",
            f"{optimal_metrics['sharpe_ratio']:.2f}",
            f"{optimal_metrics['max_drawdown']:.2%}",
            f"{optimal_metrics['calmar_ratio']:.2f}",
            f"¥{optimal_results['final_value']:,.0f}"
        ],
        'Change': [
            f"+{(optimal_metrics['annual_return'] - baseline_metrics['annual_return'])*100:.2f}%",
            f"+{(optimal_metrics['sharpe_ratio'] - baseline_metrics['sharpe_ratio']):.2f}",
            f"{(optimal_metrics['max_drawdown'] - baseline_metrics['max_drawdown'])*100:+.2f}%",
            f"+{(optimal_metrics['calmar_ratio'] - baseline_metrics['calmar_ratio']):.2f}",
            f"¥{(optimal_results['final_value'] - baseline_results['final_value']):+,.0f}"
        ]
    }, index=[
        'Annual Return',
        'Sharpe Ratio',
        'Max Drawdown',
        'Calmar Ratio',
        'Final Value'
    ])

    print(comparison)

    improvement_pct = (optimal_results['final_value'] - baseline_results['final_value']) / baseline_results['final_value']
    print(f"\nTotal Portfolio Improvement: {improvement_pct:.2%}")

    print("\n" + "=" * 80)
    print("OPTIMAL PARAMETERS DISCOVERED:")
    print("  - Rebalancing: Weekly (W-MON)")
    print("  - Lookback: 252 days (1 trading year)")
    print("  - Volatility Targeting: None (not beneficial for this portfolio)")
    print("=" * 80)

if __name__ == '__main__':
    test_optimal_configuration()
