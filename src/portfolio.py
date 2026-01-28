"""
Portfolio Management Module

Handles portfolio state, position tracking, and rebalancing with transaction costs.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Trade:
    """Record of a single trade."""
    date: datetime
    etf: str
    shares: float
    price: float
    value: float
    commission: float
    side: str  # 'buy' or 'sell'


class Portfolio:
    """
    Manages portfolio state including cash, positions, and transaction history.

    Attributes:
        initial_capital: Starting cash amount
        cash: Current cash balance
        positions: Dict mapping ETF ticker to number of shares
        trade_history: List of all trades executed
        commission_rate: Transaction cost as fraction (default 0.0003 = 0.03%)
    """

    def __init__(self, initial_capital: float = 1_000_000, commission_rate: float = 0.0003):
        """
        Initialize portfolio with cash.

        Args:
            initial_capital: Starting capital in cash
            commission_rate: Commission as fraction of trade value (default 0.03%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}
        self.trade_history: List[Trade] = []
        self.commission_rate = commission_rate

    def get_value(self, prices: pd.Series) -> float:
        """
        Calculate total portfolio value (positions + cash).

        Args:
            prices: Series of current prices with ETF tickers as index

        Returns:
            Total portfolio value
        """
        position_value = sum(
            shares * prices.get(etf, 0)
            for etf, shares in self.positions.items()
        )
        return self.cash + position_value

    def get_positions(self) -> Dict[str, float]:
        """Get current positions."""
        return self.positions.copy()

    def get_weights(self, prices: pd.Series) -> Dict[str, float]:
        """
        Calculate current portfolio weights.

        Args:
            prices: Series of current prices

        Returns:
            Dict mapping ETF to weight (fraction of portfolio value)
        """
        total_value = self.get_value(prices)

        if total_value == 0:
            return {etf: 0.0 for etf in self.positions.keys()}

        weights = {}
        for etf, shares in self.positions.items():
            position_value = shares * prices.get(etf, 0)
            weights[etf] = position_value / total_value

        return weights

    def rebalance(
        self,
        target_weights: Dict[str, float],
        prices: pd.Series,
        min_trade_value: float = 100.0
    ) -> List[Trade]:
        """
        Rebalance portfolio to target weights.

        Calculates required trades and executes them, applying transaction costs.
        Trades below min_trade_value are skipped to avoid excessive costs.

        Args:
            target_weights: Dict mapping ETF to target weight
            prices: Series of current prices
            min_trade_value: Minimum trade value to execute (default ¥100)

        Returns:
            List of trades executed
        """
        total_value = self.get_value(prices)
        trades = []

        # Ensure all ETFs in target_weights have entries in positions
        for etf in target_weights.keys():
            if etf not in self.positions:
                self.positions[etf] = 0.0

        # Calculate target position values
        target_values = {
            etf: weight * total_value
            for etf, weight in target_weights.items()
        }

        # Calculate current position values
        current_values = {
            etf: self.positions.get(etf, 0) * prices.get(etf, 0)
            for etf in target_weights.keys()
        }

        # Execute trades
        for etf in target_weights.keys():
            price = prices.get(etf)
            if price is None or price <= 0:
                print(f"Warning: Invalid price for {etf}, skipping")
                continue

            target_value = target_values[etf]
            current_value = current_values[etf]
            value_diff = target_value - current_value

            # Skip small trades
            if abs(value_diff) < min_trade_value:
                continue

            # Calculate shares to trade (round to nearest 100 for A-shares)
            shares_to_trade = round(value_diff / price / 100) * 100

            if shares_to_trade == 0:
                continue

            # Execute trade
            trade_value = abs(shares_to_trade * price)
            commission = trade_value * self.commission_rate

            if shares_to_trade > 0:
                # Buy
                total_cost = trade_value + commission
                if total_cost > self.cash:
                    # Not enough cash, scale down
                    affordable_value = self.cash - commission
                    if affordable_value > 0:
                        shares_to_trade = round(affordable_value / price / 100) * 100
                        trade_value = shares_to_trade * price
                        commission = trade_value * self.commission_rate
                        total_cost = trade_value + commission
                    else:
                        continue

                self.cash -= total_cost
                self.positions[etf] = self.positions.get(etf, 0) + shares_to_trade

                trade = Trade(
                    date=pd.Timestamp.now(),
                    etf=etf,
                    shares=shares_to_trade,
                    price=price,
                    value=trade_value,
                    commission=commission,
                    side='buy'
                )

            else:
                # Sell
                shares_to_trade_abs = abs(shares_to_trade)
                current_shares = self.positions.get(etf, 0)

                # Can't sell more than we have
                if shares_to_trade_abs > current_shares:
                    shares_to_trade_abs = round(current_shares / 100) * 100

                if shares_to_trade_abs == 0:
                    continue

                trade_value = shares_to_trade_abs * price
                commission = trade_value * self.commission_rate

                self.cash += trade_value - commission
                self.positions[etf] = self.positions.get(etf, 0) - shares_to_trade_abs

                trade = Trade(
                    date=pd.Timestamp.now(),
                    etf=etf,
                    shares=-shares_to_trade_abs,
                    price=price,
                    value=trade_value,
                    commission=commission,
                    side='sell'
                )

            trades.append(trade)
            self.trade_history.append(trade)

        return trades

    def get_total_commissions(self) -> float:
        """Calculate total commissions paid."""
        return sum(trade.commission for trade in self.trade_history)

    def get_trade_count(self) -> int:
        """Get total number of trades executed."""
        return len(self.trade_history)

    def get_turnover(self) -> float:
        """
        Calculate portfolio turnover.

        Returns:
            Total trade value / initial capital
        """
        total_trade_value = sum(abs(trade.value) for trade in self.trade_history)
        return total_trade_value / self.initial_capital if self.initial_capital > 0 else 0

    def reset(self):
        """Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.positions = {}
        self.trade_history = []

    def __repr__(self) -> str:
        return (
            f"Portfolio(cash={self.cash:.2f}, "
            f"positions={len(self.positions)}, "
            f"trades={len(self.trade_history)})"
        )
