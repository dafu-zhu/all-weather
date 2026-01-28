"""
Run v2.0 Strategy with Final 7-ETF Dataset

7-ETF configuration (removed poor-quality 30-year bond):
- 4 Stock ETFs (2 A-share, 2 US)
- 1 Bond ETF (10-year only)
- 2 Commodity ETFs (gold + commodity index)

All ETFs have excellent data quality (<5% zeros).
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('.')

from src.portfolio import Portfolio
from src.optimizer import optimize_weights_constrained
from src.backtest import Backtester
from src.metrics import calculate_all_metrics
from src.strategy import AllWeatherV2
from src.data_loader import load_prices

print("="*80)
print("ALL WEATHER v2.0 - FINAL 7-ETF DATASET")
print("="*80)

# Load 7-ETF data
prices = pd.read_csv('data/etf_prices_7etf.csv', index_col=0, parse_dates=True)

print(f"\n7-ETF Dataset:")
print(f"  ETFs: {len(prices.columns)}")
print(f"  Period: {prices.index[0].date()} to {prices.index[-1].date()}")
print(f"  Trading days: {len(prices)}")

print(f"\nAsset Universe (All EXCELLENT Quality):")
asset_map = {
    '510300.SH': 'CSI 300 (A-share large cap)',
    '510500.SH': 'CSI 500 (A-share mid cap)',
    '513500.SH': 'S&P 500 (US equity)',
    '513100.SH': 'Nasdaq 100 (US tech)',
    '511260.SH': '10-year Treasury (bonds)',
    '518880.SH': 'Gold (commodity)',
    '000066.SH': 'Commodity Index (commodity)',
}

for code, name in asset_map.items():
    if code in prices.columns:
        data = prices[code].loc['2018-01-01':]
        returns = data.pct_change().dropna()
        zero_pct = (returns == 0).sum() / len(returns) * 100

        if len(data) > 0:
            total_return = (data.iloc[-1] / data.iloc[0] - 1)
            annual_return = (1 + total_return) ** (1/8) - 1
        else:
            annual_return = 0

        print(f"  {code:12s} - {name:30s} ({zero_pct:4.1f}% zeros, {annual_return:5.1%} return)")

# Run v2.0 backtest
print("\n" + "="*80)
print("RUNNING BACKTEST (60% stocks, 35% bonds, monthly rebalancing)")
print("="*80)

strategy = AllWeatherV2(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='MS',
    lookback=100,
    commission_rate=0.0003,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35
)

results = strategy.run_backtest(start_date='2018-01-01', verbose=True)

# Print results
print("\n" + "="*80)
print("PERFORMANCE RESULTS")
print("="*80)

metrics = results['metrics']
total_return = (results['final_value'] / 1_000_000) - 1

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

# Compare to all versions
print("\n" + "="*80)
print("COMPARISON: 7-ETF vs 8-ETF vs 5-ETF")
print("="*80)

# Load other datasets and run backtests
prices_8 = pd.read_csv('data/etf_prices_enhanced.csv', index_col=0, parse_dates=True)
prices_5 = pd.read_csv('data/etf_prices_clean.csv', index_col=0, parse_dates=True)

strategy_8 = AllWeatherV2(
    prices=prices_8,
    initial_capital=1_000_000,
    rebalance_freq='MS',
    lookback=100,
    commission_rate=0.0003,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35
)
results_8 = strategy_8.run_backtest(start_date='2018-01-01', verbose=False)
metrics_8 = results_8['metrics']

strategy_5 = AllWeatherV2(
    prices=prices_5,
    initial_capital=1_000_000,
    rebalance_freq='MS',
    lookback=100,
    commission_rate=0.0003,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35
)
results_5 = strategy_5.run_backtest(start_date='2018-01-01', verbose=False)
metrics_5 = results_5['metrics']

print(f"\n{'Metric':<25s} {'7-ETF':>12s} {'8-ETF':>12s} {'5-ETF':>12s}")
print("-"*80)

metrics_to_compare = [
    ('Annual Return', 'annual_return', '%'),
    ('Sharpe Ratio', 'sharpe_ratio', 'x'),
    ('Max Drawdown', 'max_drawdown', '%'),
    ('Volatility', 'annual_volatility', '%'),
    ('Sortino Ratio', 'sortino_ratio', 'x'),
]

for label, key, unit in metrics_to_compare:
    val_7 = metrics[key]
    val_8 = metrics_8[key]
    val_5 = metrics_5[key]

    if unit == '%':
        print(f"{label:<25s} {val_7:>11.2%} {val_8:>11.2%} {val_5:>11.2%}")
    else:
        print(f"{label:<25s} {val_7:>11.2f} {val_8:>11.2f} {val_5:>11.2f}")

print(f"\n{'Final Value':<25s} ¥{results['final_value']:>10,.0f} ¥{results_8['final_value']:>10,.0f} ¥{results_5['final_value']:>10,.0f}")

# Benchmark comparison
print("\n" + "="*80)
print("vs BENCHMARK (CSI 300)")
print("="*80)

# Assuming CSI 300 is 510300.SH
benchmark = prices_5['510300.SH'].loc['2018-01-01':]
benchmark_returns = benchmark.pct_change().dropna()
benchmark_metrics = calculate_all_metrics(benchmark_returns)

print(f"\n{'Metric':<25s} {'7-ETF':>12s} {'Benchmark':>12s} {'Advantage':>12s}")
print("-"*80)

print(f"{'Annual Return':<25s} {metrics['annual_return']:>11.2%} {benchmark_metrics['annual_return']:>11.2%} {metrics['annual_return'] - benchmark_metrics['annual_return']:>11.2f}pp")
print(f"{'Sharpe Ratio':<25s} {metrics['sharpe_ratio']:>11.2f} {benchmark_metrics['sharpe_ratio']:>11.2f} {metrics['sharpe_ratio'] - benchmark_metrics['sharpe_ratio']:>+11.2f}")
print(f"{'Max Drawdown':<25s} {metrics['max_drawdown']:>11.2%} {benchmark_metrics['max_drawdown']:>11.2%} {metrics['max_drawdown'] - benchmark_metrics['max_drawdown']:>11.2f}pp")

benchmark_final = 1_000_000 * (1 + benchmark_returns).prod()
print(f"\n{'Final Value':<25s} ¥{results['final_value']:>10,.0f} ¥{benchmark_final:>10,.0f}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\n✓ 7-ETF Configuration (Removed poor-quality 30-year bond)")
print(f"\n  Assets:")
print(f"    • 4 Stock ETFs: CSI 300, CSI 500, S&P 500, Nasdaq 100")
print(f"    • 1 Bond ETF: 10-year Treasury")
print(f"    • 2 Commodity ETFs: Gold, Commodity Index")
print(f"\n  All ETFs: 🟢 EXCELLENT data quality (<5% zeros)")

# Determine best configuration
if metrics['sharpe_ratio'] > metrics_8['sharpe_ratio'] and metrics['sharpe_ratio'] > metrics_5['sharpe_ratio']:
    print(f"\n🏆 WINNER: 7-ETF has BEST risk-adjusted returns!")
    print(f"  • Sharpe: {metrics['sharpe_ratio']:.2f} (best of all 3)")
    print(f"  • Return: {metrics['annual_return']:.2%}")
    print(f"  • Maximum diversification with excellent data quality")
elif metrics['sharpe_ratio'] > metrics_8['sharpe_ratio']:
    print(f"\n🎯 7-ETF IMPROVES on 8-ETF by removing poor-quality 30-year bond")
    print(f"  • Sharpe: {metrics['sharpe_ratio']:.2f} vs {metrics_8['sharpe_ratio']:.2f} (8-ETF)")
    print(f"  • Return: {metrics['annual_return']:.2%} vs {metrics_8['annual_return']:.2%} (8-ETF)")
    if metrics['sharpe_ratio'] >= metrics_5['sharpe_ratio'] * 0.95:
        print(f"  • Competitive with 5-ETF (Sharpe: {metrics_5['sharpe_ratio']:.2f})")
        print(f"  • Provides better diversification than 5-ETF")
    else:
        print(f"  • 5-ETF still has better risk-adjusted returns (Sharpe: {metrics_5['sharpe_ratio']:.2f})")
        print(f"  • But 7-ETF provides more diversification")

# Recommendation
print(f"\n📊 RECOMMENDATION:")

if metrics['sharpe_ratio'] >= metrics_5['sharpe_ratio'] * 0.95:
    print(f"  ✅ USE 7-ETF DATASET (RECOMMENDED)")
    print(f"     • Best balance of performance and diversification")
    print(f"     • Includes all user-requested alternatives (Nasdaq, Commodity)")
    print(f"     • All assets have excellent data quality")
    print(f"     • Sharpe competitive with 5-ETF: {metrics['sharpe_ratio']:.2f} vs {metrics_5['sharpe_ratio']:.2f}")
else:
    diff = (metrics_5['annual_return'] - metrics['annual_return']) * 100
    print(f"  ⚖️  TRADE-OFF:")
    print(f"     • 5-ETF: Better performance ({metrics_5['annual_return']:.2%}, Sharpe {metrics_5['sharpe_ratio']:.2f})")
    print(f"     • 7-ETF: More diversification ({metrics['annual_return']:.2%}, Sharpe {metrics['sharpe_ratio']:.2f})")
    print(f"     • Performance difference: {diff:.2f}pp annual return")
    print(f"     • Choose based on priority: Performance vs Diversification")

print(f"\n" + "="*80)
