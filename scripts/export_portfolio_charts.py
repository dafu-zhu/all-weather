#!/usr/bin/env python3
"""
Export Portfolio Charts for Personal Website

Generates clean equity curve and weight evolution charts
for the All Weather strategy portfolio page.
"""

import sys
sys.path.insert(0, '/Users/zdf/Documents/GitHub/all-weather')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from src.optimizer import optimize_weights
from src.backtest import Backtester
from src.data_loader import load_prices

# Output paths
OUTPUT_DIR = Path('/Users/zdf/Documents/GitHub/dafu-zhu.github.io/assets/img/projects')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_charts():
    """Generate and save portfolio charts."""

    # Load data
    prices = load_prices('/Users/zdf/Documents/GitHub/all-weather/data/etf_prices_7etf.csv')
    print(f"Loaded {len(prices)} days of data for {len(prices.columns)} ETFs")

    # Run backtest (v1.0 settings: always rebalance, no shrinkage)
    backtester = Backtester(
        prices=prices,
        initial_capital=1_000_000,
        rebalance_freq='W-MON',
        lookback=252,
        commission_rate=0.0003,
        rebalance_threshold=0,  # Always rebalance (v1.0)
        use_shrinkage=False     # No shrinkage (v1.0)
    )

    print("Running backtest from 2018...")
    results = backtester.run(start_date='2018-01-01')

    equity = results['equity_curve']
    weights_df = results['weights_history']

    # Benchmark (CSI300)
    benchmark = (prices['510300.SH'] / prices['510300.SH'].loc[equity.index[0]]) * 1_000_000
    benchmark = benchmark.loc[equity.index]

    # Chart 1: Equity Curve
    print("\nGenerating equity curve chart...")
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(equity.index, equity / 1e6,
            label='All Weather Portfolio', linewidth=2, color='#2E86AB')
    ax.plot(benchmark.index, benchmark / 1e6,
            label='CSI 300 Benchmark', linewidth=2, alpha=0.7, color='#A23B72')

    ax.set_title('All Weather Strategy - Equity Curve', fontsize=14, fontweight='bold')
    ax.set_ylabel('Portfolio Value (Millions CNY)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0.8)

    # Add performance annotations
    final_return = (equity.iloc[-1] / equity.iloc[0] - 1) * 100
    benchmark_return = (benchmark.iloc[-1] / benchmark.iloc[0] - 1) * 100
    ax.annotate(f'+{final_return:.0f}%',
                xy=(equity.index[-1], equity.iloc[-1] / 1e6),
                xytext=(10, 0), textcoords='offset points',
                fontsize=10, color='#2E86AB', fontweight='bold')
    ax.annotate(f'+{benchmark_return:.0f}%',
                xy=(benchmark.index[-1], benchmark.iloc[-1] / 1e6),
                xytext=(10, 0), textcoords='offset points',
                fontsize=10, color='#A23B72', fontweight='bold')

    plt.tight_layout()
    equity_path = OUTPUT_DIR / 'allweather_equity.png'
    plt.savefig(equity_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved: {equity_path}")

    # Chart 2: Weight Evolution
    print("\nGenerating weight evolution chart...")
    fig, ax = plt.subplots(figsize=(12, 6))

    # Map ETF codes to readable names
    etf_names = {
        '510300.SH': 'CSI 300',
        '510500.SH': 'CSI 500',
        '513500.SH': 'S&P 500',
        '511260.SH': 'Gov Bonds',
        '518880.SH': 'Gold',
        '000066.SH': 'TIPS-like',
        '513100.SH': 'Nasdaq 100'
    }

    # Rename columns for display
    weights_display = weights_df.rename(columns=etf_names)

    # Use a nice color palette
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B', '#7B2D26', '#95B2B8']

    weights_display.plot.area(stacked=True, ax=ax, alpha=0.8, color=colors[:len(weights_display.columns)])

    ax.set_title('Asset Allocation Over Time', fontsize=14, fontweight='bold')
    ax.set_ylabel('Portfolio Weight', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0%}'))

    plt.tight_layout()
    weights_path = OUTPUT_DIR / 'allweather_weights.png'
    plt.savefig(weights_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved: {weights_path}")

    # Print summary
    print("\n" + "="*60)
    print("CHARTS EXPORTED SUCCESSFULLY")
    print("="*60)
    print(f"Equity curve: {equity_path}")
    print(f"Weight evolution: {weights_path}")
    print(f"\nBacktest period: {equity.index[0].date()} to {equity.index[-1].date()}")
    print(f"Final portfolio value: CNY {equity.iloc[-1]:,.0f}")
    print(f"Total return: {final_return:.1f}%")

    return equity_path, weights_path


if __name__ == '__main__':
    generate_charts()
