"""
Performance Metrics Module

Comprehensive performance calculations for portfolio analysis.
"""

import pandas as pd
import numpy as np
from typing import Union, Optional
from scipy import stats


def annual_return(returns: Union[pd.Series, np.ndarray], periods_per_year: int = 252) -> float:
    """
    Calculate annualized geometric return.

    Args:
        returns: Series or array of period returns
        periods_per_year: Number of periods in a year (252 for daily)

    Returns:
        Annualized return as decimal (e.g., 0.15 = 15%)
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        return 0.0

    total_return = (1 + returns).prod()
    n_periods = len(returns)
    ann_return = total_return ** (periods_per_year / n_periods) - 1

    return ann_return


def annual_volatility(returns: Union[pd.Series, np.ndarray], periods_per_year: int = 252) -> float:
    """
    Calculate annualized volatility (standard deviation).

    Args:
        returns: Series or array of period returns
        periods_per_year: Number of periods in a year (252 for daily)

    Returns:
        Annualized volatility as decimal
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        return 0.0

    return np.std(returns, ddof=1) * np.sqrt(periods_per_year)


def sharpe_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.03,
    periods_per_year: int = 252
) -> float:
    """
    Calculate Sharpe ratio.

    Sharpe Ratio = (Return - RiskFreeRate) / Volatility

    Args:
        returns: Series or array of period returns
        risk_free_rate: Annual risk-free rate (default 3%)
        periods_per_year: Number of periods in a year

    Returns:
        Sharpe ratio
    """
    ann_ret = annual_return(returns, periods_per_year)
    ann_vol = annual_volatility(returns, periods_per_year)

    if ann_vol == 0:
        return 0.0

    return (ann_ret - risk_free_rate) / ann_vol


def sortino_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.03,
    periods_per_year: int = 252
) -> float:
    """
    Calculate Sortino ratio (downside risk-adjusted return).

    Uses only downside volatility (negative returns) instead of total volatility.

    Args:
        returns: Series or array of period returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods in a year

    Returns:
        Sortino ratio
    """
    if isinstance(returns, pd.Series):
        returns_array = returns.values
    else:
        returns_array = returns

    ann_ret = annual_return(returns, periods_per_year)

    # Calculate downside deviation
    downside_returns = returns_array[returns_array < 0]

    if len(downside_returns) == 0:
        return np.inf  # No downside risk

    downside_vol = np.std(downside_returns, ddof=1) * np.sqrt(periods_per_year)

    if downside_vol == 0:
        return np.inf

    return (ann_ret - risk_free_rate) / downside_vol


def max_drawdown(equity_curve: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate maximum drawdown (peak to trough decline).

    Args:
        equity_curve: Series or array of portfolio values

    Returns:
        Maximum drawdown as negative decimal (e.g., -0.15 = -15%)
    """
    if isinstance(equity_curve, np.ndarray):
        equity_curve = pd.Series(equity_curve)

    if len(equity_curve) == 0:
        return 0.0

    # Calculate running maximum
    running_max = equity_curve.expanding().max()

    # Calculate drawdown at each point
    drawdown = (equity_curve - running_max) / running_max

    return drawdown.min()


def calmar_ratio(
    returns: Union[pd.Series, np.ndarray],
    equity_curve: Optional[Union[pd.Series, np.ndarray]] = None,
    periods_per_year: int = 252
) -> float:
    """
    Calculate Calmar ratio (return / max drawdown).

    Args:
        returns: Series or array of period returns
        equity_curve: Optional equity curve (will be calculated if not provided)
        periods_per_year: Number of periods in a year

    Returns:
        Calmar ratio
    """
    ann_ret = annual_return(returns, periods_per_year)

    if equity_curve is None:
        # Calculate equity curve from returns
        if isinstance(returns, np.ndarray):
            returns = pd.Series(returns)
        equity_curve = (1 + returns).cumprod()

    max_dd = abs(max_drawdown(equity_curve))

    if max_dd == 0:
        return np.inf

    return ann_ret / max_dd


def win_rate(returns: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate percentage of positive return periods.

    Args:
        returns: Series or array of period returns

    Returns:
        Win rate as decimal (e.g., 0.55 = 55%)
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        return 0.0

    return (returns > 0).sum() / len(returns)


def value_at_risk(returns: Union[pd.Series, np.ndarray], confidence: float = 0.95) -> float:
    """
    Calculate Value at Risk (VaR) at specified confidence level.

    VaR represents the maximum expected loss at a given confidence level.
    For example, VaR(95%) is the loss threshold where 95% of returns are better.

    Args:
        returns: Series or array of period returns
        confidence: Confidence level (default 0.95 for 95%)

    Returns:
        VaR as negative decimal (e.g., -0.05 means 5% loss at this confidence)
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        return 0.0

    return np.percentile(returns, (1 - confidence) * 100)


def conditional_var(returns: Union[pd.Series, np.ndarray], confidence: float = 0.95) -> float:
    """
    Calculate Conditional VaR (CVaR), also known as Expected Shortfall.

    CVaR is the expected loss given that the loss exceeds VaR.
    It's a more conservative risk measure than VaR as it considers tail risk.

    Args:
        returns: Series or array of period returns
        confidence: Confidence level (default 0.95 for 95%)

    Returns:
        CVaR as negative decimal (average of worst (1-confidence)% of returns)
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        return 0.0

    var = value_at_risk(returns, confidence)
    # Average of returns worse than VaR
    cvar = returns[returns <= var].mean()

    return cvar if not np.isnan(cvar) else var


def skewness(returns: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate skewness of return distribution.

    Skewness measures asymmetry:
    - Negative: more extreme losses than gains (bad for investors)
    - Zero: symmetric distribution
    - Positive: more extreme gains than losses (good for investors)

    Args:
        returns: Series or array of period returns

    Returns:
        Skewness coefficient
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) < 3:
        return 0.0

    return stats.skew(returns)


def kurtosis(returns: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate excess kurtosis of return distribution.

    Kurtosis measures tail heaviness:
    - Zero: normal distribution (Gaussian)
    - Positive: fat tails (more extreme events than normal)
    - Negative: thin tails (fewer extreme events than normal)

    Args:
        returns: Series or array of period returns

    Returns:
        Excess kurtosis (kurtosis - 3)
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) < 4:
        return 0.0

    # Fisher=True returns excess kurtosis (kurtosis - 3)
    return stats.kurtosis(returns, fisher=True)


def tail_ratio(returns: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate tail ratio (95th percentile / abs(5th percentile)).

    Measures asymmetry of extreme returns:
    - > 1: Larger positive extremes (good)
    - = 1: Symmetric extremes
    - < 1: Larger negative extremes (bad)

    Args:
        returns: Series or array of period returns

    Returns:
        Tail ratio
    """
    if isinstance(returns, pd.Series):
        returns = returns.values

    if len(returns) == 0:
        return 1.0

    p95 = np.percentile(returns, 95)
    p5 = np.percentile(returns, 5)

    if abs(p5) < 1e-10:
        return 1.0

    return abs(p95 / p5)


def calculate_tail_metrics(returns: Union[pd.Series, np.ndarray]) -> dict:
    """
    Calculate all tail risk metrics at once.

    Comprehensive tail risk analysis including VaR, CVaR, skewness,
    kurtosis, and tail ratio.

    Args:
        returns: Series or array of period returns

    Returns:
        Dictionary of tail risk metrics
    """
    return {
        'var_95': value_at_risk(returns, 0.95),
        'var_99': value_at_risk(returns, 0.99),
        'cvar_95': conditional_var(returns, 0.95),
        'cvar_99': conditional_var(returns, 0.99),
        'skewness': skewness(returns),
        'kurtosis': kurtosis(returns),
        'tail_ratio': tail_ratio(returns)
    }


def calculate_all_metrics(
    returns: Union[pd.Series, np.ndarray],
    equity_curve: Optional[Union[pd.Series, np.ndarray]] = None,
    risk_free_rate: float = 0.03,
    periods_per_year: int = 252
) -> dict:
    """
    Calculate all performance metrics at once.

    Args:
        returns: Series or array of period returns
        equity_curve: Optional equity curve
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods in a year

    Returns:
        Dictionary of all metrics
    """
    if equity_curve is None and isinstance(returns, pd.Series):
        equity_curve = (1 + returns).cumprod()
    elif equity_curve is None:
        equity_curve = np.cumprod(1 + returns)

    # Standard metrics
    metrics = {
        'annual_return': annual_return(returns, periods_per_year),
        'annual_volatility': annual_volatility(returns, periods_per_year),
        'sharpe_ratio': sharpe_ratio(returns, risk_free_rate, periods_per_year),
        'sortino_ratio': sortino_ratio(returns, risk_free_rate, periods_per_year),
        'max_drawdown': max_drawdown(equity_curve),
        'calmar_ratio': calmar_ratio(returns, equity_curve, periods_per_year),
        'win_rate': win_rate(returns)
    }

    # Add tail risk metrics
    tail_metrics = calculate_tail_metrics(returns)
    metrics.update(tail_metrics)

    return metrics


def format_metrics(metrics: dict) -> pd.DataFrame:
    """
    Format metrics dictionary as a nice DataFrame.

    Args:
        metrics: Dictionary of metrics from calculate_all_metrics

    Returns:
        Formatted DataFrame
    """
    formatted = {
        'Annual Return': f"{metrics['annual_return']:.2%}",
        'Annual Volatility': f"{metrics['annual_volatility']:.2%}",
        'Sharpe Ratio': f"{metrics['sharpe_ratio']:.2f}",
        'Sortino Ratio': f"{metrics['sortino_ratio']:.2f}",
        'Max Drawdown': f"{metrics['max_drawdown']:.2%}",
        'Calmar Ratio': f"{metrics['calmar_ratio']:.2f}",
        'Win Rate': f"{metrics['win_rate']:.2%}",
        'VaR (95%)': f"{metrics['var_95']:.2%}",
        'VaR (99%)': f"{metrics['var_99']:.2%}",
        'CVaR (95%)': f"{metrics['cvar_95']:.2%}",
        'CVaR (99%)': f"{metrics['cvar_99']:.2%}",
        'Skewness': f"{metrics['skewness']:.2f}",
        'Kurtosis': f"{metrics['kurtosis']:.2f}",
        'Tail Ratio': f"{metrics['tail_ratio']:.2f}"
    }

    return pd.DataFrame.from_dict(formatted, orient='index', columns=['Value'])
