"""
Test Drift Trigger Logic: Same-day vs Lag-1 Execution

Compares v1.2 baseline (trade at signal date close) against a lag-1 variant
(signal today, trade at next trading day's close). Both use the same 3% drift
trigger and 252-day Ledoit-Wolf covariance.

Also audits the cash-handling behavior of the Portfolio.rebalance function.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from src.data_loader import load_prices
from src.metrics import calculate_all_metrics
from src.optimizer import optimize_weights
from src.portfolio import Portfolio


def run_backtest(
    prices: pd.DataFrame,
    *,
    lag: int,
    initial_capital: float = 1_000_000,
    rebalance_freq: str = 'W-MON',
    lookback: int = 252,
    commission_rate: float = 0.0003,
    rebalance_threshold: float = 0.03,
    use_shrinkage: bool = True,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Run a backtest with configurable trade-execution lag.

    lag=0: signal computed on date T from data < T, trade at T's close (baseline).
    lag=1: signal computed on date T, trade at T+1's close.
    """
    start = pd.Timestamp(start_date) if start_date else prices.index[lookback]
    end = pd.Timestamp(end_date) if end_date else prices.index[-1]

    backtest_prices = prices.loc[:end].copy()
    rebalance_dates = backtest_prices.loc[start:end].resample(rebalance_freq).first().index

    portfolio = Portfolio(initial_capital, commission_rate)
    last_target_weights: dict | None = None

    equity_curve = []
    dates = []
    rebalances_executed = 0
    rebalances_skipped = 0
    pending_target: dict | None = None  # queued for lag execution

    idx = backtest_prices.index

    for date in backtest_prices.loc[start:end].index:
        current_prices = backtest_prices.loc[date]

        # Execute any queued trade from a previous signal (lag > 0)
        if pending_target is not None:
            portfolio.rebalance(pending_target, current_prices)
            last_target_weights = pending_target.copy()
            rebalances_executed += 1
            pending_target = None

        equity_curve.append(portfolio.get_value(current_prices))
        dates.append(date)

        if date not in rebalance_dates:
            continue

        loc = idx.get_loc(date)
        lookback_start = loc - lookback
        if lookback_start < 0:
            continue

        hist_returns = backtest_prices.iloc[lookback_start:loc].pct_change().dropna()
        if len(hist_returns) < lookback - 1:
            continue

        try:
            weights = optimize_weights(hist_returns, use_shrinkage=use_shrinkage)
        except Exception as exc:
            print(f"Error at {date.date()}: {exc}")
            continue

        target_weights = dict(zip(backtest_prices.columns, weights))

        # Drift check uses today's prices (same as baseline)
        if last_target_weights is None or rebalance_threshold == 0:
            needs_rebalance = True
            max_drift = 0.0
        else:
            current_weights = portfolio.get_weights(current_prices)
            max_drift = max(
                abs(current_weights.get(a, 0.0) - last_target_weights.get(a, 0.0))
                for a in target_weights
            )
            needs_rebalance = max_drift > rebalance_threshold

        if not needs_rebalance:
            rebalances_skipped += 1
            continue

        if lag == 0:
            portfolio.rebalance(target_weights, current_prices)
            last_target_weights = target_weights.copy()
            rebalances_executed += 1
        else:
            # Queue for next trading day (lag=1). If current bar is last, drop it.
            if loc + lag < len(idx):
                pending_target = target_weights
            # else: no bar left to execute, skip

    equity_series = pd.Series(equity_curve, index=dates)
    returns = equity_series.pct_change().dropna()

    metrics = calculate_all_metrics(returns, equity_series)

    return {
        'equity_curve': equity_series,
        'metrics': metrics,
        'final_value': equity_series.iloc[-1],
        'total_return': equity_series.iloc[-1] / initial_capital - 1,
        'rebalances_executed': rebalances_executed,
        'rebalances_skipped': rebalances_skipped,
        'total_commissions': portfolio.get_total_commissions(),
        'turnover': portfolio.get_turnover(),
        'final_cash': portfolio.cash,
        'trade_count': portfolio.get_trade_count(),
    }


def print_result(label: str, result: dict) -> None:
    m = result['metrics']
    print(f"\n{label}")
    print("-" * 60)
    print(f"  Final value        : ¥{result['final_value']:>14,.0f}")
    print(f"  Total return       : {result['total_return']*100:>14.2f}%")
    print(f"  Annual return      : {m['annual_return']*100:>14.2f}%")
    print(f"  Annual volatility  : {m['annual_volatility']*100:>14.2f}%")
    print(f"  Sharpe ratio       : {m['sharpe_ratio']:>14.2f}")
    print(f"  Sortino ratio      : {m['sortino_ratio']:>14.2f}")
    print(f"  Max drawdown       : {m['max_drawdown']*100:>14.2f}%")
    print(f"  Calmar ratio       : {m['calmar_ratio']:>14.2f}")
    print(f"  Rebalances executed: {result['rebalances_executed']:>14}")
    print(f"  Rebalances skipped : {result['rebalances_skipped']:>14}")
    print(f"  Trades             : {result['trade_count']:>14}")
    print(f"  Commissions        : ¥{result['total_commissions']:>14,.0f}")
    print(f"  Final cash         : ¥{result['final_cash']:>14,.0f}")


def diff_row(label: str, a_val: float, b_val: float, pct: bool = False, money: bool = False) -> None:
    delta = b_val - a_val
    if money:
        print(f"  {label:<22}: {a_val:>14,.0f}  {b_val:>14,.0f}  {delta:>+14,.0f}")
    elif pct:
        print(f"  {label:<22}: {a_val*100:>13.2f}%  {b_val*100:>13.2f}%  {delta*100:>+13.2f}%")
    else:
        print(f"  {label:<22}: {a_val:>14.2f}  {b_val:>14.2f}  {delta:>+14.2f}")


def main():
    print("=" * 72)
    print("Drift Trigger Logic Test: same-day vs lag-1 execution")
    print("=" * 72)

    prices = load_prices('data/etf_prices_7etf.csv')
    # Match the baseline backtest window used in CLAUDE.md / comparison scripts
    start_date = '2018-01-01'
    end_date = None
    print(f"\nData: {prices.index[0].date()} to {prices.index[-1].date()}")
    print(f"ETFs: {list(prices.columns)}")
    print(f"Backtest window: {start_date} to end")

    baseline = run_backtest(prices, lag=0, start_date=start_date, end_date=end_date)
    lag1 = run_backtest(prices, lag=1, start_date=start_date, end_date=end_date)

    print_result("Baseline v1.2 (trade at signal-day close)", baseline)
    print_result("Lag-1 (signal at T, trade at T+1 close)", lag1)

    print("\n" + "=" * 72)
    print("Side-by-side comparison")
    print("=" * 72)
    print(f"  {'Metric':<22}  {'Baseline':>14}  {'Lag-1':>14}  {'Delta':>14}")
    diff_row("Final value (¥)", baseline['final_value'], lag1['final_value'], money=True)
    diff_row("Total return", baseline['total_return'], lag1['total_return'], pct=True)
    diff_row("Annual return", baseline['metrics']['annual_return'], lag1['metrics']['annual_return'], pct=True)
    diff_row("Sharpe ratio", baseline['metrics']['sharpe_ratio'], lag1['metrics']['sharpe_ratio'])
    diff_row("Max drawdown", baseline['metrics']['max_drawdown'], lag1['metrics']['max_drawdown'], pct=True)
    diff_row("Commissions (¥)", baseline['total_commissions'], lag1['total_commissions'], money=True)

    print()


if __name__ == '__main__':
    main()
