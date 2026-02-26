#!/usr/bin/env python3
"""
Generate strategy performance data for the live tracker.

Simulates the All-Weather strategy from 2026-01-02 with:
- Risk parity initial weights (Ledoit-Wolf shrinkage)
- Auto-rebalancing when drift > 5%
- 0.03% commission per trade

Outputs JSON for the portfolio site tracker.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.optimizer import optimize_weights
from src.metrics import calculate_all_metrics

# Strategy configuration
TRADABLE_ETFS = [
    '510300.SH',  # CSI 300
    '510500.SH',  # CSI 500
    '513500.SH',  # S&P 500
    '511260.SH',  # 10Y Treasury
    '518880.SH',  # Gold
    '513100.SH',  # Nasdaq-100
]
START_DATE = '2026-01-02'
COMMISSION_RATE = 0.0003  # 0.03%
REBALANCE_THRESHOLD = 0.05  # 5% drift
LOOKBACK = 252


def fetch_prices(tickers: list[str], start: str = '2015-01-01') -> pd.DataFrame:
    """Fetch historical prices from yfinance."""
    data = {}
    for ticker in tickers:
        yf_ticker = ticker.replace('.SH', '.SS')
        hist = yf.Ticker(yf_ticker).history(start=start, auto_adjust=True)
        if hist.empty:
            raise ValueError(f"No data for {ticker}")
        data[ticker] = hist['Close']

    prices = pd.DataFrame(data)
    prices.index = prices.index.tz_localize(None)
    return prices.dropna()


def calculate_weights(prices: pd.DataFrame, lookback: int = 252) -> np.ndarray:
    """Calculate risk parity weights using Ledoit-Wolf shrinkage."""
    returns = prices.iloc[-lookback:].pct_change().dropna()
    return optimize_weights(returns, use_shrinkage=True)


def simulate_strategy(prices: pd.DataFrame) -> dict:
    """
    Simulate the All-Weather strategy with auto-rebalancing.

    Returns dict with pnl series, rebalance events, and metrics.
    """
    # Get tracking period (from START_DATE onwards)
    tracking_prices = prices.loc[START_DATE:]
    if tracking_prices.empty:
        raise ValueError(f"No data available from {START_DATE}")

    # Calculate initial weights using data before start date
    pre_start_prices = prices.loc[:START_DATE].iloc[:-1]
    if len(pre_start_prices) < LOOKBACK:
        raise ValueError(f"Insufficient historical data for lookback period")

    weights = calculate_weights(pre_start_prices, LOOKBACK)

    # Initialize tracking
    pnl_series = []
    rebalances = []
    initial_value = 1.0  # Normalized
    portfolio_value = initial_value

    # Track positions (normalized)
    positions = {etf: weights[i] for i, etf in enumerate(TRADABLE_ETFS)}
    prev_prices = tracking_prices.iloc[0]

    for date, current_prices in tracking_prices.iterrows():
        # Update portfolio value based on price changes
        if date != tracking_prices.index[0]:
            returns = (current_prices - prev_prices) / prev_prices
            for i, etf in enumerate(TRADABLE_ETFS):
                positions[etf] *= (1 + returns[etf])

        # Calculate current portfolio value and weights
        portfolio_value = sum(positions.values())
        current_weights = {etf: pos / portfolio_value for etf, pos in positions.items()}

        # Check for rebalancing
        target_weights = dict(zip(TRADABLE_ETFS, weights))
        max_drift = max(abs(current_weights[etf] - target_weights[etf]) for etf in TRADABLE_ETFS)

        if max_drift > REBALANCE_THRESHOLD:
            # Recalculate target weights with current data
            hist_prices = prices.loc[:date]
            if len(hist_prices) >= LOOKBACK:
                weights = calculate_weights(hist_prices, LOOKBACK)
                target_weights = dict(zip(TRADABLE_ETFS, weights))

            # Simulate rebalancing with commission
            turnover = sum(abs(current_weights[etf] - target_weights[etf]) for etf in TRADABLE_ETFS) / 2
            commission_cost = turnover * COMMISSION_RATE * portfolio_value
            portfolio_value -= commission_cost

            # Reset positions to target weights
            positions = {etf: target_weights[etf] * portfolio_value for etf in TRADABLE_ETFS}

            rebalances.append({
                'date': date.strftime('%Y-%m-%d'),
                'drift': round(max_drift * 100, 2)
            })

        # Record PnL
        pnl_pct = (portfolio_value - initial_value) / initial_value * 100
        pnl_series.append({
            'date': date.strftime('%Y-%m-%d'),
            'value': round(pnl_pct, 2)
        })

        prev_prices = current_prices

    # Calculate performance metrics
    pnl_values = [p['value'] for p in pnl_series]
    daily_returns = pd.Series(pnl_values).diff().dropna() / 100
    equity_curve = pd.Series([1 + p['value']/100 for p in pnl_series])

    metrics_raw = calculate_all_metrics(daily_returns, equity_curve)

    return {
        'last_updated': datetime.now().isoformat(),
        'start_date': START_DATE,
        'pnl': pnl_series,
        'rebalances': rebalances,
        'metrics': {
            'total_return': round(pnl_series[-1]['value'], 2),
            'sharpe': round(metrics_raw.get('sharpe_ratio', 0), 2),
            'max_drawdown': round(metrics_raw.get('max_drawdown', 0) * 100, 2),
            'win_rate': round(metrics_raw.get('win_rate', 0) * 100, 1)
        }
    }


def main():
    """Generate tracker data and save to JSON."""
    print("Fetching prices...")
    prices = fetch_prices(TRADABLE_ETFS)

    print("Simulating strategy...")
    result = simulate_strategy(prices)

    # Save to data directory
    output_path = Path(__file__).parent.parent / 'data' / 'pnl_tracker.json'
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Saved to {output_path}")
    print(f"Total return: {result['metrics']['total_return']}%")
    print(f"Rebalances: {len(result['rebalances'])}")


if __name__ == '__main__':
    main()
