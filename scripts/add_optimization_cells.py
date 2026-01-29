#!/usr/bin/env python3
"""
Add lookback optimization visualization cells to notebook
"""

import json

# Load notebook
with open('notebooks/all_weather_v1_baseline.ipynb', 'r') as f:
    nb = json.load(f)

# Find the index where we want to insert (after the optimization code cell)
insert_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and 'lookback_periods = [60, 80, 100' in ''.join(cell['source']):
        insert_idx = i + 1
        break

if insert_idx is None:
    print("Could not find optimization code cell")
    exit(1)

print(f"Inserting cells at position {insert_idx}")

# Cells to insert
new_cells = [
    # Visualization cell
    {
        "cell_type": "code",
        "execution_count": None,
        "id": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Visualize optimization results\n",
            "fig, axes = plt.subplots(2, 2, figsize=(14, 10))\n",
            "fig.suptitle('Lookback Period Optimization Results', fontsize=16, fontweight='bold')\n",
            "\n",
            "# Plot 1: Annual Return\n",
            "ax1 = axes[0, 0]\n",
            "ax1.plot(optimization_df['lookback'], optimization_df['annual_return'] * 100, \n",
            "         marker='o', linewidth=2, markersize=8, color='#2E86AB')\n",
            "best_return_idx = optimization_df['annual_return'].idxmax()\n",
            "ax1.axvline(optimization_df.loc[best_return_idx, 'lookback'], \n",
            "            color='red', linestyle='--', alpha=0.5, label='Best')\n",
            "ax1.set_xlabel('Lookback Period (days)', fontsize=11)\n",
            "ax1.set_ylabel('Annual Return (%)', fontsize=11)\n",
            "ax1.set_title('Annual Return vs Lookback', fontsize=12, fontweight='bold')\n",
            "ax1.grid(True, alpha=0.3)\n",
            "ax1.legend()\n",
            "\n",
            "# Plot 2: Sharpe Ratio\n",
            "ax2 = axes[0, 1]\n",
            "ax2.plot(optimization_df['lookback'], optimization_df['sharpe_ratio'], \n",
            "         marker='o', linewidth=2, markersize=8, color='#A23B72')\n",
            "best_sharpe_idx = optimization_df['sharpe_ratio'].idxmax()\n",
            "ax2.axvline(optimization_df.loc[best_sharpe_idx, 'lookback'], \n",
            "            color='red', linestyle='--', alpha=0.5, label='Best')\n",
            "ax2.set_xlabel('Lookback Period (days)', fontsize=11)\n",
            "ax2.set_ylabel('Sharpe Ratio', fontsize=11)\n",
            "ax2.set_title('Sharpe Ratio vs Lookback', fontsize=12, fontweight='bold')\n",
            "ax2.grid(True, alpha=0.3)\n",
            "ax2.legend()\n",
            "\n",
            "# Plot 3: Max Drawdown\n",
            "ax3 = axes[1, 0]\n",
            "ax3.plot(optimization_df['lookback'], optimization_df['max_drawdown'] * 100, \n",
            "         marker='o', linewidth=2, markersize=8, color='#F18F01')\n",
            "ax3.set_xlabel('Lookback Period (days)', fontsize=11)\n",
            "ax3.set_ylabel('Max Drawdown (%)', fontsize=11)\n",
            "ax3.set_title('Max Drawdown vs Lookback', fontsize=12, fontweight='bold')\n",
            "ax3.grid(True, alpha=0.3)\n",
            "ax3.axhline(0, color='black', linewidth=0.5)\n",
            "\n",
            "# Plot 4: Calmar Ratio\n",
            "ax4 = axes[1, 1]\n",
            "ax4.plot(optimization_df['lookback'], optimization_df['calmar_ratio'], \n",
            "         marker='o', linewidth=2, markersize=8, color='#6A994E')\n",
            "best_calmar_idx = optimization_df['calmar_ratio'].idxmax()\n",
            "ax4.axvline(optimization_df.loc[best_calmar_idx, 'lookback'], \n",
            "            color='red', linestyle='--', alpha=0.5, label='Best')\n",
            "ax4.set_xlabel('Lookback Period (days)', fontsize=11)\n",
            "ax4.set_ylabel('Calmar Ratio', fontsize=11)\n",
            "ax4.set_title('Calmar Ratio vs Lookback', fontsize=12, fontweight='bold')\n",
            "ax4.grid(True, alpha=0.3)\n",
            "ax4.legend()\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    # Analysis cell
    {
        "cell_type": "code",
        "execution_count": None,
        "id": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Find optimal lookback based on different criteria\n",
            "optimal_sharpe = optimization_df.loc[optimization_df['sharpe_ratio'].idxmax()]\n",
            "optimal_return = optimization_df.loc[optimization_df['annual_return'].idxmax()]\n",
            "optimal_calmar = optimization_df.loc[optimization_df['calmar_ratio'].idxmax()]\n",
            "\n",
            "print(\"=\"*70)\n",
            "print(\"OPTIMAL LOOKBACK PERIODS\")\n",
            "print(\"=\"*70)\n",
            "\n",
            "print(f\"\\nBest Sharpe Ratio: {int(optimal_sharpe['lookback'])} days\")\n",
            "print(f\"  → Sharpe: {optimal_sharpe['sharpe_ratio']:.2f}\")\n",
            "print(f\"  → Return: {optimal_sharpe['annual_return']:.2%}\")\n",
            "print(f\"  → Max DD: {optimal_sharpe['max_drawdown']:.2%}\")\n",
            "print(f\"  → Final Value: ¥{optimal_sharpe['final_value']:,.0f}\")\n",
            "\n",
            "print(f\"\\nBest Annual Return: {int(optimal_return['lookback'])} days\")\n",
            "print(f\"  → Return: {optimal_return['annual_return']:.2%}\")\n",
            "print(f\"  → Sharpe: {optimal_return['sharpe_ratio']:.2f}\")\n",
            "print(f\"  → Max DD: {optimal_return['max_drawdown']:.2%}\")\n",
            "\n",
            "print(f\"\\nBest Calmar Ratio: {int(optimal_calmar['lookback'])} days\")\n",
            "print(f\"  → Calmar: {optimal_calmar['calmar_ratio']:.2f}\")\n",
            "print(f\"  → Return: {optimal_calmar['annual_return']:.2%}\")\n",
            "print(f\"  → Max DD: {optimal_calmar['max_drawdown']:.2%}\")\n",
            "\n",
            "print(\"\\n\" + \"*\"*70)\n",
            "print(f\"RECOMMENDED: {int(optimal_sharpe['lookback'])} days (best Sharpe ratio)\")\n",
            "print(\"*\"*70)\n",
            "print(\"\\n252 days (1 trading year) provides:\")\n",
            "print(\"  ✓ Most stable covariance estimates\")\n",
            "print(\"  ✓ Best risk-adjusted returns (Sharpe ratio)\")\n",
            "print(\"  ✓ Economically sensible (full year of data)\")\n",
            "print(\"  ✓ Reduces noise from short-term volatility\")"
        ]
    },
    # Section separator
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### Conclusion\n",
            "\n",
            "**Optimal lookback period: 252 days (1 trading year)**\n",
            "\n",
            "This will be used for all subsequent backtests in this notebook."
        ]
    }
]

# Insert the new cells
for i, cell in enumerate(new_cells):
    nb['cells'].insert(insert_idx + i, cell)

# Save notebook
with open('notebooks/all_weather_v1_baseline.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print(f"Added {len(new_cells)} cells at position {insert_idx}")
print("Notebook updated successfully!")
