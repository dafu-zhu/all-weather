"""
Live Portfolio Tracker with OOP design.

Provides comprehensive portfolio management with:
- Position tracking with average cost basis
- Automatic PnL calculation
- Risk parity rebalancing signals
- Performance analytics
- Trade logging with realized PnL
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


@dataclass
class Trade:
    """Trade record with realized PnL tracking."""
    date: pd.Timestamp
    etf: str
    shares: int  # Positive for buy, negative for sell
    price: float
    value: float
    commission: float
    side: str  # 'buy', 'sell', or 'deposit'
    realized_pnl: float = 0.0  # For sells only


class Portfolio:
    """Live portfolio tracker with risk parity rebalancing.

    Features:
    - Build positions via trade() method
    - Automatic PnL tracking from entry
    - Risk parity target weight calculation
    - Comprehensive performance analytics
    - Trade log with realized PnL

    Example:
        >>> portfolio = Portfolio(
        ...     tradable_etfs=['510300.SH', '510500.SH', '513500.SH',
        ...                    '511260.SH', '518880.SH', '513100.SH'],
        ...     initial_cash=30000
        ... )
        >>> portfolio.trade(700, 4.681, 'buy', '2026-01-30', '510300.SH')
        >>> print(portfolio.positions)
        >>> print(portfolio.signal)
    """

    def __init__(
        self,
        tradable_etfs: List[str],
        initial_cash: float = 0.0,
        commission_rate: float = 0.0003,
        rebalance_threshold: float = 0.05,
        lookback: int = 252
    ):
        """Initialize empty portfolio.

        Args:
            tradable_etfs: List of ETF tickers to track
            initial_cash: Starting cash balance
            commission_rate: Commission rate (default 0.03%)
            rebalance_threshold: Drift threshold for rebalancing (default 5%)
            lookback: Covariance lookback period (default 252 days)
        """
        # Core state
        self._tradable_etfs = tradable_etfs
        self._positions: Dict[str, float] = {}  # {ticker: shares}
        self._entry_prices: Dict[str, float] = {}  # {ticker: avg_cost_basis}
        self._cash = initial_cash
        self._trade_log: List[Trade] = []

        # Market data (lazy loaded)
        self._prices: Optional[pd.DataFrame] = None
        self._last_price_update: Optional[datetime] = None

        # Strategy params
        self._commission_rate = commission_rate
        self._rebalance_threshold = rebalance_threshold
        self._lookback = lookback

    def add_cash(self, amount: float) -> None:
        """Add cash to portfolio (deposits).

        Args:
            amount: Cash amount to deposit
        """
        self._cash += amount
        # Log as special trade type
        self._trade_log.append(Trade(
            date=pd.Timestamp(datetime.now()),
            etf='CASH',
            shares=0,
            price=0,
            value=amount,
            commission=0,
            side='deposit'
        ))

    def trade(
        self,
        qty: int,
        price: float,
        side: str,
        day: str,
        etf: str
    ) -> None:
        """Execute trade and update positions/cash.

        Args:
            qty: Number of shares (positive integer)
            price: Execution price
            side: 'buy' or 'sell'
            day: Trade date (YYYY-MM-DD)
            etf: ETF ticker

        Side effects:
            - Updates _positions[etf]
            - Updates _entry_prices[etf] (average cost for buys)
            - Updates _cash (deduct for buys, add for sells)
            - Appends to _trade_log with realized PnL
        """
        # Validate ETF
        if etf not in self._tradable_etfs:
            raise ValueError(f"ETF {etf} not in tradable list")

        # Round to 100-lot
        qty = round(qty / 100) * 100
        if qty == 0:
            return

        value = qty * price
        commission = value * self._commission_rate
        realized_pnl = 0.0

        if side == 'buy':
            # Check sufficient cash
            total_cost = value + commission
            if total_cost > self._cash:
                raise ValueError(f"Insufficient cash: need ¥{total_cost:.2f}, have ¥{self._cash:.2f}")

            # Update average entry price
            if etf in self._positions:
                old_qty = self._positions[etf]
                old_avg = self._entry_prices[etf]
                new_qty = old_qty + qty
                new_avg = (old_qty * old_avg + qty * price) / new_qty
                self._entry_prices[etf] = new_avg
                self._positions[etf] = new_qty
            else:
                self._positions[etf] = qty
                self._entry_prices[etf] = price

            self._cash -= total_cost

        elif side == 'sell':
            # Check sufficient shares
            if etf not in self._positions or self._positions[etf] < qty:
                current_shares = self._positions.get(etf, 0)
                raise ValueError(f"Insufficient shares: need {qty}, have {current_shares}")

            # Calculate realized PnL
            avg_cost = self._entry_prices.get(etf, price)
            realized_pnl = qty * (price - avg_cost) - commission

            self._positions[etf] -= qty
            self._cash += (value - commission)

            # If fully closed, remove entry price
            if self._positions[etf] <= 0:
                del self._positions[etf]
                if etf in self._entry_prices:
                    del self._entry_prices[etf]

        else:
            raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")

        # Log trade
        self._trade_log.append(Trade(
            date=pd.Timestamp(day),
            etf=etf,
            shares=qty if side == 'buy' else -qty,
            price=price,
            value=value,
            commission=commission,
            side=side,
            realized_pnl=realized_pnl
        ))

    def calc_value(self) -> float:
        """Calculate total portfolio value (positions + cash).

        Returns:
            Total portfolio value in CNY
        """
        self._ensure_prices_loaded()
        latest_prices = self._prices.iloc[-1]

        position_value = sum(
            self._positions.get(etf, 0) * latest_prices[etf]
            for etf in self._tradable_etfs
        )
        return position_value + self._cash

    @property
    def pnl(self) -> pd.DataFrame:
        """PnL curve from first trade to current date.

        Returns:
            DataFrame with columns: Date (index), PnL, PnL %
            Only includes trading days (no gaps)
        """
        self._ensure_prices_loaded()

        if not self._trade_log:
            return pd.DataFrame()

        # Get entry date (first trade)
        entry_date = min(t.date for t in self._trade_log)

        # Filter prices to tracking period
        tracking_prices = self._prices.loc[entry_date:]

        # Calculate entry value
        entry_value = self._calculate_initial_value()

        # Calculate daily PnL
        pnl_data = []
        for date, row in tracking_prices.iterrows():
            daily_value = sum(
                self._positions.get(etf, 0) * row[etf]
                for etf in self._tradable_etfs
            ) + self._cash

            pnl = daily_value - entry_value
            pnl_pct = (pnl / entry_value * 100) if entry_value > 0 else 0

            pnl_data.append({
                'Date': date,
                'PnL': pnl,
                'PnL %': pnl_pct
            })

        return pd.DataFrame(pnl_data).set_index('Date')

    def plot_pnl(self):
        """Display PnL % chart (removes Portfolio Value chart)."""
        pnl_df = self.pnl

        if pnl_df.empty:
            print("No PnL data available (no trades yet)")
            return

        fig, ax = plt.subplots(figsize=(14, 6))

        # Plot PnL %
        x = np.arange(len(pnl_df))
        ax.plot(x, pnl_df['PnL %'], linewidth=2, color='#A23B72')
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
        ax.fill_between(x, pnl_df['PnL %'], 0,
                         where=pnl_df['PnL %'] >= 0, alpha=0.3, color='green', label='Profit')
        ax.fill_between(x, pnl_df['PnL %'], 0,
                         where=pnl_df['PnL %'] < 0, alpha=0.3, color='red', label='Loss')

        ax.set_title('PnL % Over Time (Trading Days Only)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('PnL %', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Date labels
        num_ticks = min(10, len(pnl_df))
        tick_positions = np.linspace(0, len(pnl_df)-1, num_ticks, dtype=int)
        tick_labels = [pnl_df.index[i].strftime('%Y-%m-%d') for i in tick_positions]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right')

        plt.tight_layout()
        plt.show()

    @property
    def positions(self) -> pd.DataFrame:
        """Current position holdings.

        Returns:
            DataFrame with columns:
            - ETF
            - Shares
            - Entry Price (avg cost basis)
            - Current Price
            - Market Value
            - Unrealized PnL
            - Unrealized PnL %
            - Weight (% of portfolio)
        """
        self._ensure_prices_loaded()
        latest_prices = self._prices.iloc[-1]
        total_value = self.calc_value()

        data = []
        for etf in self._tradable_etfs:
            shares = self._positions.get(etf, 0)
            if shares == 0:
                continue

            entry_price = self._entry_prices[etf]
            current_price = latest_prices[etf]
            market_value = shares * current_price
            cost_basis = shares * entry_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            weight = (market_value / total_value * 100) if total_value > 0 else 0

            data.append({
                'ETF': etf,
                'Shares': int(shares),
                'Entry Price': entry_price,
                'Current Price': current_price,
                'Market Value': market_value,
                'Unrealized PnL': unrealized_pnl,
                'Unrealized PnL %': unrealized_pnl_pct,
                'Weight %': weight
            })

        return pd.DataFrame(data)

    @property
    def signal(self) -> Dict[str, Any]:
        """Rebalancing signal with drift analysis.

        Returns:
            Dict with:
            - current_weights: Dict[str, float]
            - target_weights: Dict[str, float] (risk parity optimized)
            - drift: float (max weight difference)
            - threshold: float (rebalance threshold, default 5%)
            - should_rebalance: bool
            - trades_needed: List[Dict] (if should_rebalance=True)
        """
        from src.optimizer import optimize_weights

        self._ensure_prices_loaded()
        latest_prices = self._prices.iloc[-1]
        total_value = self.calc_value()

        # Current weights
        current_weights = {
            etf: (self._positions.get(etf, 0) * latest_prices[etf] / total_value)
            for etf in self._tradable_etfs
        }

        # Calculate target weights (risk parity)
        hist_returns = self._prices.iloc[-self._lookback:].pct_change().dropna()
        target_weights_array = optimize_weights(hist_returns, use_shrinkage=True)
        target_weights = dict(zip(self._tradable_etfs, target_weights_array))

        # Calculate drift
        drift = max(
            abs(current_weights[etf] - target_weights[etf])
            for etf in self._tradable_etfs
        )

        should_rebalance = drift > self._rebalance_threshold

        result = {
            'current_weights': current_weights,
            'target_weights': target_weights,
            'drift': drift,
            'threshold': self._rebalance_threshold,
            'should_rebalance': should_rebalance
        }

        # Calculate trades if rebalancing needed
        if should_rebalance:
            trades = []
            for etf in self._tradable_etfs:
                target_value = total_value * target_weights[etf]
                target_shares = target_value / latest_prices[etf]
                target_shares_rounded = round(target_shares / 100) * 100

                current_shares = self._positions.get(etf, 0)
                trade_shares = target_shares_rounded - current_shares

                if trade_shares != 0:
                    trades.append({
                        'etf': etf,
                        'current_shares': int(current_shares),
                        'target_shares': int(target_shares_rounded),
                        'action': 'BUY' if trade_shares > 0 else 'SELL',
                        'shares': int(abs(trade_shares)),
                        'price': latest_prices[etf]
                    })

            result['trades_needed'] = trades

        return result

    @property
    def analysis(self) -> pd.Series:
        """Portfolio performance analytics.

        Returns:
            Series with metrics:
            - sharpe_ratio
            - annual_return
            - annualized_return (same as annual_return)
            - absolute_pnl (total PnL in CNY)
            - max_drawdown
            - sortino_ratio
            - calmar_ratio
            - win_rate
            - total_return (cumulative %)
        """
        from src.metrics import calculate_all_metrics

        pnl_df = self.pnl
        if pnl_df.empty:
            return pd.Series()

        # Calculate equity curve
        entry_value = self._calculate_initial_value()
        equity_curve = entry_value * (1 + pnl_df['PnL %'] / 100)

        # Calculate returns
        returns = equity_curve.pct_change().dropna()

        # Get all metrics
        metrics = calculate_all_metrics(returns, equity_curve)

        # Add custom metrics
        metrics['absolute_pnl'] = pnl_df['PnL'].iloc[-1]
        metrics['total_return'] = pnl_df['PnL %'].iloc[-1]
        metrics['annualized_return'] = metrics['annual_return']  # Alias

        return pd.Series(metrics)

    @property
    def log(self) -> pd.DataFrame:
        """Trading log with realized PnL.

        Returns:
            DataFrame with columns:
            - Date
            - ETF
            - Side (buy/sell/deposit)
            - Shares
            - Price
            - Value
            - Commission
            - Realized PnL (for sells, using avg cost basis)
        """
        if not self._trade_log:
            return pd.DataFrame()

        data = []
        for trade in self._trade_log:
            data.append({
                'Date': trade.date,
                'ETF': trade.etf,
                'Side': trade.side,
                'Shares': abs(trade.shares),
                'Price': trade.price,
                'Value': trade.value,
                'Commission': trade.commission,
                'Realized PnL': trade.realized_pnl
            })

        return pd.DataFrame(data)

    # Helper methods

    def _ensure_prices_loaded(self) -> None:
        """Fetch/refresh price data if needed."""
        if self._prices is None or self._needs_refresh():
            self._fetch_prices()

    def _needs_refresh(self) -> bool:
        """Check if price cache expired (>1 hour old)."""
        if self._last_price_update is None:
            return True
        return (datetime.now() - self._last_price_update).seconds > 3600

    def _fetch_prices(self) -> None:
        """Fetch historical prices from yfinance."""
        import yfinance as yf

        try:
            # Fetch from yfinance
            # Convert .SH to .SS for Yahoo Finance compatibility (Shanghai Stock Exchange)
            data = {}
            for ticker in self._tradable_etfs:
                yf_ticker = ticker.replace('.SH', '.SS')
                ticker_obj = yf.Ticker(yf_ticker)
                hist = ticker_obj.history(start='2015-01-01', auto_adjust=True)
                if hist.empty:
                    raise ValueError(f"No data for {ticker}")
                data[ticker] = hist['Close']  # Use original ticker as column name

            self._prices = pd.DataFrame(data)
            self._prices.index = self._prices.index.tz_localize(None)
            self._prices = self._prices.dropna()

        except Exception as e:
            # Fallback to local CSV
            try:
                self._prices = pd.read_csv(
                    'data/etf_prices_7etf.csv',
                    index_col=0,
                    parse_dates=True
                )
                # Filter to tradable ETFs
                self._prices = self._prices[self._tradable_etfs]
            except Exception as fallback_error:
                raise RuntimeError(
                    f"Failed to fetch prices from yfinance ({e}) "
                    f"and fallback to CSV ({fallback_error})"
                )

        self._last_price_update = datetime.now()

    def _calculate_initial_value(self) -> float:
        """Calculate portfolio value at entry (first trade date)."""
        if not self._trade_log:
            return 0.0

        entry_date = min(t.date for t in self._trade_log)

        # Find entry prices (or closest available date)
        if entry_date not in self._prices.index:
            # Find closest date
            entry_date = self._prices.index[self._prices.index >= entry_date][0]

        entry_prices = self._prices.loc[entry_date]

        # Sum up initial positions value + cash at entry
        # Note: We need to track cash at entry, which is initial_cash - sum of buy trades
        entry_value = 0.0
        for trade in self._trade_log:
            if trade.date == entry_date:
                if trade.side == 'buy':
                    entry_value += trade.shares * entry_prices[trade.etf]

        # Add remaining cash
        entry_value += self._cash

        return entry_value
