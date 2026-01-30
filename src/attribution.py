"""
Performance Attribution Module

Tools for decomposing portfolio returns and analyzing P&L sources.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple


def calculate_asset_attribution(
    returns: pd.DataFrame,
    weights: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate contribution of each asset to portfolio returns.

    For each period, contribution = weight * return

    Args:
        returns: DataFrame of asset returns (N x M)
        weights: DataFrame of asset weights (rebalance dates x M)

    Returns:
        DataFrame with cumulative contribution from each asset
    """
    # Align weights with returns (forward fill weights between rebalances)
    aligned_weights = weights.reindex(returns.index, method='ffill')

    # Calculate daily contribution from each asset
    contributions = aligned_weights.shift(1) * returns

    # Cumulative contribution
    cumulative_contrib = (1 + contributions).cumprod() - 1

    return cumulative_contrib


def calculate_period_attribution(
    equity_curve: pd.Series,
    frequency: str = 'Y'
) -> pd.DataFrame:
    """
    Break down returns by period (daily/monthly/annual).

    Args:
        equity_curve: Portfolio value over time
        frequency: Resampling frequency ('D', 'M', 'Y')

    Returns:
        DataFrame with period returns
    """
    # Resample to period frequency
    period_values = equity_curve.resample(frequency).last()

    # Calculate returns
    period_returns = period_values.pct_change().dropna()

    # Create summary
    summary = pd.DataFrame({
        'Period': period_values.index[1:].strftime('%Y-%m-%d' if frequency == 'Y' else '%Y-%m'),
        'Start Value': period_values.values[:-1],
        'End Value': period_values.values[1:],
        'Return': period_returns.values,
        'Return %': period_returns.values * 100
    })

    return summary


def detect_market_regime(
    prices: pd.DataFrame,
    method: str = 'volatility',
    window: int = 60
) -> pd.Series:
    """
    Classify each date into market regime.

    Methods:
    - 'volatility': High/Low volatility based on rolling std
    - 'trend': Bull/Bear based on rolling returns
    - 'combined': Combines both factors

    Args:
        prices: DataFrame of asset prices
        method: Classification method
        window: Rolling window for calculations

    Returns:
        Series with regime labels for each date
    """
    returns = prices.pct_change()

    if method == 'volatility':
        # Use rolling volatility of first asset (or average)
        rolling_vol = returns.iloc[:, 0].rolling(window).std() * np.sqrt(252)
        median_vol = rolling_vol.median()

        regimes = pd.Series('Stable', index=prices.index)
        regimes[rolling_vol > median_vol * 1.5] = 'High Volatility'
        regimes[rolling_vol < median_vol * 0.7] = 'Low Volatility'

    elif method == 'trend':
        # Use rolling returns
        rolling_ret = returns.mean(axis=1).rolling(window).mean()

        regimes = pd.Series('Stable', index=prices.index)
        regimes[rolling_ret > 0.001] = 'Bull Market'
        regimes[rolling_ret < -0.001] = 'Bear Market'

    elif method == 'combined':
        # Combine volatility and trend
        rolling_vol = returns.iloc[:, 0].rolling(window).std() * np.sqrt(252)
        rolling_ret = returns.mean(axis=1).rolling(window).mean()

        median_vol = rolling_vol.median()

        regimes = pd.Series('Stable', index=prices.index)

        # High volatility regimes
        high_vol = rolling_vol > median_vol * 1.5
        regimes[high_vol & (rolling_ret > 0)] = 'Volatile Bull'
        regimes[high_vol & (rolling_ret < 0)] = 'Volatile Bear'

        # Low volatility regimes
        low_vol = rolling_vol < median_vol * 0.7
        regimes[low_vol & (rolling_ret > 0)] = 'Calm Bull'
        regimes[low_vol & (rolling_ret < 0)] = 'Calm Bear'

    else:
        raise ValueError(f"Unknown method: {method}")

    return regimes


def rolling_metrics(
    returns: pd.Series,
    window: int = 252
) -> pd.DataFrame:
    """
    Calculate rolling performance metrics.

    Args:
        returns: Series of daily returns
        window: Rolling window size (252 = 1 year)

    Returns:
        DataFrame with rolling metrics
    """
    # Rolling return (annualized)
    rolling_return = returns.rolling(window).apply(
        lambda x: (1 + x).prod() ** (252 / len(x)) - 1 if len(x) > 0 else np.nan
    )

    # Rolling volatility (annualized)
    rolling_vol = returns.rolling(window).std() * np.sqrt(252)

    # Rolling Sharpe (assuming 3% risk-free rate)
    rolling_sharpe = (rolling_return - 0.03) / rolling_vol

    # Rolling max drawdown
    def calc_max_dd(rets):
        if len(rets) == 0:
            return np.nan
        cum = (1 + rets).cumprod()
        running_max = cum.expanding().max()
        dd = (cum - running_max) / running_max
        return dd.min()

    rolling_max_dd = returns.rolling(window).apply(calc_max_dd)

    # Combine into DataFrame
    result = pd.DataFrame({
        'return': rolling_return,
        'volatility': rolling_vol,
        'sharpe': rolling_sharpe,
        'max_drawdown': rolling_max_dd
    }, index=returns.index)

    return result


def decompose_volatility(
    returns: pd.DataFrame,
    weights: np.ndarray
) -> Dict:
    """
    Decompose portfolio volatility into asset contributions.

    Uses marginal contribution to variance (MCV) approach.

    Args:
        returns: DataFrame of asset returns
        weights: Array of asset weights

    Returns:
        Dictionary with:
        - total_variance: Total portfolio variance
        - total_volatility: Total portfolio volatility
        - marginal_contributions: MCV for each asset
        - risk_contributions: Risk contribution for each asset
        - risk_pct: Risk contribution as percentage
    """
    cov_matrix = returns.cov().values

    # Total portfolio variance
    portfolio_var = weights @ cov_matrix @ weights
    portfolio_vol = np.sqrt(portfolio_var)

    # Marginal contribution to variance
    mcv = cov_matrix @ weights

    # Risk contribution (absolute)
    risk_contrib = weights * mcv / portfolio_vol if portfolio_vol > 0 else np.zeros_like(weights)

    # Risk contribution (percentage)
    risk_pct = risk_contrib / risk_contrib.sum() * 100 if risk_contrib.sum() > 0 else np.zeros_like(weights)

    result = {
        'total_variance': portfolio_var,
        'total_volatility': portfolio_vol * np.sqrt(252),  # Annualized
        'marginal_contributions': mcv,
        'risk_contributions': risk_contrib,
        'risk_pct': risk_pct,
        'asset_names': list(returns.columns)
    }

    return result


def calculate_class_attribution(
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    asset_classes: Dict[str, list]
) -> pd.DataFrame:
    """
    Calculate attribution by asset class.

    Args:
        returns: DataFrame of asset returns
        weights: DataFrame of asset weights
        asset_classes: Dict mapping class names to ticker lists
                      e.g., {'Stocks': ['SPY', 'QQQ'], 'Bonds': ['TLT']}

    Returns:
        DataFrame with class-level contributions
    """
    # Align weights with returns
    aligned_weights = weights.reindex(returns.index, method='ffill')

    # Calculate contributions by class
    class_contributions = {}

    for class_name, tickers in asset_classes.items():
        # Filter to tickers in our universe
        valid_tickers = [t for t in tickers if t in returns.columns]

        if not valid_tickers:
            continue

        # Sum contributions from all assets in this class
        class_weight = aligned_weights[valid_tickers].sum(axis=1)
        class_return = returns[valid_tickers].mean(axis=1)  # Average return
        class_contrib = class_weight.shift(1) * class_return

        class_contributions[class_name] = class_contrib

    # Create DataFrame
    result = pd.DataFrame(class_contributions, index=returns.index)

    return result


def identify_significant_periods(
    equity_curve: pd.Series,
    threshold_pct: float = 5.0
) -> pd.DataFrame:
    """
    Identify periods with significant gains or losses.

    Args:
        equity_curve: Portfolio value over time
        threshold_pct: Threshold for significant move (default 5%)

    Returns:
        DataFrame with significant periods
    """
    returns = equity_curve.pct_change()

    # Find significant moves
    significant = returns[abs(returns) > threshold_pct / 100].copy()

    if len(significant) == 0:
        return pd.DataFrame()

    # Create summary
    summary = pd.DataFrame({
        'Date': significant.index,
        'Return %': significant.values * 100,
        'Value Before': equity_curve.loc[significant.index].shift(1).values,
        'Value After': equity_curve.loc[significant.index].values,
        'Change ($)': equity_curve.loc[significant.index].values - equity_curve.loc[significant.index].shift(1).values
    }).sort_values('Return %')

    return summary


def calculate_contribution_to_return(
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.Series:
    """
    Calculate each asset's total contribution to portfolio return over a period.

    Args:
        returns: DataFrame of asset returns
        weights: DataFrame of asset weights
        start_date: Start date for calculation (default: first date)
        end_date: End date for calculation (default: last date)

    Returns:
        Series with total contribution from each asset
    """
    # Filter dates if specified
    if start_date:
        returns = returns.loc[start_date:]
        weights = weights.loc[start_date:]
    if end_date:
        returns = returns.loc[:end_date]
        weights = weights.loc[:end_date]

    # Align weights with returns
    aligned_weights = weights.reindex(returns.index, method='ffill')

    # Calculate daily contribution
    daily_contrib = aligned_weights.shift(1) * returns

    # Sum over period
    total_contrib = daily_contrib.sum()

    return total_contrib.sort_values(ascending=False)


def calculate_annual_attribution(
    equity_curve: pd.Series,
    returns: pd.DataFrame,
    weights: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate annual performance attribution.

    Args:
        equity_curve: Portfolio value over time
        returns: Asset returns
        weights: Asset weights

    Returns:
        DataFrame with annual attribution by asset
    """
    years = equity_curve.index.year.unique()
    annual_data = []

    for year in years:
        # Filter data for this year
        year_mask = equity_curve.index.year == year

        if year_mask.sum() == 0:
            continue

        year_equity = equity_curve[year_mask]
        year_return = (year_equity.iloc[-1] / year_equity.iloc[0]) - 1

        # Calculate contributions
        year_returns = returns[year_mask]
        year_weights = weights[weights.index.year == year]

        if len(year_weights) == 0:
            continue

        aligned_weights = year_weights.reindex(year_returns.index, method='ffill')
        contrib = (aligned_weights.shift(1) * year_returns).sum()

        # Add to results
        result = {'Year': year, 'Portfolio Return': year_return}
        result.update(contrib.to_dict())

        annual_data.append(result)

    return pd.DataFrame(annual_data)
