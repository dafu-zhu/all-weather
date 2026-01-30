"""
Test all cells in live_portfolio_tracker.ipynb to find errors
"""

import sys
sys.path.append('.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timezone, timedelta
import pytz

from src.data_loader import load_prices
from src.optimizer import optimize_weights
from src.utils.reporting import print_section, format_currency

plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)

print("="*70)
print("TESTING LIVE PORTFOLIO TRACKER NOTEBOOK")
print("="*70)

# ========== Cell 2: Configuration ==========
print("\n[TEST] Cell 2: Configuration & Initial Position")
try:
    INITIAL_POSITIONS = {
        '510300.SH': 700,
        '510500.SH': 300,
        '513500.SH': 1100,
        '511260.SH': 100,
        '518880.SH': 300,
        '000066.SH': 0,
        '513100.SH': 1100
    }

    INITIAL_CASH = 27354
    START_DATE = '2026-01-28'  # Last available date in data
    LOOKBACK = 252
    REBALANCE_THRESHOLD = 0.05
    COMMISSION_RATE = 0.0003

    CHICAGO_TZ = pytz.timezone('America/Chicago')
    TODAY_CHICAGO = datetime.now(CHICAGO_TZ)

    print(f"Current Time (Chicago): {TODAY_CHICAGO.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"\nInitial Positions (as of {START_DATE}):")
    for etf, shares in INITIAL_POSITIONS.items():
        print(f"  {etf}: {shares:,.0f} shares")
    print(f"  Cash: {format_currency(INITIAL_CASH)}")
    print("✓ Cell 2 passed")
except Exception as e:
    print(f"✗ Cell 2 failed: {e}")
    sys.exit(1)

# ========== Cell 3: Load Market Data ==========
print("\n[TEST] Cell 3: Load Market Data")
try:
    prices = load_prices('data/etf_prices_7etf.csv')

    # Validate and adjust start date if needed
    requested_start = pd.Timestamp(START_DATE)
    if requested_start not in prices.index:
        if requested_start > prices.index[-1]:
            actual_start = prices.index[-1]
            print(f"Note: Using last available date: {actual_start.date()}")
        else:
            actual_start = prices.index[prices.index <= requested_start][-1]
            print(f"Note: Using closest previous date: {actual_start.date()}")
        START_DATE = actual_start.strftime('%Y-%m-%d')

    start_idx = prices.index.get_loc(pd.Timestamp(START_DATE))
    lookback_start = prices.index[max(0, start_idx - LOOKBACK)]

    print(f"Data loaded: {len(prices)} days")
    print(f"Period: {prices.index[0].date()} to {prices.index[-1].date()}")
    print(f"\nLatest prices (as of {prices.index[-1].date()}):")
    print(prices.iloc[-1])
    print("✓ Cell 3 passed")
except Exception as e:
    print(f"✗ Cell 3 failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ========== Cell 4: Calculate Current Portfolio Status ==========
print("\n[TEST] Cell 4: Calculate Current Portfolio Status")
try:
    def calculate_portfolio_value(positions, prices_series, cash=0):
        position_value = sum(
            shares * prices_series.get(etf, 0)
            for etf, shares in positions.items()
        )
        return position_value + cash

    def calculate_weights(positions, prices_series, cash=0):
        total_value = calculate_portfolio_value(positions, prices_series, cash)
        if total_value == 0:
            return {etf: 0.0 for etf in positions.keys()}

        weights = {}
        for etf, shares in positions.items():
            position_value = shares * prices_series.get(etf, 0)
            weights[etf] = position_value / total_value
        return weights

    latest_prices = prices.iloc[-1]
    current_value = calculate_portfolio_value(INITIAL_POSITIONS, latest_prices, INITIAL_CASH)
    current_weights = calculate_weights(INITIAL_POSITIONS, latest_prices, INITIAL_CASH)

    print_section("Current Portfolio Status")
    print(f"\nTotal Value: {format_currency(current_value)}")
    print(f"Cash: {format_currency(INITIAL_CASH)}")
    print(f"Invested: {format_currency(current_value - INITIAL_CASH)}")

    print("\nCurrent Weights:")
    for etf, weight in sorted(current_weights.items(), key=lambda x: x[1], reverse=True):
        shares = INITIAL_POSITIONS[etf]
        value = shares * latest_prices[etf]
        print(f"  {etf}: {weight:7.2%}  ({shares:>8,.0f} shares, {format_currency(value):>12s})")
    print("✓ Cell 4 passed")
except Exception as e:
    print(f"✗ Cell 4 failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ========== Cell 5: Calculate Target Weights ==========
print("\n[TEST] Cell 5: Calculate Target Weights (Risk Parity)")
try:
    hist_end_idx = prices.index.get_loc(prices.index[-1])
    hist_start_idx = max(0, hist_end_idx - LOOKBACK)
    hist_returns = prices.iloc[hist_start_idx:hist_end_idx].pct_change().dropna()

    print(f"Using {len(hist_returns)} days of returns for optimization")
    print(f"Period: {hist_returns.index[0].date()} to {hist_returns.index[-1].date()}")

    target_weights_array = optimize_weights(hist_returns, use_shrinkage=True)
    target_weights = dict(zip(prices.columns, target_weights_array))

    print_section("Target Weights (Risk Parity v1.2)")
    print("\nOptimal allocation:")
    for etf, weight in sorted(target_weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {etf}: {weight:7.2%}")
    print("✓ Cell 5 passed")
except Exception as e:
    print(f"✗ Cell 5 failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ========== Cell 6: Calculate Rebalancing Trades ==========
print("\n[TEST] Cell 6: Calculate Rebalancing Trades")
try:
    def calculate_drift(current_weights, target_weights):
        max_drift = 0.0
        for etf in current_weights.keys():
            drift = abs(current_weights[etf] - target_weights[etf])
            max_drift = max(max_drift, drift)
        return max_drift

    def round_to_lot_size(shares, etf):
        if etf == '511260.SH':
            return round(shares / 100) * 100
        else:
            return round(shares)

    def calculate_rebalance_trades(current_positions, target_weights, prices_series, total_value, cash):
        trades = {}

        for etf in current_positions.keys():
            target_value = total_value * target_weights[etf]
            target_shares = target_value / prices_series[etf]
            target_shares_rounded = round_to_lot_size(target_shares, etf)

            current_shares = current_positions[etf]
            trade_shares = target_shares_rounded - current_shares

            if trade_shares != 0:
                trade_value = trade_shares * prices_series[etf]
                commission = abs(trade_value) * COMMISSION_RATE

                trades[etf] = {
                    'current_shares': current_shares,
                    'target_shares': target_shares_rounded,
                    'trade_shares': trade_shares,
                    'price': prices_series[etf],
                    'trade_value': trade_value,
                    'commission': commission,
                    'side': 'BUY' if trade_shares > 0 else 'SELL'
                }

        return trades

    drift = calculate_drift(current_weights, target_weights)
    needs_rebalance = drift > REBALANCE_THRESHOLD

    print_section("Rebalancing Analysis")
    print(f"\nMaximum drift: {drift:.2%}")
    print(f"Rebalance threshold: {REBALANCE_THRESHOLD:.2%}")
    print(f"\nNeeds rebalancing: {'YES ✓' if needs_rebalance else 'NO - within threshold'}")

    if needs_rebalance:
        trades = calculate_rebalance_trades(
            INITIAL_POSITIONS,
            target_weights,
            latest_prices,
            current_value,
            INITIAL_CASH
        )

        if trades:
            print("\n" + "="*70)
            print("REQUIRED TRADES")
            print("="*70)

            total_commission = 0

            for etf, trade in trades.items():
                print(f"\n{etf}:")
                print(f"  Current: {trade['current_shares']:,.0f} shares")
                print(f"  Target:  {trade['target_shares']:,.0f} shares")
                print(f"  Action:  {trade['side']} {abs(trade['trade_shares']):,.0f} shares @ ¥{trade['price']:.4f}")
                print(f"  Value:   {format_currency(abs(trade['trade_value']))}")
                print(f"  Commission: {format_currency(trade['commission'])}")

                total_commission += trade['commission']

            print(f"\nTotal Commission: {format_currency(total_commission)}")
    print("✓ Cell 6 passed")
except Exception as e:
    print(f"✗ Cell 6 failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ========== Cell 7: PnL Tracking ==========
print("\n[TEST] Cell 7: PnL Tracking")
try:
    start_date_idx = prices.index.get_loc(pd.Timestamp(START_DATE))
    tracking_prices = prices.iloc[start_date_idx:]

    daily_values = []
    daily_pnl = []

    initial_value = calculate_portfolio_value(INITIAL_POSITIONS, prices.loc[START_DATE], INITIAL_CASH)

    for date, row in tracking_prices.iterrows():
        daily_value = calculate_portfolio_value(INITIAL_POSITIONS, row, INITIAL_CASH)
        pnl = daily_value - initial_value

        daily_values.append(daily_value)
        daily_pnl.append(pnl)

    pnl_df = pd.DataFrame({
        'Date': tracking_prices.index,
        'Portfolio Value': daily_values,
        'PnL': daily_pnl,
        'PnL %': [p / initial_value * 100 if initial_value > 0 else 0 for p in daily_pnl]
    }).set_index('Date')

    print_section("PnL Summary")
    print(f"\nInitial Value ({START_DATE}): {format_currency(initial_value)}")
    print(f"Current Value ({tracking_prices.index[-1].date()}): {format_currency(daily_values[-1])}")
    print(f"\nTotal PnL: {format_currency(daily_pnl[-1])} ({pnl_df['PnL %'].iloc[-1]:+.2f}%)")
    print(f"Days tracked: {len(pnl_df)}")

    if len(pnl_df) > 1:
        print(f"\nBest day: {format_currency(pnl_df['PnL'].max())} on {pnl_df['PnL'].idxmax().date()}")
        print(f"Worst day: {format_currency(pnl_df['PnL'].min())} on {pnl_df['PnL'].idxmin().date()}")

    print("\nRecent PnL:")
    print(pnl_df.tail())
    print("✓ Cell 7 passed")
except Exception as e:
    print(f"✗ Cell 7 failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ========== Cell 8: PnL Visualization ==========
print("\n[TEST] Cell 8: PnL Visualization")
try:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Portfolio value over time
    ax1.plot(pnl_df.index, pnl_df['Portfolio Value'], linewidth=2.5, color='#2ca02c')
    ax1.axhline(y=initial_value, color='gray', linestyle='--', alpha=0.5, label='Initial Value')
    ax1.set_title(f'Portfolio Value (since {START_DATE})', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Value (¥)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x/1e6:.2f}M' if x >= 1e6 else f'¥{x:,.0f}'))

    # Cumulative PnL
    colors = ['green' if x >= 0 else 'red' for x in pnl_df['PnL']]
    ax2.bar(pnl_df.index, pnl_df['PnL'], color=colors, alpha=0.7, width=0.8)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax2.set_title('Daily PnL', fontsize=14, fontweight='bold')
    ax2.set_ylabel('PnL (¥)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}'))

    plt.tight_layout()

    # Don't show in test, just verify it can create the plot
    plt.close(fig)

    print(f"\n{'='*70}")
    print(f"Last updated: {TODAY_CHICAGO.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"{'='*70}")
    print("✓ Cell 8 passed")
except Exception as e:
    print(f"✗ Cell 8 failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("ALL CELLS PASSED ✓")
print("="*70)
print("\nThe notebook is ready to use!")
