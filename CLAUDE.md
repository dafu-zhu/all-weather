# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pure implementation of Ray Dalio's All Weather Strategy using risk parity optimization. Each asset contributes **equally** to portfolio risk, ensuring consistent performance across economic environments.

**Supported Markets**:
- **A-shares (China)**: v1.0, v1.1, v1.2 (see version comparison below)
- **US Markets**: v1.1-v1.3 (see US Markets section below)

**Note**: v2.0 was removed for violating All Weather principles (see V2_REMOVAL_SUMMARY.md)

## Running the Code

### Execute Strategy
```bash
# Compare all versions (v1.0, v1.1, v1.2)
python scripts/compare_v1.0_v1.1_v1.2.py

# Test v1.2 (current version)
python scripts/test_v1.2_full.py

# Test v1.2 shrinkage feature
python scripts/test_v1.2_basic.py

# Interactive analysis - Version comparison (RECOMMENDED)
jupyter notebook notebooks/all_weather_v1.0_v1.1_v1.2_comparison.ipynb

# Interactive analysis - Original baseline
jupyter notebook notebooks/all_weather_v1_baseline.ipynb
```

### Development
```bash
# Install dependencies
uv sync

# Run any script from project root
python scripts/<script_name>.py
```

## Version Comparison: v1.0 vs v1.1 vs v1.2

### v1.0 - Pure Risk Parity (Always Rebalance)
- **Strategy**: Weekly rebalancing, 252-day lookback, sample covariance
- **Performance (2018-2026)**: 7.05% annual return, 1.11 Sharpe, -3.90% max DD
- **Rebalances**: 384 rebalances, ¥2,199 commissions
- **Behavior**: Rebalances every Monday regardless of drift
- **Use case**: Academic baseline, pure implementation

### v1.1 - Adaptive Rebalancing
- **Strategy**: v1.0 + adaptive rebalancing (5% drift threshold)
- **Performance (2018-2026)**: 7.58% annual return, 1.13 Sharpe, -6.55% max DD
- **Rebalances**: 5 rebalances, ¥615 commissions (72% savings vs v1.0)
- **Improvements over v1.0**:
  - **+¥67,064** final value (+3.9%)
  - **+0.53%** annual return
  - **-379** rebalances (98.7% reduction)
- **Use case**: Low-cost passive implementation

### v1.2 - Adaptive + Covariance Shrinkage ⭐ RECOMMENDED
- **Strategy**: v1.1 + Ledoit-Wolf shrinkage for robust covariance estimation
- **Performance (2018-2026)**: 10.62% annual return, 1.34 Sharpe, -7.68% max DD
- **Rebalances**: 175 rebalances, ¥2,165 commissions
- **Improvements over v1.0**:
  - **+¥493,591** final value (+29.1%)
  - **+3.57%** annual return
  - **+0.23** Sharpe ratio
- **Improvements over v1.1**:
  - **+¥426,527** final value (+24.2%)
  - **+3.04%** annual return
  - **+0.22** Sharpe ratio
- **Use case**: Production trading (best risk-adjusted returns)

### When to Use Each Version

| Use Case | Version | Reason |
|----------|---------|--------|
| **Production trading** | **v1.2** | **Best returns, best Sharpe** |
| Low-cost passive | v1.1 | Minimal rebalancing |
| Academic research | v1.0 | Pure baseline |
| High volatility | v1.0 | Most responsive |

### Performance Summary Table

| Metric | v1.0 | v1.1 | v1.2 ⭐ |
|--------|------|------|---------|
| Annual Return | 7.05% | 7.58% | **10.62%** |
| Sharpe Ratio | 1.11 | 1.13 | **1.34** |
| Max Drawdown | -3.90% | -6.55% | -7.68% |
| Final Value | ¥1.70M | ¥1.76M | **¥2.19M** |
| Rebalances | 384 | 5 | 175 |
| Commissions | ¥2,199 | ¥615 | ¥2,165 |

**Configuration**:
```python
# v1.0 behavior (always rebalance, no shrinkage)
strategy = AllWeatherV1(
    prices=prices,
    rebalance_threshold=0,
    use_shrinkage=False
)

# v1.1 behavior (adaptive, no shrinkage)
strategy = AllWeatherV1(
    prices=prices,
    rebalance_threshold=0.05,
    use_shrinkage=False
)

# v1.2 behavior (adaptive + shrinkage, RECOMMENDED)
strategy = AllWeatherV1(
    prices=prices,
    rebalance_threshold=0.05,
    use_shrinkage=True
)
```

## Architecture

### Core Design: Pure Risk Parity

**Single Strategy**: Equal risk contribution from all assets

**v1.2 (Adaptive + Shrinkage)** ⭐ CURRENT:
- Ledoit-Wolf covariance shrinkage for robust estimation
- Adaptive rebalancing (only when drift > 5%)
- Equal risk contribution (std = 0)
- No allocation constraints
- Result: 10.62% return, 1.34 Sharpe, -7.68% max drawdown
- **24.2% better** than v1.1, **29.1% better** than v1.0

**v1.1 (Adaptive Risk Parity)**:
- Adaptive rebalancing (only when drift > 5%)
- Sample covariance (no shrinkage)
- Result: 7.58% return, -6.55% max drawdown
- 98.7% fewer rebalances, 72% commission savings vs v1.0

**v1.0 (Pure Risk Parity)**:
- Weekly rebalancing (always)
- Sample covariance (no shrinkage)
- Result: 7.05% return, -3.90% max drawdown
- Baseline for comparison

### Module Structure

**src/**: Production code library
- `optimizer.py` - Pure risk parity optimizer (`optimize_weights`)
- `strategy.py` - `AllWeatherV1` strategy class
- `backtest.py` - Historical simulation engine
- `portfolio.py` - Position tracking, rebalancing, transaction costs
- `metrics.py` - Performance calculations (Sharpe, Sortino, drawdown, etc.)
- `data_loader.py` - ETF data loading and quality checking

**scripts/**: Experimental scripts (machine-read, create freely)
- Runner scripts for backtests
- One-off experiments and analyses

**notebooks/**: Interactive analysis (human-read, documented)
- Full strategy walkthroughs with visualizations
- Self-contained, only import from `src/`

### Key Architectural Decisions

1. **Pure Risk Parity Only**: `optimize_weights()` minimizes std(risk_contributions) without constraints. This is the ONLY way to achieve true All Weather balance.

2. **Why 78.8% Bonds?**: Bonds have ~2.7% volatility vs stocks at ~22%. For equal risk contribution, bonds need 8x the allocation of stocks. This is mathematically required.

3. **Data Quality Matters**: The 7-ETF aligned dataset (`etf_prices_7etf.csv`) has no frozen prices. All ETFs have <5% zero returns.

4. **Asset Type Detection**: Optimizer doesn't need asset classification since there are no constraints. All assets treated equally for risk parity.

## Critical Data Issues

### Frozen ETF Detection
Original dataset (`etf_prices.csv`) had frozen data:
- **511090.SH** (30yr Bond): 1,321 days frozen
- **513300.SH** (Nasdaq): 689 days frozen

**Solution**: Use `etf_prices_7etf.csv` with 7 high-quality ETFs.

### Production Dataset
Use **data/etf_prices_7etf.csv** (7 high-quality ETFs):
- 510300.SH (CSI 300) - 1.1% zeros
- 510500.SH (CSI 500) - 0.7% zeros
- 513500.SH (S&P 500) - 4.6% zeros
- 000066.SH (China Index) - 0.0% zeros
- 513100.SH (Nasdaq-100) - 1.9% zeros
- 511260.SH (10Y Treasury) - 0.8% zeros
- 518880.SH (Gold) - 1.7% zeros

All ETFs: <5% zero returns = excellent quality.

## Strategy Configuration

### v1.2 Parameters (Recommended)
```python
from src.strategy import AllWeatherV1

strategy = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',       # Weekly Monday
    lookback=252,                 # 252 days (1 year) covariance
    commission_rate=0.0003,       # 0.03%
    rebalance_threshold=0.05,     # 5% drift (adaptive rebalancing)
    use_shrinkage=True            # Ledoit-Wolf shrinkage (v1.2)
)
```

**Why these parameters?**
- **Covariance shrinkage**: Reduces estimation noise → more stable weights (+3.04% return)
- **Adaptive rebalancing**: Only rebalance when drift > 5% (avoids overtrading)
- **252-day lookback**: Full trading year for stable covariance
- **5% threshold**: Optimal balance between cost and performance
- No constraints: Required for true risk parity

**Backward Compatibility**:
- v1.1: Set `use_shrinkage=False`
- v1.0: Set `use_shrinkage=False, rebalance_threshold=0`

## Development Workflow

### Adding New ETFs
1. Check data quality: `data_loader.check_data_quality(new_prices)`
2. Verify <5% zero returns (except bonds <25% acceptable)
3. Add to dataset and re-run optimizer
4. No code changes needed (pure risk parity handles any assets)

### Creating Experiments
Put throwaway scripts in `scripts/` - no organization needed.

### Modifying Optimizer
**DON'T**: The v1.0 optimizer is mathematically proven. Modifications will break risk parity.

### Running Backtests
Notebooks are self-contained and import only from `src/`. Run independently.

## Performance Expectations

Based on 2018-2026 backtest:

**v1.2 Adaptive + Shrinkage** ⭐ CURRENT (RECOMMENDED):
- Annual Return: 10.62%
- Sharpe Ratio: 1.34
- Sortino Ratio: 1.73
- Max Drawdown: -7.68%
- Calmar Ratio: 1.38
- Final Value: ¥2,191,500 from ¥1M
- Rebalances: 175
- Commissions: ¥2,165
- **Best risk-adjusted returns across all versions**

**v1.1 Adaptive Risk Parity**:
- Annual Return: 7.58%
- Sharpe Ratio: 1.13
- Max Drawdown: -6.55%
- Final Value: ¥1,764,973 from ¥1M
- Rebalances: 5
- Commissions: ¥615
- **Commission Savings**: 72% vs v1.0

**v1.0 Pure Risk Parity** (Baseline):
- Annual Return: 7.05%
- Sharpe Ratio: 1.11
- Max Drawdown: -3.90%
- Final Value: ¥1,697,909 from ¥1M
- Rebalances: 384 (every week)
- **Risk Parity**: PERFECT (std = 0.0000000018)

**Key Insights**:
- v1.2 covariance shrinkage provides **24% better returns** than v1.1 by reducing estimation noise
- Shrinkage leads to more stable weights and better out-of-sample performance
- The additional rebalancing in v1.2 (vs v1.1) is justified by superior returns

## Documentation Structure

- **README.md**: Quick start and performance summary
- **notebooks/all_weather_v1.0_v1.1_v1.2_comparison.ipynb**: ⭐ Comprehensive version comparison
- **notebooks/all_weather_v1_baseline.ipynb**: Original baseline analysis
- **V2_REMOVAL_SUMMARY.md**: Why v2.0 was removed
- **docs/RISK_PARITY_ANALYSIS.md**: Mathematical analysis of risk parity
- **docs/versions/v1.0_baseline.md**: Baseline implementation details
- **data/DATA_QUALITY_REPORT.md**: Data quality verification
- **ALIGNMENT_SUMMARY.md**: Data alignment process

## Common Gotchas

1. **Import paths**: Notebooks use `sys.path.append('../')` to import from src/
2. **Date format**: Prices must have DatetimeIndex, not string dates
3. **Rebalance frequency**: Use `'W-MON'` (weekly Monday)
4. **Bond allocation**: 78.8% bonds is CORRECT for risk parity (not a bug)
5. **Zero returns**: <5% is excellent, bonds can be higher but our data is clean

## Why v2.0 Was Removed

v2.0 attempted "constrained risk parity" with 60% min stocks and 35% max bonds. This violated All Weather principles:

**Mathematical Impossibility**: Cannot have both equal risk AND high equity allocation.

**Result**: v2.0's risk balance was **215,948x worse** than v1.0, with bonds contributing **negative risk**.

**Decision**: Maintain theoretical integrity. This repository now implements HONEST All Weather.

See **V2_REMOVAL_SUMMARY.md** and **docs/RISK_PARITY_ANALYSIS.md** for full analysis.

## US Markets Implementation

### Overview

Three versions for US ETFs with different risk/return profiles:

**v1.1 Pure Risk Parity** (`AllWeatherUS`):
- 8 US ETFs (SPY, QQQ, IWM, TLT, IEF, TIP, GLD, DBC)
- Pure risk parity, no constraints
- Result: 3.18% return, -14.13% max drawdown
- Allocation: ~16% stocks, ~65% bonds, ~18% commodities

**v1.2 Constrained Risk Parity** (`AllWeatherConstrainedUS`):
- Same ETFs with asset class constraints
- Constraints: 25-50% stocks, 30-55% bonds, 15-35% commodities
- Result: 4.72% return, -15.35% max drawdown
- Better returns but higher drawdowns

**v1.3 4-Quadrant Risk Balance** (`AllWeather4QuadrantUS`):
- Implements Bridgewater's economic environment framework
- 4 quadrants: GR+IR, GR+IF, GF+IR, GF+IF (25% risk each)
- Optional volatility targeting
- Result (with 3.8% vol target): 1.73% return, **-8.98% max drawdown** ✓
- Achieves max drawdown < -10% goal

### When to Use Each Version

| Version | Use When | Expected Performance |
|---------|----------|---------------------|
| **v1.1 Pure RP** | Want theoretical purity | 3% return, -14% max DD |
| **v1.2 Constrained** | Want higher returns | 5% return, -15% max DD |
| **v1.3 4-Quadrant** | Want low drawdowns | 2% return, -9% max DD |

### v1.3 Configuration

```python
from src.data_loader_us import download_us_etfs, get_all_weather_us_etfs
from src.strategy_us import AllWeather4QuadrantUS

# Load US ETF data
etf_info = get_all_weather_us_etfs()
prices = download_us_etfs(list(etf_info.keys()), start_date='2015-01-01')

# Create v1.3 strategy with volatility targeting
strategy = AllWeather4QuadrantUS(
    prices=prices,
    initial_capital=100_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.001,
    target_volatility=0.038  # 3.8% for max DD < -10%
)

# Run backtest
results = strategy.run_backtest(start_date='2018-01-01')
```

### Volatility Targeting Guidelines

Choose target volatility based on risk tolerance:

| Target Vol | Expected Max DD | Expected Return | Use Case |
|-----------|----------------|-----------------|----------|
| None | -14% | 3.1% | No drawdown constraint |
| 5.0% | -12% | 2.0% | Moderate protection |
| 3.8% | **-9%** | 1.7% | **Meet -10% target** |
| 3.4% | -5% | 2.0% | Very conservative |

**Recommended**: 3.8% volatility target (highest return while meeting -10% drawdown)

### 4-Quadrant Economic Framework

Based on Bridgewater's All Weather methodology:

**Growth Rising + Inflation Rising** (25% risk):
- Assets: SPY, QQQ, IWM, GLD, DBC
- Rationale: Equities and commodities perform well

**Growth Rising + Inflation Falling** (25% risk):
- Assets: SPY, QQQ, IWM, TLT, IEF
- Rationale: Equities and bonds both benefit

**Growth Falling + Inflation Rising** (25% risk):
- Assets: TIP, GLD, DBC
- Rationale: Inflation protection needed

**Growth Falling + Inflation Falling** (25% risk):
- Assets: TLT, IEF, TIP
- Rationale: Bonds provide safety

**Key Insight**: Assets can appear in multiple quadrants (e.g., SPY in 2 quadrants), which is correct—they hedge multiple scenarios.

### Running US Backtests

```bash
# Compare all versions
python scripts/compare_4quadrant_versions.py

# Find optimal volatility target
python scripts/find_optimal_vol_target.py

# Interactive analysis
jupyter notebook notebooks/all_weather_v1.1_us.ipynb
```

### US Data Quality

**ETF Universe** (8 ETFs):
- Stocks: SPY, QQQ, IWM
- Bonds: TLT, IEF, TIP
- Commodities: GLD, DBC

**Data Source**: yfinance (Yahoo Finance API)

**Quality Metrics** (2015-2026):
- Missing data: 0%
- Zero returns: <3% for all ETFs
- Volatility: Reasonable ranges (4-14% annualized)

### Performance Summary (2018-2026)

| Metric | v1.1 Pure RP | v1.2 Constrained | v1.3 + Vol(3.8%) |
|--------|-------------|------------------|------------------|
| Annual Return | 3.18% | 4.72% | 1.73% |
| Annual Volatility | 5.97% | 6.68% | 3.27% |
| Sharpe Ratio | 0.03 | 0.26 | -0.39 |
| Max Drawdown | -14.13% | -15.35% | **-8.98%** ✓ |
| Calmar Ratio | 0.23 | 0.31 | 0.17 |
| Final Value ($100K) | $128,682 | $144,904 | $114,775 |

**Key Trade-off**: Lower drawdowns (v1.3) require accepting lower returns.

### US Markets Gotchas

1. **Low returns are expected**: 2018-2026 had poor bond performance (rising rates)
2. **Negative Sharpe ratio**: Risk-free rate > portfolio returns in low-vol portfolios
3. **Vol targeting reduces returns**: Proportional scaling down
4. **No leverage allowed**: Bridgewater uses 2:1 leverage on bonds (we don't)
5. **Quadrant overlap**: Assets in multiple quadrants is correct, not a bug

### US Documentation

- **V1.3_4QUADRANT_SUMMARY.md**: Full v1.3 implementation details
- **notebooks/all_weather_v1.1_us.ipynb**: v1.1 analysis and trading instructions
- **scripts/compare_4quadrant_versions.py**: Version comparison script
- **scripts/find_optimal_vol_target.py**: Volatility optimization

## Key Principles

1. **Risk Parity = Equal Risk**: Every asset contributes exactly the same to portfolio volatility
2. **Low Returns Are Expected**: All Weather trades return for stability (6-7% vs 10-12%)
3. **Bond-Heavy Is Correct**: 78.8% bonds is mathematically required, not conservative
4. **Data Quality Critical**: Frozen prices destroy backtests
5. **Simplicity = Honesty**: Pure risk parity without constraints maintains integrity
