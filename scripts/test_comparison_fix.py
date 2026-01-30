"""
Test fix for AttributeError in comparison.print_comparison()
"""

import sys
sys.path.append('.')

from src.data_loader import load_prices
from src.comparison import VersionComparison

# Load data
prices = load_prices('data/etf_prices_7etf.csv')

# Create comparison
comparison = VersionComparison(
    prices=prices,
    initial_capital=1_000_000,
    start_date='2018-01-01',
    lookback=252,
    commission_rate=0.0003
)

# Run all versions
print("Running backtests for v1.0, v1.1, v1.2...\n")
comparison.run_all_versions(verbose=False)

# Test the fixed print_comparison method
print("\nTesting print_comparison() (should work now):")
print("-" * 70)
try:
    comparison_df = comparison.print_comparison()
    print("\n✅ SUCCESS: print_comparison() worked without errors")
    print(f"\nReturned DataFrame shape: {comparison_df.shape}")
except AttributeError as e:
    print(f"\n❌ FAILED: {e}")
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
