"""
Lookback Period Optimization Script

Tests different covariance estimation windows to find optimal lookback period.
Evaluates based on Sharpe ratio, returns, and drawdown.
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.data_loader import load_prices
from src.strategy import AllWeatherV1

# Configuration
LOOKBACK_PERIODS = [60, 80, 100, 120, 150, 200, 252]
TARGET_VOLATILITY = 0.06  # 6% target (matching Dalio)
REBALANCE_FREQ = 'MS'  # Monthly
START_DATE = '2018-01-01'

def run_lookback_sensitivity():
    """Run backtest for each lookback period and compare results."""

    print("=" * 70)
    print("All Weather Strategy - Lookback Period Optimization")
    print("=" * 70)

    # Load data
    print("\nLoading ETF data...")
    prices = load_prices('data/etf_prices_7etf.csv')
    print(f"Loaded {len(prices.columns)} ETFs from {prices.index[0].date()} to {prices.index[-1].date()}")

    results = []

    for lookback in LOOKBACK_PERIODS:
        print(f"\n{'-' * 70}")
        print(f"Testing lookback = {lookback} days")
        print(f"{'-' * 70}")

        try:
            # Run strategy with this lookback period
            strategy = AllWeatherV1(
                prices=prices,
                initial_capital=1_000_000,
                rebalance_freq=REBALANCE_FREQ,
                lookback=lookback,
                commission_rate=0.0003,
                target_volatility=TARGET_VOLATILITY
            )

            backtest_results = strategy.run_backtest(
                start_date=START_DATE,
                verbose=False
            )

            metrics = backtest_results['metrics']

            # Store results
            results.append({
                'lookback': lookback,
                'annual_return': metrics['annual_return'],
                'annual_volatility': metrics['annual_volatility'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'sortino_ratio': metrics['sortino_ratio'],
                'max_drawdown': metrics['max_drawdown'],
                'calmar_ratio': metrics['calmar_ratio'],
                'win_rate': metrics['win_rate'],
                'final_value': backtest_results['final_value']
            })

            print(f"Annual Return:    {metrics['annual_return']:.2%}")
            print(f"Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
            print(f"Max Drawdown:     {metrics['max_drawdown']:.2%}")
            print(f"Final Value:      ¥{backtest_results['final_value']:,.0f}")

        except Exception as e:
            print(f"Error with lookback={lookback}: {e}")
            continue

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    # Find optimal based on different criteria
    print("\n" + "=" * 70)
    print("OPTIMIZATION RESULTS")
    print("=" * 70)

    print("\nComplete Results:")
    print(results_df.to_string(index=False))

    print("\n" + "-" * 70)
    print("OPTIMAL PARAMETERS")
    print("-" * 70)

    optimal_sharpe = results_df.loc[results_df['sharpe_ratio'].idxmax()]
    optimal_return = results_df.loc[results_df['annual_return'].idxmax()]
    optimal_calmar = results_df.loc[results_df['calmar_ratio'].idxmax()]

    print(f"\nBest Sharpe Ratio:  lookback = {optimal_sharpe['lookback']:.0f} days")
    print(f"  → Sharpe: {optimal_sharpe['sharpe_ratio']:.2f}")
    print(f"  → Return: {optimal_sharpe['annual_return']:.2%}")
    print(f"  → Max DD: {optimal_sharpe['max_drawdown']:.2%}")

    print(f"\nBest Annual Return: lookback = {optimal_return['lookback']:.0f} days")
    print(f"  → Return: {optimal_return['annual_return']:.2%}")
    print(f"  → Sharpe: {optimal_return['sharpe_ratio']:.2f}")
    print(f"  → Max DD: {optimal_return['max_drawdown']:.2%}")

    print(f"\nBest Calmar Ratio:  lookback = {optimal_calmar['lookback']:.0f} days")
    print(f"  → Calmar: {optimal_calmar['calmar_ratio']:.2f}")
    print(f"  → Return: {optimal_calmar['annual_return']:.2%}")
    print(f"  → Max DD: {optimal_calmar['max_drawdown']:.2%}")

    # Recommended lookback (based on Sharpe ratio)
    recommended = int(optimal_sharpe['lookback'])
    print(f"\n{'*' * 70}")
    print(f"RECOMMENDED LOOKBACK: {recommended} days (best Sharpe ratio)")
    print(f"{'*' * 70}")

    # Create visualization
    create_visualization(results_df)

    return results_df, recommended


def create_visualization(results_df):
    """Create charts comparing different lookback periods."""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Lookback Period Sensitivity Analysis', fontsize=16, fontweight='bold')

    # Plot 1: Annual Return
    ax1 = axes[0, 0]
    ax1.plot(results_df['lookback'], results_df['annual_return'] * 100,
             marker='o', linewidth=2, markersize=8, color='#2E86AB')
    ax1.set_xlabel('Lookback Period (days)', fontsize=11)
    ax1.set_ylabel('Annual Return (%)', fontsize=11)
    ax1.set_title('Annual Return vs Lookback Period', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    best_return_idx = results_df['annual_return'].idxmax()
    ax1.axvline(results_df.loc[best_return_idx, 'lookback'],
                color='red', linestyle='--', alpha=0.5, label='Best')
    ax1.legend()

    # Plot 2: Sharpe Ratio
    ax2 = axes[0, 1]
    ax2.plot(results_df['lookback'], results_df['sharpe_ratio'],
             marker='o', linewidth=2, markersize=8, color='#A23B72')
    ax2.set_xlabel('Lookback Period (days)', fontsize=11)
    ax2.set_ylabel('Sharpe Ratio', fontsize=11)
    ax2.set_title('Sharpe Ratio vs Lookback Period', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    best_sharpe_idx = results_df['sharpe_ratio'].idxmax()
    ax2.axvline(results_df.loc[best_sharpe_idx, 'lookback'],
                color='red', linestyle='--', alpha=0.5, label='Best')
    ax2.legend()

    # Plot 3: Max Drawdown
    ax3 = axes[1, 0]
    ax3.plot(results_df['lookback'], results_df['max_drawdown'] * 100,
             marker='o', linewidth=2, markersize=8, color='#F18F01')
    ax3.set_xlabel('Lookback Period (days)', fontsize=11)
    ax3.set_ylabel('Max Drawdown (%)', fontsize=11)
    ax3.set_title('Max Drawdown vs Lookback Period', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.axhline(0, color='black', linewidth=0.5)

    # Plot 4: Calmar Ratio
    ax4 = axes[1, 1]
    ax4.plot(results_df['lookback'], results_df['calmar_ratio'],
             marker='o', linewidth=2, markersize=8, color='#6A994E')
    ax4.set_xlabel('Lookback Period (days)', fontsize=11)
    ax4.set_ylabel('Calmar Ratio', fontsize=11)
    ax4.set_title('Calmar Ratio vs Lookback Period', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    best_calmar_idx = results_df['calmar_ratio'].idxmax()
    ax4.axvline(results_df.loc[best_calmar_idx, 'lookback'],
                color='red', linestyle='--', alpha=0.5, label='Best')
    ax4.legend()

    plt.tight_layout()
    plt.savefig('lookback_optimization.png', dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved to: lookback_optimization.png")
    plt.show()


if __name__ == '__main__':
    results_df, recommended_lookback = run_lookback_sensitivity()

    print("\n" + "=" * 70)
    print("Analysis complete!")
    print(f"Use lookback={recommended_lookback} for optimal Sharpe ratio")
    print("=" * 70)
