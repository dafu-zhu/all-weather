# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Implementation of Ray Dalio's All Weather Strategy for A-share markets using risk parity optimization. The project achieved 12.00% annual return (3x benchmark) through constrained risk parity with clean, high-quality ETF data.

**Current Status**: v2.0 production ready (12.00% return, 0.86 Sharpe, -13.97% max drawdown)

## Running the Code

### Execute Production Strategy
```bash
# Run v2.0 optimized strategy (recommended)
python scripts/run_v2_strategy.py

# Run comparisons
python scripts/run_v2_7etf.py          # 7-ETF vs 8-ETF vs 5-ETF
python scripts/run_clean_comparison.py  # Data quality comparison
```

### Interactive Analysis
```bash
# Launch notebooks for detailed analysis
jupyter notebook notebooks/all_weather_v1_baseline.ipynb   # v1.0 pure risk parity
jupyter notebook notebooks/all_weather_v2_optimized.ipynb  # v2.0 constrained (recommended)
```

### Development
```bash
# Install dependencies
uv sync

# Run any script from project root
python scripts/<script_name>.py
```

## Architecture

### Core Design Pattern: Two-Strategy System

The codebase implements two distinct strategies:

**v1.0 (Pure Risk Parity)**: Replicates PDF methodology
- Weekly rebalancing
- Equal risk contribution from all assets
- No allocation constraints
- Result: 3.71% return (underperformed benchmark)

**v2.0 (Constrained Risk Parity)**: Optimized for A-share market
- Monthly rebalancing (77% cost reduction)
- 60% minimum stocks, 35% maximum bonds
- 100-day covariance lookback
- Result: 12.00% return (3x benchmark)

### Module Structure

**src/**: Production code library (careful organization)
- `optimizer.py` - Both v1.0 (`optimize_weights`) and v2.0 (`optimize_weights_constrained`) optimizers
- `strategy.py` - `AllWeatherV1` and `AllWeatherV2` strategy classes
- `backtest.py` - Historical simulation engine (used by v1.0)
- `portfolio.py` - Position tracking, rebalancing, transaction costs
- `metrics.py` - Performance calculations (Sharpe, Sortino, drawdown, etc.)
- `data_loader.py` - ETF data loading and quality checking

**scripts/**: Experimental scripts (machine-read, create freely without organization)
- Runner scripts for various dataset comparisons
- One-off experiments and analyses
- Data fetching utilities

**notebooks/**: Interactive analysis (human-read, documented)
- Full strategy walkthroughs with visualizations
- Self-contained, only import from `src/`

### Key Architectural Decisions

1. **Separate Optimizers**: `optimize_weights()` (v1.0) and `optimize_weights_constrained()` (v2.0) are distinct functions because they solve fundamentally different problems. v1.0 minimizes std(risk_contributions), v2.0 adds inequality constraints for min stocks/max bonds.

2. **Strategy Classes vs Backtester**:
   - `Backtester` class: v1.0 baseline, tightly coupled to pure risk parity
   - `AllWeatherV1`/`AllWeatherV2` classes: Modern strategy wrapper with flexible optimizer selection
   - Both coexist for historical reproducibility

3. **Data Quality Over Diversification**: The 5-ETF clean dataset (12.00% return) outperforms 7-ETF with frozen data (7.92%). Always check for frozen prices using `data_loader.check_data_quality()`.

4. **Asset Type Detection**: Optimizers identify stocks/bonds/commodities by hardcoded ETF codes (e.g., `510300.SH` = stock). When adding new ETFs, update the lists in `optimizer.optimize_weights_constrained()`.

## Critical Data Issues

### Frozen ETF Detection
Two ETFs in original dataset had frozen/unreliable data:
- **511090.SH** (30yr Bond): 76% zero returns
- **513300.SH** (Nasdaq): 54% zero returns

**How to Check**: Use `data_loader.check_data_quality()` - flags assets with >30% zero returns.

### Production Dataset
Use **data/etf_prices_clean.csv** (5 high-quality ETFs):
- 510300.SH (CSI 300) - 1.2% zeros
- 510500.SH (CSI 500) - 0.7% zeros
- 513500.SH (S&P 500) - 6.3% zeros
- 511260.SH (10Y Treasury) - 24.6% zeros (normal for bonds)
- 518880.SH (Gold) - 1.8% zeros

## Strategy Configuration

### v2.0 Optimal Parameters (Tested)
```python
from src.strategy import AllWeatherV2

strategy = AllWeatherV2(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='MS',         # Monthly, not 'W-MON'
    lookback=100,                # 100 days, not 60 or 252
    commission_rate=0.0003,      # 0.03%
    min_stock_alloc=0.60,        # 60%, tested 40-70%
    max_bond_alloc=0.35          # 35%, tested 30-50%
)
```

**Why these parameters?**
- Monthly rebalancing: 77% cost reduction vs weekly, better returns
- 100-day lookback: Balances recency with stability
- 60% min stocks: Drives returns while maintaining risk parity principles
- 35% max bonds: Prevents over-conservative allocation (v1.0 allocated 80% to bonds)

## Development Workflow

### Adding New ETFs
1. Check data quality: `data_loader.check_data_quality(new_prices)`
2. Verify <30% zero returns (except bonds <50% acceptable)
3. Update asset type lists in `optimizer.optimize_weights_constrained()`:
   - Add code to `stock_indices` or `bond_indices` lists
4. Test with `scripts/run_v2_strategy.py`

### Creating Experiments
Put throwaway scripts in `scripts/` - no organization needed. The directory is machine-read only.

### Modifying Optimizers
- v1.0 optimizer: Don't modify (historical reproducibility)
- v2.0 optimizer: Constraints are in `optimize_weights_constrained()` - uses scipy.optimize.minimize with SLSQP method
- Risk contributions: Both use same calculation in `risk_contribution()` function

### Running Backtests
Notebooks are self-contained and import only from `src/`. Run them independently without script dependencies.

## Performance Expectations

Based on 2018-2026 backtest:

**v2.0 with Clean Data (Production)**:
- Annual Return: 12.00% (target: >10% ✓)
- Sharpe Ratio: 0.86 (target: >0.5 ✓)
- Max Drawdown: -13.97% (target: <15% ✓)
- Benchmark Multiple: 3x (vs CSI 300)
- Final Value: ¥2.56M from ¥1M

**Key Insight**: Data quality matters more than diversification. 5 clean ETFs > 7 ETFs with frozen data.

## Documentation Structure

- **README.md**: Quick start and performance summary
- **FINAL_RESULTS.md**: Mission summary (Phase 1 & 2 complete)
- **v1.0_baseline.md**: Baseline implementation details
- **v2.0_improved.md**: 7 optimization iterations explained
- **ETF_REPLACEMENT_GUIDE.md**: Data quality analysis
- **ALTERNATIVE_ETF_ATTEMPT.md**: Alternative ETF fetch attempts (failed due to API issues)

## Common Gotchas

1. **Import paths**: Notebooks use `sys.path.append('../')` to import from src/
2. **Date format**: Prices must have DatetimeIndex, not string dates
3. **Rebalance frequency**: Use `'MS'` (month start) not `'M'` (month end)
4. **Asset detection**: Hardcoded by ETF codes - update lists when adding new ETFs
5. **Zero returns**: Bond ETFs naturally have higher zero return % (24-30% acceptable)
