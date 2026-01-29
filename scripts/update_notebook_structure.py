#!/usr/bin/env python3
"""
Update notebook:
1. Remove lookback optimization section
2. Add trading instructions section at the end
"""

import json

# Load notebook
with open('notebooks/all_weather_v1_baseline.ipynb', 'r') as f:
    nb = json.load(f)

# Find and remove optimization cells (cells with lookback optimization content)
cells_to_remove = []
for i, cell in enumerate(nb['cells']):
    source = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']

    # Mark cells to remove
    if any(marker in source for marker in [
        '## 4. Lookback Period Optimization',
        'lookback_periods = [60, 80, 100',
        'Lookback Period Optimization Results',
        'OPTIMAL LOOKBACK PERIODS',
        '### Conclusion'
    ]):
        if '### Conclusion' in source and '252 days' in source:
            cells_to_remove.append(i)
        elif '## 4. Lookback Period Optimization' in source:
            cells_to_remove.append(i)
        elif 'lookback_periods = [60, 80, 100' in source:
            cells_to_remove.append(i)
        elif 'Lookback Period Optimization Results' in source:
            cells_to_remove.append(i)
        elif 'OPTIMAL LOOKBACK PERIODS' in source:
            cells_to_remove.append(i)

# Remove cells in reverse order to maintain indices
for i in sorted(cells_to_remove, reverse=True):
    print(f"Removing cell {i}")
    nb['cells'].pop(i)

# Renumber sections (5-10 back to 4-9)
renumber_map = {
    '## 5. Run Backtest': '## 4. Run Backtest',
    '## 6. Plot Equity Curve': '## 5. Plot Equity Curve',
    '## 7. Performance Metrics': '## 6. Performance Metrics',
    '## 8. Weight Evolution Over Time': '## 7. Weight Evolution Over Time',
    '## 9. Risk Contribution Analysis': '## 8. Risk Contribution Analysis',
    '## 10. Export Results': '## 9. Export Results'
}

for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        source = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
        for old, new in renumber_map.items():
            if source.startswith(old):
                cell['source'] = [new + source[len(old):]]
                print(f"Renumbered: {old} → {new}")
                break

# Add new trading instructions section at the end
new_cells = [
    {
        "cell_type": "markdown",
        "execution_count": None,
        "id": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "## 10. Trading Instructions (Forward-Looking)\n",
            "\n",
            "Generate actionable trading instructions for implementing the All Weather strategy with ¥30,000 initial capital.\n",
            "\n",
            "This section provides:\n",
            "- Exact number of shares to buy for each ETF\n",
            "- Next rebalancing dates\n",
            "- Portfolio tracking with PnL\n",
            "- Transaction costs included"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "id": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Trading parameters\n",
            "INITIAL_CAPITAL = 30_000  # ¥30,000 starting capital\n",
            "COMMISSION_RATE = 0.0003  # 0.03% commission\n",
            "\n",
            "# Get current prices (latest available)\n",
            "current_prices = prices.iloc[-1]\n",
            "current_date = prices.index[-1]\n",
            "\n",
            "print(\"=\"*70)\n",
            "print(\"ALL WEATHER STRATEGY - TRADING INSTRUCTIONS\")\n",
            "print(\"=\"*70)\n",
            "print(f\"\\nCurrent Date: {current_date.date()}\")\n",
            "print(f\"Initial Capital: ¥{INITIAL_CAPITAL:,.0f}\")\n",
            "print(f\"Commission Rate: {COMMISSION_RATE:.2%}\")\n",
            "\n",
            "# Calculate current risk parity weights\n",
            "recent_returns = prices.tail(252).pct_change().dropna()\n",
            "current_weights = optimize_weights(recent_returns)\n",
            "\n",
            "print(\"\\n\" + \"-\"*70)\n",
            "print(\"TARGET ALLOCATION (Risk Parity Weights)\")\n",
            "print(\"-\"*70)\n",
            "\n",
            "weight_allocation = pd.DataFrame({\n",
            "    'ETF': prices.columns,\n",
            "    'Weight': current_weights,\n",
            "    'Target Value (¥)': current_weights * INITIAL_CAPITAL\n",
            "}).sort_values('Weight', ascending=False)\n",
            "\n",
            "print(weight_allocation.to_string(index=False))\n",
            "print(f\"\\nTotal: {current_weights.sum():.4f}\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "id": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Calculate exact shares to buy (round to 100-share lots for A-shares)\n",
            "print(\"\\n\" + \"=\"*70)\n",
            "print(\"INITIAL PURCHASE INSTRUCTIONS\")\n",
            "print(\"=\"*70)\n",
            "print(f\"\\nExecute on: {current_date.date()} (or next trading day)\")\n",
            "print(\"\\n\" + \"-\"*70)\n",
            "\n",
            "trades = []\n",
            "total_cost = 0\n",
            "remaining_cash = INITIAL_CAPITAL\n",
            "\n",
            "for etf, weight, target_value in weight_allocation.values:\n",
            "    price = current_prices[etf]\n",
            "    \n",
            "    # Calculate shares (round to 100-share lots)\n",
            "    shares = round(target_value / price / 100) * 100\n",
            "    \n",
            "    if shares > 0:\n",
            "        cost = shares * price\n",
            "        commission = cost * COMMISSION_RATE\n",
            "        total_cost_with_commission = cost + commission\n",
            "        \n",
            "        # Check if we have enough cash\n",
            "        if total_cost_with_commission <= remaining_cash:\n",
            "            trades.append({\n",
            "                'ETF': etf,\n",
            "                'Shares': int(shares),\n",
            "                'Price': price,\n",
            "                'Cost': cost,\n",
            "                'Commission': commission,\n",
            "                'Total': total_cost_with_commission\n",
            "            })\n",
            "            remaining_cash -= total_cost_with_commission\n",
            "            total_cost += total_cost_with_commission\n",
            "\n",
            "trades_df = pd.DataFrame(trades)\n",
            "\n",
            "print(f\"{'ETF':<15} {'Shares':>8} {'Price':>10} {'Cost':>12} {'Commission':>12} {'Total':>12}\")\n",
            "print(\"-\"*70)\n",
            "\n",
            "for _, row in trades_df.iterrows():\n",
            "    print(f\"{row['ETF']:<15} {row['Shares']:>8,} {row['Price']:>10.2f} \"\n",
            "          f\"{row['Cost']:>12,.2f} {row['Commission']:>12,.2f} {row['Total']:>12,.2f}\")\n",
            "\n",
            "print(\"-\"*70)\n",
            "print(f\"{'TOTAL':<15} {'':<8} {'':<10} {'':<12} {'':<12} {total_cost:>12,.2f}\")\n",
            "print(f\"\\nRemaining Cash: ¥{remaining_cash:,.2f}\")\n",
            "print(f\"Total Invested: ¥{total_cost:,.2f} ({total_cost/INITIAL_CAPITAL:.1%})\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "id": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Calculate next rebalancing dates (weekly on Mondays)\n",
            "from datetime import timedelta\n",
            "\n",
            "print(\"\\n\" + \"=\"*70)\n",
            "print(\"REBALANCING SCHEDULE\")\n",
            "print(\"=\"*70)\n",
            "\n",
            "# Find next Monday\n",
            "days_ahead = 0 - current_date.weekday()\n",
            "if days_ahead <= 0:\n",
            "    days_ahead += 7\n",
            "next_monday = current_date + timedelta(days=days_ahead)\n",
            "\n",
            "print(\"\\nNext 5 rebalancing dates (Weekly Mondays):\")\n",
            "for i in range(5):\n",
            "    rebal_date = next_monday + timedelta(weeks=i)\n",
            "    print(f\"  {i+1}. {rebal_date.date()}\")\n",
            "\n",
            "print(\"\\n⚠️  IMPORTANT REBALANCING NOTES:\")\n",
            "print(\"  - Rebalance every Monday (or next trading day if holiday)\")\n",
            "print(\"  - Use 252-day lookback to recalculate weights\")\n",
            "print(\"  - Buy/sell to match target allocation\")\n",
            "print(\"  - Include 0.03% commission in calculations\")\n",
            "print(\"  - Track portfolio value changes (PnL affects next rebalance)\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "id": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Show portfolio tracking template\n",
            "print(\"\\n\" + \"=\"*70)\n",
            "print(\"PORTFOLIO TRACKING TEMPLATE\")\n",
            "print(\"=\"*70)\n",
            "\n",
            "print(\"\\nAfter initial purchase, track your portfolio like this:\\n\")\n",
            "\n",
            "# Create tracking table\n",
            "tracking = pd.DataFrame({\n",
            "    'ETF': [row['ETF'] for _, row in trades_df.iterrows()],\n",
            "    'Shares': [int(row['Shares']) for _, row in trades_df.iterrows()],\n",
            "    'Purchase Price': [row['Price'] for _, row in trades_df.iterrows()],\n",
            "    'Current Price': ['[UPDATE]'] * len(trades_df),\n",
            "    'Market Value': ['[CALC]'] * len(trades_df),\n",
            "    'PnL': ['[CALC]'] * len(trades_df)\n",
            "})\n",
            "\n",
            "print(tracking.to_string(index=False))\n",
            "\n",
            "print(\"\\n\" + \"-\"*70)\n",
            "print(\"Instructions:\")\n",
            "print(\"  1. Update 'Current Price' with latest ETF prices\")\n",
            "print(\"  2. Calculate 'Market Value' = Shares × Current Price\")\n",
            "print(\"  3. Calculate 'PnL' = Market Value - (Shares × Purchase Price)\")\n",
            "print(\"  4. Total Portfolio Value = Sum(Market Value) + Cash\")\n",
            "print(\"  5. On rebalance day: Calculate new target allocation based on total value\")\n",
            "print(\"  6. Execute trades to match new targets (account for commissions)\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "id": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Example: What to do at first rebalance\n",
            "print(\"\\n\" + \"=\"*70)\n",
            "print(\"EXAMPLE: FIRST REBALANCE PROCEDURE\")\n",
            "print(\"=\"*70)\n",
            "\n",
            "print(f\"\\nDate: {next_monday.date()} (Next Monday)\\n\")\n",
            "\n",
            "print(\"Step 1: Calculate Portfolio Value\")\n",
            "print(\"-\" * 40)\n",
            "print(\"  • Get current prices for all holdings\")\n",
            "print(\"  • Calculate: Total Value = Sum(Shares × Current Price) + Cash\")\n",
            "print(\"  • Example: If portfolio grew to ¥30,500\")\n",
            "\n",
            "print(\"\\nStep 2: Recalculate Risk Parity Weights\")\n",
            "print(\"-\" * 40)\n",
            "print(\"  • Use latest 252 days of price data\")\n",
            "print(\"  • Run: weights = optimize_weights(returns.tail(252))\")\n",
            "print(\"  • Calculate new target values = weights × Total Value\")\n",
            "\n",
            "print(\"\\nStep 3: Calculate Required Trades\")\n",
            "print(\"-\" * 40)\n",
            "print(\"  • For each ETF:\")\n",
            "print(\"    - Current Value = Shares × Current Price\")\n",
            "print(\"    - Target Value = Weight × Total Portfolio Value\")\n",
            "print(\"    - Trade Value = Target Value - Current Value\")\n",
            "print(\"    - Shares to Trade = round(Trade Value / Price / 100) × 100\")\n",
            "\n",
            "print(\"\\nStep 4: Execute Trades\")\n",
            "print(\"-\" * 40)\n",
            "print(\"  • Buy if shares > 0, Sell if shares < 0\")\n",
            "print(\"  • Account for 0.03% commission on each trade\")\n",
            "print(\"  • Update cash: Cash -= (Trade Value + Commission)\")\n",
            "\n",
            "print(\"\\nStep 5: Update Portfolio Record\")\n",
            "print(\"-\" * 40)\n",
            "print(\"  • Record new share counts\")\n",
            "print(\"  • Record new purchase prices (cost basis)\")\n",
            "print(\"  • Update remaining cash\")\n",
            "print(\"  • Wait until next Monday for next rebalance\")\n",
            "\n",
            "print(\"\\n\" + \"=\"*70)\n",
            "print(\"📊 Keep this notebook handy for future rebalancing!\")\n",
            "print(\"=\"*70)"
        ]
    }
]

# Add new cells at the end
for cell in new_cells:
    nb['cells'].append(cell)

# Save notebook
with open('notebooks/all_weather_v1_baseline.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print(f"\nNotebook updated successfully!")
print(f"- Removed {len(cells_to_remove)} optimization cells")
print(f"- Renumbered sections 5-10 → 4-9")
print(f"- Added {len(new_cells)} trading instruction cells")
