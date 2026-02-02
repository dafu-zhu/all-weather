"""
Explain why China kept cutting rates while the US was hiking (2018-2025).

Shows the fundamental economic differences between US and China during this period.
"""

print("\n" + "=" * 100)
print("WHY CHINA DIDN'T RAISE INTEREST RATES (2018-2025)")
print("=" * 100)

print("""
The short answer: China and the US faced OPPOSITE economic problems.

US: Overheating economy → Raise rates (加息) to cool it down
China: Slowing economy → Cut rates (降息) to stimulate growth

Let's dive into the details...
""")

print("\n" + "=" * 100)
print("1. INFLATION COMPARISON: THE SMOKING GUN")
print("=" * 100)

inflation_comparison = """
╔════════════════════════════════════════════════════════════════════════════╗
║                        INFLATION RATES (2021-2025)                         ║
╚════════════════════════════════════════════════════════════════════════════╝

Year       │   US Inflation   │  China Inflation  │   Difference
───────────┼──────────────────┼───────────────────┼─────────────────────
2021       │      4.7%        │      0.98%        │   +3.7% (US higher)
2022       │      8.0%  🔥    │      1.97%        │   +6.0% (US MUCH higher)
2023       │      4.1%        PageRank      0.23%        │   +3.9% (US higher)
2024       │      2.9%        │      0.2%         │   +2.7% (US higher)
2025       │      ~2.5%       │     -0.1% ⚠️     │   +2.6% (China DEFLATION!)

Peak:
  US:  9.1% (June 2022) - 40-year high! 🔥🔥🔥
  China: 2.8% (Sept 2022) - Normal, not concerning

KEY INSIGHT:
┌────────────────────────────────────────────────────────────────────────┐
│ When US inflation hit 9.1%, the Fed HAD to raise rates aggressively.  │
│ When China inflation was at 2%, PBOC had NO REASON to hike.           │
│                                                                        │
│ In fact, China feared DEFLATION (negative inflation), not inflation!  │
└────────────────────────────────────────────────────────────────────────┘

DEFLATION IN CHINA:
• April 2025: -0.1% (third consecutive month of deflation)
• Producer prices (PPI): -2.6% in 2025 (32 months of decline!)
• Consumer spending weak, prices falling

When you have DEFLATION, you CUT rates, not RAISE them!
"""

print(inflation_comparison)

print("\n" + "=" * 100)
print("2. ECONOMIC GROWTH: OVERHEATING vs SLOWING")
print("=" * 100)

gdp_comparison = """
╔════════════════════════════════════════════════════════════════════════════╗
║                        GDP GROWTH RATES (2018-2025)                        ║
╚════════════════════════════════════════════════════════════════════════════╝

Year       │   US GDP Growth  │  China GDP Growth │   Economic Status
───────────┼──────────────────┼───────────────────┼──────────────────────────
2018       │      3.0%        │      6.7%         │   Both strong
2019       │      2.3%        │      6.0%         │   China slowing (trade war)
2020       │     -2.8% (COVID)│      2.2%         │   US worse hit
2021       │      5.9%  🚀    │      8.4%         │   Post-COVID boom
2022       │      1.9%        │      3.0%         │   Both slowing
2023       │      2.5%        │      5.2%         │   US recovering
2024       │      2.8%        │      5.0%         │   China struggling
2025       │      2.4%        │      4.8%         │   China trend down

US SITUATION (2021-2022):
✗ Economy OVERHEATING after COVID stimulus
✗ Labor market TOO tight (unemployment 3.5%)
✗ Wages rising rapidly
✗ Demand exceeding supply → INFLATION
✗ Fed needed to COOL the economy → RATE HIKES

China SITUATION (2021-2025):
✓ Economy SLOWING despite official 5% target
✓ Independent estimates: Only 2.4-2.8% growth in 2024 (not official 5%)
✓ Weak consumer demand
✓ Youth unemployment crisis (20%+)
✓ PBOC needed to STIMULATE the economy → RATE CUTS
"""

print(gdp_comparison)

print("\n" + "=" * 100)
print("3. THE REAL ESTATE CRISIS: CHINA'S ALBATROSS")
print("=" * 100)

real_estate_crisis = """
╔════════════════════════════════════════════════════════════════════════════╗
║              CHINA'S REAL ESTATE CRISIS (2020-2025)                        ║
╚════════════════════════════════════════════════════════════════════════════╝

August 2020: "Three Red Lines" Policy
├─ PBOC tightens borrowing rules for property developers
└─ Aimed to reduce financial risk, but triggered crisis

2021: Evergrande Default
├─ China's 2nd largest developer defaults on $300B debt
├─ Largest real estate default in history
└─ Contagion spreads to other developers (Country Garden, etc.)

Impact on Economy:
┌────────────────────────────────────────────────────────────────────────┐
│ • Property sector = 25% of China's GDP                                │
│ • Property sales: DOWN 60%                                            │
│ • New construction starts: DOWN 70%                                   │
│ • Property prices: DOWN 16% (cumulative)                              │
│ • Consumer confidence: COLLAPSED                                      │
│                                                                        │
│ Result: Massive drag on economic growth                               │
└────────────────────────────────────────────────────────────────────────┘

Why This Matters for Interest Rates:
✗ Real estate crisis destroying household wealth
✗ Consumer confidence at historic lows
✗ People not spending → deflationary pressure
✗ PBOC must CUT rates to stimulate lending and spending
✗ Raising rates would WORSEN the crisis

US Real Estate (2021-2023):
✓ Housing market BOOMING (too much demand)
✓ Home prices rising rapidly
✓ Fed RAISED rates to cool housing market
✓ Opposite problem!
"""

print(real_estate_crisis)

print("\n" + "=" * 100)
print("4. COVID-19 LOCKDOWN DIVERGENCE")
print("=" * 100)

covid_comparison = """
╔════════════════════════════════════════════════════════════════════════════╗
║                   COVID-19 POLICY COMPARISON                               ║
╚════════════════════════════════════════════════════════════════════════════╝

US COVID Response (2020-2021):
├─ Initial lockdowns (March-June 2020)
├─ Reopened by summer 2021
├─ MASSIVE stimulus: $5 trillion in fiscal/monetary support
├─ Result: Economy OVERHEATED, demand surge
└─ Inflation consequence: Too much money chasing goods

China COVID Response (2020-2023):
├─ "Zero-COVID" policy: Rolling lockdowns through 2022
├─ Shanghai locked down 2 months (Apr-June 2022)
├─ Strict testing and quarantine requirements
├─ Only ended December 2022 (2+ years later than US!)
└─ Result: Economic activity suppressed, weak demand

Timeline Comparison:
┌────────────────────────────────────────────────────────────────────────┐
│ 2020: Both locked down                                                │
│ 2021: US reopened + stimulus → BOOM → Inflation rising                │
│ 2022: US fully open, inflation 9% → Fed hikes aggressively            │
│       China STILL locked down → Deflation risk → PBOC cuts rates      │
│ 2023: US fighting inflation → Continued hikes to 5.25%                │
│       China JUST reopened → Weak recovery → More rate cuts            │
└────────────────────────────────────────────────────────────────────────┘

China's extended lockdowns meant:
✗ NO demand surge like in US
✗ NO inflation problem
✗ NO need to raise rates
✓ In fact, needed LOWER rates to revive economy
"""

print(covid_comparison)

print("\n" + "=" * 100)
print("5. STRUCTURAL ECONOMIC DIFFERENCES")
print("=" * 100)

structural_differences = """
╔════════════════════════════════════════════════════════════════════════════╗
║            WHY US AND CHINA FACED OPPOSITE PROBLEMS                        ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│ UNITED STATES (2021-2023): OVERHEATING                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ Demand Side:                                                            │
│   ✓ $5T COVID stimulus → Too much money in economy                     │
│   ✓ Savings rate spiked → Pent-up demand                               │
│   ✓ Government checks → Direct consumer spending                        │
│   ✓ Unemployment benefits → High wages needed to attract workers        │
│                                                                         │
│ Supply Side:                                                            │
│   ✗ Supply chain disruptions (ports, shipping)                         │
│   ✗ Labor shortage (workers dropped out)                               │
│   ✗ Semiconductor shortage                                             │
│   ✗ Energy prices spiked (Ukraine war)                                 │
│                                                                         │
│ Result: DEMAND >> SUPPLY → INFLATION 9.1%                              │
│                                                                         │
│ Fed Response: RAISE RATES to kill demand                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ CHINA (2020-2025): SLOWING GROWTH                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ Demand Side:                                                            │
│   ✗ Real estate crisis → Wealth destruction                            │
│   ✗ Zero-COVID lockdowns → Suppressed consumption                      │
│   ✗ Youth unemployment 20%+ → Weak purchasing power                    │
│   ✗ Consumer confidence collapsed                                      │
│   ✗ Export slowdown (global demand weak)                               │
│                                                                         │
│ Supply Side:                                                            │
│   ✓ Overcapacity in manufacturing                                      │
│   ✓ Price competition intense (EVs, solar, etc.)                       │
│   ✓ Property oversupply (ghost cities)                                 │
│                                                                         │
│ Result: SUPPLY >> DEMAND → DEFLATION -0.1%                             │
│                                                                         │
│ PBOC Response: CUT RATES to stimulate demand                           │
└─────────────────────────────────────────────────────────────────────────┘
"""

print(structural_differences)

print("\n" + "=" * 100)
print("6. MONETARY POLICY GOALS: INFLATION vs GROWTH")
print("=" * 100)

policy_goals = """
╔════════════════════════════════════════════════════════════════════════════╗
║              CENTRAL BANK MANDATES AND PRIORITIES                          ║
╚════════════════════════════════════════════════════════════════════════════╝

Federal Reserve (US):
┌────────────────────────────────────────────────────────────────────────┐
│ Dual Mandate:                                                          │
│   1. Price stability (keep inflation at 2%)                            │
│   2. Maximum employment                                                │
│                                                                        │
│ 2022 Situation:                                                        │
│   • Inflation at 9.1% (way above 2% target) ✗                         │
│   • Unemployment at 3.5% (already maxed out) ✓                        │
│                                                                        │
│ Decision: MUST hike rates to fight inflation                           │
│           (Sacrifice #2 to achieve #1)                                 │
└────────────────────────────────────────────────────────────────────────┘

People's Bank of China (PBOC):
┌────────────────────────────────────────────────────────────────────────┐
│ Primary Mandate:                                                       │
│   1. Maintain economic growth (hit 5% GDP target)                      │
│   2. Financial stability                                               │
│   3. Currency stability                                                │
│   4. Inflation control (BUT inflation not a problem!)                  │
│                                                                        │
│ 2022-2025 Situation:                                                   │
│   • GDP growth slowing (barely hitting 5% target) ✗                   │
│   • Deflation risk, not inflation! (CPI at 0-2%) ✗                    │
│   • Real estate crisis threatening financial stability ✗              │
│   • Youth unemployment crisis ✗                                        │
│                                                                        │
│ Decision: MUST cut rates to stimulate growth                           │
│           (No inflation constraint!)                                   │
└────────────────────────────────────────────────────────────────────────┘

Different Constraints:
• Fed: Constrained by HIGH inflation → Must hike even if it hurts growth
• PBOC: No inflation constraint → Free to cut rates to boost growth
"""

print(policy_goals)

print("\n" + "=" * 100)
print("7. SUMMARY: WHY OPPOSITE POLICIES")
print("=" * 100)

summary = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    THE FUNDAMENTAL DIFFERENCE                              ║
╚════════════════════════════════════════════════════════════════════════════╝

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃         UNITED STATES             ┃            CHINA                  ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Problem:    OVERHEATING           ┃ Problem:    SLOWING GROWTH        ┃
┃ Inflation:  9.1% peak             ┃ Inflation:  0.2% (deflation risk) ┃
┃ Demand:     TOO HIGH              ┃ Demand:     TOO WEAK              ┃
┃ Stimulus:   $5T (too much)        ┃ Stimulus:   Real estate crisis    ┃
┃ Employment: 3.5% (too tight)      ┃ Employment: 20%+ youth unemployment┃
┃ Housing:    BOOMING               ┃ Housing:    CRASHING (-16%)       ┃
┃ COVID:      Ended 2021            ┃ COVID:      Ended 2022 (1yr later)┃
┃                                   ┃                                   ┃
┃ Solution:   RAISE RATES (加息)   ┃ Solution:   CUT RATES (降息)     ┃
┃ Goal:       COOL economy          ┃ Goal:       HEAT UP economy       ┃
┃ Direction:  0% → 5.25%            ┃ Direction:  4.05% → 3.0%          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

ANALOGY:
═════════════════════════════════════════════════════════════════════════
US Economy = Overheated car engine
  → Solution: Cool it down (raise rates = reduce throttle)

China Economy = Stalled car engine
  → Solution: Restart it (cut rates = hit the gas)
═════════════════════════════════════════════════════════════════════════

It's not that China "chose" not to raise rates.
They faced completely opposite economic conditions!

Raising rates in China would have been like:
✗ Hitting the brakes on a car that's already stalled
✗ Making deflation WORSE
✗ Deepening the real estate crisis
✗ Crushing consumer confidence further
✗ Economic suicide
"""

print(summary)

print("\n" + "=" * 100)
print("8. IMPACT ON ALL WEATHER STRATEGY")
print("=" * 100)

impact = """
╔════════════════════════════════════════════════════════════════════════════╗
║              WHY THIS MATTERS FOR ALL WEATHER                              ║
╚════════════════════════════════════════════════════════════════════════════╝

All Weather = Long bonds (75% of portfolio)

Bond Performance = Inverse of interest rate changes

China All Weather (2018-2026):
┌────────────────────────────────────────────────────────────────────────┐
│ Rates: 4.05% → 3.0% (FALLING) ✓                                       │
│ Bond prices: RISING ✓                                                  │
│ 10Y Treasury: +40.3% return                                            │
│ China Bond: +114.4% return                                             │
│ Portfolio: +119% total return (10.6% annualized) 🚀                   │
└────────────────────────────────────────────────────────────────────────┘

US All Weather (2018-2026):
┌────────────────────────────────────────────────────────────────────────┐
│ Rates: 0% → 5.25% (RISING) ✗                                          │
│ Bond prices: FALLING ✗                                                 │
│ TLT (20Y): -40% peak-to-trough loss                                    │
│ IEF (7-10Y): -20% loss                                                 │
│ Portfolio: +28% total return (3.2% annualized) 😢                     │
└────────────────────────────────────────────────────────────────────────┘

The 7% annualized return difference (10.6% vs 3.2%) is explained by:
1. China rate cuts → Bond gains (+40-114%)
2. US rate hikes → Bond losses (-20-40%)

Same strategy, opposite rate environments, opposite results.
"""

print(impact)

print("\n" + "=" * 100)
print("BOTTOM LINE")
print("=" * 100)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║  China didn't raise rates because they had the OPPOSITE problem:          ║
║                                                                            ║
║  • US: Too much inflation (9.1%) → HAD to raise rates                     ║
║  • China: Deflation risk (-0.1%) → HAD to cut rates                       ║
║                                                                            ║
║  • US: Overheating economy → Cool it down                                 ║
║  • China: Slowing economy → Heat it up                                    ║
║                                                                            ║
║  • US: Real estate boom → Raise rates to slow it                          ║
║  • China: Real estate crash → Cut rates to revive it                      ║
║                                                                            ║
║  This is why All Weather worked in China but failed in the US.            ║
║  The strategy needs FALLING rates, and only China had that.               ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

Sources:
- China Inflation Rate: https://tradingeconomics.com/china/inflation-cpi
- US Inflation Rate: https://www.usinflationcalculator.com/inflation/current-inflation-rates/
- China Economic Crisis: https://libertystreeteconomics.newyorkfed.org/2025/04/gauging-the-strength-of-chinas-economy-in-uncertain-times/
- World Bank China Economic Update (June 2025)
- Wikipedia: 2021-2023 inflation surge
""")

print("=" * 100)
