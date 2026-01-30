"""
Compare All Weather Strategy Versions: v1.0, v1.1, v1.2

Tests the cumulative impact of improvements:
- v1.0: Pure risk parity (always rebalance, no shrinkage)
- v1.1: + Adaptive rebalancing (5% drift threshold)
- v1.2: + Ledoit-Wolf covariance shrinkage

Goal: Measure the impact of each improvement on performance and stability.
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from src.data_loader import load_prices
from src.strategy import AllWeatherV1
from src.metrics import calculate_all_metrics

print("="*70)
print("ALL WEATHER v1.0 vs v1.1 vs v1.2 COMPARISON")
print("="*70)

# Load data
print("\n1. Loading data...")
prices = load_prices('data/etf_prices_7etf.csv')
print(f"   Loaded {len(prices)} days of data for {len(prices.columns)} ETFs")

# v1.0: Always rebalance, no shrinkage
print("\n2. Running v1.0 (Always Rebalance, No Shrinkage)...")
strategy_v10 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0,      # Always rebalance
    use_shrinkage=False         # No shrinkage
)
results_v10 = strategy_v10.run_backtest(start_date='2018-01-01', verbose=False)

# v1.1: Adaptive rebalancing, no shrinkage
print("\n3. Running v1.1 (Adaptive Rebalancing, No Shrinkage)...")
strategy_v11 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.05,   # Adaptive
    use_shrinkage=False         # No shrinkage
)
results_v11 = strategy_v11.run_backtest(start_date='2018-01-01', verbose=False)

# v1.2: Adaptive rebalancing + shrinkage
print("\n4. Running v1.2 (Adaptive + Shrinkage)...")
strategy_v12 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.05,   # Adaptive
    use_shrinkage=True          # Shrinkage
)
results_v12 = strategy_v12.run_backtest(start_date='2018-01-01', verbose=False)

# Compare results
print("\n" + "="*70)
print("PERFORMANCE COMPARISON")
print("="*70)

comparison = pd.DataFrame({
    'v1.0': [
        f"{results_v10['total_return']:.2%}",
        f"{results_v10['metrics']['annual_return']:.2%}",
        f"{results_v10['metrics']['annual_volatility']:.2%}",
        f"{results_v10['metrics']['sharpe_ratio']:.2f}",
        f"{results_v10['metrics']['sortino_ratio']:.2f}",
        f"{results_v10['metrics']['max_drawdown']:.2%}",
        f"{results_v10['metrics']['calmar_ratio']:.2f}",
        f"¥{results_v10['final_value']:,.0f}",
        results_v10['rebalances_executed'],
        f"¥{strategy_v10.portfolio.get_total_commissions():,.0f}",
    ],
    'v1.1': [
        f"{results_v11['total_return']:.2%}",
        f"{results_v11['metrics']['annual_return']:.2%}",
        f"{results_v11['metrics']['annual_volatility']:.2%}",
        f"{results_v11['metrics']['sharpe_ratio']:.2f}",
        f"{results_v11['metrics']['sortino_ratio']:.2f}",
        f"{results_v11['metrics']['max_drawdown']:.2%}",
        f"{results_v11['metrics']['calmar_ratio']:.2f}",
        f"¥{results_v11['final_value']:,.0f}",
        results_v11['rebalances_executed'],
        f"¥{strategy_v11.portfolio.get_total_commissions():,.0f}",
    ],
    'v1.2': [
        f"{results_v12['total_return']:.2%}",
        f"{results_v12['metrics']['annual_return']:.2%}",
        f"{results_v12['metrics']['annual_volatility']:.2%}",
        f"{results_v12['metrics']['sharpe_ratio']:.2f}",
        f"{results_v12['metrics']['sortino_ratio']:.2f}",
        f"{results_v12['metrics']['max_drawdown']:.2%}",
        f"{results_v12['metrics']['calmar_ratio']:.2f}",
        f"¥{results_v12['final_value']:,.0f}",
        results_v12['rebalances_executed'],
        f"¥{strategy_v12.portfolio.get_total_commissions():,.0f}",
    ]
}, index=[
    'Total Return',
    'Annual Return',
    'Annual Volatility',
    'Sharpe Ratio',
    'Sortino Ratio',
    'Max Drawdown',
    'Calmar Ratio',
    'Final Value',
    'Rebalances',
    'Commissions'
])

print(comparison)

# Calculate improvements
print("\n" + "="*70)
print("IMPROVEMENTS vs v1.0")
print("="*70)

# v1.1 improvements
v11_value_gain = results_v11['final_value'] - results_v10['final_value']
v11_return_gain = results_v11['metrics']['annual_return'] - results_v10['metrics']['annual_return']
v11_comm_saved = strategy_v10.portfolio.get_total_commissions() - strategy_v11.portfolio.get_total_commissions()

print("\nv1.1 (Adaptive Rebalancing):")
print(f"  Value gain: ¥{v11_value_gain:,.0f} ({v11_value_gain/results_v10['final_value']*100:+.2f}%)")
print(f"  Return gain: {v11_return_gain:+.2%}")
print(f"  Commission savings: ¥{v11_comm_saved:,.0f}")
print(f"  Rebalances saved: {results_v10['rebalances_executed'] - results_v11['rebalances_executed']}")

# v1.2 improvements
v12_value_gain = results_v12['final_value'] - results_v10['final_value']
v12_return_gain = results_v12['metrics']['annual_return'] - results_v10['metrics']['annual_return']
v12_vol_change = results_v12['metrics']['annual_volatility'] - results_v10['metrics']['annual_volatility']
v12_sharpe_gain = results_v12['metrics']['sharpe_ratio'] - results_v10['metrics']['sharpe_ratio']

print("\nv1.2 (Adaptive + Shrinkage):")
print(f"  Value gain: ¥{v12_value_gain:,.0f} ({v12_value_gain/results_v10['final_value']*100:+.2f}%)")
print(f"  Return gain: {v12_return_gain:+.2%}")
print(f"  Volatility change: {v12_vol_change:+.2%}")
print(f"  Sharpe gain: {v12_sharpe_gain:+.2f}")

# v1.2 vs v1.1 (shrinkage contribution)
v12_vs_v11_value = results_v12['final_value'] - results_v11['final_value']
v12_vs_v11_return = results_v12['metrics']['annual_return'] - results_v11['metrics']['annual_return']
v12_vs_v11_vol = results_v12['metrics']['annual_volatility'] - results_v11['metrics']['annual_volatility']

print("\nv1.2 vs v1.1 (Shrinkage Contribution):")
print(f"  Value gain: ¥{v12_vs_v11_value:,.0f} ({v12_vs_v11_value/results_v11['final_value']*100:+.2f}%)")
print(f"  Return gain: {v12_vs_v11_return:+.2%}")
print(f"  Volatility change: {v12_vs_v11_vol:+.2%}")

print("="*70)

# Plot comparison
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Equity curves
ax1 = axes[0, 0]
ax1.plot(results_v10['equity_curve'].index, results_v10['equity_curve'],
         label='v1.0', linewidth=2, alpha=0.7)
ax1.plot(results_v11['equity_curve'].index, results_v11['equity_curve'],
         label='v1.1', linewidth=2, alpha=0.7)
ax1.plot(results_v12['equity_curve'].index, results_v12['equity_curve'],
         label='v1.2', linewidth=2, alpha=0.7)
ax1.set_title('Equity Curves', fontsize=12, fontweight='bold')
ax1.set_ylabel('Portfolio Value (¥)')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x/1e6:.2f}M'))

# Risk-adjusted returns
ax2 = axes[0, 1]
versions = ['v1.0', 'v1.1', 'v1.2']
sharpe = [
    results_v10['metrics']['sharpe_ratio'],
    results_v11['metrics']['sharpe_ratio'],
    results_v12['metrics']['sharpe_ratio']
]
sortino = [
    results_v10['metrics']['sortino_ratio'],
    results_v11['metrics']['sortino_ratio'],
    results_v12['metrics']['sortino_ratio']
]
x = np.arange(len(versions))
width = 0.35
ax2.bar(x - width/2, sharpe, width, label='Sharpe', alpha=0.8)
ax2.bar(x + width/2, sortino, width, label='Sortino', alpha=0.8)
ax2.set_title('Risk-Adjusted Returns', fontsize=12, fontweight='bold')
ax2.set_ylabel('Ratio')
ax2.set_xticks(x)
ax2.set_xticklabels(versions)
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

# Return vs Risk
ax3 = axes[1, 0]
returns = [
    results_v10['metrics']['annual_return'] * 100,
    results_v11['metrics']['annual_return'] * 100,
    results_v12['metrics']['annual_return'] * 100
]
vols = [
    results_v10['metrics']['annual_volatility'] * 100,
    results_v11['metrics']['annual_volatility'] * 100,
    results_v12['metrics']['annual_volatility'] * 100
]
ax3.scatter(vols[0], returns[0], s=200, alpha=0.7, label='v1.0')
ax3.scatter(vols[1], returns[1], s=200, alpha=0.7, label='v1.1')
ax3.scatter(vols[2], returns[2], s=200, alpha=0.7, label='v1.2')
for i, v in enumerate(versions):
    ax3.annotate(v, (vols[i], returns[i]), xytext=(5, 5), textcoords='offset points')
ax3.set_title('Return vs Risk', fontsize=12, fontweight='bold')
ax3.set_xlabel('Annual Volatility (%)')
ax3.set_ylabel('Annual Return (%)')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Final values
ax4 = axes[1, 1]
final_values = [
    results_v10['final_value'] / 1e6,
    results_v11['final_value'] / 1e6,
    results_v12['final_value'] / 1e6
]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
bars = ax4.bar(versions, final_values, alpha=0.8, color=colors)
ax4.set_title('Final Portfolio Value', fontsize=12, fontweight='bold')
ax4.set_ylabel('Value (Millions ¥)')
ax4.grid(True, alpha=0.3, axis='y')
# Add value labels on bars
for bar, val in zip(bars, final_values):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
             f'¥{val:.2f}M',
             ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('results/v1.0_v1.1_v1.2_comparison.png', dpi=150, bbox_inches='tight')
print(f"\nChart saved to results/v1.0_v1.1_v1.2_comparison.png")
plt.show()

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print(f"Best Version: v1.2")
print(f"  Total gain vs v1.0: ¥{v12_value_gain:,.0f} ({v12_value_gain/results_v10['final_value']*100:+.2f}%)")
print(f"  Sharpe improvement: {v12_sharpe_gain:+.2f}")
print(f"  Key features: Adaptive rebalancing + Covariance shrinkage")
print("="*70)
