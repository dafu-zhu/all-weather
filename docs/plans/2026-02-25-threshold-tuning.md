# Threshold Tuning Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Find optimal `rebalance_threshold` for v1.2 strategy by grid search with train/val/test split.

**Architecture:** Single script runs backtests across 7 threshold values, outputs comparison table with recommendation.

**Tech Stack:** Python, pandas, existing `AllWeatherV1` strategy class

---

## Task 1: Create Threshold Tuning Script

**Files:**
- Create: `scripts/tune_threshold.py`

**Step 1: Write the script**

```python
"""
Tune rebalance_threshold parameter for All Weather v1.2

Train: 2018-2023 (find best threshold)
Validate: 2024 (confirm generalization)
Test: 2025-2026 (final out-of-sample check)
"""

import sys
sys.path.append('.')

import pandas as pd
from src.data_loader import load_prices
from src.strategy import AllWeatherV1

# Configuration
THRESHOLDS = [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15]
TRAIN_START = '2018-01-01'
TRAIN_END = '2023-12-31'
VAL_START = '2024-01-01'
VAL_END = '2024-12-31'
TEST_START = '2025-01-01'
TEST_END = None  # Use all available data


def run_backtest(prices, threshold, start_date, end_date):
    """Run backtest with given threshold and return metrics."""
    strategy = AllWeatherV1(
        prices=prices,
        initial_capital=1_000_000,
        rebalance_freq='W-MON',
        lookback=252,
        commission_rate=0.0003,
        rebalance_threshold=threshold,
        use_shrinkage=True  # v1.2
    )
    results = strategy.run_backtest(
        start_date=start_date,
        end_date=end_date,
        verbose=False
    )
    return {
        'sharpe': results['metrics']['sharpe_ratio'],
        'return': results['metrics']['annual_return'],
        'max_dd': results['metrics']['max_drawdown'],
        'rebalances': results['rebalances_executed'],
        'final_value': results['final_value']
    }


def main():
    print("=" * 70)
    print("THRESHOLD PARAMETER TUNING - All Weather v1.2")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    prices = load_prices('data/etf_prices_7etf.csv')
    print(f"Data range: {prices.index[0].date()} to {prices.index[-1].date()}")

    # === TRAINING PHASE ===
    print(f"\n{'=' * 70}")
    print(f"TRAINING PHASE ({TRAIN_START} to {TRAIN_END})")
    print("=" * 70)

    train_results = []
    for threshold in THRESHOLDS:
        metrics = run_backtest(prices, threshold, TRAIN_START, TRAIN_END)
        train_results.append({'threshold': threshold, **metrics})
        print(f"  {threshold:5.0%}: Sharpe={metrics['sharpe']:.3f}, "
              f"Return={metrics['return']:.2%}, MaxDD={metrics['max_dd']:.2%}, "
              f"Rebalances={metrics['rebalances']}")

    train_df = pd.DataFrame(train_results)
    train_df['rank'] = train_df['sharpe'].rank(ascending=False).astype(int)

    best_threshold = train_df.loc[train_df['sharpe'].idxmax(), 'threshold']
    best_sharpe = train_df['sharpe'].max()

    print(f"\nBest threshold (training): {best_threshold:.0%} (Sharpe={best_sharpe:.3f})")

    # === VALIDATION PHASE ===
    print(f"\n{'=' * 70}")
    print(f"VALIDATION PHASE ({VAL_START} to {VAL_END})")
    print("=" * 70)

    val_results = []
    for threshold in THRESHOLDS:
        metrics = run_backtest(prices, threshold, VAL_START, VAL_END)
        val_results.append({'threshold': threshold, **metrics})
        print(f"  {threshold:5.0%}: Sharpe={metrics['sharpe']:.3f}, "
              f"Return={metrics['return']:.2%}, MaxDD={metrics['max_dd']:.2%}")

    val_df = pd.DataFrame(val_results)
    val_df['rank'] = val_df['sharpe'].rank(ascending=False).astype(int)

    best_val_rank = val_df.loc[val_df['threshold'] == best_threshold, 'rank'].values[0]
    best_val_sharpe = val_df.loc[val_df['threshold'] == best_threshold, 'sharpe'].values[0]

    validation_passed = best_val_rank <= 3
    status = "✓ PASSED" if validation_passed else "✗ FAILED"
    print(f"\nBest threshold ({best_threshold:.0%}) validation rank: {best_val_rank}/7 {status}")

    # === TEST PHASE ===
    print(f"\n{'=' * 70}")
    print(f"TEST PHASE ({TEST_START} to end)")
    print("=" * 70)

    test_metrics = run_backtest(prices, best_threshold, TEST_START, TEST_END)
    print(f"\nThreshold {best_threshold:.0%} test results:")
    print(f"  Sharpe Ratio:  {test_metrics['sharpe']:.3f}")
    print(f"  Annual Return: {test_metrics['return']:.2%}")
    print(f"  Max Drawdown:  {test_metrics['max_dd']:.2%}")
    print(f"  Rebalances:    {test_metrics['rebalances']}")

    # === SUMMARY ===
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)

    print("\nTraining Results (sorted by Sharpe):")
    print(train_df.sort_values('sharpe', ascending=False).to_string(index=False))

    print(f"\n{'─' * 70}")
    print(f"RECOMMENDATION: Use {best_threshold:.0%} threshold")
    print(f"  Training Sharpe:   {best_sharpe:.3f}")
    print(f"  Validation Sharpe: {best_val_sharpe:.3f} (rank {best_val_rank}/7)")
    print(f"  Test Sharpe:       {test_metrics['sharpe']:.3f}")

    if not validation_passed:
        print(f"\n⚠️  WARNING: Best training threshold not in top-3 for validation.")
        print(f"   Consider using validation's best threshold instead.")
        val_best = val_df.loc[val_df['sharpe'].idxmax(), 'threshold']
        print(f"   Validation best: {val_best:.0%}")

    print("=" * 70)


if __name__ == '__main__':
    main()
```

**Step 2: Run the script**

```bash
python scripts/tune_threshold.py
```

Expected: Training table, validation check, test results, recommendation

**Step 3: Commit**

```bash
git add scripts/tune_threshold.py
git commit -m "feat: add threshold tuning script for v1.2"
```

---

## Task 2: Analyze Results and Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (if threshold changes from 5%)

**Step 1: Review output**

Examine the tuning results:
- Is best threshold different from current 5%?
- Did validation pass (top-3)?
- Is test performance reasonable?

**Step 2: Update documentation (if needed)**

If optimal threshold differs from 5%, update `CLAUDE.md`:
- Strategy Configuration section
- Performance Expectations section

**Step 3: Commit (if changes made)**

```bash
git add CLAUDE.md
git commit -m "docs: update recommended threshold based on tuning"
```

---

## Success Criteria

1. Script runs without errors
2. Training results show clear ranking
3. Best threshold is top-3 in validation
4. Test Sharpe > 0.8
5. Recommendation is actionable
