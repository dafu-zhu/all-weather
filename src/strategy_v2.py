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
        """Run backtest and return results."""
        raise NotImplementedError("To be implemented in Task 2")
