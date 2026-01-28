"""
Depression Gauge - Crisis Detection Module

Implements systematic crisis detection using multiple signals:
1. Volatility Spike: Equity volatility >2x rolling average
2. Drawdown: Any equity ETF down >15% from peak
3. Momentum: S&P 500 below 200-day MA

When crisis detected, switches to Safe Portfolio (70% bonds, 30% gold).
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple


# Stock ETF codes for crisis detection
EQUITY_ETFS = ['510300.SH', '510500.SH', '513500.SH', '513100.SH']

# S&P 500 ETF for momentum signal
SP500_ETF = '513500.SH'

# Safe Portfolio allocation during crisis
SAFE_PORTFOLIO_BONDS = 0.70
SAFE_PORTFOLIO_GOLD = 0.30


def calculate_rolling_volatility(
    prices: pd.Series,
    window: int = 60,
    annualization_factor: int = 252
) -> pd.Series:
    """
    Calculate rolling volatility from price series.

    Args:
        prices: Price series
        window: Rolling window in days (default 60)
        annualization_factor: Trading days per year (default 252)

    Returns:
        Series of rolling volatility
    """
    returns = prices.pct_change()
    rolling_vol = returns.rolling(window=window).std() * np.sqrt(annualization_factor)
    return rolling_vol


def detect_volatility_spike(
    prices: pd.Series,
    current_date: pd.Timestamp,
    vol_window: int = 60,
    avg_window: int = 252,
    spike_threshold: float = 2.0
) -> Tuple[bool, float]:
    """
    Detect if current volatility is significantly elevated.

    Signal: Current volatility > spike_threshold * average volatility

    Args:
        prices: Price series for equity ETF
        current_date: Date to check
        vol_window: Window for current volatility (default 60 days)
        avg_window: Window for average volatility (default 252 days)
        spike_threshold: Multiplier for spike detection (default 2.0x)

    Returns:
        Tuple of (is_spike, current_vol / avg_vol ratio)
    """
    if current_date not in prices.index:
        return False, 0.0

    # Calculate rolling volatility
    rolling_vol = calculate_rolling_volatility(prices, window=vol_window)

    # Get data up to current date
    historical_vol = rolling_vol.loc[:current_date]

    if len(historical_vol) < avg_window:
        return False, 0.0

    # Current volatility (most recent)
    current_vol = historical_vol.iloc[-1]

    # Average volatility over longer window
    avg_vol = historical_vol.iloc[-avg_window:].mean()

    if avg_vol < 1e-10:
        return False, 0.0

    vol_ratio = current_vol / avg_vol

    is_spike = vol_ratio > spike_threshold

    return is_spike, vol_ratio


def detect_drawdown(
    prices: pd.Series,
    current_date: pd.Timestamp,
    drawdown_threshold: float = 0.15
) -> Tuple[bool, float]:
    """
    Detect if asset is in significant drawdown.

    Signal: Current price is >15% below recent peak

    Args:
        prices: Price series
        current_date: Date to check
        drawdown_threshold: Drawdown threshold (default 15%)

    Returns:
        Tuple of (is_drawdown, current_drawdown)
    """
    if current_date not in prices.index:
        return False, 0.0

    # Get data up to current date
    historical_prices = prices.loc[:current_date]

    if len(historical_prices) < 2:
        return False, 0.0

    # Calculate running maximum (peak)
    running_max = historical_prices.expanding().max()

    # Current drawdown
    current_price = historical_prices.iloc[-1]
    peak = running_max.iloc[-1]

    if peak < 1e-10:
        return False, 0.0

    drawdown = (current_price - peak) / peak

    is_significant_dd = drawdown < -drawdown_threshold

    return is_significant_dd, drawdown


def detect_momentum_break(
    prices: pd.Series,
    current_date: pd.Timestamp,
    ma_window: int = 200
) -> Tuple[bool, float]:
    """
    Detect if price is below long-term moving average.

    Signal: Current price < 200-day MA

    Args:
        prices: Price series
        current_date: Date to check
        ma_window: Moving average window (default 200 days)

    Returns:
        Tuple of (is_below_ma, price/ma ratio)
    """
    if current_date not in prices.index:
        return False, 0.0

    # Get data up to current date
    historical_prices = prices.loc[:current_date]

    if len(historical_prices) < ma_window:
        return False, 0.0

    # Calculate moving average
    ma = historical_prices.rolling(window=ma_window).mean()

    current_price = historical_prices.iloc[-1]
    current_ma = ma.iloc[-1]

    if current_ma < 1e-10:
        return False, 0.0

    price_to_ma = current_price / current_ma

    is_below = current_price < current_ma

    return is_below, price_to_ma


def detect_crisis(
    prices: pd.DataFrame,
    current_date: pd.Timestamp,
    signals_threshold: int = 2,
    version: str = 'v3.0'
) -> Tuple[bool, Dict[str, bool]]:
    """
    Detect if market is in crisis mode.

    v3.0: Crisis declared when ≥2 of 3 signals triggered
    v3.1: Crisis declared when ALL 3 signals triggered (more conservative)

    Signals:
    1. Volatility spike (equity vol >2x average)
    2. Significant drawdown (any equity >15% below peak)
    3. Momentum break (S&P 500 below 200-day MA)

    Args:
        prices: DataFrame of ETF prices
        current_date: Date to check
        signals_threshold: Number of signals needed to declare crisis (default 2)
        version: 'v3.0' (2/3 signals) or 'v3.1' (3/3 signals, more conservative)

    Returns:
        Tuple of (is_crisis, signal_status_dict)
    """
    # Override signals_threshold based on version
    if version == 'v3.1':
        signals_threshold = 3  # Require ALL 3 signals for v3.1
    signals = {
        'volatility_spike': False,
        'drawdown': False,
        'momentum_break': False
    }

    # Signal 1: Check volatility spike on any equity
    for etf in EQUITY_ETFS:
        if etf in prices.columns:
            is_spike, _ = detect_volatility_spike(prices[etf], current_date)
            if is_spike:
                signals['volatility_spike'] = True
                break

    # Signal 2: Check drawdown on any equity
    for etf in EQUITY_ETFS:
        if etf in prices.columns:
            is_dd, _ = detect_drawdown(prices[etf], current_date)
            if is_dd:
                signals['drawdown'] = True
                break

    # Signal 3: Check momentum on S&P 500
    if SP500_ETF in prices.columns:
        is_below, _ = detect_momentum_break(prices[SP500_ETF], current_date)
        signals['momentum_break'] = is_below

    # Count active signals
    active_signals = sum(signals.values())

    is_crisis = active_signals >= signals_threshold

    return is_crisis, signals


def get_safe_portfolio_weights(
    asset_codes: list,
    bond_etfs: list = ['511260.SH'],
    gold_etfs: list = ['518880.SH']
) -> np.ndarray:
    """
    Generate Safe Portfolio weights (70% bonds, 30% gold).

    Args:
        asset_codes: List of all asset codes in portfolio
        bond_etfs: List of bond ETF codes (default: 10-year Treasury)
        gold_etfs: List of gold ETF codes (default: Gold ETF)

    Returns:
        Array of weights for Safe Portfolio
    """
    n_assets = len(asset_codes)
    weights = np.zeros(n_assets)

    # Count available bond and gold ETFs
    available_bonds = [code for code in asset_codes if code in bond_etfs]
    available_gold = [code for code in asset_codes if code in gold_etfs]

    if not available_bonds and not available_gold:
        # No safe assets available, return equal weight (fallback)
        return np.ones(n_assets) / n_assets

    # Allocate to bonds
    if available_bonds:
        bond_weight_each = SAFE_PORTFOLIO_BONDS / len(available_bonds)
        for code in available_bonds:
            idx = asset_codes.index(code)
            weights[idx] = bond_weight_each

    # Allocate to gold
    if available_gold:
        gold_weight_each = SAFE_PORTFOLIO_GOLD / len(available_gold)
        for code in available_gold:
            idx = asset_codes.index(code)
            weights[idx] = gold_weight_each

    # Normalize to ensure sum = 1.0
    weights = weights / weights.sum()

    return weights


def should_exit_crisis(
    signals_history: list,
    exit_threshold: int = 2,
    lookback: int = 5
) -> bool:
    """
    Determine if conditions are right to exit crisis mode.

    Exit when ≤1 signal remains active for multiple days.

    Args:
        signals_history: List of recent signal counts (last N days)
        exit_threshold: Max signals allowed to exit (default ≤1)
        lookback: Number of days to check (default 5)

    Returns:
        True if should exit crisis mode
    """
    if len(signals_history) < lookback:
        return False

    recent_signals = signals_history[-lookback:]

    # Exit if most recent days have ≤1 signal active
    low_signal_days = sum(1 for count in recent_signals if count <= exit_threshold - 1)

    return low_signal_days >= lookback - 1  # Allow 1 day of noise
