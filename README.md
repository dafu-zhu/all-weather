# All Weather Strategy — Pure Risk Parity

Pure implementation of Ray Dalio's All Weather Strategy using risk parity optimization. Each asset contributes **equally** to portfolio risk, ensuring consistent performance across economic environments.

## Performance (2018–2026)

| Metric | All Weather v1.2 | Benchmark (CSI 300) |
|--------|------------------|---------------------|
| Annual Return | **10.62%** | 4.02% |
| Sharpe Ratio | **1.34** | 0.05 |
| Max Drawdown | **-7.68%** | -44.75% |
| Final Value (¥1M start) | **¥2,191,500** | ¥1,363,089 |
| Rebalances | 175 | — |
| Commissions | ¥2,165 | — |

**Why 79% bonds?** Bonds have ~2.7% volatility vs stocks at ~22%. For equal risk contribution, bonds need ~8x the allocation. This is mathematically required for true risk parity.

## Usage

```python
from src.data_loader import load_prices
from src.strategy import AllWeatherV1

prices = load_prices('data/etf_prices_7etf.csv')

strategy = AllWeatherV1(
    prices=prices,
    initial_capital=1_000_000,
    rebalance_freq='W-MON',
    lookback=252,
    commission_rate=0.0003,
    rebalance_threshold=0.03,  # Adaptive rebalancing (3% drift)
    use_shrinkage=True          # Ledoit-Wolf covariance shrinkage
)

results = strategy.run_backtest(start_date='2018-01-01')
```

## Project Structure

```
all-weather/
├── src/
│   ├── optimizer.py       # Pure risk parity optimizer
│   ├── strategy.py        # AllWeatherV1 strategy class
│   ├── backtest.py        # Historical simulation engine
│   ├── portfolio.py       # Position tracking & rebalancing
│   ├── metrics.py         # Performance calculations
│   └── data_loader.py     # ETF data loading & quality checks
├── notebooks/
│   ├── all_weather_v1.0_v1.1_v1.2_comparison.ipynb  # Version comparison
│   └── all_weather_v1_baseline.ipynb                 # Baseline analysis
├── data/
│   └── etf_prices_7etf.csv   # 7 A-share ETFs (production)
├── scripts/                   # Backtest runners & experiments
└── docs/                      # Technical documentation
```

## Documentation

- **docs/RISK_PARITY_ANALYSIS.md** — Mathematical analysis of risk parity
- **docs/versions/v1.0_baseline.md** — Baseline implementation details
- **data/DATA_QUALITY_REPORT.md** — Data quality verification
- **V2_REMOVAL_SUMMARY.md** — Why constrained risk parity was removed
