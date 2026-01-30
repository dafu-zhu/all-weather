"""
Reporting and formatting utilities for strategy analysis

Provides consistent formatting for reports, tables, and metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional


def print_section(title: str, width: int = 70):
    """Print a major section header."""
    print("\n" + "="*width)
    print(title.upper())
    print("="*width)


def print_subsection(title: str, width: int = 70):
    """Print a subsection header."""
    print(f"\n{title}")
    print("-"*width)


def print_metric(name: str, value: Any, indent: int = 2):
    """Print a single metric with consistent formatting."""
    spaces = " " * indent
    print(f"{spaces}{name}: {value}")


def format_currency(value: float, symbol: str = "¥") -> str:
    """Format value as currency."""
    return f"{symbol}{value:,.0f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage."""
    return f"{value*100:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """Format number with specified decimals."""
    return f"{value:.{decimals}f}"


def print_comparison_table(
    results_dict: Dict[str, Dict],
    portfolios_dict: Dict[str, Any],
    metric_names: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Create and print comparison table for multiple strategy versions.

    Args:
        results_dict: Dict mapping version name to results dict
        portfolios_dict: Dict mapping version name to portfolio object
        metric_names: Optional list of metrics to include

    Returns:
        DataFrame with comparison table
    """
    if metric_names is None:
        metric_names = [
            'total_return',
            'annual_return',
            'annual_volatility',
            'sharpe_ratio',
            'sortino_ratio',
            'max_drawdown',
            'calmar_ratio',
            'final_value',
            'rebalances_executed',
            'rebalances_skipped',
            'total_commissions',
            'total_trades'
        ]

    comparison_data = {}

    for version, results in results_dict.items():
        portfolio = portfolios_dict[version]
        metrics = results['metrics']

        comparison_data[version] = [
            format_percentage(results['total_return']),
            format_percentage(metrics['annual_return']),
            format_percentage(metrics['annual_volatility']),
            format_number(metrics['sharpe_ratio']),
            format_number(metrics['sortino_ratio']),
            format_percentage(metrics['max_drawdown']),
            format_number(metrics['calmar_ratio']),
            format_currency(results['final_value']),
            results['rebalances_executed'],
            results['rebalances_skipped'],
            format_currency(portfolio.get_total_commissions()),
            portfolio.get_trade_count(),
        ]

    comparison = pd.DataFrame(
        comparison_data,
        index=[
            'Total Return',
            'Annual Return',
            'Annual Volatility',
            'Sharpe Ratio',
            'Sortino Ratio',
            'Max Drawdown',
            'Calmar Ratio',
            'Final Value',
            'Rebalances Executed',
            'Rebalances Skipped',
            'Total Commissions',
            'Total Trades'
        ]
    )

    print(comparison)
    return comparison


def print_improvement_summary(
    baseline_results: Dict,
    baseline_portfolio: Any,
    improved_results: Dict,
    improved_portfolio: Any,
    baseline_name: str = "Baseline",
    improved_name: str = "Improved"
):
    """
    Print improvement summary comparing two versions.

    Args:
        baseline_results: Results dict for baseline version
        baseline_portfolio: Portfolio object for baseline
        improved_results: Results dict for improved version
        improved_portfolio: Portfolio object for improved version
        baseline_name: Name for baseline version
        improved_name: Name for improved version
    """
    # Calculate differences
    value_gain = improved_results['final_value'] - baseline_results['final_value']
    value_pct = (value_gain / baseline_results['final_value']) * 100

    return_gain = improved_results['metrics']['annual_return'] - baseline_results['metrics']['annual_return']
    sharpe_gain = improved_results['metrics']['sharpe_ratio'] - baseline_results['metrics']['sharpe_ratio']
    vol_change = improved_results['metrics']['annual_volatility'] - baseline_results['metrics']['annual_volatility']

    comm_baseline = baseline_portfolio.get_total_commissions()
    comm_improved = improved_portfolio.get_total_commissions()
    comm_diff = comm_improved - comm_baseline

    rebal_diff = improved_results['rebalances_executed'] - baseline_results['rebalances_executed']

    # Print summary
    print(f"\n{baseline_name} → {improved_name}:")
    print_metric("Final value gain", f"{format_currency(value_gain)} ({value_pct:+.2f}%)")
    print_metric("Annual return gain", format_percentage(return_gain, 2))
    print_metric("Sharpe ratio gain", f"{sharpe_gain:+.2f}")
    print_metric("Volatility change", format_percentage(vol_change, 2))
    print_metric("Commission change", f"{format_currency(comm_diff)} ({comm_diff/comm_baseline*100:+.1f}%)")
    print_metric("Rebalance change", f"{rebal_diff:+d}")


def print_version_ranking(
    results_dict: Dict[str, Dict],
    metric: str = 'sharpe_ratio',
    metric_label: str = 'Sharpe Ratio'
):
    """
    Print ranking of versions by a specific metric.

    Args:
        results_dict: Dict mapping version name to results dict
        metric: Metric key to rank by
        metric_label: Human-readable metric name
    """
    # Create ranking list
    ranking_data = []
    for version, results in results_dict.items():
        if metric in results['metrics']:
            value = results['metrics'][metric]
        else:
            value = results.get(metric, 0)

        final_val = results['final_value']
        ranking_data.append((version, value, final_val))

    # Sort by metric value (descending)
    ranking_data.sort(key=lambda x: x[1], reverse=True)

    # Print ranking
    print(f"\n📊 Version Ranking (by {metric_label}):")
    medals = ['🥇', '🥈', '🥉']
    for i, (version, value, final_val) in enumerate(ranking_data):
        medal = medals[i] if i < 3 else '  '
        if 'ratio' in metric.lower():
            metric_str = f"{value:.2f}"
        elif 'return' in metric.lower() or 'volatility' in metric.lower():
            metric_str = format_percentage(value)
        else:
            metric_str = format_number(value)

        print(f"  {medal} {version}: {metric_label} {metric_str}, Final Value {format_currency(final_val)}")


def print_key_insights(
    improvements: List[Dict[str, Any]],
    best_version: str,
    best_metrics: Dict[str, float]
):
    """
    Print key insights from version comparison.

    Args:
        improvements: List of improvement dicts with keys: from_version, to_version, gain, gain_pct
        best_version: Name of best performing version
        best_metrics: Dict of best version's key metrics
    """
    print("\n💡 Key Insights:")

    for imp in improvements:
        print(f"  • {imp['from_version']} → {imp['to_version']}: "
              f"{format_currency(imp['gain'])} ({imp['gain_pct']:+.2f}%)")
        if 'feature' in imp:
            print(f"    → {imp['feature']}")

    print(f"\n🎯 Recommendation: Use {best_version} for production trading")
    print("  Reasons:")
    print(f"    ✓ Highest returns: {format_percentage(best_metrics['annual_return'])} annual")
    print(f"    ✓ Best risk-adjusted: {best_metrics['sharpe_ratio']:.2f} Sharpe ratio")
    if 'calmar_ratio' in best_metrics:
        print(f"    ✓ Strong Calmar ratio: {best_metrics['calmar_ratio']:.2f}")


def create_summary_dict(results: Dict, portfolio: Any) -> Dict[str, Any]:
    """
    Create a summary dictionary from results and portfolio.

    Args:
        results: Results dict from backtest
        portfolio: Portfolio object

    Returns:
        Dictionary with key metrics
    """
    return {
        'final_value': results['final_value'],
        'total_return': results['total_return'],
        'annual_return': results['metrics']['annual_return'],
        'annual_volatility': results['metrics']['annual_volatility'],
        'sharpe_ratio': results['metrics']['sharpe_ratio'],
        'sortino_ratio': results['metrics']['sortino_ratio'],
        'max_drawdown': results['metrics']['max_drawdown'],
        'calmar_ratio': results['metrics']['calmar_ratio'],
        'rebalances': results['rebalances_executed'],
        'commissions': portfolio.get_total_commissions(),
        'trades': portfolio.get_trade_count()
    }
