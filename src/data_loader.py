"""
Data Loading Utilities

Functions for loading and preprocessing ETF price data.
"""

import pandas as pd
import numpy as np
from typing import Optional, List


def load_prices(
    filepath: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load ETF price data from CSV file.

    Args:
        filepath: Path to CSV file
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        columns: Optional list of columns to keep

    Returns:
        DataFrame with datetime index and ETF price columns
    """
    prices = pd.read_csv(filepath, index_col=0, parse_dates=True)

    # Filter by date range
    if start_date:
        prices = prices.loc[start_date:]
    if end_date:
        prices = prices.loc[:end_date]

    # Filter by columns
    if columns:
        prices = prices[columns]

    return prices


def check_data_quality(prices: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Check data quality and return summary statistics.

    Args:
        prices: DataFrame of ETF prices
        verbose: Print summary to console

    Returns:
        DataFrame with quality metrics per asset
    """
    quality_metrics = []

    for col in prices.columns:
        data = prices[col]
        returns = data.pct_change().dropna()

        metrics = {
            'asset': col,
            'start_date': data.index[0],
            'end_date': data.index[-1],
            'total_days': len(data),
            'missing_pct': (data.isnull().sum() / len(data) * 100),
            'zero_returns_pct': ((returns == 0).sum() / len(returns) * 100),
            'mean_return': returns.mean(),
            'volatility': returns.std(),
        }
        quality_metrics.append(metrics)

    quality_df = pd.DataFrame(quality_metrics)

    if verbose:
        print("\nData Quality Report:")
        print("=" * 80)
        for _, row in quality_df.iterrows():
            print(f"\n{row['asset']}:")
            print(f"  Period: {row['start_date'].date()} to {row['end_date'].date()}")
            print(f"  Days: {row['total_days']}")
            print(f"  Missing: {row['missing_pct']:.2f}%")
            print(f"  Zero returns: {row['zero_returns_pct']:.2f}%")
            print(f"  Mean daily return: {row['mean_return']:.4f}")
            print(f"  Daily volatility: {row['volatility']:.4f}")

    return quality_df


def preprocess_prices(
    prices: pd.DataFrame,
    forward_fill: bool = True,
    drop_missing: bool = False
) -> pd.DataFrame:
    """
    Preprocess price data.

    Args:
        prices: DataFrame of ETF prices
        forward_fill: Forward fill missing values
        drop_missing: Drop rows with any missing values

    Returns:
        Preprocessed DataFrame
    """
    prices = prices.copy()

    if forward_fill:
        prices = prices.fillna(method='ffill')

    if drop_missing:
        prices = prices.dropna()

    return prices


def align_dates(*dfs: pd.DataFrame) -> List[pd.DataFrame]:
    """
    Align multiple dataframes to common date range.

    Args:
        *dfs: Variable number of DataFrames to align

    Returns:
        List of aligned DataFrames
    """
    # Find common date range
    start_date = max(df.index[0] for df in dfs)
    end_date = min(df.index[-1] for df in dfs)

    # Align all dataframes
    aligned = [df.loc[start_date:end_date] for df in dfs]

    return aligned


def calculate_returns(
    prices: pd.DataFrame,
    method: str = 'simple'
) -> pd.DataFrame:
    """
    Calculate returns from prices.

    Args:
        prices: DataFrame of ETF prices
        method: 'simple' for arithmetic or 'log' for logarithmic returns

    Returns:
        DataFrame of returns
    """
    if method == 'simple':
        returns = prices.pct_change()
    elif method == 'log':
        returns = np.log(prices / prices.shift(1))
    else:
        raise ValueError(f"Unknown method: {method}")

    return returns.dropna()
