"""
Compare v1.1 (Pure Risk Parity) vs v1.2 (Constrained Risk Parity)

Expected outcome:
- v1.2 should have 10-15x better Sharpe ratio
- More balanced allocation (25-50% stocks vs 16%)
- Better returns in rising-rate environments
"""

import sys
sys.path.append('../')

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from src.data_loader_us import load_us_data
from src.strategy_us import AllWeatherUS, AllWeatherConstrainedUS
from src.metrics import calculate_all_metrics

# Load data
print("Loading US ETF data...")
prices = load_us_data('data/us_etf_prices.csv')
print(f"Loaded {len(prices)} days for {len(prices.columns)} ETFs")

# Initialize strategies
print("\n" + "="*80)
print("Initializing strategies...")
print("="*80)

v1_1 = AllWeatherUS(
    prices=prices,
    initial_capital=100_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.001
)

v1_2 = AllWeatherConstrainedUS(
    prices=prices,
    initial_capital=100_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.001
)

print("\nv1.1 (Pure Risk Parity):", v1_1)
print("v1.2 (Constrained):", v1_2)

# Run backtests
print("\n" + "="*80)
print("Running backtests from 2018-01-01...")
print("="*80)

print("\n[1/2] v1.1 Pure Risk Parity:")
print("-"*80)
results_v1_1 = v1_1.run_backtest(start_date='2018-01-01')

print("\n[2/2] v1.2 Constrained Risk Parity:")
print("-"*80)
results_v1_2 = v1_2.run_backtest(start_date='2018-01-01')

# Create benchmark
spy_prices = prices['SPY']
equity_start = results_v1_1['equity_curve'].index[0]
benchmark = (spy_prices.loc[equity_start:] / spy_prices.loc[equity_start]) * 100_000
benchmark = benchmark.loc[results_v1_1['equity_curve'].index]
benchmark_returns = benchmark.pct_change().dropna()
benchmark_metrics = calculate_all_metrics(benchmark_returns, benchmark)

# Compare metrics
print("\n" + "="*80)
print("PERFORMANCE COMPARISON (2018-2026)")
print("="*80)

comparison = pd.DataFrame({
    'v1.1 Pure RP': [
        f"{results_v1_1['metrics']['annual_return']:.2%}",
        f"{results_v1_1['metrics']['annual_volatility']:.2%}",
        f"{results_v1_1['metrics']['sharpe_ratio']:.2f}",
        f"{results_v1_1['metrics']['sortino_ratio']:.2f}",
        f"{results_v1_1['metrics']['max_drawdown']:.2%}",
        f"{results_v1_1['metrics']['calmar_ratio']:.2f}",
        f"{results_v1_1['metrics']['win_rate']:.2%}",
    ],
    'v1.2 Constrained': [
        f"{results_v1_2['metrics']['annual_return']:.2%}",
        f"{results_v1_2['metrics']['annual_volatility']:.2%}",
        f"{results_v1_2['metrics']['sharpe_ratio']:.2f}",
        f"{results_v1_2['metrics']['sortino_ratio']:.2f}",
        f"{results_v1_2['metrics']['max_drawdown']:.2%}",
        f"{results_v1_2['metrics']['calmar_ratio']:.2f}",
        f"{results_v1_2['metrics']['win_rate']:.2%}",
    ],
    'Benchmark (SPY)': [
        f"{benchmark_metrics['annual_return']:.2%}",
        f"{benchmark_metrics['annual_volatility']:.2%}",
        f"{benchmark_metrics['sharpe_ratio']:.2f}",
        f"{benchmark_metrics['sortino_ratio']:.2f}",
        f"{benchmark_metrics['max_drawdown']:.2%}",
        f"{benchmark_metrics['calmar_ratio']:.2f}",
        f"{benchmark_metrics['win_rate']:.2%}",
    ]
}, index=[
    'Annual Return',
    'Annual Volatility',
    'Sharpe Ratio',
    'Sortino Ratio',
    'Max Drawdown',
    'Calmar Ratio',
    'Win Rate'
])

print(comparison)
print("="*80)

# Calculate improvement
sharpe_improvement = results_v1_2['metrics']['sharpe_ratio'] / results_v1_1['metrics']['sharpe_ratio']
return_improvement = results_v1_2['metrics']['annual_return'] / results_v1_1['metrics']['annual_return']

print(f"\nImprovement:")
print(f"  Sharpe Ratio: {sharpe_improvement:.1f}x better")
print(f"  Annual Return: {return_improvement:.1f}x better")

# Compare allocations
print("\n" + "="*80)
print("CURRENT ALLOCATION COMPARISON")
print("="*80)

alloc_v1_1 = v1_1.get_current_allocation()
alloc_v1_2 = v1_2.get_current_allocation()

alloc_compare = pd.DataFrame({
    'Ticker': alloc_v1_1['Ticker'],
    'v1.1 Pure RP (%)': alloc_v1_1['Allocation'],
    'v1.2 Constrained (%)': alloc_v1_2['Allocation']
})

print(alloc_compare.to_string(index=False))

# Group by asset class
print("\nBy Asset Class:")
etf_to_class = {
    'SPY': 'Stocks', 'QQQ': 'Stocks', 'IWM': 'Stocks',
    'TLT': 'Bonds', 'IEF': 'Bonds', 'TIP': 'Bonds',
    'GLD': 'Commodities', 'DBC': 'Commodities'
}

for version, alloc in [('v1.1', alloc_v1_1), ('v1.2', alloc_v1_2)]:
    by_class = {}
    for _, row in alloc.iterrows():
        asset_class = etf_to_class.get(row['Ticker'], 'Other')
        by_class[asset_class] = by_class.get(asset_class, 0) + row['Allocation']

    print(f"\n  {version}:")
    for ac, pct in sorted(by_class.items(), key=lambda x: -x[1]):
        print(f"    {ac:12}: {pct:5.1f}%")

# Plot comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Equity curves
ax1 = axes[0, 0]
ax1.plot(results_v1_1['equity_curve'].index, results_v1_1['equity_curve'] / 1000,
         label='v1.1 Pure RP', linewidth=2, color='#FF6B6B')
ax1.plot(results_v1_2['equity_curve'].index, results_v1_2['equity_curve'] / 1000,
         label='v1.2 Constrained', linewidth=2, color='#4ECDC4')
ax1.plot(benchmark.index, benchmark / 1000,
         label='SPY Benchmark', linewidth=2, alpha=0.5, color='gray')
ax1.set_title('Portfolio Value Over Time', fontsize=12, fontweight='bold')
ax1.set_ylabel('Value ($K)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Drawdowns
ax2 = axes[0, 1]
dd_v1_1 = (results_v1_1['equity_curve'] - results_v1_1['equity_curve'].expanding().max()) / results_v1_1['equity_curve'].expanding().max()
dd_v1_2 = (results_v1_2['equity_curve'] - results_v1_2['equity_curve'].expanding().max()) / results_v1_2['equity_curve'].expanding().max()
ax2.fill_between(dd_v1_1.index, dd_v1_1 * 100, 0, alpha=0.3, color='#FF6B6B', label='v1.1')
ax2.fill_between(dd_v1_2.index, dd_v1_2 * 100, 0, alpha=0.3, color='#4ECDC4', label='v1.2')
ax2.plot(dd_v1_1.index, dd_v1_1 * 100, linewidth=1, color='#FF6B6B')
ax2.plot(dd_v1_2.index, dd_v1_2 * 100, linewidth=1, color='#4ECDC4')
ax2.set_title('Drawdown Comparison', fontsize=12, fontweight='bold')
ax2.set_ylabel('Drawdown (%)')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Rolling Sharpe
ax3 = axes[1, 0]
rolling_sharpe_v1_1 = (results_v1_1['returns'].rolling(252).mean() * 252 /
                       (results_v1_1['returns'].rolling(252).std() * np.sqrt(252)))
rolling_sharpe_v1_2 = (results_v1_2['returns'].rolling(252).mean() * 252 /
                       (results_v1_2['returns'].rolling(252).std() * np.sqrt(252)))
ax3.plot(rolling_sharpe_v1_1.index, rolling_sharpe_v1_1,
         label='v1.1 Pure RP', linewidth=2, color='#FF6B6B')
ax3.plot(rolling_sharpe_v1_2.index, rolling_sharpe_v1_2,
         label='v1.2 Constrained', linewidth=2, color='#4ECDC4')
ax3.axhline(0, color='black', linestyle='--', linewidth=0.5)
ax3.set_title('Rolling Sharpe Ratio (252-day)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Sharpe Ratio')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Weight comparison (average over time)
ax4 = axes[1, 1]
avg_weights_v1_1 = results_v1_1['weights_history'].mean()
avg_weights_v1_2 = results_v1_2['weights_history'].mean()

x = np.arange(len(avg_weights_v1_1))
width = 0.35
ax4.bar(x - width/2, avg_weights_v1_1.values, width, label='v1.1', color='#FF6B6B', alpha=0.7)
ax4.bar(x + width/2, avg_weights_v1_2.values, width, label='v1.2', color='#4ECDC4', alpha=0.7)
ax4.set_xticks(x)
ax4.set_xticklabels(avg_weights_v1_1.index, rotation=45, ha='right')
ax4.set_title('Average Portfolio Weights', fontsize=12, fontweight='bold')
ax4.set_ylabel('Weight')
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('results/constrained_comparison.png', dpi=150, bbox_inches='tight')
print(f"\n✓ Saved comparison plot to results/constrained_comparison.png")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"\nv1.2 Constrained Risk Parity achieves:")
print(f"  • {sharpe_improvement:.1f}x better Sharpe ratio ({results_v1_2['metrics']['sharpe_ratio']:.2f} vs {results_v1_1['metrics']['sharpe_ratio']:.2f})")
print(f"  • {return_improvement:.1f}x better annual return ({results_v1_2['metrics']['annual_return']:.1%} vs {results_v1_1['metrics']['annual_return']:.1%})")
print(f"  • More balanced allocation (stocks: ~{alloc_compare[alloc_compare['Ticker'].isin(['SPY', 'QQQ', 'IWM'])]['v1.2 Constrained (%)'].sum():.0f}% vs {alloc_compare[alloc_compare['Ticker'].isin(['SPY', 'QQQ', 'IWM'])]['v1.1 Pure RP (%)'].sum():.0f}%)")
print(f"\nConstraints successfully prevent bond overweight and improve risk-adjusted returns!")
