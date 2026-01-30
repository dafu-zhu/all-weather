"""
Quick test of v1.1 adaptive rebalancing feature
"""

import sys
sys.path.append('.')

from src.data_loader import load_prices
from src.strategy import AllWeatherV1

print("Testing v1.1 Adaptive Rebalancing...")
print("="*60)

# Load data
prices = load_prices('data/etf_prices_7etf.csv')
print(f"Loaded {len(prices)} days of data\n")

# Test v1.0 behavior (threshold=0, always rebalance)
print("1. Testing v1.0 behavior (threshold=0):")
strategy_v10 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0
)
results_v10 = strategy_v10.run_backtest(start_date='2024-01-01', end_date='2024-12-31', verbose=False)
print(f"   Rebalances executed: {results_v10['rebalances_executed']}")
print(f"   Rebalances skipped: {results_v10['rebalances_skipped']}")
print(f"   Final value: ¥{results_v10['final_value']:,.0f}")
print(f"   Commissions: ¥{strategy_v10.portfolio.get_total_commissions():,.0f}\n")

# Test v1.1 behavior (threshold=0.05, adaptive)
print("2. Testing v1.1 behavior (threshold=0.05):")
strategy_v11 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.05
)
results_v11 = strategy_v11.run_backtest(start_date='2024-01-01', end_date='2024-12-31', verbose=False)
print(f"   Rebalances executed: {results_v11['rebalances_executed']}")
print(f"   Rebalances skipped: {results_v11['rebalances_skipped']}")
print(f"   Final value: ¥{results_v11['final_value']:,.0f}")
print(f"   Commissions: ¥{strategy_v11.portfolio.get_total_commissions():,.0f}\n")

# Compare
print("="*60)
print("COMPARISON:")
commission_saved = strategy_v10.portfolio.get_total_commissions() - strategy_v11.portfolio.get_total_commissions()
rebalances_saved = results_v10['rebalances_executed'] - results_v11['rebalances_executed']
value_diff = results_v11['final_value'] - results_v10['final_value']

print(f"  Rebalances saved: {rebalances_saved}")
print(f"  Commissions saved: ¥{commission_saved:,.0f}")
print(f"  Value difference: ¥{value_diff:,.0f}")
print("="*60)

if rebalances_saved > 0:
    print("\n✓ v1.1 adaptive rebalancing is working correctly!")
else:
    print("\n⚠  Warning: No rebalances were skipped. Check threshold setting.")
