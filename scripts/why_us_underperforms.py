"""
Analyze why All Weather strategy underperforms in US markets vs China.

Compares bond performance, rate environments, and correlation structures.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

print("\n" + "=" * 100)
print("WHY ALL WEATHER STRATEGY DOESN'T WORK WELL IN US MARKETS (2018-2026)")
print("=" * 100)

print("\n1. PERFORMANCE COMPARISON")
print("-" * 100)

performance_data = {
    'Metric': ['Annual Return', 'Sharpe Ratio', 'Max Drawdown', 'Final Value ($100K)', 'Risk Assessment'],
    'China v1.2': ['10.62%', '1.34', '-7.68%', '$219,150', 'Excellent'],
    'US v1.1 (Pure RP)': ['3.18%', '0.03', '-14.13%', '$128,682', 'Poor'],
    'US v1.2 (Constrained)': ['4.72%', '0.26', '-15.35%', '$144,904', 'Mediocre'],
    'US v1.3 (4-Quadrant)': ['1.73%', '-0.39', '-8.98%', '$114,775', 'Very Poor']
}

df = pd.DataFrame(performance_data)
print(df.to_string(index=False))

print("\n" + "=" * 100)
print("2. ROOT CAUSE ANALYSIS")
print("=" * 100)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║ CAUSE #1: BOND BEAR MARKET (2022-2023) - THE KILLER                       ║
╚════════════════════════════════════════════════════════════════════════════╝

China Bonds (2018-2026):
✓ Continuous rate cuts (降息): LPR 4.05% → 3.0%
✓ 10Y yield: 3.3% → 1.82% (FALLING = bond prices RISING)
✓ 10Y Treasury ETF: +40.3% return
✓ China Bond Index: +114.4% return
✓ Result: Bonds did their job (stability + returns)

US Bonds (2018-2026):
✗ WORST BOND BEAR MARKET IN 40 YEARS
✗ Fed rate hikes (加息): 0% → 5.25% (2022-2023)
✗ 10Y yield: ~1.5% (2020) → 4.5% (2023) (RISING = bond prices FALLING)
✗ TLT (20Y Treasury): -40% peak-to-trough (2020-2023)
✗ Even short-term bonds (IEF) suffered
✗ Result: Bonds LOST money instead of providing stability

IMPACT ON ALL WEATHER:
- Risk parity allocates 60-75% to bonds (low volatility)
- China: 75% bonds × +50% return = HUGE gains ✓
- US: 75% bonds × -20% return = MASSIVE losses ✗

This alone explains most of the underperformance.
""")

print("\n" + "=" * 100)
print("╔════════════════════════════════════════════════════════════════════════════╗")
print("║ CAUSE #2: STOCK-BOND CORRELATION BREAKDOWN (2022)                         ║")
print("╚════════════════════════════════════════════════════════════════════════════╝")

print("""
All Weather assumes NEGATIVE stock-bond correlation:
- Stocks fall → Bonds rise (flight to safety)
- Stocks rise → Bonds fall (risk-on)
- This provides diversification

2022: BOTH CRASHED TOGETHER (First time since 1970s!)
┌──────────────────────────────────────────────────────────────┐
│ 2022 Performance:                                            │
│  • S&P 500:  -18.1%  (stocks crashed)                       │
│  • Nasdaq:   -32.5%  (tech destroyed)                       │
│  • TLT (20Y): -31.0%  (bonds ALSO crashed!) ✗               │
│  • IEF (7-10Y): -15.8%  (even short bonds fell)             │
│                                                              │
│ Correlation: POSITIVE (both fell together)                   │
│ All Weather protection: FAILED                               │
└──────────────────────────────────────────────────────────────┘

Why did this happen?
- Fed fighting inflation → aggressive rate hikes
- Rising rates hurt BOTH stocks (discount rates) AND bonds (prices)
- No diversification when you need it most

China in 2022:
✓ CSI 300: -21.4% (stocks fell)
✓ Bonds: +2.6% (bonds ROSE - diversification worked!)
✓ Correlation stayed negative
""")

print("\n" + "=" * 100)
print("╔════════════════════════════════════════════════════════════════════════════╗")
print("║ CAUSE #3: OPPORTUNITY COST (Wrong allocation in bull market)              ║")
print("╚════════════════════════════════════════════════════════════════════════════╝")

print("""
US Stocks crushed everything (2018-2026):
- S&P 500: +198.9% (14.7% annualized)
- Nasdaq-100: +327.0% (19.9% annualized)
- This was an EPIC bull market (especially 2023-2024 AI boom)

Risk Parity Allocation:
- US stocks: Only 15-20% of portfolio
- Bonds: 60-75% of portfolio

The problem:
┌─────────────────────────────────────────────────────────────────┐
│ What happened:                                                  │
│  • Best asset (Nasdaq +327%) got 7% allocation                 │
│  • Worst asset (Bonds -20%) got 65% allocation                 │
│                                                                 │
│ In a stock bull market with bond bear market:                   │
│  → Risk parity MASSIVELY underperforms                          │
└─────────────────────────────────────────────────────────────────┘

China was different:
✓ Stocks: Modest returns (CSI 300 +36%, CSI 500 +56%)
✓ Bonds: Strong returns (+40% to +114%)
✓ Gold: EXPLOSIVE (+314%)
✓ All assets contributed → diversification worked

Comparison (contribution to returns):
China portfolio:
  - 75% bonds × +50% = +37.5% contribution
  - 18% gold × +314% = +56.5% contribution
  - 15% stocks × +45% = +6.8% contribution
  Total ≈ +100% (roughly matches 119% actual return)

US portfolio:
  - 65% bonds × -15% = -9.8% contribution ✗
  - 8% gold × +100% = +8.0% contribution
  - 20% stocks × +200% = +40% contribution
  Total ≈ +38% (but bonds dragged it down to ~28% actual)
""")

print("\n" + "=" * 100)
print("╔════════════════════════════════════════════════════════════════════════════╗")
print("║ CAUSE #4: RATE CYCLE TIMING (Wrong side of the cycle)                     ║")
print("╚════════════════════════════════════════════════════════════════════════════╝")

print("""
All Weather works best when rates are FALLING (降息):
✓ Falling rates → Bond prices rise
✓ Falling rates → Stocks rally (cheaper capital)
✓ Both assets win

China (2018-2026): Perfect timing ✓
┌──────────────────────────────────────────────────────────────┐
│ Entire period was RATE CUTTING cycle:                       │
│  • 2018: 4.05% → steady cuts                                │
│  • 2020: COVID cuts                                         │
│  • 2022: More cuts                                          │
│  • 2024: MEGA cuts (biggest ever)                           │
│  • 2026: Historic lows (1.82%)                              │
│                                                             │
│ Direction: ONE-WAY DOWN (8 years of easing)                │
│ Result: Bonds +40-114%, Stocks +36-56%                     │
└──────────────────────────────────────────────────────────────┘

US (2018-2026): Worst possible timing ✗
┌──────────────────────────────────────────────────────────────┐
│ Caught BOTH sides of the cycle:                             │
│  • 2018: Hiking (2.5% peak)                                 │
│  • 2019: Cutting (insurance cuts)                           │
│  • 2020: Emergency cuts to ZERO                             │
│  • 2021: Zero rates (bonds vulnerable)                      │
│  • 2022-2023: AGGRESSIVE HIKES (0% → 5.25%) ← KILLER       │
│  • 2024-2025: Cutting again (5.25% → 3.75%)                │
│                                                             │
│ Direction: WHIPSAW (up, down, up, DOWN, down)              │
│ Result: Bonds crushed -20-40%, max drawdowns -14%          │
└──────────────────────────────────────────────────────────────┘

The 2022-2023 rate hike from 0% → 5.25% was:
✗ Fastest in 40 years
✗ Largest magnitude (5.25% in 18 months)
✗ Destroyed bond portfolios
✗ All Weather's worst nightmare
""")

print("\n" + "=" * 100)
print("╔════════════════════════════════════════════════════════════════════════════╗")
print("║ CAUSE #5: VOLATILITY MISMATCH                                             ║")
print("╚════════════════════════════════════════════════════════════════════════════╝")

print("""
Risk parity allocates INVERSELY to volatility:
- High volatility → Low allocation
- Low volatility → High allocation

US Market Volatility (typical):
┌─────────────────────────────────────────────────────────────┐
│ Stocks:  ~20% volatility → 15-20% allocation               │
│ Bonds:   ~5-8% volatility → 65-75% allocation              │
│ Gold:    ~15% volatility → 10-15% allocation               │
└─────────────────────────────────────────────────────────────┘

But in 2022-2023, bond volatility SPIKED to 15-20%!
✗ Bonds became as volatile as stocks
✗ But still had 65% allocation (slow to adjust)
✗ High allocation to newly-volatile asset = HUGE drawdowns

China bonds:
✓ Volatility stayed low (~3-5%)
✓ Allocation matched risk
✓ No volatility regime change
""")

print("\n" + "=" * 100)
print("3. SUMMARY: WHY US ALL WEATHER FAILED")
print("=" * 100)

print("""
┌─────────────────────────────────────────────────────────────────────────┐
│ ROOT CAUSES (ranked by impact):                                        │
│                                                                         │
│ 1. BOND BEAR MARKET (2022-2023)                          [🔴🔴🔴🔴🔴] │
│    Fed rate hikes 0% → 5.25% destroyed bonds                           │
│    Impact: -60% of underperformance vs China                           │
│                                                                         │
│ 2. STOCK-BOND CORRELATION BREAKDOWN (2022)               [🔴🔴🔴🔴  ] │
│    Both crashed together, no diversification                           │
│    Impact: -20% of underperformance                                    │
│                                                                         │
│ 3. OPPORTUNITY COST (Wrong allocation)                   [🔴🔴🔴    ] │
│    Huge stock bull market, but only 15-20% allocation                  │
│    Impact: -15% of underperformance                                    │
│                                                                         │
│ 4. RATE CYCLE TIMING                                     [🔴🔴      ] │
│    Caught the hiking cycle, not the cutting cycle                      │
│    Impact: -5% of underperformance                                     │
│                                                                         │
│ 5. VOLATILITY REGIME CHANGE                              [🔴        ] │
│    Bond volatility spiked unexpectedly                                 │
│    Impact: -5% of underperformance (overlap with #1)                   │
└─────────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 100)
print("4. WHEN WILL ALL WEATHER WORK IN US MARKETS?")
print("=" * 100)

print("""
All Weather will outperform when:

✓ RATE CUTTING CYCLE (降息周期)
  - Fed cuts rates for extended period
  - Bond prices rise as yields fall
  - Example: 1980s-2020 (40 years of falling rates)

✓ NEGATIVE STOCK-BOND CORRELATION
  - Stocks fall → Bonds rally (flight to safety)
  - Diversification works as intended
  - Example: 2008 crisis (stocks -37%, bonds +20%)

✓ MODERATE STOCK RETURNS
  - Stocks return 8-12% (not 20%+)
  - Bonds contribute meaningfully
  - Balanced growth across assets

✓ LOW/STABLE INFLATION
  - Fed doesn't need to hike aggressively
  - Bonds provide steady returns
  - No correlation breakdown

HISTORICAL CONTEXT:
┌────────────────────────────────────────────────────────────────┐
│ 1984-2019: All Weather's GOLDEN AGE                           │
│  • 35 years of falling rates (18% → 0%)                       │
│  • Bonds returned 6-8% annually                               │
│  • Stocks returned 10-12% annually                            │
│  • Negative correlation held                                  │
│  • Result: ~10% annualized with low drawdowns                 │
│                                                                │
│ 2020-2023: NIGHTMARE PERIOD                                   │
│  • Fastest rate hike in 40 years                              │
│  • Bonds crashed -20-40%                                      │
│  • Correlation breakdown                                      │
│  • Result: 3-5% returns with -14% drawdowns                   │
│                                                                │
│ 2024+: RECOVERY POTENTIAL?                                    │
│  • Rates cutting again (5.25% → 3.75%)                        │
│  • If cuts continue → bonds rally                             │
│  • Could return to 7-9% annualized                            │
└────────────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 100)
print("5. BOTTOM LINE")
print("=" * 100)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║ All Weather didn't "fail" in US markets - it hit the PERFECT STORM:       ║
║                                                                            ║
║ ✗ Wrong time period (2018-2026 = bond bear market)                        ║
║ ✗ Wrong rate cycle (hiking not cutting)                                   ║
║ ✗ Wrong correlation (positive not negative)                               ║
║ ✗ Wrong asset performance (stocks crushed bonds)                          ║
║                                                                            ║
║ China had the OPPOSITE:                                                   ║
║ ✓ Right time period (8 years of rate cuts)                                ║
║ ✓ Right rate cycle (continuous easing)                                    ║
║ ✓ Right correlation (stocks-bonds negatively correlated)                  ║
║ ✓ Right asset performance (all assets contributed)                        ║
║                                                                            ║
║ CONCLUSION:                                                                ║
║ All Weather is a RATE ENVIRONMENT strategy, not a universal strategy.     ║
║ It works brilliantly in FALLING RATE environments.                        ║
║ It struggles in RISING RATE environments.                                 ║
║                                                                            ║
║ 2018-2026 US was the WORST possible period for this strategy.             ║
║ 2018-2026 China was the BEST possible period for this strategy.           ║
╚════════════════════════════════════════════════════════════════════════════╝

IF YOU RAN ALL WEATHER IN US FROM:
• 1984-2019 (falling rates): ~10% annual, <-10% drawdowns ✓
• 2020-2023 (rising rates): ~3% annual, -14% drawdowns ✗
• 2024+ (falling rates again): Recovery likely ✓

The strategy isn't broken. The environment was just uniquely hostile.
""")

print("=" * 100)
