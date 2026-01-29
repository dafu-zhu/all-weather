# Data Quality Report

Generated: 2026-01-28

## Dataset Comparison

| Dataset | ETFs | Date Range | Frozen Data (2018-2026) | Recommendation |
|---------|------|------------|-------------------------|----------------|
| `etf_prices.csv` | 7 | 2015-01-05 to 2026-01-28 | ❌ 513300.SH (689d), 511090.SH (1321d) | **Do not use** |
| `etf_prices_clean.csv` | 5 | 2015-01-05 to 2026-01-28 | ✓ None | Good, but limited |
| `etf_prices_7etf.csv` | 7 | 2015-01-05 to 2026-01-28 | ✓ None | **Recommended** |
| `etf_prices_enhanced.csv` | 8 | 2015-01-05 to 2026-01-28 | ❌ 511130.SH (486d) | Do not use |

## Recommended Dataset: `etf_prices_7etf.csv`

### ETF Composition

| Code | Name | Type | Annualized Vol | 2018-2026 Return |
|------|------|------|----------------|------------------|
| 510300.SH | CSI 300 | Stock (China) | 21.98% | 4.02% |
| 510500.SH | CSI 500 | Stock (China) | 22.93% | 8.82% |
| 513500.SH | S&P 500 | Stock (US) | 18.61% | 193.52% |
| 000066.SH | Unknown Index | Stock (China) | 23.97% | 114.38% |
| 513100.SH | Nasdaq-100 | Stock (US/Tech) | 24.01% | 326.96% |
| 511260.SH | 10Y Treasury | Bond | 2.68% | 13.96% |
| 518880.SH | Gold | Commodity | 13.94% | 87.01% |

### Data Quality Metrics (2018-2026)

| ETF | Zero Return % | Max Consecutive Frozen Days | Quality |
|-----|---------------|----------------------------|---------|
| 510300.SH | 1.1% | 2 | Excellent |
| 510500.SH | 0.7% | 1 | Excellent |
| 513500.SH | 4.6% | 3 | Very Good |
| 000066.SH | 0.0% | 0 | Perfect |
| 513100.SH | 1.9% | 2 | Excellent |
| 511260.SH | 0.8% | 2 | Excellent |
| 518880.SH | 1.7% | 1 | Excellent |

### Asset Allocation Breakdown

- **Stocks**: 5 ETFs (71.4%)
  - China domestic: 510300.SH, 510500.SH, 000066.SH
  - US indices: 513500.SH, 513100.SH
- **Bonds**: 1 ETF (14.3%)
  - 511260.SH (10Y Treasury)
- **Commodities**: 1 ETF (14.3%)
  - 518880.SH (Gold)

### Alignment Status

✓ All ETFs share identical date index (2692 trading days)
✓ No missing values (NaN)
✓ Maximum date gap: 11 days (holidays/weekends - normal)
✓ No frozen periods > 30 days in backtest window (2018-2026)

## Issues Found in Other Datasets

### `etf_prices.csv` - DO NOT USE
- **513300.SH** (Nasdaq): 689 consecutive days frozen (2018-01-03 to 2020-11-05)
- **511090.SH** (30Y Bond): 1,321 consecutive days frozen (2018-01-03 to 2023-06-13)
- These frozen periods cause flat PnL curves in backtests

### `etf_prices_enhanced.csv` - DO NOT USE
- **511130.SH**: 486 consecutive days frozen in backtest period
- Other ETFs are clean but this one asset compromises the dataset

## Historical Context

- **etf_prices_clean.csv**: Created to remove 513300.SH and 511090.SH frozen data
- **etf_prices_7etf.csv**: Enhanced version adding 000066.SH and 513100.SH
- Both new ETFs have excellent data quality and strong performance

## Recommendations

1. **Production Use**: `etf_prices_7etf.csv`
   - Best balance of diversification (7 ETFs) and data quality
   - All ETFs have <5% zero returns
   - No frozen periods in backtest window

2. **Notebook Updates**: Change from `etf_prices_clean.csv` → `etf_prices_7etf.csv`

3. **Optimizer Updates**: Add 000066.SH and 513100.SH to stock indices list

4. **Expected Impact**:
   - Better diversification (7 vs 5 ETFs)
   - Higher risk-adjusted returns (more equity exposure options)
   - More robust risk parity (better covariance matrix estimation)
