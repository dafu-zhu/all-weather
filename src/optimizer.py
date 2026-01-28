"""
Portfolio Optimization Module

Implements risk parity optimization with optional constraints.
Contains both v1.0 (pure risk parity) and v2.0 (constrained) optimizers.
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


def optimize_weights_constrained(
    returns: pd.DataFrame,
    min_stock_alloc: float = 0.40,
    max_bond_alloc: float = 0.50
) -> np.ndarray:
    """
    Calculate risk parity weights with allocation constraints (v2.0).

    Enforces:
    - Minimum total stock allocation
    - Maximum total bond allocation
    - Individual asset bounds [0, 1]
    - Weights sum to 1

    Args:
        returns: DataFrame of asset returns (lookback period)
        min_stock_alloc: Minimum total allocation to stocks (default 40%)
        max_bond_alloc: Maximum total allocation to bonds (default 50%)

    Returns:
        Array of optimal weights
    """
    cov_matrix = returns.cov().values
    n_assets = len(returns.columns)

    # Identify asset types based on ETF codes
    columns = returns.columns.tolist()
    stock_indices = []
    bond_indices = []
    other_indices = []

    for i, col in enumerate(columns):
        # Stock ETFs
        if col in ['510300.SH', '510500.SH', '513500.SH', '513300.SH', '510170.SH', '513100.SH']:
            stock_indices.append(i)
        # Bond ETFs
        elif col in ['511260.SH', '511090.SH', '511130.SH']:
            bond_indices.append(i)
        # Commodities and others
        else:
            other_indices.append(i)

    # Objective: minimize std(risk_contributions)
    def risk_parity_objective(weights):
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        if portfolio_vol < 1e-10:
            return 1e10

        marginal_contrib = cov_matrix @ weights
        risk_contrib = weights * marginal_contrib / portfolio_vol

        # Standard deviation of risk contributions
        return np.std(risk_contrib)

    # Constraints
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},  # Sum to 1
    ]

    # Add stock minimum constraint if we have stocks
    if stock_indices:
        constraints.append({
            'type': 'ineq',
            'fun': lambda w: np.sum([w[i] for i in stock_indices]) - min_stock_alloc
        })

    # Add bond maximum constraint if we have bonds
    if bond_indices:
        constraints.append({
            'type': 'ineq',
            'fun': lambda w: max_bond_alloc - np.sum([w[i] for i in bond_indices])
        })

    # Bounds: 0 <= weight <= 1 for all assets
    bounds = tuple((0.0, 1.0) for _ in range(n_assets))

    # Initial guess - equal weight
    x0 = np.ones(n_assets) / n_assets

    # Try to enforce constraints in initial guess
    if stock_indices and bond_indices:
        # Give stocks the minimum allocation, split equally
        for i in stock_indices:
            x0[i] = min_stock_alloc / len(stock_indices)

        # Give bonds the max allocation, split equally
        for i in bond_indices:
            x0[i] = max_bond_alloc / len(bond_indices)

        # Remaining for others
        remaining = 1.0 - (min_stock_alloc + max_bond_alloc)
        if other_indices and remaining > 0:
            for i in other_indices:
                x0[i] = remaining / len(other_indices)

    # Optimize
    result = minimize(
        risk_parity_objective,
        x0=x0,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 1000, 'ftol': 1e-9}
    )

    if not result.success:
        print(f"⚠️  Optimization warning: {result.message}")
        # Try with relaxed constraints
        constraints_relaxed = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        result = minimize(
            risk_parity_objective,
            x0=x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_relaxed,
            options={'maxiter': 1000}
        )

        if not result.success:
            # Fallback: use equal weight
            return np.ones(n_assets) / n_assets

    weights = result.x

    # Ensure weights are non-negative and sum to 1
    weights = np.maximum(weights, 0)
    weights = weights / weights.sum()

    return weights


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


def optimize_weights_v3(
    returns: pd.DataFrame,
    min_stock_alloc: float = 0.60,
    max_bond_alloc: float = 0.35,
    balance_environments: bool = True,
    expected_returns: pd.Series = None,
    lambda_sharpe: float = 0.5
) -> np.ndarray:
    """
    Calculate risk parity weights with environment balancing and return optimization (v3.0).

    Combines:
    1. Risk parity (equal risk contributions)
    2. Environment balancing (equal risk across economic environments)
    3. Return awareness (optimize for Sharpe ratio)

    Args:
        returns: DataFrame of asset returns (lookback period)
        min_stock_alloc: Minimum total allocation to stocks (default 60%)
        max_bond_alloc: Maximum total allocation to bonds (default 35%)
        balance_environments: Whether to balance risk across environments (default True)
        expected_returns: Expected returns for each asset (optional, uses EWMA if None)
        lambda_sharpe: Weight on Sharpe maximization vs risk parity (0-1, default 0.5)

    Returns:
        Array of optimal weights
    """
    from src.environment_model import environment_balance_penalty

    cov_matrix = returns.cov().values
    n_assets = len(returns.columns)
    columns = returns.columns.tolist()

    # Calculate expected returns if not provided
    if expected_returns is None:
        # Use exponentially-weighted moving average
        expected_returns = returns.ewm(span=60, adjust=False).mean().iloc[-1]

    expected_returns = expected_returns.values

    # Identify asset types
    stock_indices = []
    bond_indices = []
    other_indices = []

    for i, col in enumerate(columns):
        if col in ['510300.SH', '510500.SH', '513500.SH', '513300.SH', '510170.SH', '513100.SH']:
            stock_indices.append(i)
        elif col in ['511260.SH', '511090.SH', '511130.SH']:
            bond_indices.append(i)
        else:
            other_indices.append(i)

    # Combined objective function
    def combined_objective(weights):
        """Minimize: std(risk_contrib) + lambda * (-Sharpe) + environment_penalty"""
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)

        if portfolio_vol < 1e-10:
            return 1e10

        # Component 1: Risk parity (minimize std of risk contributions)
        marginal_contrib = cov_matrix @ weights
        risk_contrib = weights * marginal_contrib / portfolio_vol
        risk_parity_term = np.std(risk_contrib)

        # Component 2: Negative Sharpe (we minimize, so negate to maximize Sharpe)
        portfolio_return = weights @ expected_returns
        sharpe = portfolio_return / portfolio_vol if portfolio_vol > 1e-10 else 0
        sharpe_term = -sharpe

        # Component 3: Environment balance penalty
        env_penalty = 0.0
        if balance_environments:
            env_penalty = environment_balance_penalty(weights, cov_matrix, columns)

        # Weighted combination
        objective = (1 - lambda_sharpe) * risk_parity_term + lambda_sharpe * sharpe_term + 0.1 * env_penalty

        return objective

    # Constraints
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},  # Sum to 1
    ]

    # Add stock minimum constraint
    if stock_indices:
        constraints.append({
            'type': 'ineq',
            'fun': lambda w: np.sum([w[i] for i in stock_indices]) - min_stock_alloc
        })

    # Add bond maximum constraint
    if bond_indices:
        constraints.append({
            'type': 'ineq',
            'fun': lambda w: max_bond_alloc - np.sum([w[i] for i in bond_indices])
        })

    # Bounds: 0 <= weight <= 1
    bounds = tuple((0.0, 1.0) for _ in range(n_assets))

    # Initial guess
    x0 = np.ones(n_assets) / n_assets

    if stock_indices and bond_indices:
        for i in stock_indices:
            x0[i] = min_stock_alloc / len(stock_indices)
        for i in bond_indices:
            x0[i] = max_bond_alloc / len(bond_indices)

        remaining = 1.0 - (min_stock_alloc + max_bond_alloc)
        if other_indices and remaining > 0:
            for i in other_indices:
                x0[i] = remaining / len(other_indices)

    # Optimize
    result = minimize(
        combined_objective,
        x0=x0,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 1000, 'ftol': 1e-9}
    )

    if not result.success:
        print(f"⚠️  Optimization warning: {result.message}")
        # Fallback to constrained risk parity (no returns, no environment)
        return optimize_weights_constrained(returns, min_stock_alloc, max_bond_alloc)

    weights = result.x

    # Ensure weights are valid
    weights = np.maximum(weights, 0)
    weights = weights / weights.sum()

    return weights


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
