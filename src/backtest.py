"""
Backtesting Engine Module

Simulates historical strategy performance with weekly rebalancing.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from .portfolio import Portfolio
from .optimizer import optimize_weights


class Backtester:
    """
    Backtesting engine for All Weather Strategy v1.2.

    Simulates portfolio performance with:
    - Covariance shrinkage for robust estimation (v1.2)
    - Adaptive rebalancing (only when weights drift > threshold)
    - Risk parity weight optimization
    - Transaction cost application
    - Full performance tracking
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        initial_capital: float = 1_000_000,
        rebalance_freq: str = 'W-MON',
        lookback: int = 100,
        commission_rate: float = 0.0003,
        rebalance_threshold: float = 0.05,
        use_shrinkage: bool = True
    ):
        """
        Initialize backtester.

        Args:
            prices: DataFrame of ETF prices (dates × ETFs)
            initial_capital: Starting capital
            rebalance_freq: Rebalancing frequency ('W-MON' for weekly Monday)
            lookback: Number of days for covariance calculation
            commission_rate: Transaction cost as fraction
            rebalance_threshold: Max weight drift before rebalancing (default 0.05 = 5%)
                               Set to 0 to always rebalance (v1.0 behavior)
            use_shrinkage: Use Ledoit-Wolf shrinkage (v1.2, default True)
        """
        self.prices = prices
        self.initial_capital = initial_capital
        self.rebalance_freq = rebalance_freq
        self.lookback = lookback
        self.commission_rate = commission_rate
        self.rebalance_threshold = rebalance_threshold
        self.use_shrinkage = use_shrinkage

        self.portfolio = Portfolio(initial_capital, commission_rate)
        self.results = {}
        self.last_target_weights = None

    def should_rebalance(self, current_prices: pd.Series, target_weights: Dict[str, float]) -> tuple:
        """
        Check if portfolio needs rebalancing based on weight drift.

        Args:
            current_prices: Current market prices
            target_weights: Target portfolio weights

        Returns:
            Tuple of (should_rebalance, max_drift)
        """
        if self.last_target_weights is None:
            return True, 0.0

        if self.rebalance_threshold == 0:
            return True, 0.0

        current_weights = self.portfolio.get_weights(current_prices)

        max_drift = 0.0
        for asset in target_weights.keys():
            current_weight = current_weights.get(asset, 0.0)
            target_weight = self.last_target_weights.get(asset, 0.0)
            drift = abs(current_weight - target_weight)
            max_drift = max(max_drift, drift)

        return max_drift > self.rebalance_threshold, max_drift

    def run(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """
        Run backtest simulation.

        Args:
            start_date: Start date (default: first date with enough lookback)
            end_date: End date (default: last available date)

        Returns:
            Dictionary with backtest results:
            - equity_curve: Portfolio values over time
            - returns: Daily returns
            - weights_history: Rebalancing weights over time
            - trades: All trades executed
            - statistics: Performance statistics
        """
        # Determine date range
        if start_date is None:
            # Need at least lookback days of history
            start_idx = self.lookback
            start_date = self.prices.index[start_idx]
        else:
            start_date = pd.Timestamp(start_date)

        if end_date is None:
            end_date = self.prices.index[-1]
        else:
            end_date = pd.Timestamp(end_date)

        # Filter prices to backtest period
        backtest_prices = self.prices.loc[:end_date].copy()

        # Get rebalance dates (every Monday within backtest period)
        all_mondays = backtest_prices.loc[start_date:end_date].resample(self.rebalance_freq).first()
        rebalance_dates = all_mondays.index

        print(f"Backtest period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Rebalance dates: {len(rebalance_dates)}")

        # Initialize tracking
        equity_curve = []
        dates = []
        weights_history = []
        rebalances_skipped = 0

        # Run simulation
        for date in backtest_prices.loc[start_date:end_date].index:
            current_prices = backtest_prices.loc[date]

            # Calculate portfolio value
            portfolio_value = self.portfolio.get_value(current_prices)
            equity_curve.append(portfolio_value)
            dates.append(date)

            # Rebalance if today is a rebalance date
            if date in rebalance_dates:
                # Get historical returns for covariance calculation
                hist_end = date
                hist_start_idx = backtest_prices.index.get_loc(date) - self.lookback

                if hist_start_idx < 0:
                    print(f"Warning: Not enough history at {date}, skipping rebalance")
                    continue

                hist_returns = backtest_prices.iloc[hist_start_idx:backtest_prices.index.get_loc(date)].pct_change().dropna()

                if len(hist_returns) < self.lookback - 1:
                    print(f"Warning: Insufficient returns at {date}, skipping rebalance")
                    continue

                # Calculate risk parity weights (v1.2: with optional shrinkage)
                try:
                    weights = optimize_weights(hist_returns, use_shrinkage=self.use_shrinkage)
                    target_weights = dict(zip(backtest_prices.columns, weights))

                    # Check if we need to rebalance (v1.1 adaptive feature)
                    needs_rebalance, drift = self.should_rebalance(current_prices, target_weights)

                    if needs_rebalance:
                        # Execute rebalancing
                        trades = self.portfolio.rebalance(target_weights, current_prices)
                        self.last_target_weights = target_weights.copy()

                        # Record weights
                        weights_history.append({
                            'date': date,
                            **target_weights
                        })

                        print(f"[{date.strftime('%Y-%m-%d')}] Rebalanced: {len(trades)} trades, Drift: {drift:.2%}, Value: ¥{portfolio_value:,.0f}")
                    else:
                        rebalances_skipped += 1
                        print(f"[{date.strftime('%Y-%m-%d')}] Skipped (drift {drift:.2%} < {self.rebalance_threshold:.2%})")

                except Exception as e:
                    print(f"Error at {date}: {e}")
                    continue

        # Compile results
        equity_series = pd.Series(equity_curve, index=dates)
        returns = equity_series.pct_change().dropna()

        weights_df = pd.DataFrame(weights_history).set_index('date') if weights_history else pd.DataFrame()

        self.results = {
            'equity_curve': equity_series,
            'returns': returns,
            'weights_history': weights_df,
            'dates': dates,
            'final_value': equity_curve[-1] if equity_curve else 0,
            'total_return': (equity_curve[-1] / self.initial_capital - 1) if equity_curve else 0,
            'total_commissions': self.portfolio.get_total_commissions(),
            'trade_count': self.portfolio.get_trade_count(),
            'turnover': self.portfolio.get_turnover(),
            'rebalance_count': len(weights_history),
            'rebalances_executed': len(weights_history),
            'rebalances_skipped': rebalances_skipped,
            'rebalance_efficiency': 1 - (rebalances_skipped / len(rebalance_dates)) if len(rebalance_dates) > 0 else 0
        }

        print(f"\n{'='*70}")
        print(f"Backtest Summary:")
        print(f"  Rebalances executed: {len(weights_history)}")
        print(f"  Rebalances skipped: {rebalances_skipped}")
        print(f"  Efficiency: {self.results['rebalance_efficiency']:.1%}")
        print(f"  Total commissions: ¥{self.results['total_commissions']:,.0f}")
        print(f"{'='*70}")

        return self.results

    def get_results(self) -> Dict:
        """Get backtest results."""
        return self.results

    def __repr__(self) -> str:
        if not self.results:
            return "Backtester(not run)"

        return (
            f"Backtester(\n"
            f"  Period: {self.results['dates'][0]} to {self.results['dates'][-1]}\n"
            f"  Final Value: ¥{self.results['final_value']:,.0f}\n"
            f"  Total Return: {self.results['total_return']:.2%}\n"
            f"  Trades: {self.results['trade_count']}\n"
            f")"
        )
