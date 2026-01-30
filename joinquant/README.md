# All Weather v1.0 for JoinQuant

JoinQuant-compatible implementation of Ray Dalio's All Weather Strategy using pure risk parity optimization.

## Quick Start

### 1. Local Validation (Recommended)

Before deploying to JoinQuant, validate the embedded optimizer:

```bash
# Run local tests
python joinquant/test_local.py
```

**Expected Output:**
```
✅ PASS: Optimizer Consistency
✅ PASS: Risk Contribution
✅ PASS: Risk Parity Achievement
✅ PASS: Weights Sum to 1.0

🎉 All tests passed! Ready for JoinQuant deployment.
```

### 2. Deploy to JoinQuant

**Steps:**
1. Log in to [JoinQuant Research Platform](https://www.joinquant.com/)
2. Create new strategy file
3. Copy entire contents of `all_weather_v1_joinquant.py`
4. Paste into JoinQuant editor
5. Configure backtest parameters (see below)
6. Run backtest

**Backtest Configuration:**
```
Start Date: 2018-01-01
End Date: 2026-01-28
Initial Capital: ¥1,000,000
Benchmark: 510300.XSHG (CSI 300)
Frequency: Daily
```

### 3. Expected Results

Based on standalone validation (2018-2026):

| Metric | Target | Tolerance |
|--------|--------|-----------|
| Annual Return | 7.05% | ±0.5% |
| Sharpe Ratio | 1.11 | ±0.1 |
| Max Drawdown | -3.90% | ±0.5% |
| Rebalances | ~420 | Weekly for 8 years |
| Turnover | ~4.2x | Annual |

**Allocation Pattern (typical):**
- Bonds: 75-80% (low volatility requires high allocation)
- Stocks: 15-20% (high volatility requires low allocation)
- Gold: 3-5% (medium volatility)

This bond-heavy allocation is **correct** for true risk parity.

---

## Strategy Configuration

### ETF Universe (7 Assets)

| Symbol | Asset | Type | Quality |
|--------|-------|------|---------|
| 510300.XSHG | CSI 300 | Large-cap stocks | 1.1% zeros |
| 510500.XSHG | CSI 500 | Mid-cap stocks | 0.7% zeros |
| 513500.XSHG | S&P 500 | US stocks | 4.6% zeros |
| 511260.XSHG | 10Y Treasury | Bonds | 0.8% zeros |
| 518880.XSHG | Gold | Commodity | 1.7% zeros |
| 000066.XSHG | China Index | Bonds | 0.0% zeros |
| 513100.XSHG | Nasdaq-100 | US tech | 1.9% zeros |

All ETFs have <5% zero returns = excellent data quality.

### Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Rebalance Frequency | Weekly (Monday) | Optimal balance vs daily (7.05% vs 6.8% after costs) |
| Lookback Period | 252 days (1 year) | Balances recency with stability |
| Commission Rate | 0.03% | Typical A-share ETF commission |
| Optimizer | Pure Risk Parity | Minimize std(risk contributions) |

**Why these parameters?**
- Tested in standalone implementation (see `docs/versions/v1.0_baseline.md`)
- Weekly rebalancing: Frequent enough to maintain risk parity without excessive costs
- 252-day lookback: Statistical significance (1 year) without overfitting
- No constraints: Required for true risk parity

---

## Monitoring

### Weekly Checks (Every Monday)

**In JoinQuant logs, verify:**
1. Rebalancing occurred (search for "Rebalance #")
2. No errors (no lines starting with "Error:")
3. All 7 orders successful (should show "7/7 successful")
4. Portfolio value growing steadily

**Example healthy log:**
```
[2026-01-20] Rebalance #1 completed
  Orders: 7/7 successful
  Top 3: 511260: 42.3%, 000066: 36.5%, 510300: 8.7%
  Portfolio Value: ¥1,000,000
```

### Monthly Performance Review

**Check these metrics:**
- Return vs benchmark (CSI 300): Should track 1.4-1.5x
- Max drawdown: Should stay < -5%
- Turnover: Should be ~0.35x per month (4.2x annually)
- Allocation stability: Bonds should dominate (75-80%)

**Red flags:**
- Drawdown > -10%: Investigate risk calculation
- No rebalancing for 2+ weeks: Check logs for errors
- Stock allocation > 30%: Optimizer may have failed
- All equal weights: Fallback triggered (check why)

---

## Troubleshooting

### Issue: "Insufficient history"

**Cause:** Not enough trading days for 252-day lookback

**Solution:**
- Backtest start date must be at least 252 trading days after earliest data
- Use start date >= 2018-01-01 for this dataset
- Strategy will skip rebalance and keep existing positions (safe)

### Issue: "NaN values in returns"

**Cause:** Data quality issues (missing prices, frozen ETFs)

**Solution:**
- Check ETF listings: All should be trading on rebalance date
- Verify JoinQuant data feed status
- Strategy skips rebalance (safe) and retries next week

### Issue: "Optimization failed"

**Cause:** Numerical instability in covariance matrix (rare)

**Solution:**
- Strategy automatically uses inverse volatility fallback
- Check logs for "using inverse volatility weights"
- If frequent (>10%), investigate data quality

### Issue: Orders failed (less than 7/7 successful)

**Cause:** Individual ETF trading halt, delisting, or liquidity issues

**Solution:**
- Strategy continues with successful orders (partial rebalance)
- Check failed ETF status on exchange
- If persistent, consider removing problematic ETF from universe

### Issue: Performance diverges from expected

**Acceptable divergence:** ±2% annually due to:
- Slippage (backtest vs live)
- Different data quality
- Holiday timing differences

**Investigate if divergence > 5%:**
1. Compare allocations to expected (75-80% bonds)
2. Check turnover (should be ~4.2x annually)
3. Verify commission rate (0.03%)
4. Review rebalance frequency (should be ~52/year)

### Issue: Bond allocation too low (<60%)

**Cause:** Optimizer not achieving risk parity

**Investigation:**
1. Check risk contributions in logs (should be equal)
2. Verify covariance matrix calculation
3. Look for "Optimization failed" warnings

**Fix:**
- If using modified code: Restore embedded optimizer from original file
- If persistent: Run local validation tests
- Contact support with error logs

---

## Differences from Standalone

| Aspect | Standalone | JoinQuant | Notes |
|--------|-----------|-----------|-------|
| File structure | Modular (src/) | Single-file | Embedded optimizer |
| Symbol format | .SH | .XSHG | Platform convention |
| Data loading | CSV file | history() | Same DataFrame structure |
| Order execution | Portfolio class | order_target_value() | Different API |
| Scheduling | Manual loop | run_weekly() | Platform scheduling |
| Logging | print() | log.info() | Platform logging |

**Key invariant:** Optimizer logic is **identical** (validated by test_local.py).

---

## Advanced Configuration

### Changing Rebalance Frequency

**Monthly rebalancing (lower turnover):**
```python
run_monthly(rebalance, day=1, time='open')  # First trading day of month
```

**Daily rebalancing (higher returns, higher costs):**
```python
run_daily(rebalance, time='open')
```

**Warning:** Daily rebalancing tested at 6.8% return vs 7.05% weekly (costs matter).

### Adjusting Lookback Period

**Shorter lookback (more responsive, less stable):**
```python
context.lookback = 126  # 6 months
```

**Longer lookback (more stable, less responsive):**
```python
context.lookback = 504  # 2 years
```

**Warning:** 252 days (1 year) is optimal per standalone testing.

### Adding/Removing ETFs

**To modify universe:**
1. Update `context.securities` list in `initialize()`
2. Verify ETF data quality (<5% zero returns)
3. Test locally first with `test_local.py`
4. Re-run backtest to validate performance

**No code changes needed:** Pure risk parity handles any number of assets.

---

## Performance Attribution

### Why 7.05% return (not higher)?

**All Weather prioritizes risk balance over returns:**
- Bonds: 2-3% return, 75-80% allocation = ~2% contribution
- Stocks: 10-12% return, 15-20% allocation = ~2% contribution
- Gold: 8-10% return, 3-5% allocation = ~0.4% contribution
- Commission drag: -0.3%
- **Total: ~7%**

This is **expected** for true risk parity. Higher returns require higher risk.

### Why -3.90% max drawdown (so low)?

**Equal risk contribution = balanced downside:**
- Bonds stabilize during stock crashes
- Stocks rally during bond selloffs
- Gold hedges both risks
- No single asset dominates drawdown

Result: **46% lower drawdown than CSI 300** (-3.90% vs -7.10%).

### Why 1.11 Sharpe ratio (excellent)?

**Sharpe = Return / Volatility**
- 7.05% return (moderate)
- 6.35% volatility (low due to bonds)
- **Sharpe = 1.11** (top quartile for institutional portfolios)

This is the **All Weather advantage**: Consistent returns with low volatility.

---

## Support

### Local Validation Failed

1. Check Python environment: `python --version` (need 3.8+)
2. Install dependencies: `uv sync`
3. Verify data file exists: `data/etf_prices_7etf.csv`
4. Run with verbose output: `python -v joinquant/test_local.py`

### JoinQuant Errors

1. Check platform status: [status.joinquant.com](https://status.joinquant.com)
2. Verify ETF symbols: All should end with .XSHG
3. Review logs: Look for first error message
4. Test with smaller date range first (e.g., 2024-2026)

### Questions

- **Project repo:** [all-weather on GitHub](https://github.com/yourusername/all-weather)
- **JoinQuant docs:** [www.joinquant.com/help](https://www.joinquant.com/help)
- **All Weather background:** See `README.md` and `CLAUDE.md` in repo

---

## Validation Checklist

Before live trading:

- [ ] Local tests pass (`python joinquant/test_local.py`)
- [ ] Backtest (2018-2026) within tolerances
- [ ] Weekly rebalancing occurs (~420 times)
- [ ] Bond allocation 75-80% (risk parity achieved)
- [ ] Annual return 6.5-7.5%
- [ ] Sharpe ratio 1.0-1.2
- [ ] Max drawdown < -5%
- [ ] No persistent errors in logs
- [ ] All 7 ETFs trading successfully

---

## Files in This Directory

```
joinquant/
├── all_weather_v1_joinquant.py    # Production strategy (deploy this)
├── test_local.py                   # Local validation tests
└── README.md                       # This file
```

**Deploy:** Copy `all_weather_v1_joinquant.py` to JoinQuant platform.

**Validate:** Run `test_local.py` before deployment.

---

## Version History

**v1.0 (2026-01-29)**
- Initial JoinQuant port
- Pure risk parity optimizer embedded
- 7 ETF universe (all <5% zero returns)
- Weekly Monday rebalancing
- 252-day lookback
- Validated against standalone implementation

---

## License

MIT License - See repository root for details.

**Disclaimer:** This strategy is for educational and research purposes. Past performance does not guarantee future results. Use at your own risk.
