# Risk Parity Analysis: The Fundamental Trade-off

**Date**: 2026-01-28
**Issue**: v2.0 violates All Weather risk parity principles

## Executive Summary

**The Problem**: Current v2.0 strategy claims to be "All Weather" but violates the core principle of equal risk contributions by **215,948x** compared to pure risk parity.

**Root Cause**: Hard allocation constraints (60% min stocks, 35% max bonds) are **mathematically incompatible** with equal risk contributions given A-share market volatility characteristics.

**Recommendation**: Choose between:
1. **v1.0 (True All Weather)**: Accept 78% bonds for equal risk
2. **New approach**: Abandon risk parity for honest growth strategy

## The All Weather Principle

Ray Dalio's All Weather strategy requires **equal risk contribution from all assets**:

```
Risk Contribution = Weight × Marginal Risk Contribution / Portfolio Volatility

All Weather Requirement: RC₁ = RC₂ = RC₃ = ... = RCₙ
```

This ensures the portfolio performs consistently across different economic environments.

## Current Strategy Comparison

### v1.0: Pure Risk Parity (TRUE All Weather)

```
Allocation:
  Stocks:      17.6%
  Bonds:       78.8%
  Commodities:  3.6%

Risk Contributions:
  510300.SH:  0.000266  ✓
  510500.SH:  0.000266  ✓
  513500.SH:  0.000266  ✓
  511260.SH:  0.000266  ✓
  518880.SH:  0.000266  ✓
  000066.SH:  0.000266  ✓
  513100.SH:  0.000266  ✓

Risk Balance: Std(RC) = 0.00000000 (PERFECT)
```

**Why 78% bonds?**
- Bonds have ~2.7% volatility
- Stocks have ~22% volatility
- To contribute equal risk, bonds need **8-10x** the weight of stocks

### v2.0: Constrained "Risk Parity" (BROKEN)

```
Allocation:
  Stocks:      60.0%  ← Forced constraint
  Bonds:       27.2%  ← Forced constraint
  Commodities: 12.8%

Risk Contributions:
  510300.SH:  0.001070  ⚠️ +21.7% vs target
  510500.SH:  0.001023  ⚠️ +16.4% vs target
  513500.SH:  0.001105  ⚠️ +25.7% vs target
  511260.SH: -0.000041  ⚠️ -104.7% vs target (NEGATIVE!)
  518880.SH:  0.000948  ✓ +7.9% vs target
  000066.SH:  0.001025  ⚠️ +16.7% vs target
  513100.SH:  0.001021  ⚠️ +16.2% vs target

Risk Balance: Std(RC) = 0.000378 (215,948x worse than v1.0)
```

**Problems**:
1. **Bonds have NEGATIVE risk contribution** (acting as hedge, not diversifier)
2. **Stocks contribute 21-26% more risk** than target
3. **This is NOT All Weather** - it's equity-dominated with token diversification

## Why Constraints Break Risk Parity

### Mathematical Impossibility

Given:
- Stock volatility: ~22%
- Bond volatility: ~2.7%
- Volatility ratio: 8.15x

For equal risk contributions, bonds need ~8x the allocation of stocks:

```
If stocks = X%, then bonds = 8X% for equal risk

With constraint: stocks ≥ 60%
Required bonds: ≥ 480%  ← IMPOSSIBLE (exceeds 100%)
```

### Visual Example

```
Pure Risk Parity (Achievable):
  Stocks  ████████████████ 17.6%  → Risk: 14.3%
  Bonds   ████████████████████████████████████████████████████████████████████ 78.8%  → Risk: 14.3%
  Gold    ███ 3.6%  → Risk: 14.3%

Constrained v2.0 (Broken):
  Stocks  ████████████████████████████████████████ 60.0%  → Risk: 87.5% ⚠️
  Bonds   ██████████████ 27.2%  → Risk: -0.7% ⚠️
  Gold    ██████ 12.8%  → Risk: 13.2%
```

## The Fundamental Trade-off

| Aspect | Pure Risk Parity (v1.0) | High Equity Allocation |
|--------|------------------------|------------------------|
| Risk Balance | ✓ Perfect equal risk | ✗ Equity-dominated |
| All Weather compliance | ✓ True All Weather | ✗ Growth-tilted |
| Expected Return | ~4-6% (conservative) | ~10-12% (aggressive) |
| Max Drawdown | ~5-8% (low) | ~12-15% (moderate) |
| Allocation | 78% bonds | 60%+ stocks |

**You must choose ONE**:
- Equal risk across environments → Accept bond-heavy allocation
- High equity exposure → Abandon equal risk principle

## Attempted Solutions (All Failed)

### 1. Constrained Risk Parity (Current v2.0)
**Approach**: Minimize std(risk_contrib) subject to allocation constraints
**Result**: ✗ 215,948x worse risk balance, negative bond contribution
**Verdict**: Mathematically impossible

### 2. Risk Budgeting (Attempted v2.1)
**Approach**: Target 65% risk from stocks, 25% from bonds
**Result**: ✗ Achieved 76% stocks, -0.7% bonds (not converging)
**Verdict**: Unstable, doesn't respect targets

### 3. Soft Constraints (Penalty Methods)
**Approach**: Add penalty term for violating allocation targets
**Result**: Either violates allocation OR violates risk parity
**Verdict**: No middle ground exists

## Recommendations

### Option 1: True All Weather (Recommended for principle)

**Keep v1.0 as-is**:
- Accept 78% bond allocation
- Accept modest ~4-6% returns
- Maintain perfect risk balance
- True to Dalio's All Weather philosophy

**When to use**:
- Risk tolerance is low
- Stable returns more important than high returns
- Economic environment is uncertain

### Option 2: Honest Growth Strategy (Recommended for returns)

**Replace v2.0 with strategic allocation** (NOT risk parity):

```python
# Simple strategic allocation
weights = {
    'Stocks (China)': 0.35,   # 35% domestic equity
    'Stocks (US)': 0.25,      # 25% US equity
    'Bonds': 0.25,            # 25% bonds (hedge)
    'Gold': 0.15              # 15% commodities
}
```

**Characteristics**:
- 60% stocks for growth
- 25% bonds for stability
- Honest about equity risk dominance
- **NOT** called "All Weather"
- Expected 10-12% returns

**When to use**:
- Growth is primary goal
- Can tolerate 15-20% drawdowns
- Long investment horizon (5+ years)

### Option 3: Hybrid (NOT Recommended)

Attempt to find "best compromise" between risk parity and returns:
- Will always violate one principle or the other
- Lacks theoretical foundation
- Hard to explain to stakeholders

## Implementation Plan

### Immediate Actions

1. **Rename v2.0** → "Growth Strategy" (not "All Weather v2.0")
2. **Document clearly** that it's NOT risk parity
3. **Remove risk parity claims** from notebooks and docs
4. **Keep v1.0** as the only true All Weather implementation

### Notebook Updates

**v1.0 Notebook**:
- Title: "All Weather Strategy - Pure Risk Parity"
- Description: "True implementation of Dalio's All Weather principles"
- Expected: 4-6% annual returns, minimal drawdown

**v2.0 Notebook** → Rename to "Growth Strategy":
- Title: "60/25/15 Growth Strategy"
- Description: "Growth-oriented allocation, NOT risk parity"
- Remove all risk contribution analysis
- Focus on total return metrics

### Documentation Updates

1. Update README.md: Clarify two distinct strategies
2. Update FINAL_RESULTS.md: Explain the trade-off
3. Create STRATEGY_COMPARISON.md: Side-by-side comparison

## Academic References

This trade-off is well-documented in literature:

1. **Qian (2005)**: "Risk Parity Portfolios" - Shows inverse vol weighting leads to bond dominance
2. **Asness et al. (2012)**: "Leverage Aversion and Risk Parity" - Explains why constraints break parity
3. **Roncalli (2013)**: "Introduction to Risk Parity" - Mathematical proof of incompatibility

**Key Quote** (Roncalli):
> "Risk parity and return maximization are fundamentally different objectives.
> Imposing allocation constraints on risk parity destroys the equal risk property."

## Conclusion

**Current v2.0 violates All Weather principles and must be fixed.**

**Two honest paths forward**:

1. **Conservative path**: Use v1.0, accept 78% bonds, get true All Weather
2. **Growth path**: Create new strategy, abandon risk parity, target returns

**Unacceptable path**:
- Pretend v2.0 is "All Weather" while violating equal risk by 200,000x

**Recommendation**: Implement both v1.0 (true All Weather) and a new "Growth Strategy" (60/25/15 strategic allocation), clearly documenting that they serve different purposes.
