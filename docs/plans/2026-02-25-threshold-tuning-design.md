# Threshold Parameter Tuning Design

## Goal

Tune the `rebalance_threshold` parameter for All Weather v1.2 strategy to optimize Sharpe ratio.

## Data Split

| Period | Dates | Purpose |
|--------|-------|---------|
| **Train** | 2018-01-01 to 2023-12-31 | Grid search across thresholds (6 years) |
| **Validate** | 2024-01-01 to 2024-12-31 | Confirm generalization |
| **Test** | 2025-01-01 to 2026-01-28 | Final out-of-sample check |

## Parameter Grid

Thresholds to test: `[0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15]`

- 0.01 (1%): Frequent rebalancing
- 0.05 (5%): Current default
- 0.15 (15%): Minimal rebalancing

## Optimization Metric

**Primary**: Sharpe Ratio (risk-adjusted returns)

**Secondary** (for reference): Annual Return, Max Drawdown, Rebalance Count

## Implementation

**Script**: `scripts/tune_threshold.py`

**Process**:
1. Load `etf_prices_7etf.csv`
2. For each threshold in grid:
   - Run backtest on train period (2018-2023)
   - Record Sharpe ratio, return, max drawdown, rebalance count
3. Select threshold with best Sharpe on training
4. Validate: run that threshold on 2024, confirm it's still top-3
5. Test: run on 2025-2026, report final metrics
6. Output comparison table + recommendation

## Output Format

```
=== Training Results (2018-2023) ===
Threshold | Sharpe | Return | Max DD | Rebalances
----------|--------|--------|--------|----------
1%        | 1.25   | 9.5%   | -8.2%  | 210
...

Best threshold (training): X%

=== Validation (2024) ===
Threshold X% Sharpe: 1.15 (rank: 2/7)

=== Test Results (2025-2026) ===
Threshold X%: Sharpe=1.20, Return=8.5%, MaxDD=-6.2%

Recommendation: Use X% threshold
```

## Success Criteria

1. Best training threshold is **top-3 in validation** (guards against overfitting)
2. Test performance is **reasonable** (Sharpe > 0.8, not drastically worse than training)
3. Clear winner emerges (not a tie between multiple thresholds)

## Rationale

- **Simple train/val/test split**: Sufficient for single parameter tuning
- **6-year training**: Covers multiple market regimes (2018 volatility, 2020 COVID, 2022 rate hikes)
- **Validation check**: Guards against overfitting to training period
- **Test holdout**: True out-of-sample verification
