"""
Enhanced vs Baseline Comparison

Compares the original v1.0 baseline with enhanced version featuring:
- Volatility targeting (6% target)
- Monthly rebalancing (vs weekly)
- Enhanced tail risk metrics
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.data_loader import load_prices
from src.strategy import AllWeatherV1
from src.metrics import format_metrics

# Configuration
START_DATE = '2018-01-01'
INITIAL_CAPITAL = 1_000_000

def run_comparison():
    """Run baseline vs enhanced comparison."""

    print("=" * 80)
    print("All Weather Strategy - Enhanced vs Baseline Comparison")
    print("=" * 80)

    # Load data
    print("\nLoading ETF data...")
    prices = load_prices('data/etf_prices_7etf.csv')
    print(f"Loaded {len(prices.columns)} ETFs from {prices.index[0].date()} to {prices.index[-1].date()}")

    # ===== BASELINE v1.0 (Original) =====
    print("\n" + "=" * 80)
    print("BASELINE v1.0 (Original)")
    print("=" * 80)
    print("Config: Weekly rebalancing, 100-day lookback, NO volatility targeting")

    baseline = AllWeatherV1(
        prices=prices,
        initial_capital=INITIAL_CAPITAL,
        rebalance_freq='W-MON',  # Weekly (original)
        lookback=100,
        commission_rate=0.0003,
        target_volatility=None  # No vol targeting (original)
    )

    baseline_results = baseline.run_backtest(start_date=START_DATE, verbose=True)
    baseline_metrics = baseline_results['metrics']

    print("\nBASELINE Performance:")
    print(format_metrics(baseline_metrics))
    print(f"\nFinal Value: ¥{baseline_results['final_value']:,.0f}")
    print(f"Total Return: {baseline_results['total_return']:.2%}")

    # ===== ENHANCED v1.0 =====
    print("\n" + "=" * 80)
    print("ENHANCED v1.0")
    print("=" * 80)
    print("Config: Monthly rebalancing, 100-day lookback, 6% volatility targeting")

    enhanced = AllWeatherV1(
        prices=prices,
        initial_capital=INITIAL_CAPITAL,
        rebalance_freq='MS',  # Monthly (enhanced)
        lookback=100,
        commission_rate=0.0003,
        target_volatility=0.06  # 6% target (enhanced)
    )

    enhanced_results = enhanced.run_backtest(start_date=START_DATE, verbose=True)
    enhanced_metrics = enhanced_results['metrics']

    print("\nENHANCED Performance:")
    print(format_metrics(enhanced_metrics))
    print(f"\nFinal Value: ¥{enhanced_results['final_value']:,.0f}")
    print(f"Total Return: {enhanced_results['total_return']:.2%}")

    # ===== COMPARISON =====
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)

    comparison = pd.DataFrame({
        'Baseline': [
            f"{baseline_metrics['annual_return']:.2%}",
            f"{baseline_metrics['annual_volatility']:.2%}",
            f"{baseline_metrics['sharpe_ratio']:.2f}",
            f"{baseline_metrics['sortino_ratio']:.2f}",
            f"{baseline_metrics['max_drawdown']:.2%}",
            f"{baseline_metrics['calmar_ratio']:.2f}",
            f"{baseline_metrics['win_rate']:.2%}",
            f"¥{baseline_results['final_value']:,.0f}"
        ],
        'Enhanced': [
            f"{enhanced_metrics['annual_return']:.2%}",
            f"{enhanced_metrics['annual_volatility']:.2%}",
            f"{enhanced_metrics['sharpe_ratio']:.2f}",
            f"{enhanced_metrics['sortino_ratio']:.2f}",
            f"{enhanced_metrics['max_drawdown']:.2%}",
            f"{enhanced_metrics['calmar_ratio']:.2f}",
            f"{enhanced_metrics['win_rate']:.2%}",
            f"¥{enhanced_results['final_value']:,.0f}"
        ],
        'Improvement': [
            f"{(enhanced_metrics['annual_return'] - baseline_metrics['annual_return']):.2%}",
            f"{(enhanced_metrics['annual_volatility'] - baseline_metrics['annual_volatility']):.2%}",
            f"{(enhanced_metrics['sharpe_ratio'] - baseline_metrics['sharpe_ratio']):.2f}",
            f"{(enhanced_metrics['sortino_ratio'] - baseline_metrics['sortino_ratio']):.2f}",
            f"{(enhanced_metrics['max_drawdown'] - baseline_metrics['max_drawdown']):.2%}",
            f"{(enhanced_metrics['calmar_ratio'] - baseline_metrics['calmar_ratio']):.2f}",
            f"{(enhanced_metrics['win_rate'] - baseline_metrics['win_rate']):.2%}",
            f"¥{(enhanced_results['final_value'] - baseline_results['final_value']):,.0f}"
        ]
    }, index=[
        'Annual Return',
        'Annual Volatility',
        'Sharpe Ratio',
        'Sortino Ratio',
        'Max Drawdown',
        'Calmar Ratio',
        'Win Rate',
        'Final Value'
    ])

    print(comparison)

    # ===== TAIL RISK COMPARISON =====
    print("\n" + "=" * 80)
    print("TAIL RISK COMPARISON")
    print("=" * 80)

    tail_comparison = pd.DataFrame({
        'Baseline': [
            f"{baseline_metrics['var_95']:.2%}",
            f"{baseline_metrics['var_99']:.2%}",
            f"{baseline_metrics['cvar_95']:.2%}",
            f"{baseline_metrics['cvar_99']:.2%}",
            f"{baseline_metrics['skewness']:.2f}",
            f"{baseline_metrics['kurtosis']:.2f}",
            f"{baseline_metrics['tail_ratio']:.2f}"
        ],
        'Enhanced': [
            f"{enhanced_metrics['var_95']:.2%}",
            f"{enhanced_metrics['var_99']:.2%}",
            f"{enhanced_metrics['cvar_95']:.2%}",
            f"{enhanced_metrics['cvar_99']:.2%}",
            f"{enhanced_metrics['skewness']:.2f}",
            f"{enhanced_metrics['kurtosis']:.2f}",
            f"{enhanced_metrics['tail_ratio']:.2f}"
        ]
    }, index=[
        'VaR (95%)',
        'VaR (99%)',
        'CVaR (95%)',
        'CVaR (99%)',
        'Skewness',
        'Kurtosis',
        'Tail Ratio'
    ])

    print(tail_comparison)

    # ===== VISUALIZATIONS =====
    create_comparison_charts(
        baseline_results['equity_curve'],
        enhanced_results['equity_curve'],
        baseline_results['weights_history'],
        enhanced_results['weights_history']
    )

    return baseline_results, enhanced_results


def create_comparison_charts(baseline_equity, enhanced_equity, baseline_weights, enhanced_weights):
    """Create comparison visualizations."""

    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # Plot 1: Equity Curves
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(baseline_equity.index, baseline_equity.values / 1_000_000,
             label='Baseline (Weekly, No Vol Target)', linewidth=2, color='#2E86AB')
    ax1.plot(enhanced_equity.index, enhanced_equity.values / 1_000_000,
             label='Enhanced (Monthly, 6% Vol Target)', linewidth=2, color='#A23B72')
    ax1.set_xlabel('Date', fontsize=11)
    ax1.set_ylabel('Portfolio Value (¥ Million)', fontsize=11)
    ax1.set_title('Equity Curve Comparison', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Plot 2: Drawdown Comparison
    ax2 = fig.add_subplot(gs[1, 0])
    baseline_dd = (baseline_equity / baseline_equity.expanding().max() - 1) * 100
    enhanced_dd = (enhanced_equity / enhanced_equity.expanding().max() - 1) * 100
    ax2.fill_between(baseline_dd.index, baseline_dd.values, 0,
                      alpha=0.3, color='#2E86AB', label='Baseline')
    ax2.fill_between(enhanced_dd.index, enhanced_dd.values, 0,
                      alpha=0.3, color='#A23B72', label='Enhanced')
    ax2.set_xlabel('Date', fontsize=11)
    ax2.set_ylabel('Drawdown (%)', fontsize=11)
    ax2.set_title('Drawdown Comparison', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    # Plot 3: Rolling Sharpe Ratio (252-day window)
    ax3 = fig.add_subplot(gs[1, 1])
    baseline_returns = baseline_equity.pct_change().dropna()
    enhanced_returns = enhanced_equity.pct_change().dropna()

    baseline_rolling_sharpe = (
        baseline_returns.rolling(252).mean() * 252 /
        (baseline_returns.rolling(252).std() * np.sqrt(252))
    )
    enhanced_rolling_sharpe = (
        enhanced_returns.rolling(252).mean() * 252 /
        (enhanced_returns.rolling(252).std() * np.sqrt(252))
    )

    ax3.plot(baseline_rolling_sharpe.index, baseline_rolling_sharpe.values,
             label='Baseline', linewidth=2, alpha=0.7, color='#2E86AB')
    ax3.plot(enhanced_rolling_sharpe.index, enhanced_rolling_sharpe.values,
             label='Enhanced', linewidth=2, alpha=0.7, color='#A23B72')
    ax3.set_xlabel('Date', fontsize=11)
    ax3.set_ylabel('Rolling Sharpe Ratio', fontsize=11)
    ax3.set_title('Rolling Sharpe Ratio (252-day)', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='black', linestyle='--', linewidth=0.5)

    # Plot 4: Baseline Allocation
    ax4 = fig.add_subplot(gs[2, 0])
    if not baseline_weights.empty:
        baseline_weights_pct = baseline_weights * 100
        ax4.stackplot(baseline_weights_pct.index,
                      *[baseline_weights_pct[col].values for col in baseline_weights_pct.columns],
                      labels=baseline_weights_pct.columns,
                      alpha=0.8)
    ax4.set_xlabel('Date', fontsize=11)
    ax4.set_ylabel('Allocation (%)', fontsize=11)
    ax4.set_title('Baseline Allocation (Weekly Rebalance)', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper left', fontsize=8)
    ax4.set_ylim(0, 100)
    ax4.grid(True, alpha=0.3)

    # Plot 5: Enhanced Allocation
    ax5 = fig.add_subplot(gs[2, 1])
    if not enhanced_weights.empty:
        enhanced_weights_pct = enhanced_weights * 100
        ax5.stackplot(enhanced_weights_pct.index,
                      *[enhanced_weights_pct[col].values for col in enhanced_weights_pct.columns],
                      labels=enhanced_weights_pct.columns,
                      alpha=0.8)
    ax5.set_xlabel('Date', fontsize=11)
    ax5.set_ylabel('Allocation (%)', fontsize=11)
    ax5.set_title('Enhanced Allocation (Monthly Rebalance)', fontsize=12, fontweight='bold')
    ax5.legend(loc='upper left', fontsize=8)
    ax5.set_ylim(0, 100)
    ax5.grid(True, alpha=0.3)

    plt.suptitle('All Weather Strategy: Enhanced vs Baseline', fontsize=16, fontweight='bold', y=0.995)
    plt.savefig('enhanced_vs_baseline_comparison.png', dpi=300, bbox_inches='tight')
    print(f"\nComparison charts saved to: enhanced_vs_baseline_comparison.png")
    plt.show()


if __name__ == '__main__':
    baseline_results, enhanced_results = run_comparison()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    improvement = (enhanced_results['final_value'] - baseline_results['final_value']) / baseline_results['final_value']
    print(f"\nEnhanced strategy improved portfolio value by {improvement:.2%}")

    print("\nKey Enhancements:")
    print("  1. Volatility targeting (6% annualized)")
    print("  2. Monthly rebalancing (reduced transaction costs)")
    print("  3. Enhanced tail risk metrics (VaR, CVaR, skewness, kurtosis)")
    print("\nRisk Parity: Maintained (uniform scaling preserves equal risk contributions)")
    print("=" * 80)
