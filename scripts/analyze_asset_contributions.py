"""
Analyze profit contribution by asset for All Weather v1.2.

This script calculates how much profit each asset contributed to the total
portfolio returns over the backtest period.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.data_loader import load_prices
from src.strategy import AllWeatherV1

# Load data
print("Loading data...")
prices = load_prices('data/etf_prices_7etf.csv')

# Run v1.2 strategy
print("\nRunning v1.2 backtest (2018-2026)...")
strategy = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.05,  # v1.2
    use_shrinkage=True  # v1.2
)

results = strategy.run_backtest(start_date='2018-01-01')

# Get portfolio history
portfolio_history = results['portfolio_history']

# Calculate asset-level profit contributions
print("\nCalculating asset profit contributions...")
print("=" * 80)

asset_profits = {}
asset_weights_avg = {}

for asset in prices.columns:
    # Get position values over time for this asset
    asset_values = portfolio_history[f'{asset}_value']

    # Calculate profit: final value - total invested
    # We need to track the cumulative investment in each asset
    # For simplicity, we'll use the change in position value

    # Initial value (first non-zero value)
    first_value = asset_values[asset_values > 0].iloc[0] if (asset_values > 0).any() else 0
    final_value = asset_values.iloc[-1]

    # Profit is the difference between final and initial values
    # But this doesn't account for capital added/removed during rebalancing
    # Better approach: calculate daily returns and multiply by daily position values

    # Get daily returns for this asset
    asset_returns = prices[asset].pct_change()

    # Align with portfolio history dates
    asset_returns = asset_returns.reindex(portfolio_history.index)

    # Daily profit = position value * daily return
    daily_profits = asset_values.shift(1) * asset_returns

    # Total profit from this asset
    total_profit = daily_profits.sum()

    asset_profits[asset] = total_profit

    # Calculate average weight
    portfolio_values = portfolio_history['portfolio_value']
    asset_weights = asset_values / portfolio_values
    avg_weight = asset_weights.mean()
    asset_weights_avg[asset] = avg_weight

# Convert to DataFrame for better display
profit_df = pd.DataFrame({
    'Asset': list(asset_profits.keys()),
    'Profit (¥)': list(asset_profits.values()),
    'Avg Weight': list(asset_weights_avg.values())
})

# Add asset names
asset_names = {
    '510300.SH': 'CSI 300 (Large-cap)',
    '510500.SH': 'CSI 500 (Mid-cap)',
    '513500.SH': 'S&P 500',
    '511260.SH': '10Y Treasury',
    '518880.SH': 'Gold',
    '000066.SH': 'China Bond',
    '513100.SH': 'Nasdaq-100'
}

profit_df['Name'] = profit_df['Asset'].map(asset_names)

# Calculate profit percentage
total_profit = results['metrics']['final_value'] - results['metrics']['initial_capital']
profit_df['Profit %'] = (profit_df['Profit (¥)'] / total_profit * 100)

# Sort by profit
profit_df = profit_df.sort_values('Profit (¥)', ascending=False)

# Add asset class
asset_classes = {
    '510300.SH': 'Stock',
    '510500.SH': 'Stock',
    '513500.SH': 'Stock',
    '511260.SH': 'Bond',
    '518880.SH': 'Commodity',
    '000066.SH': 'Bond',
    '513100.SH': 'Stock'
}
profit_df['Class'] = profit_df['Asset'].map(asset_classes)

# Display results
print("\nPROFIT CONTRIBUTION BY ASSET (v1.2, 2018-2026)")
print("=" * 80)
print(f"\nTotal Portfolio Profit: ¥{total_profit:,.0f}")
print(f"Initial Capital: ¥{results['metrics']['initial_capital']:,.0f}")
print(f"Final Value: ¥{results['metrics']['final_value']:,.0f}")
print(f"Total Return: {(results['metrics']['final_value'] / results['metrics']['initial_capital'] - 1) * 100:.2f}%")
print("\n" + "=" * 80)
print(f"{'Rank':<6}{'Asset':<15}{'Name':<25}{'Class':<12}{'Avg Weight':<12}{'Profit (¥)':<15}{'% of Total'}")
print("=" * 80)

for idx, row in profit_df.iterrows():
    rank = profit_df.index.get_loc(idx) + 1
    print(f"{rank:<6}{row['Asset']:<15}{row['Name']:<25}{row['Class']:<12}{row['Avg Weight']:>10.1%}  "
          f"{row['Profit (¥)']:>13,.0f}  {row['Profit %']:>8.1f}%")

print("=" * 80)

# Summary by asset class
print("\n\nPROFIT CONTRIBUTION BY ASSET CLASS")
print("=" * 80)

class_summary = profit_df.groupby('Class').agg({
    'Profit (¥)': 'sum',
    'Avg Weight': 'sum'
})
class_summary['Profit %'] = (class_summary['Profit (¥)'] / total_profit * 100)
class_summary = class_summary.sort_values('Profit (¥)', ascending=False)

print(f"{'Asset Class':<15}{'Avg Weight':<15}{'Profit (¥)':<15}{'% of Total'}")
print("=" * 80)
for asset_class, row in class_summary.iterrows():
    print(f"{asset_class:<15}{row['Avg Weight']:>13.1%}  {row['Profit (¥)']:>13,.0f}  {row['Profit %']:>8.1f}%")

print("=" * 80)

# Key insights
print("\n\nKEY INSIGHTS")
print("=" * 80)

top_asset = profit_df.iloc[0]
worst_asset = profit_df.iloc[-1]

print(f"1. Top Performer: {top_asset['Name']} ({top_asset['Asset']})")
print(f"   - Contributed ¥{top_asset['Profit (¥)']:,.0f} ({top_asset['Profit %']:.1f}% of total profit)")
print(f"   - Average weight: {top_asset['Avg Weight']:.1%}")

print(f"\n2. Worst Performer: {worst_asset['Name']} ({worst_asset['Asset']})")
print(f"   - Contributed ¥{worst_asset['Profit (¥)']:,.0f} ({worst_asset['Profit %']:.1f}% of total profit)")
print(f"   - Average weight: {worst_asset['Avg Weight']:.1%}")

# Calculate return per unit weight for efficiency
profit_df['Return per Weight'] = profit_df['Profit (¥)'] / profit_df['Avg Weight']
most_efficient = profit_df.sort_values('Return per Weight', ascending=False).iloc[0]

print(f"\n3. Most Efficient (highest return per unit weight): {most_efficient['Name']}")
print(f"   - Return per 1% weight: ¥{most_efficient['Return per Weight']:,.0f}")

# Risk parity check
print(f"\n4. Risk Parity Balance:")
print(f"   - Bonds contribute {class_summary.loc['Bond', 'Avg Weight']:.1%} weight → "
      f"{class_summary.loc['Bond', 'Profit %']:.1f}% of profit")
print(f"   - Stocks contribute {class_summary.loc['Stock', 'Avg Weight']:.1%} weight → "
      f"{class_summary.loc['Stock', 'Profit %']:.1f}% of profit")
print(f"   - Commodities contribute {class_summary.loc['Commodity', 'Avg Weight']:.1%} weight → "
      f"{class_summary.loc['Commodity', 'Profit %']:.1f}% of profit")

print("\n" + "=" * 80)
print("\nNOTE: In risk parity, all assets contribute EQUAL RISK, not equal returns.")
print("Bonds have high weights but lower returns. Stocks have low weights but higher returns.")
print("=" * 80)
