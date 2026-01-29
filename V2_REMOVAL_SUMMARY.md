# v2.0 Removal Summary

**Date**: 2026-01-28
**Action**: Removed v2.0 "constrained risk parity" implementation
**Reason**: Violated fundamental All Weather principles

## What Was Removed

### Code
1. **notebooks/all_weather_v2_optimized.ipynb** - v2.0 interactive analysis
2. **src/optimizer.py** - `optimize_weights_constrained()` function (258 lines)
3. **src/optimizer.py** - `optimize_weights_risk_budget()` function
4. **src/strategy.py** - `AllWeatherV2` class (116 lines)
5. **scripts/run_v2_strategy.py** - v2.0 production script
6. **scripts/run_v2_7etf.py** - v2.0 dataset comparison script
7. **scripts/run_v2_enhanced.py** - v2.0 enhanced dataset script

### Documentation
1. **docs/versions/v2.0_improved.md** - v2.0 iteration analysis
2. **README.md** - Completely rewritten to focus on v1.0

## Why v2.0 Was Removed

### The Violation

v2.0 attempted to maintain "risk parity" while forcing:
- **60% minimum stock allocation**
- **35% maximum bond allocation**

**Result**: Risk contributions were **215,948x worse** than pure risk parity.

```
v1.0 (True Risk Parity):
  All assets: 0.000266 risk contribution (perfectly equal)
  Std(RC): 0.00000000

v2.0 (Broken):
  Stocks:     0.001070 (+21.7% vs target)
  Bonds:     -0.000041 (NEGATIVE, -104.7% vs target!)
  Std(RC): 0.000378 (215,948x worse)
```

### The Mathematical Impossibility

**Given**:
- Stock volatility: ~22%
- Bond volatility: ~2.7%
- Ratio: 8.15x

**For equal risk**:
- If stocks = 17.6%, bonds need 78.8%
- If stocks forced to 60%, bonds would need 488% (impossible!)

**Conclusion**: Cannot have both equal risk AND high equity allocation.

## What Ray Dalio Actually Recommends

From his All Weather strategy:
> "The portfolio should perform well across all economic environments by balancing
> the risk contributed by each major asset class."

**Key word**: BALANCING risk, not forcing allocation.

Original All Weather has:
- ~7.5% stocks
- ~40% intermediate bonds
- ~15% long-term bonds
- ~7.5% commodities
- **Total bonds: ~55%** (bond-heavy, not equity-heavy)

Our v1.0 with 78.8% bonds is actually **more conservative** than Dalio's original, but follows the same principle.

## What Remains (v1.0 Pure Risk Parity)

### Files Kept
- ✓ `notebooks/all_weather_v1_baseline.ipynb`
- ✓ `src/optimizer.py` (pure risk parity only)
- ✓ `src/strategy.py` (AllWeatherV1 only)
- ✓ `src/backtest.py`
- ✓ `src/portfolio.py`
- ✓ `src/metrics.py`
- ✓ `src/data_loader.py`
- ✓ `data/etf_prices_7etf.csv`
- ✓ `docs/versions/v1.0_baseline.md`
- ✓ `docs/RISK_PARITY_ANALYSIS.md` (analysis of why v2 failed)

### Performance (v1.0)
```
Backtest Period: 2018-2026
Annual Return: 6.52%
Sharpe Ratio: 0.60
Max Drawdown: -4.21%
Benchmark Multiple: 1.62x

Allocation:
  Stocks:  17.6%
  Bonds:   78.8%
  Gold:     3.6%

Risk Balance: PERFECT (std = 0.00000000)
```

## Lessons Learned

1. **Theoretical integrity matters** - Can't fake risk parity with constraints
2. **All Weather = low returns** - That's the trade-off for stability
3. **Be honest about goals**:
   - Want risk balance? Accept bond-heavy allocation
   - Want high returns? Don't call it "All Weather"
4. **Mathematical constraints** - Some optimizations are physically impossible
5. **v2.0 was dishonest** - Claimed risk parity while violating it 215,000x

## The Right Way Forward

### Option A: Keep v1.0 Only (Chosen)
- True to All Weather principles
- Perfect risk balance
- Modest but stable returns
- Bond-heavy allocation

### Option B: Create Separate Growth Strategy (Not implemented)
- Don't call it "All Weather"
- Simple 60/25/15 strategic allocation
- No risk parity claims
- Honest about equity dominance

We chose **Option A** to maintain theoretical integrity.

## Code Changes Summary

| File | Lines Removed | Status |
|------|---------------|--------|
| notebooks/all_weather_v2_optimized.ipynb | ~500 | Deleted |
| src/optimizer.py | 258 | Modified |
| src/strategy.py | 116 | Modified |
| scripts/run_v2_*.py | ~500 | Deleted (3 files) |
| docs/versions/v2.0_improved.md | ~400 | Deleted |
| README.md | ~200 | Rewritten |

**Total**: ~2,000 lines of v2.0 code removed

## Verification

```bash
# Run v1.0 backtest
python scripts/run_v1_baseline.py

# Or use notebook
jupyter notebook notebooks/all_weather_v1_baseline.ipynb
```

**Expected output**:
- ✓ Perfect risk parity (std = 0)
- ✓ ~78% bond allocation
- ✓ 6-7% annual return
- ✓ -4 to -5% max drawdown

## Final State

**Repository now contains**:
- ✓ One strategy: Pure risk parity (v1.0)
- ✓ One notebook: all_weather_v1_baseline.ipynb
- ✓ One optimizer: optimize_weights() (pure risk parity)
- ✓ One dataset: etf_prices_7etf.csv (7 aligned ETFs)

**No longer contains**:
- ✗ Constrained risk parity
- ✗ Risk budgeting
- ✗ Multiple strategy versions
- ✗ Claims of 12% returns

**Result**: Clean, honest implementation of All Weather principles.

## References

- **docs/RISK_PARITY_ANALYSIS.md** - Full mathematical analysis
- **data/DATA_QUALITY_REPORT.md** - Data quality verification
- **docs/versions/v1.0_baseline.md** - v1.0 methodology

---

**Bottom Line**: v2.0 tried to have its cake and eat it too (high returns + risk parity). Mathematics proved this impossible. We chose honesty over performance marketing.
