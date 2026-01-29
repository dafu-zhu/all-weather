"""
Portfolio Optimization Module

Implements pure risk parity optimization following Ray Dalio's All Weather principles.
Each asset contributes equally to portfolio risk.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Tuple


def optimize_weights(returns: pd.DataFrame) -> np.ndarray:
    """
    Calculate risk parity weights for a portfolio (v1.0).

    The objective is to find weights such that each asset contributes equally
    to the portfolio's total risk. This is achieved by minimizing the standard
    deviation of risk contributions across all assets.

    Args:
        returns: DataFrame of asset returns (N x M where N=days, M=assets)

    Returns:
        Array of optimal weights summing to 1.0

    Raises:
        ValueError: If returns DataFrame is empty or has invalid data
    """
    if returns.empty:
        raise ValueError("Returns DataFrame is empty")

    if returns.isnull().any().any():
        raise ValueError("Returns contains NaN values")

    cov_matrix = returns.cov()
    n_assets = len(returns.columns)

    def risk_parity_objective(weights):
        """Objective function: minimize std deviation of risk contributions."""
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)

        # Avoid division by zero
        if portfolio_vol < 1e-10:
            return 1e10

        marginal_contrib = cov_matrix @ weights
        risk_contrib = weights * marginal_contrib / portfolio_vol

        # Minimize standard deviation of risk contributions
        return np.std(risk_contrib)

    # Initial guess: equal weights
    x0 = np.array([1/n_assets] * n_assets)

    # Constraints: weights sum to 1
    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}

    # Bounds: no leverage, no shorting
    bounds = tuple((0, 1) for _ in range(n_assets))

    # Optimize
    result = minimize(
        risk_parity_objective,
        x0,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 1000, 'ftol': 1e-9}
    )

    if not result.success:
        # Fallback: inverse volatility weights
        print(f"Warning: Optimization failed ({result.message}), using inverse volatility weights")
        return _inverse_volatility_weights(cov_matrix)

    return result.x




def risk_contribution(weights: np.ndarray, cov_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate each asset's contribution to portfolio risk.

    Risk contribution for asset i is defined as:
    RC_i = w_i * (Σ * w)_i / σ_p

    where:
    - w_i is the weight of asset i
    - Σ is the covariance matrix
    - σ_p is the portfolio volatility

    Args:
        weights: Asset weights (summing to 1)
        cov_matrix: Covariance matrix of asset returns

    Returns:
        Array of risk contributions for each asset
    """
    portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)

    if portfolio_vol < 1e-10:
        # Edge case: zero volatility portfolio
        return np.zeros_like(weights)

    marginal_contrib = cov_matrix @ weights
    risk_contrib = weights * marginal_contrib / portfolio_vol

    return risk_contrib


def validate_weights(weights: np.ndarray, tolerance: float = 0.001) -> Tuple[bool, str]:
    """
    Validate that weights meet portfolio constraints.

    Args:
        weights: Asset weights to validate
        tolerance: Tolerance for sum and bound checks

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check sum to 1
    if abs(weights.sum() - 1.0) > tolerance:
        return False, f"Weights sum to {weights.sum():.4f}, expected 1.0"

    # Check bounds [0, 1]
    if (weights < -tolerance).any():
        return False, f"Negative weights found: {weights[weights < 0]}"

    if (weights > 1 + tolerance).any():
        return False, f"Weights > 1 found: {weights[weights > 1]}"

    return True, "Valid"


def check_risk_parity(weights: np.ndarray, cov_matrix: np.ndarray, tolerance: float = 0.05) -> Tuple[bool, float]:
    """
    Check if weights achieve risk parity (equal risk contributions).

    Args:
        weights: Asset weights
        cov_matrix: Covariance matrix
        tolerance: Maximum acceptable std dev of risk contributions

    Returns:
        Tuple of (is_risk_parity, std_dev_of_risk_contributions)
    """
    risk_contribs = risk_contribution(weights, cov_matrix)
    std_risk_contrib = np.std(risk_contribs)

    return std_risk_contrib < tolerance, std_risk_contrib


def apply_volatility_target(
    weights: np.ndarray,
    cov_matrix: np.ndarray,
    target_vol: float = 0.06,
    annualization_factor: float = np.sqrt(252)
) -> np.ndarray:
    """
    Scale risk parity weights to target volatility level.

    This function uniformly scales all weights to achieve a target portfolio
    volatility while maintaining the equal risk contribution property of risk parity.

    Based on Asness et al. (2012) - volatility targeting is a proven approach
    for scaling All Weather portfolios to desired risk levels.

    Args:
        weights: Risk parity weights (summing to 1.0)
        cov_matrix: Covariance matrix of asset returns
        target_vol: Target annualized portfolio volatility (default 6%)
        annualization_factor: Factor to annualize volatility (default sqrt(252) for daily)

    Returns:
        Scaled weights targeting the specified volatility level

    Note:
        - Uniform scaling preserves risk parity ratios
        - If scaled weights sum > 1.0, they are normalized (no leverage constraint)
        - For leverage-allowed portfolios, weights can sum > 1.0
    """
    # Calculate current portfolio volatility (annualized)
    portfolio_variance = weights @ cov_matrix @ weights
    portfolio_vol = np.sqrt(portfolio_variance) * annualization_factor

    # Avoid division by zero
    if portfolio_vol < 1e-10:
        return weights

    # Calculate scaling factor
    scaling_factor = target_vol / portfolio_vol

    # Scale all weights uniformly (preserves risk parity)
    scaled_weights = weights * scaling_factor

    # Apply leverage constraint if needed (normalize if sum > 1.0)
    # For no-leverage portfolios, ensure weights sum to 1.0
    if scaled_weights.sum() > 1.0:
        scaled_weights = scaled_weights / scaled_weights.sum()

    return scaled_weights


def _inverse_volatility_weights(cov_matrix: np.ndarray) -> np.ndarray:
    """
    Fallback method: inverse volatility weighting.

    Args:
        cov_matrix: Covariance matrix of asset returns

    Returns:
        Weights inversely proportional to asset volatilities
    """
    vols = np.sqrt(np.diag(cov_matrix))

    # Avoid division by zero
    vols = np.where(vols < 1e-10, 1e-10, vols)

    weights = 1 / vols
    weights = weights / weights.sum()

    return weights
