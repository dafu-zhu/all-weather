"""
Run All Weather v3.0 Strategy with Bridgewater Improvements

Implements:
1. Economic Environment Framework - Balance risk across 4 quadrants
2. Volatility Targeting - Dynamic position sizing for 10% target vol
3. Return-Aware Optimization - Optimize Sharpe ratio, not just risk parity
4. Depression Gauge - Crisis detection with Safe Portfolio mode
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('.')

from src.strategy import AllWeatherV3
from src.metrics import calculate_all_metrics

print("="*80)
print("ALL WEATHER v3.0 - BRIDGEWATER-INSPIRED IMPROVEMENTS")
print("="*80)

# Load 7-ETF data
prices = pd.read_csv('data/etf_prices_7etf.csv', index_col=0, parse_dates=True)

print(f"\n7-ETF Dataset:")
print(f"  ETFs: {len(prices.columns)}")
print(f"  Period: {prices.index[0].date()} to {prices.index[-1].date()}")
print(f"  Trading days: {len(prices)}")

# Configuration
config = {
    'initial_capital': 1_000_000,
    'rebalance_freq': 'MS',           # Monthly
    'lookback': 100,                  # 100-day covariance/returns
    'commission_rate': 0.0003,        # 0.03%
    'min_stock_alloc': 0.60,          # 60% minimum stocks
    'max_bond_alloc': 0.35,           # 35% maximum bonds
    'target_volatility': 0.10,        # 10% target annual vol
    'balance_environments': True,     # Economic environment balancing
    'use_return_expectations': True,  # Sharpe optimization
    'use_depression_gauge': True,     # Crisis detection
    'lambda_sharpe': 0.5,             # 50/50 weight on risk parity vs Sharpe
}

print("\nv3.0 Configuration:")
print(f"  Rebalancing: Monthly")
print(f"  Stock Allocation: ≥{config['min_stock_alloc']:.0%}")
print(f"  Bond Allocation: ≤{config['max_bond_alloc']:.0%}")
print(f"  Target Volatility: {config['target_volatility']:.0%}")
print(f"  Environment Balancing: {config['balance_environments']}")
print(f"  Return Optimization: {config['use_return_expectations']}")
print(f"  Depression Gauge: {config['use_depression_gauge']}")
print(f"  Lambda (Sharpe weight): {config['lambda_sharpe']}")

# Run v3.0 backtest
print("\n" + "="*80)
print("RUNNING v3.0 BACKTEST")
print("="*80)

strategy = AllWeatherV3(
    prices=prices,
    **config
)

results = strategy.run_backtest(start_date='2018-01-01', verbose=True)

# Print results
print("\n" + "="*80)
print("v3.0 PERFORMANCE RESULTS")
print("="*80)

metrics = results['metrics']
total_return = (results['final_value'] / config['initial_capital']) - 1

print(f"\nReturns:")
print(f"  Annual Return:        {metrics['annual_return']:>8.2%}")
print(f"  Total Return:         {total_return:>8.2%}")
print(f"  Final Value:          ¥{results['final_value']:>12,.0f}")

print(f"\nRisk:")
print(f"  Annual Volatility:    {metrics['annual_volatility']:>8.2%}")
print(f"  Max Drawdown:         {metrics['max_drawdown']:>8.2%}")

print(f"\nRisk-Adjusted:")
print(f"  Sharpe Ratio:         {metrics['sharpe_ratio']:>8.2f}")
print(f"  Sortino Ratio:        {metrics['sortino_ratio']:>8.2f}")
print(f"  Calmar Ratio:         {metrics['calmar_ratio']:>8.2f}")

print(f"\nTrading:")
num_rebalances = len(results['weights_history']) if isinstance(results['weights_history'], pd.DataFrame) else 0
print(f"  Total Rebalances:     {num_rebalances:>8d}")
print(f"  Win Rate:             {metrics['win_rate']:>8.2%}")

if results['crisis_dates']:
    print(f"\nCrisis Events:")
    print(f"  Crisis periods:       {len(results['crisis_dates']):>8d}")
    for crisis_date in results['crisis_dates']:
        print(f"    • {crisis_date.date()}")

# Compare to v2.0 baseline
print("\n" + "="*80)
print("COMPARISON: v3.0 vs v2.0 BASELINE")
print("="*80)

from src.strategy import AllWeatherV2

# Run v2.0 for comparison
strategy_v2 = AllWeatherV2(
    prices=prices,
    initial_capital=config['initial_capital'],
    rebalance_freq=config['rebalance_freq'],
    lookback=config['lookback'],
    commission_rate=config['commission_rate'],
    min_stock_alloc=config['min_stock_alloc'],
    max_bond_alloc=config['max_bond_alloc']
)
results_v2 = strategy_v2.run_backtest(start_date='2018-01-01', verbose=False)
metrics_v2 = results_v2['metrics']

print(f"\n{'Metric':<25s} {'v3.0':>12s} {'v2.0':>12s} {'Improvement':>12s}")
print("-"*80)

metrics_to_compare = [
    ('Annual Return', 'annual_return', '%'),
    ('Sharpe Ratio', 'sharpe_ratio', 'x'),
    ('Max Drawdown', 'max_drawdown', '%'),
    ('Volatility', 'annual_volatility', '%'),
    ('Sortino Ratio', 'sortino_ratio', 'x'),
    ('Calmar Ratio', 'calmar_ratio', 'x'),
]

improvements = {}

for label, key, unit in metrics_to_compare:
    val_v3 = metrics[key]
    val_v2 = metrics_v2[key]

    if unit == '%':
        diff = (val_v3 - val_v2) * 100  # Difference in percentage points
        print(f"{label:<25s} {val_v3:>11.2%} {val_v2:>11.2%} {diff:>+10.2f}pp")
    else:
        diff = val_v3 - val_v2
        print(f"{label:<25s} {val_v3:>11.2f} {val_v2:>11.2f} {diff:>+11.2f}")

    improvements[key] = diff

print(f"\n{'Final Value':<25s} ¥{results['final_value']:>10,.0f} ¥{results_v2['final_value']:>10,.0f}")

# Evaluate success
print("\n" + "="*80)
print("EVALUATION")
print("="*80)

return_improvement = improvements['annual_return'] * 100  # Convert to pp
sharpe_improvement = improvements['sharpe_ratio']
dd_improvement = improvements['max_drawdown'] * 100  # Convert to pp (negative is better)

print(f"\nPerformance Changes:")
print(f"  Return:     {return_improvement:+.2f}pp {'✅ BETTER' if return_improvement > 0 else '❌ WORSE'}")
print(f"  Sharpe:     {sharpe_improvement:+.2f} {'✅ BETTER' if sharpe_improvement > 0 else '❌ WORSE'}")
print(f"  Max DD:     {dd_improvement:+.2f}pp {'✅ BETTER' if dd_improvement > 0 else '❌ WORSE'}")

# Success criteria
meaningful_return = return_improvement >= 0.5
meaningful_sharpe = sharpe_improvement >= 0.05
meaningful_dd = dd_improvement >= 2.0

is_meaningful = meaningful_return or meaningful_sharpe or meaningful_dd

print(f"\nSuccess Thresholds:")
print(f"  Return ≥ +0.5pp:      {'✅ YES' if meaningful_return else '❌ NO'} ({return_improvement:+.2f}pp)")
print(f"  Sharpe ≥ +0.05:       {'✅ YES' if meaningful_sharpe else '❌ NO'} ({sharpe_improvement:+.2f})")
print(f"  Max DD ≥ +2pp:        {'✅ YES' if meaningful_dd else '❌ NO'} ({dd_improvement:+.2f}pp)")

print(f"\nOverall Assessment:")
if is_meaningful:
    print(f"  ✅ v3.0 MEANINGFUL IMPROVEMENT")
    print(f"     v3.0 shows significant improvement over v2.0 baseline")
    print(f"     Recommendation: PROCEED with v3.0 as production candidate")
else:
    print(f"  ⚠️  v3.0 INSUFFICIENT IMPROVEMENT")
    print(f"     v3.0 does not meet meaningful improvement threshold")
    print(f"     Recommendation: Consider Phase 2 fallback improvements")

# Worse check
is_worse = (
    return_improvement < -0.5 or
    sharpe_improvement < -0.05 or
    dd_improvement < -5.0
)

if is_worse:
    print(f"\n  ❌ WARNING: v3.0 significantly underperforms v2.0!")
    print(f"     Consider reverting to v2.0 or debugging v3.0 implementation")

print("\n" + "="*80)
