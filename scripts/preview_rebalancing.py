"""
Preview rebalancing actions for live portfolio
Shows what trades are needed without running full notebook
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
from src.data_loader import load_prices
from src.optimizer import optimize_weights

# User's current positions
POSITIONS = {
    '510300.SH': 700,
    '510500.SH': 300,
    '513500.SH': 1100,
    '511260.SH': 100,
    '518880.SH': 300,
    '000066.SH': 0,
    '513100.SH': 1100
}

CASH = 27354
REBALANCE_THRESHOLD = 0.05
COMMISSION_RATE = 0.0003

def round_to_lot_size(shares, etf):
    """Round shares to appropriate lot size."""
    if etf == '511260.SH':
        return round(shares / 100) * 100
    else:
        return round(shares)

# Load data
prices = load_prices('data/etf_prices_7etf.csv')
latest_prices = prices.iloc[-1]

# Calculate current portfolio
total_value = CASH
current_weights = {}

for etf, shares in POSITIONS.items():
    value = shares * latest_prices[etf]
    total_value += value

for etf, shares in POSITIONS.items():
    value = shares * latest_prices[etf]
    current_weights[etf] = value / total_value

# Calculate target weights (risk parity v1.2)
lookback = 252
hist_returns = prices.iloc[-lookback:].pct_change().dropna()
target_weights_array = optimize_weights(hist_returns, use_shrinkage=True)
target_weights = dict(zip(prices.columns, target_weights_array))

# Calculate drift
max_drift = 0.0
for etf in current_weights.keys():
    drift = abs(current_weights[etf] - target_weights[etf])
    max_drift = max(max_drift, drift)

print("="*70)
print("LIVE PORTFOLIO REBALANCING PREVIEW")
print("="*70)
print(f"\nPortfolio Value: ¥{total_value:,.2f}")
print(f"Maximum Drift: {max_drift:.2%}")
print(f"Threshold: {REBALANCE_THRESHOLD:.2%}")

needs_rebalance = max_drift > REBALANCE_THRESHOLD
print(f"\nRebalancing Needed: {'YES ✓' if needs_rebalance else 'NO'}")

if needs_rebalance:
    print("\n" + "="*70)
    print("CURRENT vs TARGET WEIGHTS")
    print("="*70)

    print(f"\n{'ETF':<12} {'Current':<10} {'Target':<10} {'Drift':<10}")
    print("-"*70)

    for etf in sorted(POSITIONS.keys()):
        curr = current_weights[etf]
        tgt = target_weights[etf]
        drift = curr - tgt
        print(f"{etf:<12} {curr:>8.2%}  {tgt:>8.2%}  {drift:>+8.2%}")

    print("\n" + "="*70)
    print("REQUIRED TRADES")
    print("="*70)

    total_commission = 0
    trades = []

    for etf in POSITIONS.keys():
        target_value = total_value * target_weights[etf]
        target_shares = target_value / latest_prices[etf]
        target_shares_rounded = round_to_lot_size(target_shares, etf)

        current_shares = POSITIONS[etf]
        trade_shares = target_shares_rounded - current_shares

        if trade_shares != 0:
            trade_value = trade_shares * latest_prices[etf]
            commission = abs(trade_value) * COMMISSION_RATE
            side = 'BUY' if trade_shares > 0 else 'SELL'

            trades.append({
                'etf': etf,
                'current': current_shares,
                'target': target_shares_rounded,
                'trade': trade_shares,
                'side': side,
                'price': latest_prices[etf],
                'value': trade_value,
                'commission': commission
            })

            total_commission += commission

    if trades:
        for trade in trades:
            print(f"\n{trade['etf']}:")
            print(f"  Current: {trade['current']:>8,.0f} shares")
            print(f"  Target:  {trade['target']:>8,.0f} shares")
            print(f"  Action:  {trade['side']} {abs(trade['trade']):>6,.0f} shares @ ¥{trade['price']:.4f}")
            print(f"  Value:   ¥{abs(trade['value']):>10,.2f}")
            print(f"  Commission: ¥{trade['commission']:>7,.2f}")

        print(f"\nTotal Commission: ¥{total_commission:,.2f}")
        print(f"\n{'='*70}")
        print(f"EXECUTE THESE TRADES ON NEXT TRADING DAY")
        print(f"{'='*70}")
    else:
        print("\nNo trades needed - positions already aligned")
else:
    print("\n✓ Portfolio is within drift threshold")
    print("✓ No rebalancing action required")

print("\n" + "="*70)
