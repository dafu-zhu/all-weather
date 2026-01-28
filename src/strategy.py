"""
All Weather Strategy - Core Implementation

Contains both v1.0 (pure risk parity) and v2.0 (constrained) strategy classes.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.portfolio import Portfolio
from src.optimizer import optimize_weights, optimize_weights_constrained, optimize_weights_v3
from src.metrics import calculate_all_metrics
from src.volatility_targeting import apply_volatility_targeting
from src.depression_gauge import detect_crisis, get_safe_portfolio_weights


class AllWeatherV1:
    """
    All Weather Strategy v1.0 - Pure Risk Parity

    Weekly rebalancing with equal risk contribution from each asset.
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        initial_capital: float = 1_000_000,
        rebalance_freq: str = 'W-MON',
        lookback: int = 100,
        commission_rate: float = 0.0003
    ):
        """
        Initialize v1.0 strategy.

        Args:
            prices: DataFrame of ETF prices
            initial_capital: Starting capital
            rebalance_freq: 'W-MON' for weekly Monday rebalancing
            lookback: Days for covariance calculation
            commission_rate: Transaction cost (0.03% = 0.0003)
        """
        self.prices = prices
        self.initial_capital = initial_capital
        self.rebalance_freq = rebalance_freq
        self.lookback = lookback
        self.commission_rate = commission_rate
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
                    weights = optimize_weights(hist_returns)
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


class AllWeatherV2:
    """
    All Weather Strategy v2.0 - Constrained Risk Parity

    Monthly rebalancing with minimum stock allocation constraints
    for higher returns while maintaining risk parity principles.
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        initial_capital: float = 1_000_000,
        rebalance_freq: str = 'MS',
        lookback: int = 100,
        commission_rate: float = 0.0003,
        min_stock_alloc: float = 0.60,
        max_bond_alloc: float = 0.35
    ):
        """
        Initialize v2.0 strategy.

        Args:
            prices: DataFrame of ETF prices
            initial_capital: Starting capital
            rebalance_freq: 'MS' for monthly, 'W-MON' for weekly
            lookback: Days for covariance calculation
            commission_rate: Transaction cost (0.03% = 0.0003)
            min_stock_alloc: Minimum total stock allocation
            max_bond_alloc: Maximum total bond allocation
        """
        self.prices = prices
        self.initial_capital = initial_capital
        self.rebalance_freq = rebalance_freq
        self.lookback = lookback
        self.commission_rate = commission_rate
        self.min_stock_alloc = min_stock_alloc
        self.max_bond_alloc = max_bond_alloc
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
                    weights = optimize_weights_constrained(
                        hist_returns,
                        min_stock_alloc=self.min_stock_alloc,
                        max_bond_alloc=self.max_bond_alloc
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

    def plot_results(self, results, benchmark_prices=None):
        """Plot equity curve and drawdown."""

        equity = results['equity_curve']
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))

        # Equity curve
        ax1 = axes[0]
        ax1.plot(equity.index, equity, label='All Weather v2.0',
                linewidth=2, color='#2E86AB')

        if benchmark_prices is not None:
            bench = (benchmark_prices / benchmark_prices.iloc[0]) * self.initial_capital
            bench = bench.loc[equity.index]
            ax1.plot(bench.index, bench, label='Benchmark (沪深300)',
                    linewidth=2, alpha=0.7, color='#A23B72')

        ax1.set_title('Portfolio Value Over Time', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Value (¥)', fontsize=12)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'¥{x/1e6:.1f}M'
        ))

        # Drawdown
        ax2 = axes[1]
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max
        ax2.fill_between(drawdown.index, drawdown, 0, alpha=0.3, color='red')
        ax2.plot(drawdown.index, drawdown, color='darkred', linewidth=1.5)
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Drawdown', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x:.0%}'
        ))

        plt.tight_layout()
        plt.show()


class AllWeatherV3:
    """
    All Weather Strategy v3.0 - Advanced Risk Parity

    Implements Bridgewater-inspired improvements:
    1. Economic Environment Framework - Balance risk across 4 quadrants
    2. Volatility Targeting - Dynamic position sizing for 10% target vol
    3. Return-Aware Optimization - Optimize Sharpe ratio, not just risk parity
    4. Depression Gauge - Crisis detection with Safe Portfolio mode
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        initial_capital: float = 1_000_000,
        rebalance_freq: str = 'MS',
        lookback: int = 100,
        commission_rate: float = 0.0003,
        min_stock_alloc: float = 0.60,
        max_bond_alloc: float = 0.35,
        target_volatility: float = 0.10,
        balance_environments: bool = True,
        use_return_expectations: bool = True,
        use_depression_gauge: bool = True,
        lambda_sharpe: float = 0.5
    ):
        """
        Initialize v3.0 strategy.

        Args:
            prices: DataFrame of ETF prices
            initial_capital: Starting capital
            rebalance_freq: 'MS' for monthly (default)
            lookback: Days for covariance/return calculation (default 100)
            commission_rate: Transaction cost (default 0.03%)
            min_stock_alloc: Minimum total stock allocation (default 60%)
            max_bond_alloc: Maximum total bond allocation (default 35%)
            target_volatility: Target annual portfolio volatility (default 10%)
            balance_environments: Whether to balance risk across environments (default True)
            use_return_expectations: Whether to optimize for Sharpe ratio (default True)
            use_depression_gauge: Whether to use crisis detection (default True)
            lambda_sharpe: Weight on Sharpe vs risk parity (0-1, default 0.5)
        """
        self.prices = prices
        self.initial_capital = initial_capital
        self.rebalance_freq = rebalance_freq
        self.lookback = lookback
        self.commission_rate = commission_rate
        self.min_stock_alloc = min_stock_alloc
        self.max_bond_alloc = max_bond_alloc
        self.target_volatility = target_volatility
        self.balance_environments = balance_environments
        self.use_return_expectations = use_return_expectations
        self.use_depression_gauge = use_depression_gauge
        self.lambda_sharpe = lambda_sharpe
        self.portfolio = Portfolio(initial_capital, commission_rate)

        # Track crisis state
        self.in_crisis = False
        self.crisis_history = []

    def run_backtest(self, start_date=None, end_date=None, verbose=True):
        """Run backtest with v3.0 improvements."""

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
            print(f"Target Volatility: {self.target_volatility:.1%}")
            print(f"Environment Balancing: {self.balance_environments}")
            print(f"Return Optimization: {self.use_return_expectations}")
            print(f"Depression Gauge: {self.use_depression_gauge}")

        equity_curve = []
        dates = []
        weights_history = []
        crisis_dates = []

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
                    # Step 1: Check for crisis
                    is_crisis = False
                    if self.use_depression_gauge:
                        is_crisis, signals = detect_crisis(backtest_prices, date)

                        if is_crisis and not self.in_crisis:
                            if verbose:
                                print(f"\n⚠️  CRISIS DETECTED at {date.date()}")
                                print(f"   Signals: {sum(signals.values())}/3 active")
                                print(f"   Switching to Safe Portfolio (70% bonds, 30% gold)")
                            crisis_dates.append(date)
                            self.in_crisis = True

                        elif not is_crisis and self.in_crisis:
                            if verbose:
                                print(f"\n✅ CRISIS CLEARED at {date.date()}")
                                print(f"   Returning to normal allocation")
                            self.in_crisis = False

                    # Step 2: Calculate weights
                    if is_crisis:
                        # Use Safe Portfolio during crisis (overrides constraints)
                        weights = get_safe_portfolio_weights(
                            backtest_prices.columns.tolist()
                        )
                    else:
                        # Normal optimization
                        if self.use_return_expectations:
                            weights = optimize_weights_v3(
                                hist_returns,
                                min_stock_alloc=self.min_stock_alloc,
                                max_bond_alloc=self.max_bond_alloc,
                                balance_environments=self.balance_environments,
                                expected_returns=None,  # Will use EWMA
                                lambda_sharpe=self.lambda_sharpe
                            )
                        else:
                            weights = optimize_weights_constrained(
                                hist_returns,
                                min_stock_alloc=self.min_stock_alloc,
                                max_bond_alloc=self.max_bond_alloc
                            )

                    # Step 3: Apply volatility targeting (if not in crisis)
                    if not is_crisis and len(equity_curve) > 60:
                        # Calculate portfolio returns for vol targeting
                        equity_series = pd.Series(equity_curve, index=dates)
                        portfolio_returns = equity_series.pct_change().dropna()

                        weights = apply_volatility_targeting(
                            weights,
                            portfolio_returns,
                            target_volatility=self.target_volatility,
                            lookback_window=60
                        )

                    # Step 4: Rebalance
                    target_weights = dict(zip(backtest_prices.columns, weights))
                    self.portfolio.rebalance(target_weights, current_prices)

                    weights_history.append({'date': date, 'in_crisis': is_crisis, **target_weights})

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
            'crisis_dates': crisis_dates
        }

        return results
