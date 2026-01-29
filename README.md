# All Weather Strategy - Pure Risk Parity Implementation

Pure implementation of Ray Dalio's All Weather Strategy for **A-share and US markets** following risk parity principles.

## Overview

This project implements **true All Weather** strategy where each asset contributes **equally** to portfolio risk, ensuring consistent performance across different economic environments.

**Key Principle**: Equal risk contribution from all assets (bonds, stocks, commodities).

## Two Implementations

### v1.0 - A-share Markets (China ETFs)
- **Data Source**: Local CSV with 7 A-share ETFs
- **Market**: Shanghai Stock Exchange
- **Period**: 2018-2026 (8 years)
- **Currency**: CNY (¥)
- **Transaction Cost**: 0.03%
- **Status**: ✅ Production

### v1.1 - US Markets (US ETFs)
- **Data Source**: yfinance (real-time download)
- **Market**: US equity and bond markets
- **ETF Universe**: 8 US ETFs (SPY, QQQ, IWM, TLT, IEF, TIP, GLD, DBC)
- **Currency**: USD ($)
- **Transaction Cost**: 0.10%
- **Status**: ✅ Production

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

### A-share Version (v1.0)

```bash
# Activate environment
uv sync

# Run backtest
python scripts/run_v1_baseline.py

# Or launch Jupyter notebook
jupyter notebook notebooks/all_weather_v1_baseline.ipynb
```

### US Version (v1.1)

```bash
# Activate environment
uv sync

# Launch Jupyter notebook (downloads data via yfinance)
jupyter notebook notebooks/all_weather_v1.1_us.ipynb
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

## US Asset Universe (8 ETFs)

| Class | Ticker | Name | Description |
|-------|--------|------|-------------|
| Stock | SPY | SPDR S&P 500 | US large-cap stocks (S&P 500) |
| Stock | QQQ | Invesco QQQ Trust | US tech stocks (Nasdaq-100) |
| Stock | IWM | iShares Russell 2000 | US small-cap stocks |
| Bond | TLT | iShares 20+ Year Treasury | Long-term US Treasury bonds |
| Bond | IEF | iShares 7-10 Year Treasury | Intermediate-term Treasury bonds |
| Bond | TIP | iShares TIPS Bond | Inflation-protected Treasury bonds |
| Commodity | GLD | SPDR Gold Shares | Physical gold |
| Commodity | DBC | Invesco DB Commodity | Broad commodity index |

**Data Source**: yfinance API (real-time historical data from 2015-present)

**Note**: US version uses higher transaction cost (0.10% vs 0.03%) due to typical US brokerage fees.

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
│   ├── optimizer.py          # Pure risk parity optimizer (shared)
│   ├── portfolio.py          # Portfolio management (shared)
│   ├── metrics.py            # Performance calculations (shared)
│   ├── strategy.py           # AllWeatherV1 - A-share strategy
│   ├── data_loader.py        # A-share ETF data loading
│   ├── strategy_us.py        # AllWeatherUS - US strategy
│   └── data_loader_us.py     # US ETF data loading (yfinance)
├── notebooks/
│   ├── all_weather_v1_baseline.ipynb   # A-share interactive analysis
│   └── all_weather_v1.1_us.ipynb       # US interactive analysis
├── data/
│   └── etf_prices_7etf.csv             # 7 A-share ETFs (production)
├── scripts/
│   └── run_v1_baseline.py              # A-share backtest script
└── docs/
    ├── versions/v1.0_baseline.md       # Baseline documentation
    └── RISK_PARITY_ANALYSIS.md         # Risk parity principles
```

**Modular Design**: Core modules (optimizer, portfolio, metrics) are shared between A-share and US implementations.

## Usage Examples

### A-share Version (v1.0)

```python
from src.data_loader import load_prices
from src.strategy import AllWeatherV1

# Load data
prices = load_prices('data/etf_prices_7etf.csv')

# Run backtest
strategy = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003
)

results = strategy.run_backtest(start_date='2018-01-01')

print(f"Final Value: ¥{results['final_value']:,.0f}")
print(f"Annual Return: {results['metrics']['annual_return']:.2%}")
print(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['metrics']['max_drawdown']:.2%}")
```

### US Version (v1.1)

```python
from src.data_loader_us import download_us_etfs, get_all_weather_us_etfs
from src.strategy_us import AllWeatherUS

# Download US ETF data
etf_universe = get_all_weather_us_etfs()
tickers = list(etf_universe.keys())
prices = download_us_etfs(tickers, start_date='2015-01-01')

# Run backtest
strategy = AllWeatherUS(
    prices=prices,
    initial_capital=100_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.001
)

results = strategy.run_backtest(start_date='2018-01-01')

print(f"Final Value: ${results['final_value']:,.0f}")
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
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.7.0
seaborn>=0.12.0
yfinance>=0.2.0
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
