#!/usr/bin/env python3
"""Compare symmetric 3% threshold vs old asymmetric 3%/10%."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategy_v2 import AllWeatherV2


TRADABLE_ETFS = [
    '510300.SH', '510500.SH', '513500.SH',
    '511260.SH', '518880.SH', '513100.SH',
]
START_DATE = '2025-01-01'
INITIAL_CAPITAL = 1_000_000


class AllWeatherV2Asymmetric(AllWeatherV2):
    """V2 with old asymmetric thresholds for comparison."""

    def __init__(self, trim_threshold, buy_threshold, **kwargs):
        super().__init__(**kwargs)
        self._trim_threshold = trim_threshold
        self._buy_threshold = buy_threshold

    def check_daily_drift(self, current_prices):
        if self.target_weights is None:
            return []

        trades_needed = []
        current_weights = self.portfolio.get_weights(current_prices)

        for asset, target_weight in self.target_weights.items():
            current_weight = current_weights.get(asset, 0.0)
            drift = current_weight - target_weight

            if drift > self._trim_threshold:
                trades_needed.append({
                    'asset': asset, 'action': 'sell', 'drift': drift,
                    'current_weight': current_weight, 'target_weight': target_weight,
                })
            elif drift < -self._buy_threshold:
                trades_needed.append({
                    'asset': asset, 'action': 'buy', 'drift': drift,
                    'current_weight': current_weight, 'target_weight': target_weight,
                })

        return trades_needed


def main():
    prices = pd.read_csv('data/etf_prices_7etf.csv', index_col=0, parse_dates=True)
    prices = prices[TRADABLE_ETFS]

    # Symmetric 3%
    s1 = AllWeatherV2(
        prices=prices, initial_capital=INITIAL_CAPITAL,
        drift_threshold=0.03, use_shrinkage=True,
    )
    r1 = s1.run_backtest(start_date=START_DATE, verbose=False)

    # Old asymmetric 3% trim / 10% buy
    s2 = AllWeatherV2Asymmetric(
        trim_threshold=0.03, buy_threshold=0.10,
        prices=prices, initial_capital=INITIAL_CAPITAL,
        drift_threshold=0.05, use_shrinkage=True,
    )
    r2 = s2.run_backtest(start_date=START_DATE, verbose=False)

    # Print comparison
    print(f"\n{'='*62}")
    print(f"  Symmetric 3% vs Asymmetric 3%/10%  (from {START_DATE})")
    print(f"{'='*62}")
    print(f"{'Metric':<22} {'3% Symmetric':>18} {'3%/10% Asymmetric':>18}")
    print(f"{'-'*62}")

    rows = [
        ("Final Value", "¥{:,.0f}", lambda r: r['final_value']),
        ("Total Return", "{:+.2f}%", lambda r: r['total_return'] * 100),
        ("Annual Return", "{:+.2f}%", lambda r: r['metrics']['annual_return'] * 100),
        ("Sharpe Ratio", "{:.2f}", lambda r: r['metrics']['sharpe_ratio']),
        ("Sortino Ratio", "{:.2f}", lambda r: r['metrics']['sortino_ratio']),
        ("Max Drawdown", "{:.2f}%", lambda r: r['metrics']['max_drawdown'] * 100),
        ("Calmar Ratio", "{:.2f}", lambda r: r['metrics']['calmar_ratio']),
        ("Win Rate", "{:.1f}%", lambda r: r['metrics']['win_rate'] * 100),
        ("Daily Rebalances", "{}", lambda r: r['daily_rebalance_count']),
        ("Total Trades", "{}", lambda r: len(r['daily_trades'])),
    ]

    for label, fmt, getter in rows:
        v1 = fmt.format(getter(r1))
        v2 = fmt.format(getter(r2))
        print(f"{label:<22} {v1:>18} {v2:>18}")

    # Show trade details
    print(f"\n{'='*62}")
    print("  Trade Details")
    print(f"{'='*62}")

    for label, r in [("3% Symmetric", r1), ("3%/10% Asymmetric", r2)]:
        print(f"\n  {label}:")
        if r['daily_trades']:
            buys = [t for t in r['daily_trades'] if t['action'] == 'buy']
            sells = [t for t in r['daily_trades'] if t['action'] == 'sell']
            print(f"    Buy trades:  {len(buys)}")
            print(f"    Sell trades: {len(sells)}")
            for t in r['daily_trades']:
                print(f"    [{t['date'].date()}] {t['action']:>4} {t['asset']} (drift {t['drift']:+.2%})")
        else:
            print("    No trades")


if __name__ == '__main__':
    main()
