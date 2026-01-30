"""
All Weather Strategy - Core Implementation

Pure risk parity implementation following Ray Dalio's All Weather principles.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.portfolio import Portfolio
from src.optimizer import optimize_weights, apply_volatility_target
from src.metrics import calculate_all_metrics


class AllWeatherV1:
    """
    All Weather Strategy v1.2 - Pure Risk Parity with Adaptive Rebalancing + Shrinkage

    Weekly rebalancing with equal risk contribution from each asset.
    Uses 252-day (1 year) lookback for stable covariance estimation.
    Optional volatility targeting available but not recommended for this portfolio.

    Version History:
    - v1.0: Pure risk parity, always rebalance
    - v1.1: + Adaptive rebalancing (5% drift threshold)
    - v1.2: + Ledoit-Wolf covariance shrinkage for robust estimation

    v1.2 Features:
    - Covariance shrinkage: More stable weight estimates (10-15% less noise)
    - Adaptive rebalancing: Only rebalance when weights drift > threshold
    - Set use_shrinkage=False, rebalance_threshold=0 for v1.0 behavior
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        initial_capital: float = 1_000_000,
        rebalance_freq: str = 'W-MON',
        lookback: int = 252,
        commission_rate: float = 0.0003,
        target_volatility: float = None,
        rebalance_threshold: float = 0.05,
        use_shrinkage: bool = True
    ):
        """
        Initialize v1.2 strategy with optimized parameters.

        Args:
            prices: DataFrame of ETF prices
            initial_capital: Starting capital
            rebalance_freq: 'W-MON' for weekly Monday (optimal), 'MS' for monthly
            lookback: Days for covariance calculation (252 = 1 year, optimal)
            commission_rate: Transaction cost (0.03% = 0.0003)
            target_volatility: Target annualized volatility (e.g., 0.06 for 6%)
                             None = no targeting (recommended for this portfolio)
            rebalance_threshold: Max weight drift before rebalancing (default 0.05 = 5%)
                               Set to 0 for v1.0 behavior (always rebalance)
            use_shrinkage: Use Ledoit-Wolf shrinkage for covariance (v1.2, default True)
                          Set to False for v1.0/v1.1 behavior
        """
        self.prices = prices
        self.initial_capital = initial_capital
        self.rebalance_freq = rebalance_freq
        self.lookback = lookback
        self.commission_rate = commission_rate
        self.target_volatility = target_volatility
        self.rebalance_threshold = rebalance_threshold
        self.use_shrinkage = use_shrinkage
        self.portfolio = Portfolio(initial_capital, commission_rate)
        self.last_target_weights = None  # Track last target for drift calculation

    def should_rebalance(self, current_prices: pd.Series, target_weights: dict) -> tuple[bool, float]:
        """
        Check if portfolio needs rebalancing based on weight drift.

        Args:
            current_prices: Current market prices
            target_weights: Target portfolio weights

        Returns:
            Tuple of (should_rebalance, max_drift)
            - should_rebalance: True if max drift > threshold
            - max_drift: Maximum weight drift across all assets
        """
        # Always rebalance if no previous target (first rebalance)
        if self.last_target_weights is None:
            return True, 0.0

        # Always rebalance if threshold is 0 (v1.0 behavior)
        if self.rebalance_threshold == 0:
            return True, 0.0

        # Calculate current weights
        current_weights = self.portfolio.get_weights(current_prices)

        # Calculate maximum drift from target
        max_drift = 0.0
        for asset in target_weights.keys():
            current_weight = current_weights.get(asset, 0.0)
            target_weight = self.last_target_weights.get(asset, 0.0)
            drift = abs(current_weight - target_weight)
            max_drift = max(max_drift, drift)

        return max_drift > self.rebalance_threshold, max_drift

    def run_backtest(self, start_date=None, end_date=None, verbose=True):
        """Run backtest and return results."""

        if start_date is None:
            start_date = self.prices.index[self.lookback]
        else:
            start_date = pd.Timestamp(start_date)

        if end_date is None:
            end_date = self.prices.index[-1]
        else:
            end_date = pd.Timestamp(end_date)

        backtest_prices = self.prices.loc[:end_date].copy()
        rebalance_dates = backtest_prices.loc[start_date:end_date].resample(
            self.rebalance_freq
        ).first().index

        if verbose:
            print(f"Backtest: {start_date.date()} to {end_date.date()}")
            print(f"Rebalances: {len(rebalance_dates)}")

        equity_curve = []
        dates = []
        weights_history = []
        rebalances_skipped = 0

        for date in backtest_prices.loc[start_date:end_date].index:
            current_prices = backtest_prices.loc[date]
            portfolio_value = self.portfolio.get_value(current_prices)
            equity_curve.append(portfolio_value)
            dates.append(date)

            if date in rebalance_dates:
                hist_start_idx = backtest_prices.index.get_loc(date) - self.lookback
                if hist_start_idx < 0:
                    continue

                hist_returns = backtest_prices.iloc[
                    hist_start_idx:backtest_prices.index.get_loc(date)
                ].pct_change().dropna()

                if len(hist_returns) < self.lookback - 1:
                    continue

                try:
                    # Get risk parity weights (v1.2: with optional shrinkage)
                    weights = optimize_weights(hist_returns, use_shrinkage=self.use_shrinkage)

                    # Apply volatility targeting if specified
                    if self.target_volatility is not None:
                        cov_matrix = hist_returns.cov()
                        weights = apply_volatility_target(
                            weights,
                            cov_matrix.values,
                            target_vol=self.target_volatility
                        )

                    target_weights = dict(zip(backtest_prices.columns, weights))

                    # Check if we need to rebalance (v1.1 adaptive feature)
                    needs_rebalance, drift = self.should_rebalance(current_prices, target_weights)

                    if needs_rebalance:
                        self.portfolio.rebalance(target_weights, current_prices)
                        self.last_target_weights = target_weights.copy()
                        weights_history.append({'date': date, **target_weights})

                        if verbose and drift > 0:
                            print(f"[{date.date()}] Rebalanced (drift={drift:.2%})")
                    else:
                        rebalances_skipped += 1
                        if verbose:
                            print(f"[{date.date()}] Skipped rebalance (drift={drift:.2%} < {self.rebalance_threshold:.2%})")

                except Exception as e:
                    if verbose:
                        print(f"Error at {date}: {e}")
                    continue

        equity_series = pd.Series(equity_curve, index=dates)
        returns = equity_series.pct_change().dropna()
        weights_df = pd.DataFrame(weights_history).set_index('date') if weights_history else pd.DataFrame()

        results = {
            'equity_curve': equity_series,
            'returns': returns,
            'weights_history': weights_df,
            'final_value': equity_curve[-1],
            'total_return': (equity_curve[-1] / self.initial_capital - 1),
            'metrics': calculate_all_metrics(returns, equity_series),
            'rebalances_executed': len(weights_history),
            'rebalances_skipped': rebalances_skipped,
            'rebalance_efficiency': 1 - (rebalances_skipped / len(rebalance_dates)) if len(rebalance_dates) > 0 else 0
        }

        if verbose:
            print(f"\n{'='*60}")
            print(f"Backtest Complete!")
            print(f"{'='*60}")
            print(f"Rebalances executed: {results['rebalances_executed']}")
            print(f"Rebalances skipped: {rebalances_skipped}")
            print(f"Efficiency: {results['rebalance_efficiency']:.1%}")

        return results
