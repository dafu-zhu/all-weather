#!/usr/bin/env python3
"""
Generate strategy performance data for the live tracker.

Simulates the All-Weather v2.0 strategy from 2026-01-02 with:
- Risk parity weights (Ledoit-Wolf shrinkage)
- Daily mean-reversion (10% drift threshold)
- Weekly target weight updates (Mondays)
- 0.03% commission per trade

Outputs JSON for the portfolio site tracker.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategy_v2 import AllWeatherV2

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
DRIFT_THRESHOLD = 0.10  # 10% drift (v2.0 tuned parameter)
COMMISSION_RATE = 0.0003  # 0.03%
LOOKBACK = 252
INITIAL_CAPITAL = 1_000_000


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


def simulate_strategy(prices: pd.DataFrame) -> dict:
    """
    Simulate the All-Weather v2.0 strategy.

    Returns dict with pnl series, rebalance events, and metrics.
    """
    # Run v2.0 backtest
    strategy = AllWeatherV2(
        prices=prices,
        initial_capital=INITIAL_CAPITAL,
        lookback=LOOKBACK,
        commission_rate=COMMISSION_RATE,
        drift_threshold=DRIFT_THRESHOLD,
        use_shrinkage=True,
    )

    results = strategy.run_backtest(
        start_date=START_DATE,
        end_date=None,
        verbose=False,
    )

    # Convert equity curve to PnL percentage series
    equity = results['equity_curve']
    pnl_series = []
    for date, value in equity.items():
        pnl_pct = (value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
        pnl_series.append({
            'date': date.strftime('%Y-%m-%d'),
            'value': round(pnl_pct, 2)
        })

    # Convert daily trades to rebalance events
    rebalances = []
    for trade in results['daily_trades']:
        rebalances.append({
            'date': trade['date'].strftime('%Y-%m-%d'),
            'drift': round(abs(trade['drift']) * 100, 2)
        })

    # Get metrics
    metrics = results['metrics']

    return {
        'last_updated': datetime.now().isoformat(),
        'start_date': START_DATE,
        'strategy_version': 'v2.0',
        'drift_threshold': f"{DRIFT_THRESHOLD:.0%}",
        'pnl': pnl_series,
        'rebalances': rebalances,
        'metrics': {
            'total_return': round(results['total_return'] * 100, 2),
            'sharpe': round(metrics.get('sharpe_ratio', 0), 2),
            'max_drawdown': round(metrics.get('max_drawdown', 0) * 100, 2),
            'win_rate': round(metrics.get('win_rate', 0) * 100, 1)
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
