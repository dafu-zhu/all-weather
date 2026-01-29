"""
All Weather Strategy v1.1 - US Markets

Pure risk parity implementation for US ETFs using yfinance data.
Reuses core modules: optimizer, portfolio, metrics.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
from src.portfolio import Portfolio
from src.optimizer import optimize_weights, apply_volatility_target
from src.metrics import calculate_all_metrics


class AllWeatherUS:
    """
    All Weather Strategy v1.1 - US Markets

    Pure risk parity portfolio for US ETFs with weekly rebalancing.
    Uses 252-day (1 year) lookback for stable covariance estimation.
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        initial_capital: float = 100_000,
        rebalance_freq: str = 'W-MON',
        lookback: int = 252,
        commission_rate: float = 0.001,
        target_volatility: Optional[float] = None
    ):
        """
        Initialize US All Weather strategy.

        Args:
            prices: DataFrame of US ETF prices
            initial_capital: Starting capital in USD
            rebalance_freq: 'W-MON' for weekly Monday (optimal for risk parity)
            lookback: Days for covariance calculation (252 = 1 year, optimal)
            commission_rate: Transaction cost (0.1% = 0.001, typical for US stocks)
            target_volatility: Target annualized volatility (e.g., 0.06 for 6%)
                             None = no targeting (recommended)
        """
        self.prices = prices
        self.initial_capital = initial_capital
        self.rebalance_freq = rebalance_freq
        self.lookback = lookback
        self.commission_rate = commission_rate
        self.target_volatility = target_volatility
        self.portfolio = Portfolio(initial_capital, commission_rate)

        # Store ETF universe
        self.etfs = list(prices.columns)

    def run_backtest(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Run backtest simulation.

        Args:
            start_date: Start date (default: first date with enough lookback)
            end_date: End date (default: last date in data)

        Returns:
            Dictionary with:
            - equity_curve: Portfolio value over time
            - returns: Daily returns
            - weights_history: Weight allocations over time
            - final_value: Final portfolio value
            - total_return: Total return
            - metrics: Performance metrics
            - rebalance_count: Number of rebalances
            - trade_count: Number of trades
            - total_commissions: Total commissions paid
            - turnover: Portfolio turnover ratio
        """
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
            'rebalance_count': len(weights_history),
            'trade_count': self.portfolio.get_trade_count(),
            'total_commissions': self.portfolio.get_total_commissions(),
            'turnover': self.portfolio.get_turnover()
        }

        return results

    def get_current_allocation(self) -> pd.DataFrame:
        """
        Get current recommended allocation based on latest data.

        Returns:
            DataFrame with tickers, weights, and descriptions
        """
        recent_returns = self.prices.tail(self.lookback).pct_change().dropna()
        weights = optimize_weights(recent_returns)

        if self.target_volatility is not None:
            cov_matrix = recent_returns.cov()
            weights = apply_volatility_target(
                weights,
                cov_matrix.values,
                target_vol=self.target_volatility
            )

        allocation = pd.DataFrame({
            'Ticker': self.etfs,
            'Weight': weights,
            'Allocation': weights * 100
        }).sort_values('Weight', ascending=False)

        return allocation

    def __repr__(self) -> str:
        return (
            f"AllWeatherUS(etfs={len(self.etfs)}, "
            f"capital=${self.initial_capital:,.0f}, "
            f"lookback={self.lookback}d)"
        )
