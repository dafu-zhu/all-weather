"""
All Weather Strategy v2.0 - Daily Mean-Reversion

Extends v1.2 with daily drift checking and per-asset rebalancing.
"""

from typing import Optional, List, Dict
import numpy as np
import pandas as pd

from src.metrics import calculate_all_metrics
from src.optimizer import optimize_weights
from src.portfolio import Portfolio


class AllWeatherV2:
    """
    All Weather Strategy v2.0 - Daily Mean-Reversion

    Key differences from v1.2:
    - Daily drift checking (not just weekly)
    - Per-asset trim/buy (not full portfolio rebalance)
    - Single symmetric drift_threshold parameter

    Version History:
    - v1.0: Pure risk parity, always rebalance
    - v1.1: + Adaptive rebalancing (weekly, 5% drift threshold)
    - v1.2: + Ledoit-Wolf covariance shrinkage
    - v2.0: + Daily mean-reversion (per-asset drift checking)
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        initial_capital: float = 1_000_000,
        lookback: int = 252,
        commission_rate: float = 0.0003,
        drift_threshold: float = 0.05,
        use_shrinkage: bool = True,
    ) -> None:
        """
        Initialize v2.0 strategy.

        Args:
            prices: DataFrame of ETF prices
            initial_capital: Starting capital
            lookback: Days for covariance calculation (252 = 1 year)
            commission_rate: Transaction cost (0.03% = 0.0003)
            drift_threshold: Trigger threshold for per-asset rebalancing (default 5%)
            use_shrinkage: Use Ledoit-Wolf shrinkage (default True)
        """
        self.prices = prices
        self.initial_capital = initial_capital
        self.lookback = lookback
        self.commission_rate = commission_rate
        self.drift_threshold = drift_threshold
        self.use_shrinkage = use_shrinkage

        self.portfolio = Portfolio(initial_capital, commission_rate)
        self.target_weights: Optional[Dict[str, float]] = None
        self.daily_trades: List[Dict] = []

    def check_daily_drift(self, current_prices: pd.Series) -> List[Dict]:
        """
        Check each asset for drift beyond threshold.

        Returns list of trades needed: [{'asset': str, 'action': 'buy'|'sell', 'drift': float}]
        """
        if self.target_weights is None:
            return []

        trades_needed = []
        current_weights = self.portfolio.get_weights(current_prices)

        for asset, target_weight in self.target_weights.items():
            current_weight = current_weights.get(asset, 0.0)
            drift = current_weight - target_weight

            if abs(drift) > self.drift_threshold:
                action = 'sell' if drift > 0 else 'buy'
                trades_needed.append({
                    'asset': asset,
                    'action': action,
                    'drift': drift,
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                })

        return trades_needed

    def execute_daily_rebalance(
        self,
        trades_needed: List[Dict],
        current_prices: pd.Series,
        date: pd.Timestamp,
    ) -> int:
        """
        Execute per-asset rebalancing for assets that drifted beyond threshold.

        Returns number of trades executed.
        """
        if not trades_needed:
            return 0

        # For simplicity, rebalance all drifted assets back to target
        # This is equivalent to a partial rebalance
        portfolio_value = self.portfolio.get_value(current_prices)
        executed_count = 0

        for trade in trades_needed:
            asset = trade['asset']
            target_weight = trade['target_weight']
            target_value = portfolio_value * target_weight
            current_shares = self.portfolio.positions.get(asset, 0)
            current_value = current_shares * current_prices[asset]

            if trade['action'] == 'sell':
                # Sell excess
                sell_value = current_value - target_value
                sell_shares = sell_value / current_prices[asset]
                if sell_shares > 0:
                    result = self.portfolio.sell(asset, sell_shares, current_prices[asset], date)
                    if result:
                        executed_count += 1
                        self.daily_trades.append({
                            'date': date,
                            'asset': asset,
                            'action': trade['action'],
                            'drift': trade['drift'],
                        })
            else:
                # Buy deficit
                buy_value = target_value - current_value
                buy_shares = buy_value / current_prices[asset]
                total_cost = buy_value * (1 + self.commission_rate)
                if buy_shares > 0 and self.portfolio.cash >= total_cost:
                    result = self.portfolio.buy(asset, buy_shares, current_prices[asset], date)
                    if result:
                        executed_count += 1
                        self.daily_trades.append({
                            'date': date,
                            'asset': asset,
                            'action': trade['action'],
                            'drift': trade['drift'],
                        })

        return executed_count

    def run_backtest(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        verbose: bool = True,
    ) -> dict:
        """
        Run backtest with daily drift checking and weekly weight optimization.

        Args:
            start_date: Backtest start date (defaults to lookback days after first price)
            end_date: Backtest end date (defaults to last price date)
            verbose: Print progress messages

        Returns:
            dict with keys:
                - equity_curve: pd.Series of portfolio values
                - returns: pd.Series of daily returns
                - weights_history: pd.DataFrame of target weights over time
                - final_value: final portfolio value
                - total_return: total return as decimal
                - metrics: dict from calculate_all_metrics
                - daily_rebalance_count: number of daily drift rebalances
                - weekly_rebalance_count: number of weekly weight updates
                - daily_trades: list of daily trade records
        """
        # Set date range
        start = pd.Timestamp(start_date) if start_date else self.prices.index[self.lookback]
        end = pd.Timestamp(end_date) if end_date else self.prices.index[-1]

        backtest_prices = self.prices.loc[:end].copy()

        if verbose:
            print(f"Backtest: {start.date()} to {end.date()}")
            print(f"Drift threshold: {self.drift_threshold:.1%}")

        # Tracking variables
        equity_curve = []
        dates = []
        weights_history = []
        daily_rebalance_count = 0
        weekly_rebalance_count = 0
        self.daily_trades = []  # Reset daily trades
        last_rebalance_week = None  # Track last week we rebalanced (I1 - Monday holiday handling)

        # Main backtest loop
        for date in backtest_prices.loc[start:end].index:
            weekly_updated_today = False  # I3 - Race condition guard
            current_prices = backtest_prices.loc[date]
            portfolio_value = self.portfolio.get_value(current_prices)

            # Track equity curve
            equity_curve.append(portfolio_value)
            dates.append(date)

            # WEEKLY: Update target weights via risk parity optimization
            # I1 - Use week number comparison instead of exact date matching (handles Monday holidays)
            current_week = date.isocalendar()[:2]  # (year, week_number)
            is_new_week = current_week != last_rebalance_week

            if date.weekday() == 0 and is_new_week:  # Monday of a new week
                # M1 - Cache the get_loc result for efficiency
                current_idx = backtest_prices.index.get_loc(date)
                lookback_start = current_idx - self.lookback
                if lookback_start < 0:
                    # I2 - Add verbose logging when skipping due to insufficient data
                    if verbose:
                        print(f"[{date.date()}] Skipped: insufficient lookback data")
                    continue

                lookback_end = current_idx
                hist_returns = backtest_prices.iloc[lookback_start:lookback_end].pct_change().dropna()

                if len(hist_returns) < self.lookback - 1:
                    continue

                try:
                    weights = optimize_weights(hist_returns, use_shrinkage=self.use_shrinkage)
                    self.target_weights = dict(zip(backtest_prices.columns, weights))
                    weekly_rebalance_count += 1
                    last_rebalance_week = current_week  # I1 - Track the week we rebalanced
                    weekly_updated_today = True  # I3 - Skip daily drift check after weekly update

                    # Record weights history
                    weights_history.append({'date': date, **self.target_weights})

                    # Initial allocation: buy into positions on first Monday
                    if portfolio_value == self.initial_capital and self.portfolio.cash == self.initial_capital:
                        self.portfolio.rebalance(self.target_weights, current_prices)
                        if verbose:
                            print(f"[{date.date()}] Initial allocation (weekly #{weekly_rebalance_count})")
                    elif verbose:
                        print(f"[{date.date()}] Weights updated (weekly #{weekly_rebalance_count})")

                except Exception as e:
                    if verbose:
                        print(f"Error at {date}: {e}")
                    continue

            # DAILY: Check drift and execute rebalancing if needed
            # I3 - Skip daily drift check on days when weekly weights are updated
            if self.target_weights is not None and not weekly_updated_today:
                trades_needed = self.check_daily_drift(current_prices)
                if trades_needed:
                    executed = self.execute_daily_rebalance(trades_needed, current_prices, date)
                    if executed > 0:
                        daily_rebalance_count += 1
                        if verbose:
                            assets = [t['asset'] for t in trades_needed]
                            print(f"[{date.date()}] Daily rebalance: {executed} trades ({', '.join(assets)})")

        # Build results
        equity_series = pd.Series(equity_curve, index=dates)
        returns = equity_series.pct_change().dropna()

        if weights_history:
            weights_df = pd.DataFrame(weights_history).set_index('date')
        else:
            weights_df = pd.DataFrame()

        results = {
            'equity_curve': equity_series,
            'returns': returns,
            'weights_history': weights_df,
            'final_value': equity_curve[-1] if equity_curve else self.initial_capital,
            'total_return': (equity_curve[-1] / self.initial_capital - 1) if equity_curve else 0.0,
            'metrics': calculate_all_metrics(returns, equity_series),
            'daily_rebalance_count': daily_rebalance_count,
            'weekly_rebalance_count': weekly_rebalance_count,
            'daily_trades': self.daily_trades,
        }

        if verbose:
            print(f"\n{'='*60}")
            print("Backtest Complete!")
            print(f"{'='*60}")
            print(f"Weekly weight updates: {weekly_rebalance_count}")
            print(f"Daily drift rebalances: {daily_rebalance_count}")
            print(f"Total daily trades: {len(self.daily_trades)}")

        return results
