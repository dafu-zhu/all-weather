"""
Volatility Targeting Module

Implements dynamic position scaling to maintain target portfolio volatility.
This helps manage risk across different market regimes.
"""

import numpy as np
import pandas as pd


def calculate_realized_volatility(
    returns: pd.Series,
    window: int = 60,
    annualization_factor: int = 252
) -> float:
    """
    Calculate realized volatility from recent returns.

    Args:
        returns: Series of portfolio returns
        window: Number of days to use for volatility calculation (default 60)
        annualization_factor: Trading days per year (default 252)

    Returns:
        Annualized realized volatility
    """
    if len(returns) < window:
        window = len(returns)

    recent_returns = returns.iloc[-window:]
    realized_vol = recent_returns.std() * np.sqrt(annualization_factor)

    return realized_vol


def scale_weights_for_target_volatility(
    base_weights: np.ndarray,
    realized_volatility: float,
    target_volatility: float = 0.10,
    max_leverage: float = 1.0
) -> np.ndarray:
    """
    Scale weights to achieve target portfolio volatility.

    Formula: scaled_weights = base_weights * (target_vol / realized_vol)

    Constraints:
    - No leverage (sum of scaled weights = 1.0)
    - Maintains relative proportions of base weights

    Args:
        base_weights: Base asset weights from optimization
        realized_volatility: Current realized portfolio volatility
        target_volatility: Target portfolio volatility (default 10%)
        max_leverage: Maximum leverage allowed (default 1.0 = no leverage)

    Returns:
        Scaled weights normalized to sum to 1.0
    """
    if realized_volatility < 1e-10:
        # Edge case: zero volatility, return base weights
        return base_weights

    # Calculate scaling factor
    scale = target_volatility / realized_volatility

    # Apply max leverage constraint
    scale = min(scale, max_leverage)

    # Scale weights
    scaled_weights = base_weights * scale

    # Normalize to sum to 1.0 (no leverage)
    # This maintains proportions while ensuring sum=1
    scaled_weights = scaled_weights / scaled_weights.sum()

    return scaled_weights


def apply_volatility_targeting(
    base_weights: np.ndarray,
    portfolio_returns: pd.Series,
    target_volatility: float = 0.10,
    lookback_window: int = 60
) -> np.ndarray:
    """
    Apply volatility targeting to base weights.

    Convenience function combining realized vol calculation and scaling.

    Args:
        base_weights: Base weights from optimization
        portfolio_returns: Historical portfolio returns
        target_volatility: Target annual volatility (default 10%)
        lookback_window: Window for volatility calculation (default 60 days)

    Returns:
        Volatility-adjusted weights
    """
    if len(portfolio_returns) < 10:
        # Not enough history, return base weights
        return base_weights

    realized_vol = calculate_realized_volatility(
        portfolio_returns,
        window=lookback_window
    )

    scaled_weights = scale_weights_for_target_volatility(
        base_weights,
        realized_vol,
        target_volatility
    )

    return scaled_weights


def check_volatility_target(
    portfolio_volatility: float,
    target_volatility: float,
    tolerance: float = 0.02
) -> bool:
    """
    Check if portfolio volatility is within tolerance of target.

    Args:
        portfolio_volatility: Current portfolio volatility
        target_volatility: Target volatility
        tolerance: Acceptable deviation (default 2%)

    Returns:
        True if within tolerance, False otherwise
    """
    deviation = abs(portfolio_volatility - target_volatility)
    return deviation <= tolerance
