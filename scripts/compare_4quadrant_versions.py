"""
Compare All Weather Strategy Versions with 4-Quadrant Approach

Tests 4 versions to reduce max drawdown below -10%:
- v1.1: Pure Risk Parity (baseline)
- v1.2: Constrained Risk Parity
- v1.3: 4-Quadrant Risk Balance
- v1.3+Vol: 4-Quadrant + 5% Volatility Targeting

Goal: Achieve max drawdown < -10% while maintaining positive returns.
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.data_loader_us import download_us_etfs, get_all_weather_us_etfs
from src.strategy_us import AllWeatherUS, AllWeatherConstrainedUS, AllWeather4QuadrantUS
from src.metrics import calculate_all_metrics

# Plotting style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 10)


def load_data():
    """Load US ETF data."""
    print("Loading US ETF data...")
    etf_info = get_all_weather_us_etfs()
    tickers = list(etf_info.keys())

    prices = download_us_etfs(
        tickers=tickers,
        start_date='2015-01-01',
        progress=False
    )

    print(f"✓ Loaded {len(prices)} days of data ({len(prices.columns)} ETFs)")
    print(f"  Period: {prices.index[0].date()} to {prices.index[-1].date()}\n")

    return prices


def run_version(name, strategy, start_date='2018-01-01'):
    """Run backtest for a strategy version."""
    print(f"\n{'='*70}")
    print(f"Running {name}...")
    print(f"{'='*70}")

    results = strategy.run_backtest(start_date=start_date)

    # Calculate metrics
    equity = results['equity_curve']
    returns = results['returns']
    metrics = results['metrics']

    # Calculate drawdown
    running_max = equity.expanding().max()
    drawdown = (equity - running_max) / running_max
    max_dd = drawdown.min()

    print(f"\nResults for {name}:")
    print(f"  Final Value: ${results['final_value']:,.0f}")
    print(f"  Total Return: {results['total_return']:.2%}")
    print(f"  Annual Return: {metrics['annual_return']:.2%}")
    print(f"  Annual Volatility: {metrics['annual_volatility']:.2%}")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {max_dd:.2%}")
    print(f"  Calmar Ratio: {metrics['calmar_ratio']:.2f}")

    return {
        'name': name,
        'equity': equity,
        'returns': returns,
        'drawdown': drawdown,
        'final_value': results['final_value'],
        'total_return': results['total_return'],
        'annual_return': metrics['annual_return'],
        'annual_volatility': metrics['annual_volatility'],
        'sharpe_ratio': metrics['sharpe_ratio'],
        'sortino_ratio': metrics['sortino_ratio'],
        'max_drawdown': max_dd,
        'calmar_ratio': metrics['calmar_ratio'],
        'win_rate': metrics['win_rate'],
        'rebalance_count': results['rebalance_count'],
        'total_commissions': results['total_commissions']
    }


def create_comparison_table(results_list):
    """Create comparison table."""
    comparison = pd.DataFrame({
        result['name']: [
            f"${result['final_value']:,.0f}",
            f"{result['total_return']:.2%}",
            f"{result['annual_return']:.2%}",
            f"{result['annual_volatility']:.2%}",
            f"{result['sharpe_ratio']:.2f}",
            f"{result['sortino_ratio']:.2f}",
            f"{result['max_drawdown']:.2%}",
            f"{result['calmar_ratio']:.2f}",
            f"{result['win_rate']:.2%}",
            f"{result['rebalance_count']}",
            f"${result['total_commissions']:,.0f}"
        ]
        for result in results_list
    }, index=[
        'Final Value',
        'Total Return',
        'Annual Return',
        'Annual Volatility',
        'Sharpe Ratio',
        'Sortino Ratio',
        'Max Drawdown',
        'Calmar Ratio',
        'Win Rate',
        'Rebalances',
        'Total Commissions'
    ])

    return comparison


def plot_comparison(results_list):
    """Plot comparison charts."""
    fig, axes = plt.subplots(3, 2, figsize=(16, 12))

    # 1. Equity curves
    ax = axes[0, 0]
    for result in results_list:
        ax.plot(result['equity'].index, result['equity'] / 1000,
               label=result['name'], linewidth=2, alpha=0.8)
    ax.set_title('Portfolio Value Over Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('Portfolio Value ($K)', fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 2. Drawdowns
    ax = axes[0, 1]
    for result in results_list:
        ax.plot(result['drawdown'].index, result['drawdown'] * 100,
               label=result['name'], linewidth=2, alpha=0.8)
    ax.axhline(-10, color='red', linestyle='--', label='Target (-10%)', alpha=0.7)
    ax.set_title('Drawdown Over Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('Drawdown (%)', fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 3. Returns comparison (bar chart)
    ax = axes[1, 0]
    names = [r['name'] for r in results_list]
    returns = [r['annual_return'] * 100 for r in results_list]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    bars = ax.bar(range(len(names)), returns, color=colors[:len(names)], alpha=0.7)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_title('Annual Return Comparison', fontsize=12, fontweight='bold')
    ax.set_ylabel('Annual Return (%)', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    # Add values on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}%', ha='center', va='bottom', fontsize=9)

    # 4. Max drawdown comparison (bar chart)
    ax = axes[1, 1]
    max_dds = [r['max_drawdown'] * 100 for r in results_list]
    bars = ax.bar(range(len(names)), max_dds, color=colors[:len(names)], alpha=0.7)
    ax.axhline(-10, color='red', linestyle='--', label='Target (-10%)', alpha=0.7)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_title('Max Drawdown Comparison', fontsize=12, fontweight='bold')
    ax.set_ylabel('Max Drawdown (%)', fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Add values on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}%', ha='center', va='top', fontsize=9)

    # 5. Sharpe ratio comparison
    ax = axes[2, 0]
    sharpes = [r['sharpe_ratio'] for r in results_list]
    bars = ax.bar(range(len(names)), sharpes, color=colors[:len(names)], alpha=0.7)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_title('Sharpe Ratio Comparison', fontsize=12, fontweight='bold')
    ax.set_ylabel('Sharpe Ratio', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    # Add values on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}', ha='center', va='bottom', fontsize=9)

    # 6. Risk-Return scatter
    ax = axes[2, 1]
    vols = [r['annual_volatility'] * 100 for r in results_list]
    rets = [r['annual_return'] * 100 for r in results_list]
    for i, result in enumerate(results_list):
        ax.scatter(vols[i], rets[i], s=200, color=colors[i], alpha=0.7,
                  label=result['name'])
        ax.annotate(result['name'], (vols[i], rets[i]),
                   xytext=(5, 5), textcoords='offset points', fontsize=8)
    ax.set_xlabel('Annual Volatility (%)', fontsize=10)
    ax.set_ylabel('Annual Return (%)', fontsize=10)
    ax.set_title('Risk-Return Profile', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('results/4quadrant_comparison.png', dpi=300, bbox_inches='tight')
    print("\n✓ Saved comparison chart to results/4quadrant_comparison.png")
    plt.show()


def main():
    """Main comparison workflow."""
    print("="*70)
    print("ALL WEATHER STRATEGY - 4-QUADRANT COMPARISON")
    print("="*70)
    print("\nGoal: Reduce max drawdown below -10%\n")

    # Load data
    prices = load_data()

    # Initialize strategies
    v1_1 = AllWeatherUS(
        prices=prices,
        initial_capital=100_000,
        rebalance_freq='W-MON',
        lookback=252,
        commission_rate=0.001,
        target_volatility=None
    )

    v1_2 = AllWeatherConstrainedUS(
        prices=prices,
        initial_capital=100_000,
        rebalance_freq='W-MON',
        lookback=252,
        commission_rate=0.001,
        target_volatility=None
    )

    v1_3 = AllWeather4QuadrantUS(
        prices=prices,
        initial_capital=100_000,
        rebalance_freq='W-MON',
        lookback=252,
        commission_rate=0.001,
        target_volatility=None
    )

    v1_3_vol = AllWeather4QuadrantUS(
        prices=prices,
        initial_capital=100_000,
        rebalance_freq='W-MON',
        lookback=252,
        commission_rate=0.001,
        target_volatility=0.038  # 3.8% target volatility (optimal)
    )

    # Run backtests
    results = []
    results.append(run_version("v1.1 Pure RP", v1_1))
    results.append(run_version("v1.2 Constrained RP", v1_2))
    results.append(run_version("v1.3 4-Quadrant", v1_3))
    results.append(run_version("v1.3 + Vol(3.8%)", v1_3_vol))

    # Create comparison table
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON")
    print("="*70)
    comparison_table = create_comparison_table(results)
    print(comparison_table)
    print("="*70)

    # Highlight which versions meet goal
    print("\n" + "="*70)
    print("MAX DRAWDOWN TARGET ANALYSIS")
    print("="*70)
    for result in results:
        status = "✓ PASS" if result['max_drawdown'] > -0.10 else "✗ FAIL"
        print(f"{result['name']:20} | Max DD: {result['max_drawdown']:7.2%} | {status}")
    print("="*70)

    # Plot comparison
    plot_comparison(results)

    # Save results
    comparison_table.to_csv('results/4quadrant_comparison.csv')
    print("\n✓ Saved comparison table to results/4quadrant_comparison.csv")

    print("\n" + "="*70)
    print("✓ Comparison complete!")
    print("="*70)


if __name__ == '__main__':
    main()
