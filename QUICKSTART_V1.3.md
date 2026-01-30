# All Weather v1.3 - Quick Start Guide

## Goal: Reduce Max Drawdown Below -10%

✅ **ACHIEVED**: Max drawdown reduced from -14.13% to **-8.98%**

## How to Use v1.3

### Basic Usage

```python
from src.data_loader_us import download_us_etfs, get_all_weather_us_etfs
from src.strategy_us import AllWeather4QuadrantUS

# Load US ETF data
etf_info = get_all_weather_us_etfs()
tickers = list(etf_info.keys())
prices = download_us_etfs(tickers, start_date='2015-01-01')

# Create v1.3 strategy (recommended settings)
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

print(f"Final Value: ${results['final_value']:,.0f}")
print(f"Max Drawdown: {results['metrics']['max_drawdown']:.2%}")
```

## Version Comparison

| Version | Return | Max DD | Sharpe | When to Use |
|---------|--------|--------|--------|-------------|
| v1.1 Pure RP | 3.18% | -14.13% | 0.03 | Theoretical purity |
| v1.2 Constrained | 4.72% | -15.35% | 0.26 | Higher returns |
| **v1.3 + Vol(3.8%)** | **1.73%** | **-8.98%** ✓ | -0.39 | **Low drawdowns** |

## Volatility Target Selection

Choose based on your risk tolerance:

```python
# Very conservative (max DD ~-5%)
target_volatility=0.034  # 3.4%

# Balanced - RECOMMENDED (max DD ~-9%)
target_volatility=0.038  # 3.8%

# Moderate (max DD ~-12%)
target_volatility=0.050  # 5.0%

# No constraint (max DD ~-14%)
target_volatility=None
```

## Run Comparison

Compare all versions side-by-side:

```bash
python scripts/compare_4quadrant_versions.py
```

This generates:
- `results/4quadrant_comparison.csv` - Performance metrics table
- `results/4quadrant_comparison.png` - Visualization charts

## Performance Summary (2018-2026)

**v1.3 with 3.8% Vol Targeting**:
- 📊 Annual Return: 1.73%
- 📉 Max Drawdown: -8.98% ✓ (meets -10% target)
- 📈 Annual Volatility: 3.27%
- 💰 Final Value: $114,789 from $100,000
- 🔄 Rebalances: 380 (weekly)
- 💸 Total Commissions: $529

## What's Different in v1.3?

**4-Quadrant Economic Framework**:
- Divides portfolio risk across 4 economic environments
- Each quadrant gets ~25% of risk:
  - Growth Rising + Inflation Rising → Stocks + Commodities
  - Growth Rising + Inflation Falling → Stocks + Bonds
  - Growth Falling + Inflation Rising → TIPS + Commodities
  - Growth Falling + Inflation Falling → All Bonds

**Volatility Targeting**:
- Scales portfolio to achieve target volatility level
- Lower volatility = lower drawdowns
- Preserves risk parity ratios while reducing exposure

## Key Trade-offs

**Pros**:
- ✅ Achieves max drawdown < -10%
- ✅ Much lower volatility (3.27% vs 5.97%)
- ✅ Smoother equity curve
- ✅ Better downside protection

**Cons**:
- ❌ Lower returns (1.73% vs 3.18%)
- ❌ Negative Sharpe ratio (barely beats T-bills)
- ❌ May underperform in bull markets

## When NOT to Use v1.3

Use v1.1 or v1.2 instead if:
- You can tolerate -14% to -15% drawdowns
- You need higher returns (4-5% annual)
- You're investing for 10+ years
- You want positive Sharpe ratio

## Documentation

- **V1.3_4QUADRANT_SUMMARY.md** - Full implementation details
- **CLAUDE.md** - Architecture and usage guide
- **notebooks/all_weather_v1.1_us.ipynb** - Interactive analysis

## Questions?

**Q: Why such low returns?**
A: Achieving -9% max DD requires very low volatility (3.27%). This proportionally reduces returns. This is the fundamental trade-off of All Weather.

**Q: Why negative Sharpe ratio?**
A: In 2018-2026, risk-free rates (T-bills) exceeded 1.73% portfolio returns. This is expected in ultra-low-volatility portfolios.

**Q: Can I get higher returns with low drawdowns?**
A: Not with this approach. Try v1.2 for 4.72% returns (but -15% max DD).

**Q: Is this better than Bridgewater's All Weather?**
A: No. Bridgewater gets 8%+ returns using leverage (2:1 on bonds). We don't allow leverage.

## Next Steps

1. Test with your own capital amount
2. Adjust `target_volatility` to your risk tolerance
3. Monitor weekly rebalancing schedule
4. Review V1.3_4QUADRANT_SUMMARY.md for details
