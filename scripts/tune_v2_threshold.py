"""
Tune drift_threshold parameter for All Weather v2.0

Train: 2018-2023 (find best threshold)
Validate: 2024 (confirm generalization - must rank top-3)
Test: 2025-onwards (final out-of-sample check)

Compares v2.0 against v1.2 baseline.
"""

import sys
sys.path.append('.')

import pandas as pd
from src.data_loader import load_prices
from src.strategy import AllWeatherV1
from src.strategy_v2 import AllWeatherV2

# Configuration
THRESHOLDS = [0.03, 0.05, 0.07, 0.10, 0.15]
TRAIN_START = '2018-01-01'
TRAIN_END = '2023-12-31'
VAL_START = '2024-01-01'
VAL_END = '2024-12-31'
TEST_START = '2025-01-01'
TEST_END = None  # Use all available data


def run_v2_backtest(prices, threshold, start_date, end_date):
    """Run v2.0 backtest with given drift_threshold and return metrics."""
    strategy = AllWeatherV2(
        prices=prices,
        initial_capital=1_000_000,
        lookback=252,
        commission_rate=0.0003,
        drift_threshold=threshold,
        use_shrinkage=True,
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
        'daily_rebalances': results['daily_rebalance_count'],
        'weekly_rebalances': results['weekly_rebalance_count'],
        'final_value': results['final_value']
    }


def run_v12_backtest(prices, start_date, end_date):
    """Run v1.2 baseline backtest and return metrics."""
    strategy = AllWeatherV1(
        prices=prices,
        initial_capital=1_000_000,
        rebalance_freq='W-MON',
        lookback=252,
        commission_rate=0.0003,
        rebalance_threshold=0.05,
        use_shrinkage=True,
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
    print("DRIFT THRESHOLD PARAMETER TUNING - All Weather v2.0")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    prices = load_prices('data/etf_prices_7etf.csv')
    print(f"Data range: {prices.index[0].date()} to {prices.index[-1].date()}")

    # === TRAINING PHASE ===
    print(f"\n{'=' * 70}")
    print(f"TRAINING PHASE ({TRAIN_START} to {TRAIN_END})")
    print("=" * 70)

    print("\nv2.0 Results:")
    train_results = []
    for threshold in THRESHOLDS:
        metrics = run_v2_backtest(prices, threshold, TRAIN_START, TRAIN_END)
        train_results.append({'threshold': threshold, **metrics})
        print(f"  {threshold:5.0%}: Sharpe={metrics['sharpe']:.3f}, "
              f"Return={metrics['return']:.2%}, MaxDD={metrics['max_dd']:.2%}, "
              f"DailyRebalances={metrics['daily_rebalances']}")

    train_df = pd.DataFrame(train_results)
    train_df['rank'] = train_df['sharpe'].rank(ascending=False).astype(int)

    best_threshold = train_df.loc[train_df['sharpe'].idxmax(), 'threshold']
    best_sharpe = train_df['sharpe'].max()

    # v1.2 baseline
    v12_train = run_v12_backtest(prices, TRAIN_START, TRAIN_END)
    print(f"\nv1.2 Baseline: Sharpe={v12_train['sharpe']:.3f}, "
          f"Return={v12_train['return']:.2%}, MaxDD={v12_train['max_dd']:.2%}")

    print(f"\nBest v2.0 threshold (training): {best_threshold:.0%} (Sharpe={best_sharpe:.3f})")

    # === VALIDATION PHASE ===
    print(f"\n{'=' * 70}")
    print(f"VALIDATION PHASE ({VAL_START} to {VAL_END})")
    print("=" * 70)

    print("\nv2.0 Results:")
    val_results = []
    for threshold in THRESHOLDS:
        metrics = run_v2_backtest(prices, threshold, VAL_START, VAL_END)
        val_results.append({'threshold': threshold, **metrics})
        print(f"  {threshold:5.0%}: Sharpe={metrics['sharpe']:.3f}, "
              f"Return={metrics['return']:.2%}, MaxDD={metrics['max_dd']:.2%}")

    val_df = pd.DataFrame(val_results)
    val_df['rank'] = val_df['sharpe'].rank(ascending=False).astype(int)

    best_val_rank = val_df.loc[val_df['threshold'] == best_threshold, 'rank'].values[0]
    best_val_sharpe = val_df.loc[val_df['threshold'] == best_threshold, 'sharpe'].values[0]

    # v1.2 baseline
    v12_val = run_v12_backtest(prices, VAL_START, VAL_END)
    print(f"\nv1.2 Baseline: Sharpe={v12_val['sharpe']:.3f}, "
          f"Return={v12_val['return']:.2%}, MaxDD={v12_val['max_dd']:.2%}")

    validation_passed = best_val_rank <= 3
    status = "PASSED" if validation_passed else "FAILED"
    print(f"\nBest threshold ({best_threshold:.0%}) validation rank: {best_val_rank}/{len(THRESHOLDS)} [{status}]")

    # === TEST PHASE ===
    print(f"\n{'=' * 70}")
    print(f"TEST PHASE ({TEST_START} to end)")
    print("=" * 70)

    v2_test = run_v2_backtest(prices, best_threshold, TEST_START, TEST_END)
    v12_test = run_v12_backtest(prices, TEST_START, TEST_END)

    print(f"\nv2.0 (threshold={best_threshold:.0%}) test results:")
    print(f"  Sharpe Ratio:     {v2_test['sharpe']:.3f}")
    print(f"  Annual Return:    {v2_test['return']:.2%}")
    print(f"  Max Drawdown:     {v2_test['max_dd']:.2%}")
    print(f"  Daily Rebalances: {v2_test['daily_rebalances']}")

    print(f"\nv1.2 Baseline test results:")
    print(f"  Sharpe Ratio:     {v12_test['sharpe']:.3f}")
    print(f"  Annual Return:    {v12_test['return']:.2%}")
    print(f"  Max Drawdown:     {v12_test['max_dd']:.2%}")
    print(f"  Rebalances:       {v12_test['rebalances']}")

    # === SUMMARY ===
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)

    print("\nTraining Results (sorted by Sharpe):")
    print(train_df.sort_values('sharpe', ascending=False).to_string(index=False))

    print(f"\n{'-' * 70}")

    # Decision logic
    v2_better_train = best_sharpe > v12_train['sharpe']
    v2_better_val = best_val_sharpe > v12_val['sharpe']
    v2_better_test = v2_test['sharpe'] > v12_test['sharpe']

    print("\nComparison Summary:")
    print(f"  Training:   v2.0 {'>' if v2_better_train else '<='} v1.2 "
          f"({best_sharpe:.3f} vs {v12_train['sharpe']:.3f})")
    print(f"  Validation: v2.0 {'>' if v2_better_val else '<='} v1.2 "
          f"({best_val_sharpe:.3f} vs {v12_val['sharpe']:.3f})")
    print(f"  Test:       v2.0 {'>' if v2_better_test else '<='} v1.2 "
          f"({v2_test['sharpe']:.3f} vs {v12_test['sharpe']:.3f})")

    print(f"\n{'-' * 70}")

    # Final recommendation
    if validation_passed and v2_better_test:
        print(f"RECOMMENDATION: ADOPT v2.0 with drift_threshold={best_threshold:.0%}")
        print(f"  - Validation passed (rank {best_val_rank}/{len(THRESHOLDS)})")
        print(f"  - Test Sharpe improved: {v2_test['sharpe']:.3f} vs {v12_test['sharpe']:.3f}")
    elif validation_passed and not v2_better_test:
        print(f"RECOMMENDATION: KEEP v1.2 (v2.0 validation passed but test underperformed)")
        print(f"  - v2.0 Test Sharpe: {v2_test['sharpe']:.3f}")
        print(f"  - v1.2 Test Sharpe: {v12_test['sharpe']:.3f}")
    else:
        print(f"RECOMMENDATION: KEEP v1.2 (v2.0 validation failed)")
        print(f"  - Best threshold rank in validation: {best_val_rank}/{len(THRESHOLDS)} (need top-3)")

    print("=" * 70)


if __name__ == '__main__':
    main()
