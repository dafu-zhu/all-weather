# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pure implementation of Ray Dalio's All Weather Strategy for A-share markets using risk parity optimization. Each asset contributes **equally** to portfolio risk, ensuring consistent performance across economic environments.

**Current Status**: v1.0 production (6.90% return, 1.05 Sharpe, -4.66% max drawdown, PERFECT risk parity)

**Note**: v2.0 was removed for violating All Weather principles (see V2_REMOVAL_SUMMARY.md)

## Running the Code

### Execute Strategy
```bash
# Run v1.0 pure risk parity
python scripts/run_v1_baseline.py

# Interactive analysis
jupyter notebook notebooks/all_weather_v1_baseline.ipynb
```

### Development
```bash
# Install dependencies
uv sync

# Run any script from project root
python scripts/<script_name>.py
```

## Architecture

### Core Design: Pure Risk Parity

**Single Strategy**: Equal risk contribution from all assets

**v1.0 (Pure Risk Parity)**:
- Weekly rebalancing
- Equal risk contribution (std = 0)
- No allocation constraints
- Result: 6.90% return, -4.66% max drawdown
- Allocation: 17.6% stocks, 78.8% bonds, 3.6% gold

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

### v1.0 Parameters
```python
from src.strategy import AllWeatherV1

strategy = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',  # Weekly Monday
    lookback=100,            # 100 days covariance
    commission_rate=0.0003   # 0.03%
)
```

**Why these parameters?**
- Weekly rebalancing: Frequent enough to maintain risk parity
- 100-day lookback: Balances recency with stability
- No constraints: Required for true risk parity

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

**v1.0 Pure Risk Parity**:
- Annual Return: 6.90%
- Sharpe Ratio: 1.05
- Max Drawdown: -4.66%
- Benchmark Multiple: 1.46x (vs CSI 300)
- Final Value: ¥1,679,345 from ¥1M
- **Risk Parity**: PERFECT (std = 0.0000000018)

**Key Insight**: True All Weather prioritizes risk balance over returns. This is Ray Dalio's original philosophy.

## Documentation Structure

- **README.md**: Quick start and performance summary
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

## Key Principles

1. **Risk Parity = Equal Risk**: Every asset contributes exactly the same to portfolio volatility
2. **Low Returns Are Expected**: All Weather trades return for stability (6-7% vs 10-12%)
3. **Bond-Heavy Is Correct**: 78.8% bonds is mathematically required, not conservative
4. **Data Quality Critical**: Frozen prices destroy backtests
5. **Simplicity = Honesty**: Pure risk parity without constraints maintains integrity
