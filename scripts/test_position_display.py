"""
Test the position display section of the comparison notebook
"""

import sys
sys.path.append('.')

import pandas as pd
from src.data_loader import load_prices
from src.comparison import VersionComparison
from src.utils.reporting import print_section

def calculate_average_entry_price(portfolio, etf):
    """Calculate average entry price for an ETF from trade history."""
    buy_trades = [t for t in portfolio.trade_history if t.etf == etf and t.side == 'buy']

    if not buy_trades:
        return 0.0

    total_cost = sum(t.shares * t.price for t in buy_trades)
    total_shares = sum(t.shares for t in buy_trades)

    return total_cost / total_shares if total_shares > 0 else 0.0

# Load data
prices = load_prices('data/etf_prices_7etf.csv')

# Create comparison and run backtests
comparison = VersionComparison(
    prices=prices,
    initial_capital=1_000_000,
    start_date='2018-01-01',
    lookback=252,
    commission_rate=0.0003
)

print("Running backtests...")
comparison.run_all_versions(verbose=False)

results = comparison.results
versions = list(results.keys())
final_prices = prices.iloc[-1]

print_section("Current Portfolio Positions (as of latest rebalance)")

for version in versions:
    strategy = comparison.strategies[version]
    portfolio = strategy.portfolio
    weights_history = results[version]['weights_history']

    # Get latest rebalance date
    if not weights_history.empty:
        latest_rebalance = weights_history.index[-1]
        print(f"\n{'='*70}")
        print(f"{version.upper()} - Latest Rebalance: {latest_rebalance.date()}")
        print(f"{'='*70}")

        # Get positions at final date
        positions = portfolio.get_positions()
        weights = portfolio.get_weights(final_prices)
        total_value = portfolio.get_value(final_prices)

        # Build position table
        position_data = []
        for etf in sorted(positions.keys()):
            shares = positions[etf]
            if shares > 0:  # Only show non-zero positions
                current_price = final_prices[etf]
                market_value = shares * current_price
                weight = weights[etf]
                avg_entry_price = calculate_average_entry_price(portfolio, etf)

                position_data.append({
                    'ETF': etf,
                    'Shares': shares,
                    'Avg Entry Price': avg_entry_price,
                    'Current Price': current_price,
                    'Market Value': market_value,
                    'Weight (%)': weight * 100,
                    'Unrealized P&L': (current_price - avg_entry_price) * shares
                })

        # Create and display DataFrame
        if position_data:
            df = pd.DataFrame(position_data)
            df = df.set_index('ETF')

            # Format for display
            df_display = df.copy()
            df_display['Shares'] = df_display['Shares'].apply(lambda x: f'{x:,.0f}')
            df_display['Avg Entry Price'] = df_display['Avg Entry Price'].apply(lambda x: f'¥{x:.4f}')
            df_display['Current Price'] = df_display['Current Price'].apply(lambda x: f'¥{x:.4f}')
            df_display['Market Value'] = df_display['Market Value'].apply(lambda x: f'¥{x:,.0f}')
            df_display['Weight (%)'] = df_display['Weight (%)'].apply(lambda x: f'{x:.2f}%')
            df_display['Unrealized P&L'] = df_display['Unrealized P&L'].apply(
                lambda x: f'¥{x:+,.0f}' if x != 0 else '¥0'
            )

            print("\nPositions:")
            print(df_display.to_string())

            # Summary statistics
            print(f"\nPortfolio Summary:")
            print(f"  Total Market Value: ¥{total_value:,.0f}")
            print(f"  Cash: ¥{portfolio.cash:,.0f}")
            print(f"  Total Unrealized P&L: ¥{df['Unrealized P&L'].sum():+,.0f}")
            print(f"  Number of Positions: {len(position_data)}")
        else:
            print("\n  No positions found (likely before first rebalance)")
    else:
        print(f"\n{version.upper()}: No rebalancing history")

print("\n" + "="*70)
print("✅ Position display test completed successfully")
print("="*70)
