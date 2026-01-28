"""
All Weather v3.1 Comparison Script

Compares v3.1 (fixed) against v2.0 baseline and v3.0 original.

v3.1 Fixes:
1. Longer EWMA (252 days = 1 year)
2. Concentration limit (max 35% per asset)
3. Lower lambda (0.2 = 80% risk parity focus)
4. Stricter crisis detection (3/3 signals)
5. Removed volatility targeting
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
from src.strategy import AllWeatherV2, AllWeatherV3, AllWeatherV3_1
from src.metrics import calculate_all_metrics

# Load 7-ETF dataset
prices = pd.read_csv('data/etf_prices_7etf.csv', index_col=0, parse_dates=True)

print("=" * 70)
print("ALL WEATHER V3.1 COMPARISON")
print("=" * 70)

# Parameters
initial_capital = 1_000_000
rebalance_freq = 'MS'  # Monthly
lookback = 100
commission_rate = 0.0003

# Run v2.0 Baseline
print("\n" + "=" * 70)
print("v2.0 BASELINE (Constrained Risk Parity)")
print("=" * 70)
v2 = AllWeatherV2(
    prices=prices,
    initial_capital=initial_capital,
    rebalance_freq=rebalance_freq,
    lookback=lookback,
    commission_rate=commission_rate,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35
)
results_v2 = v2.run_backtest(start_date='2018-01-01', verbose=False)
metrics_v2 = results_v2['metrics']

print(f"\nFinal Value: ¥{results_v2['final_value']:,.0f}")
print(f"Total Return: {results_v2['total_return']:.2%}")
print(f"Annual Return: {metrics_v2['annual_return']:.2%}")
print(f"Sharpe Ratio: {metrics_v2['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics_v2['max_drawdown']:.2%}")
print(f"Volatility: {metrics_v2['annual_volatility']:.2%}")

# Run v3.0 Original (for reference)
print("\n" + "=" * 70)
print("v3.0 ORIGINAL (All Improvements)")
print("=" * 70)
v3_0 = AllWeatherV3(
    prices=prices,
    initial_capital=initial_capital,
    rebalance_freq=rebalance_freq,
    lookback=lookback,
    commission_rate=commission_rate,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35,
    target_volatility=0.10,
    balance_environments=True,
    use_return_expectations=True,
    use_depression_gauge=True,
    lambda_sharpe=0.5
)
results_v3_0 = v3_0.run_backtest(start_date='2018-01-01', verbose=False)
metrics_v3_0 = results_v3_0['metrics']

print(f"\nFinal Value: ¥{results_v3_0['final_value']:,.0f}")
print(f"Total Return: {results_v3_0['total_return']:.2%}")
print(f"Annual Return: {metrics_v3_0['annual_return']:.2%}")
print(f"Sharpe Ratio: {metrics_v3_0['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics_v3_0['max_drawdown']:.2%}")
print(f"Volatility: {metrics_v3_0['annual_volatility']:.2%}")
print(f"Crisis Events: {len(results_v3_0['crisis_dates'])}")

# Run v3.1 with Fixes
print("\n" + "=" * 70)
print("v3.1 FIXED (Return Opt + Stricter Crisis)")
print("=" * 70)
v3_1 = AllWeatherV3_1(
    prices=prices,
    initial_capital=initial_capital,
    rebalance_freq=rebalance_freq,
    lookback=lookback,
    commission_rate=commission_rate,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35,
    max_single_asset=0.35,
    balance_environments=True,
    use_return_expectations=True,
    use_depression_gauge=True,
    lambda_sharpe=0.2,
    ewma_span=252
)
results_v3_1 = v3_1.run_backtest(start_date='2018-01-01', verbose=True)
metrics_v3_1 = results_v3_1['metrics']

print(f"\nFinal Value: ¥{results_v3_1['final_value']:,.0f}")
print(f"Total Return: {results_v3_1['total_return']:.2%}")
print(f"Annual Return: {metrics_v3_1['annual_return']:.2%}")
print(f"Sharpe Ratio: {metrics_v3_1['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics_v3_1['max_drawdown']:.2%}")
print(f"Volatility: {metrics_v3_1['annual_volatility']:.2%}")
print(f"Crisis Events: {len(results_v3_1['crisis_dates'])}")

# Comparison Table
print("\n" + "=" * 70)
print("PERFORMANCE COMPARISON")
print("=" * 70)

comparison = pd.DataFrame({
    'v2.0 Baseline': {
        'Annual Return': f"{metrics_v2['annual_return']:.2%}",
        'Sharpe Ratio': f"{metrics_v2['sharpe_ratio']:.2f}",
        'Max Drawdown': f"{metrics_v2['max_drawdown']:.2%}",
        'Volatility': f"{metrics_v2['annual_volatility']:.2%}",
        'Final Value': f"¥{results_v2['final_value']:,.0f}",
        'Crisis Events': '-'
    },
    'v3.0 Original': {
        'Annual Return': f"{metrics_v3_0['annual_return']:.2%}",
        'Sharpe Ratio': f"{metrics_v3_0['sharpe_ratio']:.2f}",
        'Max Drawdown': f"{metrics_v3_0['max_drawdown']:.2%}",
        'Volatility': f"{metrics_v3_0['annual_volatility']:.2%}",
        'Final Value': f"¥{results_v3_0['final_value']:,.0f}",
        'Crisis Events': f"{len(results_v3_0['crisis_dates'])}"
    },
    'v3.1 Fixed': {
        'Annual Return': f"{metrics_v3_1['annual_return']:.2%}",
        'Sharpe Ratio': f"{metrics_v3_1['sharpe_ratio']:.2f}",
        'Max Drawdown': f"{metrics_v3_1['max_drawdown']:.2%}",
        'Volatility': f"{metrics_v3_1['annual_volatility']:.2%}",
        'Final Value': f"¥{results_v3_1['final_value']:,.0f}",
        'Crisis Events': f"{len(results_v3_1['crisis_dates'])}"
    }
})

print(comparison.T)

# Numeric comparison for delta calculation
print("\n" + "=" * 70)
print("v3.1 vs v2.0 DELTA")
print("=" * 70)

return_delta = metrics_v3_1['annual_return'] - metrics_v2['annual_return']
sharpe_delta = metrics_v3_1['sharpe_ratio'] - metrics_v2['sharpe_ratio']
dd_delta = metrics_v3_1['max_drawdown'] - metrics_v2['max_drawdown']

print(f"Annual Return: {return_delta:+.2%} ({metrics_v3_1['annual_return']:.2%} vs {metrics_v2['annual_return']:.2%})")
print(f"Sharpe Ratio: {sharpe_delta:+.2f} ({metrics_v3_1['sharpe_ratio']:.2f} vs {metrics_v2['sharpe_ratio']:.2f})")
print(f"Max Drawdown: {dd_delta:+.2%} ({metrics_v3_1['max_drawdown']:.2%} vs {metrics_v2['max_drawdown']:.2%})")

# Verdict
print("\n" + "=" * 70)
print("VERDICT")
print("=" * 70)

if return_delta >= 0.005 or sharpe_delta >= 0.05:
    print("✅ SUCCESS: v3.1 shows meaningful improvement over v2.0")
    print(f"   Improvement: {return_delta:.2%} return OR {sharpe_delta:+.2f} Sharpe")
elif return_delta >= 0 and sharpe_delta >= 0:
    print("⚠️  MARGINAL: v3.1 slightly better but not meaningful improvement")
    print(f"   Improvement: {return_delta:.2%} return, {sharpe_delta:+.2f} Sharpe")
else:
    print("❌ FAILED: v3.1 does not beat v2.0 baseline")
    print(f"   Degradation: {return_delta:.2%} return, {sharpe_delta:+.2f} Sharpe")
    print("   Recommendation: Keep v2.0 in production")

print("\n" + "=" * 70)
