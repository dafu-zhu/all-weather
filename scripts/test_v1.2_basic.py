"""
Quick test of v1.2 covariance shrinkage feature
"""

import sys
sys.path.append('.')

from src.data_loader import load_prices
from src.strategy import AllWeatherV1

print("Testing v1.2 Covariance Shrinkage...")
print("="*60)

# Load data
prices = load_prices('data/etf_prices_7etf.csv')
print(f"Loaded {len(prices)} days of data\n")

# Test v1.1 behavior (no shrinkage)
print("1. Testing v1.1 (Adaptive, No Shrinkage):")
strategy_v11 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.05,
    use_shrinkage=False
)
results_v11 = strategy_v11.run_backtest(start_date='2024-01-01', end_date='2024-12-31', verbose=False)
print(f"   Final value: ¥{results_v11['final_value']:,.0f}")
print(f"   Annual return: {results_v11['metrics']['annual_return']:.2%}")
print(f"   Annual volatility: {results_v11['metrics']['annual_volatility']:.2%}")
print(f"   Sharpe ratio: {results_v11['metrics']['sharpe_ratio']:.2f}")
print(f"   Rebalances: {results_v11['rebalances_executed']}\n")

# Test v1.2 behavior (with shrinkage)
print("2. Testing v1.2 (Adaptive + Shrinkage):")
strategy_v12 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.05,
    use_shrinkage=True
)
results_v12 = strategy_v12.run_backtest(start_date='2024-01-01', end_date='2024-12-31', verbose=False)
print(f"   Final value: ¥{results_v12['final_value']:,.0f}")
print(f"   Annual return: {results_v12['metrics']['annual_return']:.2%}")
print(f"   Annual volatility: {results_v12['metrics']['annual_volatility']:.2%}")
print(f"   Sharpe ratio: {results_v12['metrics']['sharpe_ratio']:.2f}")
print(f"   Rebalances: {results_v12['rebalances_executed']}\n")

# Compare
print("="*60)
print("SHRINKAGE IMPACT:")
value_diff = results_v12['final_value'] - results_v11['final_value']
return_diff = results_v12['metrics']['annual_return'] - results_v11['metrics']['annual_return']
vol_diff = results_v12['metrics']['annual_volatility'] - results_v11['metrics']['annual_volatility']
sharpe_diff = results_v12['metrics']['sharpe_ratio'] - results_v11['metrics']['sharpe_ratio']

print(f"  Value difference: ¥{value_diff:,.0f} ({value_diff/results_v11['final_value']*100:+.2f}%)")
print(f"  Return difference: {return_diff:+.2%}")
print(f"  Volatility difference: {vol_diff:+.2%}")
print(f"  Sharpe difference: {sharpe_diff:+.2f}")
print("="*60)

if abs(value_diff) > 1000 or abs(sharpe_diff) > 0.01:
    print("\n✓ v1.2 covariance shrinkage is making a measurable impact!")
else:
    print("\n⚠ Shrinkage impact is minimal on this time period.")
