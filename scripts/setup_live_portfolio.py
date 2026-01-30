"""
Helper script to set up initial positions for live portfolio tracking.

Run this script to input your initial positions, then it will update the notebook.
"""

import sys
sys.path.append('.')

def get_initial_positions():
    """Interactive input for initial positions."""
    print("="*70)
    print("LIVE PORTFOLIO SETUP - Initial Positions")
    print("="*70)
    print("\nEnter your current holdings as of January 29, 2026:")
    print("(Press Enter to skip an ETF if you don't own it)\n")

    etfs = {
        '510300.SH': 'CSI 300 (Large cap stocks)',
        '510500.SH': 'CSI 500 (Mid/small cap stocks)',
        '513500.SH': 'S&P 500',
        '511260.SH': '10Y Treasury (trades in 100s)',
        '518880.SH': 'Gold',
        '000066.SH': 'China Index',
        '513100.SH': 'Nasdaq-100'
    }

    positions = {}

    for etf, description in etfs.items():
        while True:
            try:
                shares_input = input(f"{etf} ({description}): ")
                if shares_input.strip() == '':
                    positions[etf] = 0
                    break
                shares = float(shares_input.replace(',', ''))
                positions[etf] = int(shares)
                break
            except ValueError:
                print("  Invalid input. Please enter a number.")

    while True:
        try:
            cash_input = input("\nCash balance (CNY): ")
            if cash_input.strip() == '':
                cash = 0
                break
            cash = float(cash_input.replace(',', ''))
            break
        except ValueError:
            print("  Invalid input. Please enter a number.")

    return positions, cash

def display_positions(positions, cash):
    """Display entered positions for confirmation."""
    print("\n" + "="*70)
    print("CONFIRMATION - Your Initial Positions")
    print("="*70)

    total_shares = sum(positions.values())

    for etf, shares in positions.items():
        if shares > 0:
            print(f"  {etf}: {shares:>10,} shares")

    print(f"\n  Cash: ¥{cash:>10,.2f}")
    print(f"\n  Total positions: {total_shares:,} shares across {sum(1 for s in positions.values() if s > 0)} ETFs")

def update_notebook(positions, cash):
    """Update the live_portfolio_tracker notebook with initial positions."""
    import json

    notebook_path = 'notebooks/live_portfolio_tracker.ipynb'

    # Read notebook
    with open(notebook_path, 'r') as f:
        nb = json.load(f)

    # Find the cell with INITIAL_POSITIONS (should be cell index 2)
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code' and 'INITIAL_POSITIONS' in cell.get('source', ''):
            # Build new source
            new_source = []
            new_source.append("# ========== EDIT YOUR INITIAL POSITIONS HERE ==========\\n")
            new_source.append("# Initial position as of January 29, 2026\\n")
            new_source.append("INITIAL_POSITIONS = {\\n")

            for etf, shares in positions.items():
                comment = {
                    '510300.SH': 'CSI 300 - Large cap stocks',
                    '510500.SH': 'CSI 500 - Mid/small cap stocks',
                    '513500.SH': 'S&P 500',
                    '511260.SH': '10Y Treasury (trades in 100s)',
                    '518880.SH': 'Gold',
                    '000066.SH': 'China Index',
                    '513100.SH': 'Nasdaq-100'
                }.get(etf, '')
                new_source.append(f"    '{etf}': {shares},")
                if comment:
                    new_source.append(f"      # {comment}\\n")
                else:
                    new_source.append("\\n")

            new_source.append("}\\n")
            new_source.append("\\n")
            new_source.append(f"INITIAL_CASH = {cash}  # Remaining cash in CNY\\n")
            new_source.append("# ======================================================\\n")
            new_source.append("\\n")
            new_source.append("# Strategy parameters\\n")
            new_source.append("START_DATE = '2026-01-29'\\n")
            new_source.append("LOOKBACK = 252  # Days for covariance calculation\\n")
            new_source.append("REBALANCE_THRESHOLD = 0.05  # 5% drift triggers rebalance\\n")
            new_source.append("COMMISSION_RATE = 0.0003  # 0.03%\\n")
            new_source.append("\\n")
            new_source.append("# Chicago timezone\\n")
            new_source.append("CHICAGO_TZ = pytz.timezone('America/Chicago')\\n")
            new_source.append("TODAY_CHICAGO = datetime.now(CHICAGO_TZ)\\n")
            new_source.append("\\n")
            new_source.append("print(f\\\"Current Time (Chicago): {TODAY_CHICAGO.strftime('%Y-%m-%d %H:%M:%S %Z')}\\\")\\n")
            new_source.append("print(f\\\"\\\\nInitial Positions (as of {START_DATE}):\\\")\\n")
            new_source.append("for etf, shares in INITIAL_POSITIONS.items():\\n")
            new_source.append("    print(f\\\"  {etf}: {shares:,.0f} shares\\\")\\n")
            new_source.append("print(f\\\"  Cash: {format_currency(INITIAL_CASH)}\\\")")

            cell['source'] = ''.join(new_source)
            break

    # Write back
    with open(notebook_path, 'w') as f:
        json.dump(nb, f, indent=1)

    print(f"\n✓ Notebook updated: {notebook_path}")

if __name__ == '__main__':
    print("\n")

    # Get positions
    positions, cash = get_initial_positions()

    # Display for confirmation
    display_positions(positions, cash)

    # Confirm
    confirm = input("\nIs this correct? (yes/no): ").strip().lower()

    if confirm in ['yes', 'y']:
        update_notebook(positions, cash)
        print("\n" + "="*70)
        print("✓ Setup complete!")
        print("="*70)
        print("\nNext steps:")
        print("1. Open: notebooks/live_portfolio_tracker.ipynb")
        print("2. Run all cells to see your portfolio status")
        print("3. Check 'Required Trades' section for rebalancing actions")
        print("\n" + "="*70)
    else:
        print("\nSetup cancelled. Run this script again to re-enter positions.")
