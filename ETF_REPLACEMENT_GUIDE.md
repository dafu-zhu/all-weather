# ETF Replacement Guide - Fixing Data Quality Issues

## 🔴 Problem Identified

Current backtest has **unreliable results** due to frozen ETF data:

| ETF | Issue | Impact |
|-----|-------|--------|
| **511090.SH** (30yr Bond) | 76% zero returns<br>Flat 2018-2022 (5 years!) | 25-35% of portfolio earned 0% for 5 years |
| **513300.SH** (Nasdaq) | 54% zero returns<br>Flat 2018-2019 (2 years) | Missed US tech growth 2018-2019 |

**Result**: v2.0 backtest shows -10.71% max drawdown, but data quality makes this unreliable.

---

## ✅ Solution: Replace with High-Quality ETFs

### Current Dataset Quality Analysis

| ETF | Zero Returns | Annual Return | Quality | Action |
|-----|--------------|---------------|---------|--------|
| 510500.SH (中证500) | 0.7% | 6.23% | 🟢 EXCELLENT | ✓ KEEP |
| 510300.SH (沪深300) | 1.2% | 4.57% | 🟢 EXCELLENT | ✓ KEEP |
| 518880.SH (黄金) | 1.8% | 15.05% | 🟢 EXCELLENT | ✓ KEEP |
| 513500.SH (标普500) | 6.3% | 14.16% | 🟢 GOOD | ✓ KEEP |
| 511260.SH (10年国债) | 24.6% | 3.00% | 🟡 OK | ✓ KEEP (bonds are typically less liquid) |
| 513300.SH (纳指) | 54.2% | 7.91% | 🔴 POOR | ✗ REPLACE |
| 511090.SH (30年国债) | 76.3% | 1.90% | 🔴 POOR | ✗ REPLACE |

---

## 📋 Recommended Replacements

### Option 1: Simplify to 5 High-Quality ETFs (Quick Fix)

**Remove problematic ETFs, keep only high-quality ones:**

```python
# New asset universe (5 ETFs)
CLEAN_ETFS = [
    '510300.SH',  # 沪深300 (A-share large cap)
    '510500.SH',  # 中证500 (A-share mid cap)
    '513500.SH',  # 标普500 (US large cap)
    '511260.SH',  # 10年国债 (bonds)
    '518880.SH',  # 黄金 (gold/commodity)
]
```

**Advantages**:
- ✅ All have excellent data quality (<7% zeros)
- ✅ Covers all major asset classes
- ✅ Can run backtest immediately
- ✅ Still achieves diversification

**Trade-offs**:
- ❌ Loses long-duration bond exposure (30yr)
- ❌ Loses Nasdaq tech exposure (but has S&P 500)
- ❌ Less diversification (5 vs 7 ETFs)

---

### Option 2: Fetch Better Alternatives (Recommended)

**Replace with different ETFs that have better data:**

| Replace | With | Code | Expected Quality |
|---------|------|------|------------------|
| 513300.SH<br>(Nasdaq) | Nasdaq 100 ETF | **159941.SZ** | Should be better |
| | OR use 513500.SH only | Already have | 6.3% zeros (good) |
| | OR China Internet | 513050.SH | Need to check |
| 511090.SH<br>(30yr Bond) | 5-year Treasury | **511010.SH** | Typically more liquid |
| | OR double up 10yr | 511260.SH | Already have (24.6% zeros) |
| | OR Corporate Bond | 511220.SH | Need to check |

**To fetch (using akshare, tushare, or yfinance)**:

```python
# Priority 1: Try these first
fetch_and_check('159941.SZ')  # Nasdaq 100 (Shenzhen)
fetch_and_check('511010.SH')  # 5-year Bond

# Priority 2: Backups
fetch_and_check('513100.SH')  # Alternative Nasdaq
fetch_and_check('511220.SH')  # Corporate Bond

# Bonus: Add commodity diversity
fetch_and_check('510170.SH')  # Commodity ETF (originally planned but missing)
```

---

### Option 3: Start Backtest from 2023 (Alternative)

**When all ETFs have real data:**

```python
# Run backtest from 2023-01-01 instead of 2018-01-01
results = backtester.run(start_date='2023-01-01')
```

**Advantages**:
- ✅ All ETFs have real data from 2023
- ✅ No data quality concerns
- ✅ Can use all 7 current ETFs

**Trade-offs**:
- ❌ Only 3 years of backtest (vs 8 years)
- ❌ Less statistically significant
- ❌ Doesn't cover multiple market cycles

---

## 🛠️ Implementation Steps

### Quick Fix (Option 1) - 5 minutes

```bash
# 1. Create clean dataset
python << 'EOF'
import pandas as pd

prices = pd.read_csv('data/etf_prices.csv', index_col=0, parse_dates=True)

# Keep only high-quality ETFs
clean_etfs = ['510300.SH', '510500.SH', '513500.SH', '511260.SH', '518880.SH']
clean_prices = prices[clean_etfs]

clean_prices.to_csv('data/etf_prices_clean.csv')
print(f"✓ Created clean dataset with {len(clean_etfs)} ETFs")
print(f"ETFs: {clean_etfs}")
EOF

# 2. Update strategy to use clean data
# In your scripts, change:
# prices = pd.read_csv('data/etf_prices.csv', ...)
# To:
# prices = pd.read_csv('data/etf_prices_clean.csv', ...)

# 3. Rerun backtests
python run_v2_strategy.py  # Will use v2.0 strategy with clean 5-ETF dataset
```

### Proper Fix (Option 2) - 30-60 minutes

```bash
# 1. Install data fetching library
pip install akshare

# 2. Run the replacement fetcher
python fetch_replacement_etfs.py
# This will:
#   - Try multiple alternative ETFs
#   - Check data quality for each
#   - Select the best ones
#   - Create data/etf_prices_v2.csv

# 3. Update strategy
# Change: pd.read_csv('data/etf_prices.csv')
# To:     pd.read_csv('data/etf_prices_v2.csv')

# 4. Rerun all backtests
python run_v2_strategy.py
```

---

## 📊 Expected Impact on Results

### With Clean Data (5 ETFs)

**Expected changes:**
- ✅ Max drawdown likely **improves** (no frozen bonds dragging portfolio)
- ✅ Early period (2018-2020) performance **improves** (no frozen assets)
- ✅ More reliable / trustworthy results
- ≈ Similar overall return (still limited by market conditions)

**Why drawdown should improve:**
- Current: 25-35% allocated to frozen bond (511090.SH) = dead weight in crashes
- Clean: Remove frozen bond = portfolio more responsive = better hedge

### With Better Alternatives (6-8 ETFs)

**Expected changes:**
- ✅ All benefits of clean data above
- ✅ Better diversification
- ✅ Potential for higher returns (if alternatives have better performance)

---

## 🎯 Recommendation

**Immediate Action**: Use Option 1 (5-ETF clean dataset)
- Takes 5 minutes
- Solves data quality issue immediately
- Can run reliable backtests today

**Follow-up**: Try Option 2 (fetch better alternatives)
- Do this when you have time
- Could improve diversification
- Might find better performing alternatives

**Document**: Note data quality issue in all reports
- Current v1.0 and v2.0 results are conservative estimates
- Real performance likely better (frozen bonds = 0% return)
- Clean data provides more reliable assessment

---

## 📝 Next Steps

1. **Create clean dataset**:
   ```bash
   python -c "import pandas as pd; prices = pd.read_csv('data/etf_prices.csv', index_col=0, parse_dates=True); clean = prices[['510300.SH', '510500.SH', '513500.SH', '511260.SH', '518880.SH']]; clean.to_csv('data/etf_prices_clean.csv'); print('✓ Created clean dataset')"
   ```

2. **Rerun v2.0 with clean data**:
   - Update `run_v2_strategy.py` to use `etf_prices_clean.csv`
   - Rerun backtest
   - Compare old vs new results

3. **Update documentation**:
   - Add data quality section to v2.0_improved.md
   - Explain frozen ETF issue
   - Note that clean results are more reliable

4. **Optional: Fetch alternatives**:
   - Install akshare: `pip install akshare`
   - Run: `python fetch_replacement_etfs.py`
   - Test new alternatives

---

Want me to create the clean 5-ETF dataset and rerun the backtest now?
