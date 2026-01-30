"""
Test different volatility targets to find optimal drawdown reduction.
"""

import sys
sys.path.append('.')

from src.data_loader_us import download_us_etfs, get_all_weather_us_etfs
from src.strategy_us import AllWeather4QuadrantUS

# Load data
etf_info = get_all_weather_us_etfs()
tickers = list(etf_info.keys())
prices = download_us_etfs(tickers=tickers, start_date='2015-01-01', progress=False)

print("Testing different volatility targets...\n")
print("="*70)

vol_targets = [None, 0.06, 0.05, 0.04, 0.03]

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

    vol_str = f"{vol_target:.1%}" if vol_target else "None"
    status = "✓ PASS" if max_dd > -0.10 else "✗ FAIL"

    print(f"Vol Target: {vol_str:6} | Return: {results['metrics']['annual_return']:6.2%} | "
          f"Max DD: {max_dd:7.2%} | Sharpe: {results['metrics']['sharpe_ratio']:5.2f} | {status}")

print("="*70)
