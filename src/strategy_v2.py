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

    def run_backtest(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        verbose: bool = True,
    ) -> dict:
        """Run backtest and return results."""
        raise NotImplementedError("To be implemented in Task 2")
