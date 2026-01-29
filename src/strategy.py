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
    All Weather Strategy v1.0 - Pure Risk Parity

    Weekly rebalancing with equal risk contribution from each asset.
    Uses 252-day (1 year) lookback for stable covariance estimation.
    Optional volatility targeting available but not recommended for this portfolio.
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        initial_capital: float = 1_000_000,
        rebalance_freq: str = 'W-MON',
        lookback: int = 252,
        commission_rate: float = 0.0003,
        target_volatility: float = None
    ):
        """
        Initialize v1.0 strategy with optimized parameters.

        Args:
            prices: DataFrame of ETF prices
            initial_capital: Starting capital
            rebalance_freq: 'W-MON' for weekly Monday (optimal), 'MS' for monthly
            lookback: Days for covariance calculation (252 = 1 year, optimal)
            commission_rate: Transaction cost (0.03% = 0.0003)
            target_volatility: Target annualized volatility (e.g., 0.06 for 6%)
                             None = no targeting (recommended for this portfolio)
        """
        self.prices = prices
        self.initial_capital = initial_capital
        self.rebalance_freq = rebalance_freq
        self.lookback = lookback
        self.commission_rate = commission_rate
        self.target_volatility = target_volatility
        self.portfolio = Portfolio(initial_capital, commission_rate)

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
                    # Get risk parity weights
                    weights = optimize_weights(hist_returns)

                    # Apply volatility targeting if specified
                    if self.target_volatility is not None:
                        cov_matrix = hist_returns.cov()
                        weights = apply_volatility_target(
                            weights,
                            cov_matrix.values,
                            target_vol=self.target_volatility
                        )

                    target_weights = dict(zip(backtest_prices.columns, weights))

                    self.portfolio.rebalance(target_weights, current_prices)

                    weights_history.append({'date': date, **target_weights})

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
            'metrics': calculate_all_metrics(returns, equity_series)
        }

        return results
