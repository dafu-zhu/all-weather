"""
Test v3.1 feature variants to isolate performance issues
"""

import sys
sys.path.append('.')

import pandas as pd
from src.strategy import AllWeatherV2, AllWeatherV3_1

# Load data
prices = pd.read_csv('data/etf_prices_7etf.csv', index_col=0, parse_dates=True)

print("=" * 70)
print("v3.1 VARIANT TESTING")
print("=" * 70)

initial_capital = 1_000_000

# Baseline
print("\n" + "=" * 70)
print("v2.0 BASELINE")
print("=" * 70)
v2 = AllWeatherV2(
    prices=prices,
    initial_capital=initial_capital,
    rebalance_freq='MS',
    lookback=100,
    commission_rate=0.0003,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35
)
results_v2 = v2.run_backtest(start_date='2018-01-01', verbose=False)
print(f"Return: {results_v2['metrics']['annual_return']:.2%}, Sharpe: {results_v2['metrics']['sharpe_ratio']:.2f}")

# Variant 1: Only stricter crisis detection (no return optimization)
print("\n" + "=" * 70)
print("v3.1 VARIANT 1: Crisis Only (No Return Opt)")
print("=" * 70)
v3_1_crisis = AllWeatherV3_1(
    prices=prices,
    initial_capital=initial_capital,
    rebalance_freq='MS',
    lookback=100,
    commission_rate=0.0003,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35,
    balance_environments=False,
    use_return_expectations=False,  # Disabled
    use_depression_gauge=True,  # Enabled
    lambda_sharpe=0.2,
    ewma_span=252
)
results_crisis = v3_1_crisis.run_backtest(start_date='2018-01-01', verbose=False)
print(f"Return: {results_crisis['metrics']['annual_return']:.2%}, Sharpe: {results_crisis['metrics']['sharpe_ratio']:.2f}")
print(f"Crisis Events: {len(results_crisis['crisis_dates'])}")

# Variant 2: Only return optimization (no crisis detection)
print("\n" + "=" * 70)
print("v3.1 VARIANT 2: Return Opt Only (No Crisis)")
print("=" * 70)
v3_1_return = AllWeatherV3_1(
    prices=prices,
    initial_capital=initial_capital,
    rebalance_freq='MS',
    lookback=100,
    commission_rate=0.0003,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35,
    max_single_asset=0.35,
    balance_environments=True,
    use_return_expectations=True,  # Enabled
    use_depression_gauge=False,  # Disabled
    lambda_sharpe=0.2,
    ewma_span=252
)
results_return = v3_1_return.run_backtest(start_date='2018-01-01', verbose=False)
print(f"Return: {results_return['metrics']['annual_return']:.2%}, Sharpe: {results_return['metrics']['sharpe_ratio']:.2f}")

# Variant 3: Neither (should match v2.0)
print("\n" + "=" * 70)
print("v3.1 VARIANT 3: Neither (Should Match v2.0)")
print("=" * 70)
v3_1_neither = AllWeatherV3_1(
    prices=prices,
    initial_capital=initial_capital,
    rebalance_freq='MS',
    lookback=100,
    commission_rate=0.0003,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35,
    balance_environments=False,
    use_return_expectations=False,  # Disabled
    use_depression_gauge=False,  # Disabled
)
results_neither = v3_1_neither.run_backtest(start_date='2018-01-01', verbose=False)
print(f"Return: {results_neither['metrics']['annual_return']:.2%}, Sharpe: {results_neither['metrics']['sharpe_ratio']:.2f}")

# Variant 4: Full v3.1 (both features)
print("\n" + "=" * 70)
print("v3.1 FULL (Both Features)")
print("=" * 70)
v3_1_full = AllWeatherV3_1(
    prices=prices,
    initial_capital=initial_capital,
    rebalance_freq='MS',
    lookback=100,
    commission_rate=0.0003,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35,
    max_single_asset=0.35,
    balance_environments=True,
    use_return_expectations=True,  # Enabled
    use_depression_gauge=True,  # Enabled
    lambda_sharpe=0.2,
    ewma_span=252
)
results_full = v3_1_full.run_backtest(start_date='2018-01-01', verbose=False)
print(f"Return: {results_full['metrics']['annual_return']:.2%}, Sharpe: {results_full['metrics']['sharpe_ratio']:.2f}")
print(f"Crisis Events: {len(results_full['crisis_dates'])}")

# Summary table
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"{'Variant':<40} {'Return':>10} {'Sharpe':>8} {'vs v2.0':>10}")
print("-" * 70)
print(f"{'v2.0 Baseline':<40} {results_v2['metrics']['annual_return']:>10.2%} {results_v2['metrics']['sharpe_ratio']:>8.2f} {0:>10.2%}")
print(f"{'v3.1 Crisis Only':<40} {results_crisis['metrics']['annual_return']:>10.2%} {results_crisis['metrics']['sharpe_ratio']:>8.2f} {results_crisis['metrics']['annual_return'] - results_v2['metrics']['annual_return']:>10.2%}")
print(f"{'v3.1 Return Opt Only':<40} {results_return['metrics']['annual_return']:>10.2%} {results_return['metrics']['sharpe_ratio']:>8.2f} {results_return['metrics']['annual_return'] - results_v2['metrics']['annual_return']:>10.2%}")
print(f"{'v3.1 Neither':<40} {results_neither['metrics']['annual_return']:>10.2%} {results_neither['metrics']['sharpe_ratio']:>8.2f} {results_neither['metrics']['annual_return'] - results_v2['metrics']['annual_return']:>10.2%}")
print(f"{'v3.1 Full':<40} {results_full['metrics']['annual_return']:>10.2%} {results_full['metrics']['sharpe_ratio']:>8.2f} {results_full['metrics']['annual_return'] - results_v2['metrics']['annual_return']:>10.2%}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
if results_return['metrics']['annual_return'] < results_v2['metrics']['annual_return']:
    print("❌ Return optimization STILL HARMFUL even with fixes (EWMA 252, concentration limit, lambda=0.2)")
    print(f"   Impact: {results_return['metrics']['annual_return'] - results_v2['metrics']['annual_return']:.2%}")
else:
    print("✅ Return optimization improved!")

if results_crisis['metrics']['annual_return'] < results_v2['metrics']['annual_return']:
    print("❌ Crisis detection STILL HARMFUL even with stricter threshold (3/3 signals)")
    print(f"   Impact: {results_crisis['metrics']['annual_return'] - results_v2['metrics']['annual_return']:.2%}")
else:
    print("✅ Crisis detection improved!")

print("\n⚠️  Fundamental insight: Return optimization may not work for this strategy/dataset")
