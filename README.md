# All Weather Strategy - Pure Risk Parity Implementation

Pure implementation of Ray Dalio's All Weather Strategy for the A-share market following risk parity principles.

## Overview

This project implements **true All Weather** strategy where each asset contributes **equally** to portfolio risk, ensuring consistent performance across different economic environments.

**Key Principle**: Equal risk contribution from all assets (bonds, stocks, commodities).

## Performance (2018-2026)

### Optimized v1.0 (Current)

| Metric | All Weather v1.0 | Benchmark (CSI 300) | Advantage |
|--------|------------------|---------------------|-----------|
| Annual Return | **7.05%** | 4.02% | **+3.03%** |
| Sharpe Ratio | **1.11** | 0.05 | **22x better** |
| Max Drawdown | **-3.90%** | -44.75% | **91% lower** |
| Volatility | 3.65% | 21.98% | 83% lower |
| Final Value (¥1M start) | **¥1,697,909** | ¥1,363,089 | **+¥334,820** |

**Key Achievements**:
- ✅ 1.75x benchmark return with 91% lower drawdown
- ✅ Perfect risk parity (std(RC) < 1e-6)
- ✅ Enhanced tail risk analytics (VaR, CVaR, skewness, kurtosis)

**Recent Improvements** (Jan 2026):
- Optimized lookback period: 100 → 252 days (+0.15% return)
- Enhanced risk metrics: Added VaR, CVaR, distribution analysis
- Performance gain: +1.11% portfolio value vs baseline

## Strategy Configuration

### Optimized Parameters (v1.0)

- **Optimization**: Pure risk parity (equal risk from each asset)
- **Rebalancing**: Weekly (Mondays) - optimal for risk parity
- **Lookback**: 252 days (1 trading year) - optimal for stability
- **Transaction Cost**: 0.03% per trade
- **Volatility Targeting**: None (not beneficial for this portfolio)
- **Dataset**: 7 high-quality ETFs (aligned data)

**Why these parameters?**
- 252-day lookback provides most stable covariance estimates (+0.15% return vs 100-day)
- Weekly rebalancing maintains optimal allocation (+0.49% vs monthly)
- No volatility targeting needed (natural 3.65% vol is appropriate)

## Quick Start

```bash
# Activate environment
uv sync

# Run backtest
python scripts/run_v1_baseline.py

# Or launch Jupyter notebook
jupyter notebook notebooks/all_weather_v1_baseline.ipynb
```

## Asset Universe (7 High-Quality ETFs)

| Class | ETF Code | Name | Allocation |
|-------|----------|------|------------|
| Stock | 510300.SH | CSI 300 | ~4% |
| Stock | 510500.SH | CSI 500 | ~3% |
| Stock | 513500.SH | S&P 500 | ~5% |
| Stock | 000066.SH | China Index | ~2% |
| Stock | 513100.SH | Nasdaq-100 | ~3% |
| Bond | 511260.SH | 10Y Treasury | ~79% |
| Commodity | 518880.SH | Gold | ~4% |

**Total Stocks**: 17.6% | **Bonds**: 78.8% | **Commodities**: 3.6%

**Why 79% bonds?** Bonds have ~2.7% volatility vs stocks at ~22%. For equal risk contribution, bonds need 8x the allocation of stocks.

**Data Quality**: All ETFs have <5% zero returns in backtest period (2018-2026). No frozen data issues.

## Risk Parity Verification

```
Risk Contributions (all equal):
  510300.SH:  0.000266  ✓
  510500.SH:  0.000266  ✓
  513500.SH:  0.000266  ✓
  511260.SH:  0.000266  ✓
  518880.SH:  0.000266  ✓
  000066.SH:  0.000266  ✓
  513100.SH:  0.000266  ✓

Std(RC): 0.00000000 (perfect balance)
```

## Project Structure

```
all-weather/
├── src/
│   ├── optimizer.py       # Pure risk parity optimizer
│   ├── strategy.py        # AllWeatherV1 strategy class
│   ├── portfolio.py       # Portfolio management
│   ├── backtest.py        # Backtesting engine
│   ├── metrics.py         # Performance calculations
│   └── data_loader.py     # ETF data loading
├── notebooks/
│   └── all_weather_v1_baseline.ipynb   # Interactive analysis
├── data/
│   └── etf_prices_7etf.csv             # 7 high-quality ETFs
├── scripts/
│   └── run_v1_baseline.py              # Production script
└── docs/
    ├── versions/v1.0_baseline.md       # Baseline documentation
    └── RISK_PARITY_ANALYSIS.md         # Risk parity principles
```

## Usage Example

```python
from src.data_loader import load_prices
from src.optimizer import optimize_weights
from src.strategy import AllWeatherV1

# Load data
prices = load_prices('data/etf_prices_7etf.csv')

# Run backtest
strategy = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',  # Weekly
    lookback=100,
    commission_rate=0.0003
)

results = strategy.run_backtest(start_date='2018-01-01')

print(f"Final Value: ¥{results['final_value']:,.0f}")
print(f"Annual Return: {results['metrics']['annual_return']:.2%}")
print(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['metrics']['max_drawdown']:.2%}")
```

## Why v2.0 Was Removed

An earlier version (v2.0) attempted to improve returns by forcing 60% stock allocation while maintaining "risk parity." However, this violated the fundamental All Weather principle:

**Mathematical Impossibility**: Cannot have both equal risk contributions AND high equity allocation given volatility differences (stocks 22% vs bonds 2.7%).

**Result**: v2.0's risk contributions were **215,948x worse** than true risk parity, with bonds contributing **negative risk** and stocks dominating.

**Decision**: Removed v2.0 to maintain integrity of All Weather principles. This implementation is honest pure risk parity.

See `docs/RISK_PARITY_ANALYSIS.md` for full analysis.

## Documentation

- **docs/versions/v1.0_baseline.md**: Implementation details and methodology
- **docs/RISK_PARITY_ANALYSIS.md**: Why risk parity and high returns are incompatible
- **data/DATA_QUALITY_REPORT.md**: Data alignment and quality analysis
- **ALIGNMENT_SUMMARY.md**: Data cleaning process

## Key Insights

1. **True All Weather = Low Returns**: Ray Dalio's original strategy accepts modest returns (4-6%) for stability
2. **Data Quality Matters**: Clean, aligned data is critical - frozen prices destroy backtests
3. **Risk Parity Works**: -4.21% max drawdown vs -44.75% benchmark proves risk balance
4. **Simple is Honest**: Pure risk parity without constraints maintains theoretical integrity

## When to Use This Strategy

**Use All Weather when:**
- Risk control is priority over returns
- Want stable performance across economic environments
- Can tolerate 78% bond allocation
- Value low drawdowns over high returns

**Don't use when:**
- Need >10% annual returns
- Can't tolerate bond-heavy allocation
- Want equity-driven growth
- Have aggressive risk tolerance

## Requirements

```
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.4.0
seaborn>=0.11.0
jupyter>=1.0.0
```

Install with:
```bash
uv sync
```

## License

MIT

## Acknowledgments

- Strategy concept: Ray Dalio's All Weather Portfolio
- Optimization: Pure risk parity (equal risk contribution)
- Implementation: Python + scipy + pandas
- Principle: Theoretical integrity over performance optimization
