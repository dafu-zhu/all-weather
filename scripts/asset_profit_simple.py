"""
Analyze profit contribution by asset for All Weather v1.2.

Simple approach using average weights and asset returns.
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
    use_shrinkage=True,  # v1.2
)

results = strategy.run_backtest(start_date='2018-01-01', verbose=False)

# Get backtest period
start_date = '2018-01-01'
end_date = results['equity_curve'].index[-1]

# Filter prices to backtest period
backtest_prices = prices.loc[start_date:end_date]

# Calculate asset returns over the full period
asset_returns = {}
for asset in backtest_prices.columns:
    start_price = backtest_prices[asset].iloc[0]
    end_price = backtest_prices[asset].iloc[-1]
    total_return = (end_price / start_price - 1)
    asset_returns[asset] = total_return

# Get average weights from weights_history
weights_df = results['weights_history']

if len(weights_df) > 0:
    avg_weights = weights_df.mean()
else:
    # Fallback: equal weights
    avg_weights = pd.Series({asset: 1/len(backtest_prices.columns) for asset in backtest_prices.columns})

# Calculate profit contribution
# Profit contribution ≈ avg_weight × total_return × initial_capital
total_profit = results['final_value'] - strategy.initial_capital

profit_contributions = {}
for asset in backtest_prices.columns:
    # Contribution = weight × asset return × initial capital
    avg_weight = avg_weights.get(asset, 0)
    asset_return = asset_returns[asset]
    contribution = avg_weight * asset_return * strategy.initial_capital
    profit_contributions[asset] = contribution

# Create DataFrame
profit_df = pd.DataFrame({
    'Asset': list(profit_contributions.keys()),
    'Avg Weight': [avg_weights.get(a, 0) for a in profit_contributions.keys()],
    'Total Return': [asset_returns[a] for a in profit_contributions.keys()],
    'Profit (¥)': list(profit_contributions.values())
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

# Calculate percentage of total profit
profit_df['Profit %'] = (profit_df['Profit (¥)'] / total_profit * 100)

# Sort by profit
profit_df = profit_df.sort_values('Profit (¥)', ascending=False)

# Display results
print("\n" + "=" * 90)
print("PROFIT CONTRIBUTION BY ASSET (v1.2, 2018-2026)")
print("=" * 90)
print(f"\nTotal Portfolio Profit: ¥{total_profit:,.0f}")
print(f"Initial Capital: ¥{strategy.initial_capital:,.0f}")
print(f"Final Value: ¥{results['final_value']:,.0f}")
print(f"Total Return: {(results['final_value'] / strategy.initial_capital - 1) * 100:.2f}%")
print(f"\nNote: Profit contribution = Avg Weight × Asset Return × Initial Capital")
print("=" * 90)

# Individual assets
print(f"\n{'Rank':<6}{'Asset':<15}{'Name':<25}{'Class':<10}{'Avg Wt':<10}{'Return':<10}{'Profit (¥)':<15}{'% Total'}")
print("=" * 90)

for idx, row in profit_df.iterrows():
    rank = profit_df.index.get_loc(idx) + 1
    print(f"{rank:<6}{row['Asset']:<15}{row['Name']:<25}{row['Class']:<10}"
          f"{row['Avg Weight']:>8.1%}  {row['Total Return']:>8.1%}  "
          f"{row['Profit (¥)']:>13,.0f}  {row['Profit %']:>6.1f}%")

print("=" * 90)

# Summary by asset class
print("\n\nPROFIT CONTRIBUTION BY ASSET CLASS")
print("=" * 90)

class_summary = profit_df.groupby('Class').agg({
    'Avg Weight': 'sum',
    'Profit (¥)': 'sum'
})
class_summary['Profit %'] = (class_summary['Profit (¥)'] / total_profit * 100)
class_summary['Avg Return'] = class_summary['Profit (¥)'] / (class_summary['Avg Weight'] * strategy.initial_capital)
class_summary = class_summary.sort_values('Profit (¥)', ascending=False)

print(f"{'Asset Class':<15}{'Avg Weight':<15}{'Profit (¥)':<18}{'% of Total':<15}{'Avg Return'}")
print("=" * 90)
for asset_class, row in class_summary.iterrows():
    print(f"{asset_class:<15}{row['Avg Weight']:>13.1%}  {row['Profit (¥)']:>15,.0f}  "
          f"{row['Profit %']:>11.1f}%  {row['Avg Return']:>13.1%}")

print("=" * 90)

# Key insights
print("\n\nKEY INSIGHTS")
print("=" * 90)

top_asset = profit_df.iloc[0]
worst_asset = profit_df.iloc[-1]

print(f"1. TOP PROFIT GENERATOR: {top_asset['Name']} ({top_asset['Asset']})")
print(f"   - Contributed: ¥{top_asset['Profit (¥)']:,.0f} ({top_asset['Profit %']:.1f}% of total profit)")
print(f"   - Average weight: {top_asset['Avg Weight']:.1%}")
print(f"   - Total return: {top_asset['Total Return']:.1%}")

print(f"\n2. WORST PERFORMER: {worst_asset['Name']} ({worst_asset['Asset']})")
if worst_asset['Profit (¥)'] < 0:
    print(f"   - LOST: ¥{abs(worst_asset['Profit (¥)']):,.0f} ({worst_asset['Profit %']:.1f}% of total profit)")
else:
    print(f"   - Contributed: ¥{worst_asset['Profit (¥)']:,.0f} ({worst_asset['Profit %']:.1f}% of total profit)")
print(f"   - Average weight: {worst_asset['Avg Weight']:.1%}")
print(f"   - Total return: {worst_asset['Total Return']:.1%}")

# Return per weight efficiency
profit_df['Efficiency'] = profit_df['Total Return'] / profit_df['Avg Weight']
most_efficient = profit_df.sort_values('Efficiency', ascending=False).iloc[0]

print(f"\n3. MOST EFFICIENT (highest return per unit weight): {most_efficient['Name']}")
print(f"   - Efficiency ratio: {most_efficient['Efficiency']:.2f}")
print(f"   - {most_efficient['Total Return']:.1%} return with only {most_efficient['Avg Weight']:.1%} weight")

# Top 3 contributors
print(f"\n4. TOP 3 PROFIT CONTRIBUTORS:")
for i, (idx, row) in enumerate(profit_df.head(3).iterrows(), 1):
    print(f"   {i}. {row['Name']}: ¥{row['Profit (¥)']:,.0f} ({row['Profit %']:.1f}%)")

# Asset class insights
print(f"\n5. ASSET CLASS PERFORMANCE:")
for asset_class, row in class_summary.iterrows():
    print(f"   {asset_class}s ({row['Avg Weight']:.1%} weight) → ¥{row['Profit (¥)']:,.0f} profit ({row['Profit %']:.1f}%)")

print("\n" + "=" * 90)
print("\nIMPORTANT NOTES:")
print("- In risk parity, all assets contribute EQUAL RISK, not equal returns")
print("- Bonds have HIGH weights but LOWER returns (stability)")
print("- Stocks have LOW weights but HIGHER returns (growth)")
print("- Gold provides diversification (uncorrelated with stocks/bonds)")
print("- The strategy balances risk across all economic environments")
print("=" * 90)
