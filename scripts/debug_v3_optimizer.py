"""
Debug v3.0 Optimizer

Check what weights the new optimizer is producing vs v2.0.
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('.')

from src.optimizer import optimize_weights_constrained, optimize_weights_v3

# Load data
prices = pd.read_csv('data/etf_prices_7etf.csv', index_col=0, parse_dates=True)

# Get a sample period
sample_start = '2020-01-01'
sample_end = '2020-03-01'

sample_prices = prices.loc[sample_start:sample_end]
returns = sample_prices.pct_change().dropna()

print("="*80)
print("OPTIMIZER COMPARISON - Sample Period")
print("="*80)

print(f"\nSample period: {sample_start} to {sample_end}")
print(f"Assets: {list(returns.columns)}")

# v2.0 weights (constrained risk parity)
weights_v2 = optimize_weights_constrained(
    returns,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35
)

# v3.0 weights (with return optimization)
weights_v3 = optimize_weights_v3(
    returns,
    min_stock_alloc=0.60,
    max_bond_alloc=0.35,
    balance_environments=True,
    expected_returns=None,  # Will use EWMA
    lambda_sharpe=0.5
)

# Compare
print(f"\n{'Asset':<15s} {'v2.0':>10s} {'v3.0':>10s} {'Diff':>10s}")
print("-"*80)

for i, asset in enumerate(returns.columns):
    diff = weights_v3[i] - weights_v2[i]
    print(f"{asset:<15s} {weights_v2[i]:>9.2%} {weights_v3[i]:>9.2%} {diff:>+9.2%}")

# Calculate metrics for both
cov = returns.cov().values
expected_returns = returns.ewm(span=60, adjust=False).mean().iloc[-1].values

def calc_metrics(weights, cov, expected_returns):
    port_vol = np.sqrt(weights @ cov @ weights)
    port_return = weights @ expected_returns
    sharpe = port_return / port_vol if port_vol > 1e-10 else 0

    # Risk contributions
    marginal_contrib = cov @ weights
    risk_contrib = weights * marginal_contrib / port_vol if port_vol > 1e-10 else np.zeros_like(weights)

    return {
        'return': port_return,
        'volatility': port_vol,
        'sharpe': sharpe,
        'risk_contrib_std': np.std(risk_contrib)
    }

metrics_v2 = calc_metrics(weights_v2, cov, expected_returns)
metrics_v3 = calc_metrics(weights_v3, cov, expected_returns)

print(f"\n{'Metric':<20s} {'v2.0':>12s} {'v3.0':>12s}")
print("-"*80)
print(f"{'Expected Return':<20s} {metrics_v2['return']:>11.4%} {metrics_v3['return']:>11.4%}")
print(f"{'Volatility':<20s} {metrics_v2['volatility']:>11.4%} {metrics_v3['volatility']:>11.4%}")
print(f"{'Sharpe Ratio':<20s} {metrics_v2['sharpe']:>11.4f} {metrics_v3['sharpe']:>11.4f}")
print(f"{'Risk Contrib Std':<20s} {metrics_v2['risk_contrib_std']:>11.6f} {metrics_v3['risk_contrib_std']:>11.6f}")

# Test with different lambda values
print("\n" + "="*80)
print("LAMBDA SENSITIVITY ANALYSIS")
print("="*80)

lambdas = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]

print(f"\n{'Lambda':<10s} {'Return':>10s} {'Vol':>10s} {'Sharpe':>10s} {'RC Std':>10s}")
print("-"*80)

for lam in lambdas:
    weights = optimize_weights_v3(
        returns,
        min_stock_alloc=0.60,
        max_bond_alloc=0.35,
        balance_environments=False,  # Disable environment balancing
        expected_returns=None,
        lambda_sharpe=lam
    )

    metrics = calc_metrics(weights, cov, expected_returns)

    print(f"{lam:<10.1f} {metrics['return']:>9.4%} {metrics['volatility']:>9.4%} "
          f"{metrics['sharpe']:>9.4f} {metrics['risk_contrib_std']:>9.6f}")

print("\n(Lambda 0.0 = pure risk parity, 1.0 = pure Sharpe maximization)")

print("\n" + "="*80)
