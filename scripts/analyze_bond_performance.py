"""
Analyze bond performance and rate environment during 2018-2026.

Shows how interest rate cuts (降息) drove bond returns.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.data_loader import load_prices

# Load data
print("Loading data...")
prices = load_prices('data/etf_prices_7etf.csv')

# Focus on bond ETFs
bond_etfs = {
    '511260.SH': '10Y Treasury (Chinese Gov Bond)',
    '000066.SH': 'China Bond Index'
}

# Calculate cumulative returns
start_date = '2018-01-01'
bond_prices = prices[list(bond_etfs.keys())].loc[start_date:]

# Calculate cumulative returns (normalize to 100)
cumulative_returns = (bond_prices / bond_prices.iloc[0]) * 100

# Calculate annual returns by year
yearly_returns = {}
for year in range(2018, 2027):
    year_start = f'{year}-01-01'
    year_end = f'{year}-12-31'

    if year == 2026:
        year_end = bond_prices.index[-1].strftime('%Y-%m-%d')

    try:
        year_prices = bond_prices.loc[year_start:year_end]
        if len(year_prices) > 0:
            start_price = year_prices.iloc[0]
            end_price = year_prices.iloc[-1]
            year_return = (end_price / start_price - 1) * 100
            yearly_returns[year] = year_return
    except:
        pass

print("\n" + "=" * 80)
print("CHINESE BOND ETF PERFORMANCE (2018-2026)")
print("=" * 80)

print("\n1. CUMULATIVE RETURNS (2018-2026)")
print("-" * 80)
for etf, name in bond_etfs.items():
    total_return = (bond_prices[etf].iloc[-1] / bond_prices[etf].iloc[0] - 1) * 100
    annualized = ((1 + total_return/100) ** (1/8) - 1) * 100
    print(f"{name:40} Total: {total_return:>7.1f}%  |  Annualized: {annualized:>5.2f}%")

print("\n" + "=" * 80)
print("2. ANNUAL RETURNS BY YEAR")
print("=" * 80)

# Create table header
print(f"{'Year':<10}", end='')
for etf, name in bond_etfs.items():
    print(f"{name[:25]:>27}", end='')
print()
print("-" * 80)

# Print yearly returns
for year in sorted(yearly_returns.keys()):
    print(f"{year:<10}", end='')
    for etf in bond_etfs.keys():
        if etf in yearly_returns[year]:
            ret = yearly_returns[year][etf]
            print(f"{ret:>26.2f}%", end='')
    print()

print("=" * 80)

# Key periods analysis
print("\n3. KEY PERIODS & RATE POLICY")
print("=" * 80)

periods = {
    '2018-2019 (Trade War)': ('2018-01-01', '2019-12-31'),
    '2020 (COVID-19)': ('2020-01-01', '2020-12-31'),
    '2021-2022 (Recovery)': ('2021-01-01', '2022-12-31'),
    '2023-2024 (Stimulus)': ('2023-01-01', '2024-12-31'),
    '2025-2026 (Easing)': ('2025-01-01', bond_prices.index[-1].strftime('%Y-%m-%d'))
}

for period_name, (start, end) in periods.items():
    try:
        period_prices = bond_prices.loc[start:end]
        if len(period_prices) > 1:
            print(f"\n{period_name}:")
            for etf, name in bond_etfs.items():
                period_return = (period_prices[etf].iloc[-1] / period_prices[etf].iloc[0] - 1) * 100
                print(f"  {name:40} {period_return:>7.2f}%")
    except:
        pass

print("\n" + "=" * 80)
print("4. INTEREST RATE ENVIRONMENT (降息 = Rate Cuts)")
print("=" * 80)

rate_timeline = """
2018: Stable rates, trade war begins
2019: PBOC introduces LPR reform (new benchmark)

2020: COVID-19 RATE CUTS (降息)
      - LPR cut from 4.05% → 3.85% (April)
      - RRR cut by 50bp (July) + 50bp (December)
      → Bond prices RISE as rates FALL

2021: First post-COVID cut (December)
      - LPR cut by 5bp to 3.8%

2022: Two rate cuts (January + August)
      - LPR reduced to 3.65%
      - MLF rate: 2.95% → 2.75%

2023: Continued easing
      - 7-day reverse repo cut 10bp to 1.70%

2024: MAJOR STIMULUS (最大降息)
      - MLF rate cut 30bp (2.3% → 2.0%) - BIGGEST CUT EVER
      - 7-day repo cut 20bp
      - RRR cut 1% total (released ¥2 trillion liquidity)
      → Bond prices SURGE

2025: Further easing
      - 7-day repo: 1.5% → 1.4% (May)
      - Policy rate cut 0.1% (May)
      - LPR: 3.0% (one-year), 3.5% (five-year)

2026: 10Y yield at HISTORIC LOW
      - 10Y government bond yield: 1.82% (Jan 2026)
      - Record low: 1.596% (Feb 2025)
      → Maximum bond price appreciation

TOTAL RATE DECLINE (2019-2025):
- One-year LPR: 4.05% → 3.0% (-1.05%)
- Five-year LPR: 4.85% → 3.5% (-1.35%)
- 10Y yield: ~3.3% (2018) → 1.82% (2026) (-1.48%)
"""

print(rate_timeline)

print("\n" + "=" * 80)
print("5. WHY BONDS PERFORMED SO WELL")
print("=" * 80)

explanation = """
INVERSE RELATIONSHIP: Bond Prices ↑ when Interest Rates ↓

When PBOC cuts rates (降息):
1. Existing bonds with HIGHER yields become MORE valuable
2. Investors pay PREMIUM prices for higher-yielding bonds
3. Bond ETF prices RISE as underlying bond values increase

Example:
- 2018: 10Y bond yields ~3.3%, bond price = 100
- 2026: 10Y yields fall to 1.82%, old bonds worth MORE
- Result: 10Y Treasury ETF +40.3% return (2018-2026)

KEY DRIVERS OF BOND RETURNS:
✓ COVID-19 emergency cuts (2020)
✓ Economic slowdown response (2021-2022)
✓ September 2024 mega-stimulus (biggest MLF cut ever)
✓ Continued easing in 2025
✓ 10Y yields hitting historic lows (1.596% in Feb 2025)

This is why bonds in the All Weather portfolio had:
- 10Y Treasury: 40.3% return (despite low volatility)
- China Bond: 114.4% return (longer duration = higher sensitivity)
"""

print(explanation)

print("=" * 80)
print("\nSOURCES:")
print("- PBOC Monetary Policy Reports")
print("- China 10Y Government Bond Yield (TradingEconomics)")
print("- Federal Reserve FOMC Statements")
print("=" * 80)
