"""
Full period test: v1.1 vs v1.2 (2018-2026)
"""

import sys
sys.path.append('.')

import pandas as pd
from src.data_loader import load_prices
from src.strategy import AllWeatherV1

print("="*70)
print("v1.1 vs v1.2 Full Period Test (2018-2026)")
print("="*70)

prices = load_prices('data/etf_prices_7etf.csv')
print(f"\nLoaded {len(prices)} days of data for {len(prices.columns)} ETFs")

# v1.1: Adaptive, no shrinkage
print("\n1. Running v1.1 (Adaptive, No Shrinkage)...")
strategy_v11 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.05,
    use_shrinkage=False
)
results_v11 = strategy_v11.run_backtest(start_date='2018-01-01', verbose=False)

# v1.2: Adaptive + shrinkage
print("\n2. Running v1.2 (Adaptive + Shrinkage)...")
strategy_v12 = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.05,
    use_shrinkage=True
)
results_v12 = strategy_v12.run_backtest(start_date='2018-01-01', verbose=False)

# Compare
print("\n" + "="*70)
print("RESULTS COMPARISON")
print("="*70)

comparison = pd.DataFrame({
    'v1.1 (No Shrinkage)': [
        f"¥{results_v11['final_value']:,.0f}",
        f"{results_v11['total_return']:.2%}",
        f"{results_v11['metrics']['annual_return']:.2%}",
        f"{results_v11['metrics']['annual_volatility']:.2%}",
        f"{results_v11['metrics']['sharpe_ratio']:.2f}",
        f"{results_v11['metrics']['sortino_ratio']:.2f}",
        f"{results_v11['metrics']['max_drawdown']:.2%}",
        f"{results_v11['metrics']['calmar_ratio']:.2f}",
        results_v11['rebalances_executed'],
        f"¥{strategy_v11.portfolio.get_total_commissions():,.0f}",
    ],
    'v1.2 (With Shrinkage)': [
        f"¥{results_v12['final_value']:,.0f}",
        f"{results_v12['total_return']:.2%}",
        f"{results_v12['metrics']['annual_return']:.2%}",
        f"{results_v12['metrics']['annual_volatility']:.2%}",
        f"{results_v12['metrics']['sharpe_ratio']:.2f}",
        f"{results_v12['metrics']['sortino_ratio']:.2f}",
        f"{results_v12['metrics']['max_drawdown']:.2%}",
        f"{results_v12['metrics']['calmar_ratio']:.2f}",
        results_v12['rebalances_executed'],
        f"¥{strategy_v12.portfolio.get_total_commissions():,.0f}",
    ]
}, index=[
    'Final Value',
    'Total Return',
    'Annual Return',
    'Annual Volatility',
    'Sharpe Ratio',
    'Sortino Ratio',
    'Max Drawdown',
    'Calmar Ratio',
    'Rebalances',
    'Total Commissions'
])

print(comparison)

# Calculate differences
print("\n" + "="*70)
print("v1.2 IMPROVEMENTS OVER v1.1")
print("="*70)

value_diff = results_v12['final_value'] - results_v11['final_value']
return_diff = results_v12['metrics']['annual_return'] - results_v11['metrics']['annual_return']
vol_diff = results_v12['metrics']['annual_volatility'] - results_v11['metrics']['annual_volatility']
sharpe_diff = results_v12['metrics']['sharpe_ratio'] - results_v11['metrics']['sharpe_ratio']
rebal_diff = results_v12['rebalances_executed'] - results_v11['rebalances_executed']

print(f"Final Value:      ¥{value_diff:+,.0f} ({value_diff/results_v11['final_value']*100:+.2f}%)")
print(f"Annual Return:    {return_diff:+.2%}")
print(f"Annual Volatility:{vol_diff:+.2%}")
print(f"Sharpe Ratio:     {sharpe_diff:+.2f}")
print(f"Rebalances:       {rebal_diff:+d}")
print("="*70)

if value_diff > 10000:
    print(f"\n✓ v1.2 significantly outperforms v1.1 by ¥{value_diff:,.0f}!")
elif value_diff > 0:
    print(f"\n✓ v1.2 modestly outperforms v1.1 by ¥{value_diff:,.0f}")
else:
    print(f"\n⚠ v1.2 underperforms v1.1 by ¥{abs(value_diff):,.0f}")
    print("   Shrinkage may not benefit this particular dataset/period")
