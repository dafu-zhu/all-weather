"""
Find optimal volatility target that just meets -10% max drawdown threshold.
"""

import sys
sys.path.append('.')

from src.data_loader_us import download_us_etfs, get_all_weather_us_etfs
from src.strategy_us import AllWeather4QuadrantUS

# Load data
etf_info = get_all_weather_us_etfs()
tickers = list(etf_info.keys())
prices = download_us_etfs(tickers=tickers, start_date='2015-01-01', progress=False)

print("Finding optimal volatility target (max DD < -10%)...\n")
print("="*80)

# Test range: 3.0% to 4.0% in 0.1% steps
vol_targets = [0.030, 0.032, 0.034, 0.036, 0.038, 0.040]

for vol_target in vol_targets:
    strategy = AllWeather4QuadrantUS(
        prices=prices,
        initial_capital=100_000,
        rebalance_freq='W-MON',
        lookback=252,
        commission_rate=0.001,
        target_volatility=vol_target
    )

    results = strategy.run_backtest(start_date='2018-01-01')

    equity = results['equity_curve']
    running_max = equity.expanding().max()
    drawdown = (equity - running_max) / running_max
    max_dd = drawdown.min()

    status = "✓ PASS" if max_dd > -0.10 else "✗ FAIL"

    print(f"Vol: {vol_target:.1%} | Return: {results['metrics']['annual_return']:6.2%} | "
          f"Vol: {results['metrics']['annual_volatility']:6.2%} | "
          f"Max DD: {max_dd:7.2%} | Sharpe: {results['metrics']['sharpe_ratio']:5.2f} | {status}")

print("="*80)
print("\nRecommendation: Use the highest volatility target that still achieves max DD < -10%")
print("This maximizes returns while meeting the drawdown constraint.")
