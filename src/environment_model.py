"""
Economic Environment Framework

Implements Bridgewater's 4-quadrant economic model:
- Growth Rising / Inflation Rising (Growth+ / Inflation+)
- Growth Rising / Inflation Falling (Growth+ / Inflation-)
- Growth Falling / Inflation Rising (Growth- / Inflation+)
- Growth Falling / Inflation Falling (Growth- / Inflation-)

Each environment should contribute ~25% of portfolio risk for true balance.
"""

import numpy as np
import pandas as pd
from typing import Dict, List


# Asset-to-environment mapping for 7-ETF universe
ASSET_ENVIRONMENTS = {
    # Stocks perform well in Growth Rising
    '510300.SH': 'growth_rising',      # CSI 300
    '510500.SH': 'growth_rising',      # CSI 500
    '513500.SH': 'growth_rising',      # S&P 500
    '513100.SH': 'growth_rising',      # Nasdaq 100

    # Bonds perform well in Growth Falling (deflation)
    '511260.SH': 'growth_falling',     # 10-year Treasury

    # Gold performs well in Inflation Rising
    '518880.SH': 'inflation_rising',   # Gold

    # Commodity index performs well in Inflation Rising
    '000066.SH': 'inflation_rising',   # Commodity Index
}

# Canonical environment names
ENVIRONMENTS = [
    'growth_rising',      # Growth+ / Inflation- (stocks thrive)
    'growth_falling',     # Growth- / Inflation- (bonds, deflation)
    'inflation_rising',   # Growth- / Inflation+ (commodities, gold)
    # Note: We don't have assets for Growth+ / Inflation+ (growth stocks in inflation)
]


def get_environment_indices(asset_codes: List[str]) -> Dict[str, List[int]]:
    """
    Map asset codes to environment indices.

    Args:
        asset_codes: List of asset ticker codes

    Returns:
        Dictionary mapping environment name to list of asset indices
    """
    env_indices = {env: [] for env in ENVIRONMENTS}

    for i, code in enumerate(asset_codes):
        env = ASSET_ENVIRONMENTS.get(code)
        if env and env in env_indices:
            env_indices[env].append(i)

    return env_indices


def calculate_environment_risk_contributions(
    weights: np.ndarray,
    cov_matrix: np.ndarray,
    asset_codes: List[str]
) -> Dict[str, float]:
    """
    Calculate risk contribution by economic environment.

    Args:
        weights: Asset weights
        cov_matrix: Asset covariance matrix
        asset_codes: List of asset ticker codes

    Returns:
        Dictionary mapping environment to its risk contribution percentage
    """
    # Calculate portfolio volatility
    portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)

    if portfolio_vol < 1e-10:
        return {env: 0.0 for env in ENVIRONMENTS}

    # Calculate marginal contributions
    marginal_contrib = cov_matrix @ weights

    # Map assets to environments
    env_indices = get_environment_indices(asset_codes)

    # Sum risk contributions by environment
    env_risk_contrib = {}
    for env, indices in env_indices.items():
        if not indices:
            env_risk_contrib[env] = 0.0
            continue

        # Sum risk contribution for all assets in this environment
        env_rc = sum(weights[i] * marginal_contrib[i] for i in indices)
        env_risk_contrib[env] = env_rc / portfolio_vol

    return env_risk_contrib


def environment_balance_penalty(
    weights: np.ndarray,
    cov_matrix: np.ndarray,
    asset_codes: List[str],
    target_contribution: float = 0.25
) -> float:
    """
    Calculate penalty for unbalanced environment risk contributions.

    Ideally, each environment should contribute ~25% of risk.
    This penalty increases as environment contributions deviate from target.

    Args:
        weights: Asset weights
        cov_matrix: Asset covariance matrix
        asset_codes: List of asset ticker codes
        target_contribution: Target risk contribution per environment (default 0.25 = 25%)

    Returns:
        Penalty value (higher = more unbalanced)
    """
    env_risk = calculate_environment_risk_contributions(weights, cov_matrix, asset_codes)

    # Calculate squared deviations from target
    # We only penalize environments that have assets
    active_envs = [env for env, rc in env_risk.items() if rc > 0]

    if not active_envs:
        return 0.0

    # Adjust target if we don't have all 4 environments
    adjusted_target = 1.0 / len(active_envs)

    deviations = [(rc - adjusted_target) ** 2 for rc in env_risk.values() if rc > 0]

    return np.sqrt(np.mean(deviations))


def validate_environment_balance(
    weights: np.ndarray,
    cov_matrix: np.ndarray,
    asset_codes: List[str],
    tolerance: float = 0.10
) -> tuple[bool, Dict[str, float]]:
    """
    Validate that environment risk contributions are reasonably balanced.

    Args:
        weights: Asset weights
        cov_matrix: Asset covariance matrix
        asset_codes: List of asset ticker codes
        tolerance: Maximum acceptable deviation from equal contribution (default 10%)

    Returns:
        Tuple of (is_balanced, environment_contributions)
    """
    env_risk = calculate_environment_risk_contributions(weights, cov_matrix, asset_codes)

    # Check if active environments are reasonably balanced
    active_contribs = [rc for rc in env_risk.values() if rc > 0]

    if not active_contribs:
        return False, env_risk

    target = 1.0 / len(active_contribs)
    max_deviation = max(abs(rc - target) for rc in active_contribs)

    is_balanced = max_deviation <= tolerance

    return is_balanced, env_risk
