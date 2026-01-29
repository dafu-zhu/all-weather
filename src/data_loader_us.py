"""
US Market Data Loader using yfinance

Fetches historical price data for US ETFs.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Optional, Dict
from datetime import datetime, timedelta


def download_us_etfs(
    tickers: List[str],
    start_date: str = '2015-01-01',
    end_date: Optional[str] = None,
    progress: bool = True
) -> pd.DataFrame:
    """
    Download US ETF price data using yfinance.

    Args:
        tickers: List of ticker symbols (e.g., ['SPY', 'TLT', 'GLD'])
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format (default: today)
        progress: Show download progress

    Returns:
        DataFrame with adjusted close prices (dates × tickers)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"Downloading {len(tickers)} US ETFs from yfinance...")
    print(f"Period: {start_date} to {end_date}")
    print(f"Tickers: {', '.join(tickers)}")

    # Download data (auto_adjust=False to get 'Adj Close' column)
    data = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        progress=progress,
        auto_adjust=False
    )

    # Extract adjusted close prices
    if len(tickers) == 1:
        prices = data['Adj Close'].to_frame()
        prices.columns = tickers
    else:
        # yfinance returns MultiIndex: (price_type, ticker)
        prices = data['Adj Close'].copy()

    # Remove timezone info if present
    if prices.index.tz is not None:
        prices.index = prices.index.tz_localize(None)

    # Drop any rows with all NaN
    prices = prices.dropna(how='all')

    print(f"\n✓ Downloaded {len(prices)} days of data")
    print(f"  Date range: {prices.index[0].date()} to {prices.index[-1].date()}")

    return prices


def get_all_weather_us_etfs() -> Dict[str, Dict[str, str]]:
    """
    Get default US ETF universe for All Weather strategy.

    Returns:
        Dictionary with ETF info:
        {
            'ticker': {
                'name': 'Full name',
                'asset_class': 'Stocks/Bonds/Commodities',
                'description': 'Brief description'
            }
        }
    """
    return {
        'SPY': {
            'name': 'SPDR S&P 500 ETF',
            'asset_class': 'Stocks',
            'description': 'US large-cap stocks (S&P 500)'
        },
        'QQQ': {
            'name': 'Invesco QQQ Trust',
            'asset_class': 'Stocks',
            'description': 'US tech stocks (Nasdaq-100)'
        },
        'IWM': {
            'name': 'iShares Russell 2000 ETF',
            'asset_class': 'Stocks',
            'description': 'US small-cap stocks'
        },
        'TLT': {
            'name': 'iShares 20+ Year Treasury Bond ETF',
            'asset_class': 'Bonds',
            'description': 'Long-term US Treasury bonds'
        },
        'IEF': {
            'name': 'iShares 7-10 Year Treasury Bond ETF',
            'asset_class': 'Bonds',
            'description': 'Intermediate-term US Treasury bonds'
        },
        'TIP': {
            'name': 'iShares TIPS Bond ETF',
            'asset_class': 'Bonds',
            'description': 'Inflation-protected Treasury bonds'
        },
        'GLD': {
            'name': 'SPDR Gold Shares',
            'asset_class': 'Commodities',
            'description': 'Physical gold'
        },
        'DBC': {
            'name': 'Invesco DB Commodity Index Tracking Fund',
            'asset_class': 'Commodities',
            'description': 'Broad commodity index'
        }
    }


def check_us_data_quality(prices: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Check data quality for US ETF data.

    Args:
        prices: DataFrame of ETF prices
        verbose: Print detailed report

    Returns:
        DataFrame with quality metrics per ETF
    """
    quality_metrics = []

    for ticker in prices.columns:
        data = prices[ticker]
        returns = data.pct_change().dropna()

        metrics = {
            'ticker': ticker,
            'start_date': data.index[0],
            'end_date': data.index[-1],
            'total_days': len(data),
            'missing_pct': (data.isnull().sum() / len(data) * 100),
            'zero_returns_pct': ((returns == 0).sum() / len(returns) * 100),
            'mean_return': returns.mean(),
            'volatility': returns.std(),
            'min_price': data.min(),
            'max_price': data.max(),
            'latest_price': data.iloc[-1]
        }
        quality_metrics.append(metrics)

    quality_df = pd.DataFrame(quality_metrics)

    if verbose:
        print("\n" + "="*80)
        print("US ETF DATA QUALITY REPORT")
        print("="*80)

        for _, row in quality_df.iterrows():
            print(f"\n{row['ticker']}:")
            print(f"  Period: {row['start_date'].date()} to {row['end_date'].date()}")
            print(f"  Days: {row['total_days']}")
            print(f"  Missing: {row['missing_pct']:.2f}%")
            print(f"  Zero returns: {row['zero_returns_pct']:.2f}%")
            print(f"  Mean daily return: {row['mean_return']:.4f}")
            print(f"  Daily volatility: {row['volatility']:.4f}")
            print(f"  Price range: ${row['min_price']:.2f} - ${row['max_price']:.2f}")
            print(f"  Latest price: ${row['latest_price']:.2f}")

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total ETFs: {len(quality_df)}")
        print(f"Avg missing data: {quality_df['missing_pct'].mean():.2f}%")
        print(f"Avg zero returns: {quality_df['zero_returns_pct'].mean():.2f}%")

        # Flag issues
        issues = []
        if (quality_df['missing_pct'] > 1.0).any():
            issues.append("⚠️  Some ETFs have >1% missing data")
        if (quality_df['zero_returns_pct'] > 5.0).any():
            issues.append("⚠️  Some ETFs have >5% zero returns")

        if issues:
            print("\nIssues detected:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✓ All ETFs pass quality checks")

    return quality_df


def save_us_data(prices: pd.DataFrame, filepath: str = 'data/us_etf_prices.csv'):
    """
    Save US ETF data to CSV.

    Args:
        prices: DataFrame of ETF prices
        filepath: Output file path
    """
    prices.to_csv(filepath)
    print(f"\n✓ Saved data to {filepath}")
    print(f"  Shape: {prices.shape}")
    print(f"  Size: {prices.memory_usage(deep=True).sum() / 1024:.1f} KB")


def load_us_data(filepath: str = 'data/us_etf_prices.csv') -> pd.DataFrame:
    """
    Load US ETF data from CSV.

    Args:
        filepath: Input file path

    Returns:
        DataFrame of ETF prices
    """
    prices = pd.read_csv(filepath, index_col=0, parse_dates=True)
    print(f"✓ Loaded US data from {filepath}")
    print(f"  Shape: {prices.shape}")
    print(f"  Period: {prices.index[0].date()} to {prices.index[-1].date()}")
    return prices
