"""
Fetch ETF Data Using AkShare
=============================
AkShare (开源财经数据接口库) - Free, no registration needed
Install: pip install akshare
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 80)
print("FETCHING DATA FROM AKSHARE")
print("=" * 80)

# ETF codes (6-digit codes without exchange suffix)
etf_codes = {
    '510300': '沪深300ETF',
    '510500': '中证500ETF',
    '513500': '标普500ETF',
    '513300': '纳指ETF',
    '511260': '10年期国债ETF',
    '511090': '30年期国债ETF',
    '518880': '黄金ETF',
    '510170': '大宗商品ETF',
}

print("\nFetching data from AkShare...")
print("-" * 80)

prices_dict = {}

for code, name in etf_codes.items():
    print(f"\nFetching {code} ({name})...")

    try:
        # AkShare ETF historical data function
        # symbol: ETF code (6 digits)
        # period: 'daily'
        # start_date: 'YYYYMMDD' format
        # end_date: 'YYYYMMDD' format
        # adjust: 'qfq' (前复权, forward adjusted)

        df = ak.fund_etf_hist_em(
            symbol=code,
            period="daily",
            start_date="20150101",
            end_date=datetime.now().strftime("%Y%m%d"),
            adjust="qfq"  # 前复权
        )

        if df is not None and len(df) > 0:
            # AkShare returns columns: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
            # We need: 日期 (date) and 收盘 (close)

            # Rename and select columns
            df['date'] = pd.to_datetime(df['日期'])
            df['close'] = df['收盘'].astype(float)

            # Set date as index
            df = df.set_index('date')

            # Store close prices
            prices_dict[code] = df['close']

            print(f"  ✓ Success: {len(df)} days")
            print(f"    Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
            print(f"    First price: {df['close'].iloc[0]:.3f}")
            print(f"    Last price: {df['close'].iloc[-1]:.3f}")

        else:
            print(f"  ✗ No data returned")

    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

print(f"\n" + "=" * 80)
print(f"Successfully fetched: {len(prices_dict)}/8 ETFs")
print("=" * 80)

if len(prices_dict) == 0:
    print("\n❌ ERROR: No data fetched!")
    print("Possible issues:")
    print("  1. AkShare needs to be installed: pip install akshare")
    print("  2. ETF codes might be incorrect")
    print("  3. Network connection issues")
    exit(1)

# Combine into DataFrame
print("\nCombining data...")
prices = pd.DataFrame(prices_dict)

# Add .SH suffix to match strategy format
prices.columns = [f'{code}.SH' for code in prices.columns]

# Handle missing values
missing = prices.isnull().sum()
if missing.sum() > 0:
    print("\nMissing values detected:")
    print(missing[missing > 0])
    print("Forward filling...")
    prices = prices.ffill().bfill()

print(f"\n✓ Data ready!")
print(f"  Shape: {prices.shape}")
print(f"  Date range: {prices.index[0].strftime('%Y-%m-%d')} to {prices.index[-1].strftime('%Y-%m-%d')}")
print(f"  Missing values: {prices.isnull().sum().sum()}")

# Summary statistics
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

for col in prices.columns:
    code = col.replace('.SH', '')
    returns = prices[col].pct_change().dropna()
    total_return = (prices[col].iloc[-1] / prices[col].iloc[0] - 1) * 100
    ann_vol = returns.std() * np.sqrt(252) * 100

    print(f"\n{col} ({etf_codes[code]}):")
    print(f"  First: {prices[col].iloc[0]:.3f}")
    print(f"  Last: {prices[col].iloc[-1]:.3f}")
    print(f"  Total return: {total_return:.2f}%")
    print(f"  Ann. volatility: {ann_vol:.2f}%")

# Preview
print("\n" + "=" * 80)
print("DATA PREVIEW")
print("=" * 80)

print("\nFirst 5 rows:")
print(prices.head())

print("\nLast 5 rows:")
print(prices.tail())

# Save
output_file = 'etf_prices_akshare.csv'
prices.to_csv(output_file)

print("\n" + "=" * 80)
print("✅ SUCCESS")
print("=" * 80)

print(f"\n✓ Data saved to: {output_file}")
print(f"  ETFs: {len(prices.columns)}")
print(f"  Trading days: {len(prices)}")
print(f"  Date range: {prices.index[0].strftime('%Y-%m-%d')} to {prices.index[-1].strftime('%Y-%m-%d')}")

print("\nNext steps:")
print("1. Rename file to: etf_prices.csv")
print("2. Move to: all-weather/data/etf_prices.csv")
print("3. Ready for strategy implementation!")

print("\n" + "=" * 80)
