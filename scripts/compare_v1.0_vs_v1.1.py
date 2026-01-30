"""
Compare v1.0 (always rebalance) vs v1.1 (adaptive rebalancing)

Tests the impact of adaptive rebalancing on transaction costs and performance.
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

from src.data_loader import load_prices
from src.strategy import AllWeatherV1
from src.metrics import calculate_all_metrics

print("="*70)
print("ALL WEATHER v1.0 vs v1.1 COMPARISON")
print("="*70)

# Load data
print("\n1. Loading data...")
prices = load_prices('data/etf_prices_7etf.csv')
print(f"   Loaded {len(prices)} days of data for {len(prices.columns)} ETFs")

# v1.0: Always rebalance (threshold=0)
print("\n2. Running v1.0 (Always Rebalance)...")
strategy_v10 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0  # v1.0 behavior
)

results_v10 = strategy_v10.run_backtest(start_date='2018-01-01', verbose=False)

# v1.1: Adaptive rebalancing (threshold=0.05)
print("\n3. Running v1.1 (Adaptive Rebalancing, threshold=5%)...")
strategy_v11 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.05  # v1.1 default
)

results_v11 = strategy_v11.run_backtest(start_date='2018-01-01', verbose=False)

# Compare results
print("\n" + "="*70)
print("PERFORMANCE COMPARISON")
print("="*70)

comparison = pd.DataFrame({
    'v1.0 (Always)': [
        f"{results_v10['total_return']:.2%}",
        f"{results_v10['metrics']['annual_return']:.2%}",
        f"{results_v10['metrics']['annual_volatility']:.2%}",
        f"{results_v10['metrics']['sharpe_ratio']:.2f}",
        f"{results_v10['metrics']['max_drawdown']:.2%}",
        f"¥{results_v10['final_value']:,.0f}",
        results_v10['rebalances_executed'],
        results_v10['rebalances_skipped'],
        f"¥{strategy_v10.portfolio.get_total_commissions():,.0f}",
        strategy_v10.portfolio.get_trade_count(),
    ],
    'v1.1 (Adaptive)': [
        f"{results_v11['total_return']:.2%}",
        f"{results_v11['metrics']['annual_return']:.2%}",
        f"{results_v11['metrics']['annual_volatility']:.2%}",
        f"{results_v11['metrics']['sharpe_ratio']:.2f}",
        f"{results_v11['metrics']['max_drawdown']:.2%}",
        f"¥{results_v11['final_value']:,.0f}",
        results_v11['rebalances_executed'],
        results_v11['rebalances_skipped'],
        f"¥{strategy_v11.portfolio.get_total_commissions():,.0f}",
        strategy_v11.portfolio.get_trade_count(),
    ]
}, index=[
    'Total Return',
    'Annual Return',
    'Annual Volatility',
    'Sharpe Ratio',
    'Max Drawdown',
    'Final Value',
    'Rebalances Executed',
    'Rebalances Skipped',
    'Total Commissions',
    'Total Trades'
])

print(comparison)

# Calculate savings
commission_v10 = strategy_v10.portfolio.get_total_commissions()
commission_v11 = strategy_v11.portfolio.get_total_commissions()
commission_saved = commission_v10 - commission_v11
commission_pct_saved = (commission_saved / commission_v10) * 100 if commission_v10 > 0 else 0

value_diff = results_v11['final_value'] - results_v10['final_value']
return_diff = results_v11['metrics']['annual_return'] - results_v10['metrics']['annual_return']

print("\n" + "="*70)
print("IMPROVEMENTS")
print("="*70)
print(f"Commission Savings:     ¥{commission_saved:,.0f} ({commission_pct_saved:.1f}%)")
print(f"Rebalances Reduced:     {results_v10['rebalances_executed'] - results_v11['rebalances_executed']} "
      f"({(results_v10['rebalances_executed'] - results_v11['rebalances_executed']) / results_v10['rebalances_executed'] * 100:.1f}%)")
print(f"Final Value Difference: ¥{value_diff:,.0f}")
print(f"Annual Return Gain:     {return_diff:.2%}")
print("="*70)

# Plot comparison
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Equity curves
ax1 = axes[0, 0]
ax1.plot(results_v10['equity_curve'].index, results_v10['equity_curve'],
         label='v1.0 (Always)', linewidth=2, alpha=0.8)
ax1.plot(results_v11['equity_curve'].index, results_v11['equity_curve'],
         label='v1.1 (Adaptive)', linewidth=2, alpha=0.8)
ax1.set_title('Equity Curves', fontsize=12, fontweight='bold')
ax1.set_ylabel('Portfolio Value (¥)')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x/1e6:.2f}M'))

# Cumulative commissions
ax2 = axes[0, 1]
trades_v10 = strategy_v10.portfolio.trade_history
trades_v11 = strategy_v11.portfolio.trade_history
cum_comm_v10 = np.cumsum([t.commission for t in trades_v10])
cum_comm_v11 = np.cumsum([t.commission for t in trades_v11])
ax2.plot(range(len(cum_comm_v10)), cum_comm_v10, label='v1.0 (Always)', linewidth=2, alpha=0.8)
ax2.plot(range(len(cum_comm_v11)), cum_comm_v11, label='v1.1 (Adaptive)', linewidth=2, alpha=0.8)
ax2.set_title('Cumulative Commissions', fontsize=12, fontweight='bold')
ax2.set_xlabel('Trade Number')
ax2.set_ylabel('Cumulative Commission (¥)')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Rebalance counts
ax3 = axes[1, 0]
versions = ['v1.0\n(Always)', 'v1.1\n(Adaptive)']
executed = [results_v10['rebalances_executed'], results_v11['rebalances_executed']]
skipped = [results_v10['rebalances_skipped'], results_v11['rebalances_skipped']]
x = np.arange(len(versions))
width = 0.35
ax3.bar(x - width/2, executed, width, label='Executed', alpha=0.8)
ax3.bar(x + width/2, skipped, width, label='Skipped', alpha=0.8)
ax3.set_title('Rebalancing Activity', fontsize=12, fontweight='bold')
ax3.set_ylabel('Count')
ax3.set_xticks(x)
ax3.set_xticklabels(versions)
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')

# Performance metrics
ax4 = axes[1, 1]
metrics_labels = ['Annual\nReturn', 'Sharpe\nRatio', 'Max DD\n(abs)', 'Final Value\n(millions)']
v10_metrics = [
    results_v10['metrics']['annual_return'] * 100,
    results_v10['metrics']['sharpe_ratio'],
    abs(results_v10['metrics']['max_drawdown']) * 100,
    results_v10['final_value'] / 1e6
]
v11_metrics = [
    results_v11['metrics']['annual_return'] * 100,
    results_v11['metrics']['sharpe_ratio'],
    abs(results_v11['metrics']['max_drawdown']) * 100,
    results_v11['final_value'] / 1e6
]
x = np.arange(len(metrics_labels))
width = 0.35
ax4.bar(x - width/2, v10_metrics, width, label='v1.0', alpha=0.8)
ax4.bar(x + width/2, v11_metrics, width, label='v1.1', alpha=0.8)
ax4.set_title('Performance Metrics Comparison', fontsize=12, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(metrics_labels, fontsize=9)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('results/v1.0_vs_v1.1_comparison.png', dpi=150, bbox_inches='tight')
print(f"\nChart saved to results/v1.0_vs_v1.1_comparison.png")
plt.show()

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
if value_diff > 0:
    print(f"✓ v1.1 outperforms v1.0 by ¥{value_diff:,.0f}")
    print(f"✓ Commission savings: ¥{commission_saved:,.0f} ({commission_pct_saved:.1f}%)")
    print(f"✓ {results_v11['rebalances_skipped']} unnecessary rebalances avoided")
else:
    print(f"v1.0 and v1.1 perform similarly")
    print(f"Commission savings: ¥{commission_saved:,.0f}")

print("="*70)
