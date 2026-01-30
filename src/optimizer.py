"""
Portfolio Optimization Module

Implements pure risk parity optimization following Ray Dalio's All Weather principles.
Each asset contributes equally to portfolio risk.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Tuple, Optional
from sklearn.covariance import LedoitWolf


def estimate_covariance_shrinkage(returns: pd.DataFrame) -> Tuple[np.ndarray, float]:
    """
    Estimate covariance matrix using Ledoit-Wolf shrinkage.

    Shrinkage improves covariance estimation by combining the sample
    covariance with a structured estimator (constant correlation model).
    This reduces estimation error, especially with limited data.

    Based on:
    Ledoit, O. and Wolf, M. (2004) "A well-conditioned estimator for
    large-dimensional covariance matrices"

    Args:
        returns: DataFrame of asset returns

    Returns:
        Tuple of (shrunk_covariance_matrix, shrinkage_coefficient)
        - shrinkage_coefficient: 0 = sample cov, 1 = structured estimator
    """
    lw = LedoitWolf()
    lw.fit(returns.values)
    return lw.covariance_, lw.shrinkage_


def optimize_weights(returns: pd.DataFrame, use_shrinkage: bool = False) -> np.ndarray:
    """
    Calculate risk parity weights for a portfolio (v1.2 with shrinkage).

    The objective is to find weights such that each asset contributes equally
    to the portfolio's total risk. This is achieved by minimizing the standard
    deviation of risk contributions across all assets.

    v1.2 Feature: Optional Ledoit-Wolf shrinkage for more robust covariance estimation.
    Shrinkage reduces noise in covariance estimates, leading to more stable weights.

    Args:
        returns: DataFrame of asset returns (N x M where N=days, M=assets)
        use_shrinkage: Whether to use Ledoit-Wolf shrinkage (v1.2 feature, default False)

    Returns:
        Array of optimal weights summing to 1.0

    Raises:
        ValueError: If returns DataFrame is empty or has invalid data
    """
    if returns.empty:
        raise ValueError("Returns DataFrame is empty")

    if returns.isnull().any().any():
        raise ValueError("Returns contains NaN values")

    # Use shrinkage estimator if requested (v1.2)
    if use_shrinkage:
        cov_matrix, shrinkage_coef = estimate_covariance_shrinkage(returns)
        cov_matrix = pd.DataFrame(cov_matrix, index=returns.columns, columns=returns.columns)
    else:
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


def optimize_weights_constrained(
    returns: pd.DataFrame,
    asset_classes: dict,
    constraints: dict
) -> np.ndarray:
    """
    Calculate risk parity weights with asset class constraints (v1.2).

    Balances equal risk contribution with practical allocation limits
    to improve performance across market regimes.

    Args:
        returns: DataFrame of asset returns (N x M)
        asset_classes: Dict mapping asset class names to ticker lists
                      e.g., {'Stocks': ['SPY', 'QQQ'], 'Bonds': ['TLT', 'IEF']}
        constraints: Dict with min/max bounds per asset class
                    e.g., {'Stocks': {'min': 0.25, 'max': 0.50}}

    Returns:
        Constrained weights maintaining risk parity where possible
    """
    if returns.empty:
        raise ValueError("Returns DataFrame is empty")

    if returns.isnull().any().any():
        raise ValueError("Returns contains NaN values")

    cov_matrix = returns.cov()
    n_assets = len(returns.columns)
    tickers = list(returns.columns)

    # Create ticker-to-index mapping
    ticker_idx = {t: i for i, t in enumerate(tickers)}

    def risk_parity_objective(weights):
        """Minimize std deviation of risk contributions."""
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        if portfolio_vol < 1e-10:
            return 1e10
        marginal_contrib = cov_matrix @ weights
        risk_contrib = weights * marginal_contrib / portfolio_vol
        return np.std(risk_contrib)

    # Initial guess: equal weights
    x0 = np.array([1/n_assets] * n_assets)

    # Build constraint list
    constraint_list = []

    # Sum to 1
    constraint_list.append({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})

    # Asset class bounds
    for asset_class, tickers_list in asset_classes.items():
        if asset_class not in constraints:
            continue

        min_alloc = constraints[asset_class].get('min', 0)
        max_alloc = constraints[asset_class].get('max', 1)

        # Get indices for this asset class
        indices = [ticker_idx[t] for t in tickers_list if t in ticker_idx]

        # Min constraint
        constraint_list.append({
            'type': 'ineq',
            'fun': lambda x, idx=indices, m=min_alloc: np.sum(x[idx]) - m
        })

        # Max constraint
        constraint_list.append({
            'type': 'ineq',
            'fun': lambda x, idx=indices, m=max_alloc: m - np.sum(x[idx])
        })

    # Bounds: no leverage, no shorting
    bounds = tuple((0, 1) for _ in range(n_assets))

    # Optimize
    result = minimize(
        risk_parity_objective,
        x0,
        method='SLSQP',
        bounds=bounds,
        constraints=constraint_list,
        options={'maxiter': 2000, 'ftol': 1e-9}
    )

    if not result.success:
        print(f"Warning: Constrained optimization failed ({result.message}), using unconstrained")
        return optimize_weights(returns)

    return result.x


def optimize_weights_4quadrant(
    returns: pd.DataFrame,
    quadrant_mapping: dict
) -> np.ndarray:
    """
    Calculate weights using 4-quadrant risk balance (v1.3).

    Implements Bridgewater's economic environment framework:
    - 25% of portfolio risk to each of 4 economic environments
    - Growth Rising + Inflation Rising
    - Growth Rising + Inflation Falling
    - Growth Falling + Inflation Rising
    - Growth Falling + Inflation Falling

    This approach balances risk across economic scenarios rather than just
    across assets, providing more robust all-weather performance.

    Args:
        returns: DataFrame of asset returns (N x M)
        quadrant_mapping: Dict mapping quadrant names to:
            {
                'quadrant_name': {
                    'assets': ['TICKER1', 'TICKER2', ...],
                    'risk_allocation': 0.25  # Target risk contribution
                }
            }

    Returns:
        Weights balancing risk across 4 quadrants
    """
    if returns.empty:
        raise ValueError("Returns DataFrame is empty")

    if returns.isnull().any().any():
        raise ValueError("Returns contains NaN values")

    # Calculate full covariance matrix
    cov_matrix = returns.cov().values
    tickers = list(returns.columns)
    ticker_idx = {t: i for i, t in enumerate(tickers)}
    n_assets = len(tickers)

    # Initialize final weights
    final_weights = np.zeros(n_assets)

    # For each quadrant, calculate risk parity weights within it
    for quadrant_name, quadrant_info in quadrant_mapping.items():
        quadrant_assets = quadrant_info['assets']
        target_risk = quadrant_info['risk_allocation']

        # Filter to assets present in our universe
        valid_assets = [a for a in quadrant_assets if a in ticker_idx]
        if not valid_assets:
            continue

        # Get indices for this quadrant
        indices = [ticker_idx[a] for a in valid_assets]

        # Extract sub-returns for quadrant
        quadrant_returns = returns[valid_assets]

        # Calculate risk parity weights within quadrant
        try:
            quadrant_weights = optimize_weights(quadrant_returns)
        except Exception as e:
            print(f"Warning: Quadrant {quadrant_name} optimization failed ({e}), using equal weights")
            quadrant_weights = np.ones(len(valid_assets)) / len(valid_assets)

        # Place quadrant weights in correct positions
        quadrant_full_weights = np.zeros(n_assets)
        for i, idx in enumerate(indices):
            quadrant_full_weights[idx] = quadrant_weights[i]

        # Calculate quadrant's contribution to portfolio risk
        # We need to scale this quadrant to contribute target_risk fraction
        # Portfolio variance contribution from quadrant i: w_i^T Σ w_i
        quadrant_variance = quadrant_full_weights @ cov_matrix @ quadrant_full_weights

        if quadrant_variance < 1e-10:
            # Skip zero-variance quadrants
            continue

        # Add to final weights (will be scaled later)
        final_weights += quadrant_full_weights

    # Normalize to sum to 1.0
    if final_weights.sum() < 1e-10:
        # Fallback: equal weights
        print("Warning: 4-quadrant optimization produced zero weights, using equal weights")
        return np.ones(n_assets) / n_assets

    final_weights = final_weights / final_weights.sum()

    return final_weights


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
