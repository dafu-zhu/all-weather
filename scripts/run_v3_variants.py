"""
Test v3.0 Variants to Isolate Issues

Test different combinations of v3.0 features to identify what's causing underperformance.
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('.')

from src.strategy import AllWeatherV2, AllWeatherV3

print("="*80)
print("ALL WEATHER v3.0 - VARIANT TESTING")
print("="*80)

# Load data
prices = pd.read_csv('data/etf_prices_7etf.csv', index_col=0, parse_dates=True)

# Base config
base_config = {
    'initial_capital': 1_000_000,
    'rebalance_freq': 'MS',
    'lookback': 100,
    'commission_rate': 0.0003,
    'min_stock_alloc': 0.60,
    'max_bond_alloc': 0.35,
}

# Test variants
variants = {
    'v2.0 Baseline': {
        'class': AllWeatherV2,
        'config': base_config
    },
    'v3.0 Full (All Features)': {
        'class': AllWeatherV3,
        'config': {
            **base_config,
            'target_volatility': 0.10,
            'balance_environments': True,
            'use_return_expectations': True,
            'use_depression_gauge': True,
            'lambda_sharpe': 0.5,
        }
    },
    'v3.0 No Crisis': {
        'class': AllWeatherV3,
        'config': {
            **base_config,
            'target_volatility': 0.10,
            'balance_environments': True,
            'use_return_expectations': True,
            'use_depression_gauge': False,  # DISABLE
            'lambda_sharpe': 0.5,
        }
    },
    'v3.0 No Vol Target': {
        'class': AllWeatherV3,
        'config': {
            **base_config,
            'target_volatility': 0.10,
            'balance_environments': True,
            'use_return_expectations': True,
            'use_depression_gauge': False,
            'lambda_sharpe': 0.5,
        }
    },
    'v3.0 Only Return Opt': {
        'class': AllWeatherV3,
        'config': {
            **base_config,
            'target_volatility': 0.10,
            'balance_environments': False,  # DISABLE
            'use_return_expectations': True,  # ENABLE
            'use_depression_gauge': False,  # DISABLE
            'lambda_sharpe': 0.5,
        }
    },
    'v3.0 Only Environment': {
        'class': AllWeatherV3,
        'config': {
            **base_config,
            'target_volatility': 0.10,
            'balance_environments': True,  # ENABLE
            'use_return_expectations': False,  # DISABLE
            'use_depression_gauge': False,  # DISABLE
            'lambda_sharpe': 0.5,
        }
    },
}

# Run all variants
results_summary = []

for name, variant in variants.items():
    print(f"\nRunning: {name}...")

    strategy_class = variant['class']
    config = variant['config']

    strategy = strategy_class(prices=prices, **config)
    results = strategy.run_backtest(start_date='2018-01-01', verbose=False)

    metrics = results['metrics']

    results_summary.append({
        'Variant': name,
        'Annual Return': metrics['annual_return'],
        'Sharpe Ratio': metrics['sharpe_ratio'],
        'Max Drawdown': metrics['max_drawdown'],
        'Volatility': metrics['annual_volatility'],
        'Final Value': results['final_value']
    })

# Display comparison
print("\n" + "="*80)
print("VARIANT COMPARISON")
print("="*80)

df = pd.DataFrame(results_summary)

print(f"\n{'Variant':<30s} {'Return':>10s} {'Sharpe':>8s} {'Max DD':>10s} {'Vol':>8s}")
print("-"*80)

for _, row in df.iterrows():
    print(f"{row['Variant']:<30s} {row['Annual Return']:>9.2%} {row['Sharpe Ratio']:>8.2f} "
          f"{row['Max Drawdown']:>9.2%} {row['Volatility']:>8.2%}")

# Identify best variant
print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

baseline = df[df['Variant'] == 'v2.0 Baseline'].iloc[0]

print(f"\nv2.0 Baseline: {baseline['Annual Return']:.2%} return, {baseline['Sharpe Ratio']:.2f} Sharpe")
print(f"\nVariant Performance vs v2.0:")

for _, row in df.iterrows():
    if row['Variant'] == 'v2.0 Baseline':
        continue

    return_diff = (row['Annual Return'] - baseline['Annual Return']) * 100
    sharpe_diff = row['Sharpe Ratio'] - baseline['Sharpe Ratio']

    status = "✅" if return_diff > 0 and sharpe_diff > 0 else "❌"

    print(f"\n{status} {row['Variant']}")
    print(f"   Return: {return_diff:+.2f}pp, Sharpe: {sharpe_diff:+.2f}")

# Recommendations
print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

best_sharpe = df.loc[df['Sharpe Ratio'].idxmax()]
best_return = df.loc[df['Annual Return'].idxmax()]

print(f"\nBest Sharpe Ratio: {best_sharpe['Variant']}")
print(f"  • {best_sharpe['Sharpe Ratio']:.2f} Sharpe, {best_sharpe['Annual Return']:.2%} return")

print(f"\nBest Return: {best_return['Variant']}")
print(f"  • {best_return['Annual Return']:.2%} return, {best_return['Sharpe Ratio']:.2f} Sharpe")

# Find which features help
improvements = df[df['Sharpe Ratio'] > baseline['Sharpe Ratio']]

if len(improvements) > 0:
    print(f"\n✅ Features that IMPROVE performance:")
    for _, row in improvements.iterrows():
        if row['Variant'] != 'v2.0 Baseline':
            print(f"  • {row['Variant']}")
else:
    print(f"\n❌ NO v3.0 variants improve over v2.0 baseline")
    print(f"   Root cause analysis needed for each feature")

print("\n" + "="*80)
