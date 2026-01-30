"""
All Weather v1.0 Strategy for JoinQuant Platform

Pure risk parity implementation following Ray Dalio's All Weather principles.
Each asset contributes equally to portfolio risk.

Expected Performance (2018-2026 backtest):
- Annual Return: 7.05%
- Sharpe Ratio: 1.11
- Max Drawdown: -3.90%

Strategy Configuration:
- Universe: 7 A-share ETFs (stocks, bonds, gold)
- Rebalancing: Weekly (every Monday)
- Lookback: 252 trading days (1 year)
- Commission: 0.03%

Author: All Weather Project
Version: 1.0
Date: 2026-01-29
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


# ==============================================================================
# SECTION 1: EMBEDDED OPTIMIZER (from src/optimizer.py)
# ==============================================================================

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


# ==============================================================================
# SECTION 2: JOINQUANT STRATEGY
# ==============================================================================

def initialize(context):
    """
    Initialize All Weather v1.0 strategy.

    This function runs once at the start of the backtest/live trading.
    Sets up the ETF universe, strategy parameters, and schedules rebalancing.

    Args:
        context: JoinQuant context object containing strategy state
    """
    # ETF Universe (7 high-quality A-share ETFs)
    # Symbol mapping: .SH → .XSHG for JoinQuant platform
    context.securities = [
        '510300.XSHG',  # CSI 300 Index (Large-cap stocks)
        '510500.XSHG',  # CSI 500 Index (Mid-cap stocks)
        '513500.XSHG',  # S&P 500 (US stocks)
        '511260.XSHG',  # 10-Year Treasury Bond
        '518880.XSHG',  # Gold ETF
        '000066.XSHG',  # China Index Bond
        '513100.XSHG',  # Nasdaq-100 (US tech)
    ]

    # Strategy Parameters (optimized v1.0 configuration)
    context.lookback = 252              # 252 trading days = 1 year
    context.commission_rate = 0.0003    # 0.03% commission

    # State Tracking
    context.rebalance_count = 0         # Number of rebalances executed
    context.last_rebalance_date = None  # Last rebalance date for logging

    # Schedule weekly Monday rebalancing at market open
    # weekday: 1=Monday, 2=Tuesday, ..., 5=Friday
    run_weekly(rebalance, weekday=1, time='open')

    # Set commission rate for all orders
    set_order_cost(OrderCost(
        open_commission=context.commission_rate,
        close_commission=context.commission_rate,
        min_commission=0
    ), type='stock')

    log.info("=" * 60)
    log.info("All Weather v1.0 Strategy Initialized")
    log.info("=" * 60)
    log.info(f"Universe: {len(context.securities)} ETFs")
    log.info(f"Rebalancing: Weekly (Monday)")
    log.info(f"Lookback: {context.lookback} days")
    log.info(f"Commission: {context.commission_rate:.4%}")
    log.info("=" * 60)


def rebalance(context):
    """
    Execute weekly portfolio rebalancing.

    This function runs every Monday (or next trading day if holiday).
    Calculates risk parity weights based on historical returns and rebalances
    the portfolio to target allocations.

    Workflow:
    1. Fetch historical prices (253 days for 252-day returns)
    2. Calculate daily returns
    3. Validate data quality (length, NaNs)
    4. Optimize weights using pure risk parity
    5. Execute orders to achieve target weights
    6. Log rebalancing info

    Args:
        context: JoinQuant context object
    """
    current_date = context.current_dt.strftime('%Y-%m-%d')

    try:
        # Step 1: Fetch historical prices
        # Need lookback+1 days to calculate lookback returns via pct_change()
        # history() is the correct API for multiple securities in backtesting
        hist_prices = history(
            count=context.lookback + 1,  # 253 days
            unit='1d',
            field='close',
            security_list=context.securities,
            df=True,  # Return DataFrame with securities as columns
            skip_paused=False,  # Must be False for multiple securities (date alignment)
            fq='pre'  # Pre-adjusted for splits/dividends
        )

        # Validate we have a DataFrame with correct structure
        if not isinstance(hist_prices, pd.DataFrame):
            log.info(f"[{current_date}] Invalid price data type: {type(hist_prices)}. Skipping rebalance.")
            return

        if len(hist_prices.columns) != len(context.securities):
            log.info(f"[{current_date}] Price data has {len(hist_prices.columns)} securities, expected {len(context.securities)}. Skipping rebalance.")
            return

        # Step 2: Calculate returns
        # pct_change() drops first row, so we get exactly 252 days of returns
        returns = hist_prices.pct_change().dropna()

        # Step 3: Validate data quality
        if len(returns) < context.lookback:
            log.info(f"[{current_date}] Insufficient history: {len(returns)}/{context.lookback} days. Skipping rebalance.")
            return

        if returns.isnull().any().any():
            log.info(f"[{current_date}] NaN values in returns. Skipping rebalance.")
            return

        # Step 4: Optimize weights (pure risk parity)
        weights_array = optimize_weights(returns)
        weights_dict = dict(zip(context.securities, weights_array))

        # Step 5: Execute orders
        # Get current portfolio value for position sizing
        portfolio_value = context.portfolio.portfolio_value
        successful_orders = 0
        failed_orders = []

        for security, target_weight in weights_dict.items():
            target_value = portfolio_value * target_weight

            try:
                # Order to target value (JoinQuant handles current position automatically)
                order_target_value(security, target_value)
                successful_orders += 1
            except Exception as e:
                failed_orders.append(f"{security}: {str(e)}")

        # Step 6: Log rebalancing info
        context.rebalance_count += 1
        context.last_rebalance_date = current_date

        # Get top 3 weights for quick inspection
        sorted_weights = sorted(weights_dict.items(), key=lambda x: x[1], reverse=True)
        top_3 = ", ".join([f"{s.split('.')[0]}: {w:.1%}" for s, w in sorted_weights[:3]])

        log.info(f"[{current_date}] Rebalance #{context.rebalance_count} completed")
        log.info(f"  Orders: {successful_orders}/{len(context.securities)} successful")
        log.info(f"  Top 3: {top_3}")
        log.info(f"  Portfolio Value: ¥{portfolio_value:,.0f}")

        if failed_orders:
            log.info(f"  Failed Orders: {', '.join(failed_orders)}")

    except Exception as e:
        log.info(f"[{current_date}] Rebalance error: {str(e)}")
        log.info("  Keeping existing positions. Will retry next week.")


def handle_data(context, data):
    """
    Optional: Monitor portfolio on every bar (daily).

    This function runs on every trading day and can be used for:
    - Daily performance monitoring
    - Risk checks
    - Logging

    Currently: No action needed (weekly rebalancing only).

    Args:
        context: JoinQuant context object
        data: Current bar data for all securities
    """
    pass


# ==============================================================================
# IMPLEMENTATION NOTES
# ==============================================================================
#
# 1. Symbol Mapping:
#    Standalone (.SH) → JoinQuant (.XSHG)
#    510300.SH → 510300.XSHG
#
# 2. Data Access:
#    history() with df=True returns DataFrame directly
#    Rows=dates, Columns=securities, Values=close prices
#    Same structure as standalone load_prices()
#
# 3. Order Execution:
#    order_target_value() automatically handles:
#    - Current position (buys/sells to reach target)
#    - Commission calculation
#    - Order validation
#
# 4. Error Handling:
#    - Insufficient history: Skip rebalance
#    - NaN in returns: Skip rebalance
#    - Optimization failure: Use inverse volatility fallback (embedded)
#    - Order failure: Continue with other orders (partial rebalance)
#
# 5. Expected Performance (2018-2026):
#    - Annual Return: 7.05%
#    - Sharpe Ratio: 1.11
#    - Max Drawdown: -3.90%
#    - Turnover: ~4.2x annually
#    - Rebalances: ~420 (weekly for 8 years)
#
# 6. Risk Parity Result:
#    Typical allocation (bonds dominate for equal risk):
#    - Bonds: ~75-80% (low volatility requires high allocation)
#    - Stocks: ~15-20% (high volatility requires low allocation)
#    - Gold: ~3-5% (medium volatility)
#
#    This is CORRECT for true All Weather risk parity.
#
# ==============================================================================
