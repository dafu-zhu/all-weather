"""
Version Comparison Module

Provides utilities for comparing different versions of the All Weather Strategy.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .strategy import AllWeatherV1
from .utils.reporting import (
    print_section,
    print_comparison_table,
    print_improvement_summary,
    print_version_ranking,
    print_key_insights,
    create_summary_dict
)


@dataclass
class VersionConfig:
    """Configuration for a strategy version."""
    name: str
    description: str
    rebalance_threshold: float
    use_shrinkage: bool


# Predefined version configurations
VERSION_CONFIGS = {
    'v1.0': VersionConfig(
        name='v1.0',
        description='Pure Risk Parity (Always Rebalance, Sample Covariance)',
        rebalance_threshold=0,
        use_shrinkage=False
    ),
    'v1.1': VersionConfig(
        name='v1.1',
        description='+ Adaptive Rebalancing (5% drift threshold)',
        rebalance_threshold=0.05,
        use_shrinkage=False
    ),
    'v1.2': VersionConfig(
        name='v1.2',
        description='+ Ledoit-Wolf Covariance Shrinkage',
        rebalance_threshold=0.05,
        use_shrinkage=True
    )
}


class VersionComparison:
    """
    Compare multiple versions of the All Weather Strategy.

    Handles running backtests, storing results, and generating comparison reports.
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        initial_capital: float = 1_000_000,
        start_date: str = '2018-01-01',
        lookback: int = 252,
        commission_rate: float = 0.0003
    ):
        """
        Initialize version comparison.

        Args:
            prices: DataFrame of ETF prices
            initial_capital: Starting capital for all versions
            start_date: Backtest start date
            lookback: Lookback period for covariance
            commission_rate: Transaction cost rate
        """
        self.prices = prices
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.lookback = lookback
        self.commission_rate = commission_rate

        self.strategies: Dict[str, AllWeatherV1] = {}
        self.results: Dict[str, Dict] = {}

    def run_version(
        self,
        version_name: str,
        config: Optional[VersionConfig] = None,
        verbose: bool = False
    ) -> Dict:
        """
        Run backtest for a specific version.

        Args:
            version_name: Name of the version
            config: VersionConfig object (uses predefined if None)
            verbose: Print progress messages

        Returns:
            Results dictionary
        """
        if config is None:
            if version_name not in VERSION_CONFIGS:
                raise ValueError(f"Unknown version: {version_name}. "
                               f"Available: {list(VERSION_CONFIGS.keys())}")
            config = VERSION_CONFIGS[version_name]

        if verbose:
            print(f"\nRunning {config.name}: {config.description}...")

        # Create strategy
        strategy = AllWeatherV1(
            prices=self.prices,
            initial_capital=self.initial_capital,
            rebalance_freq='W-MON',
            lookback=self.lookback,
            commission_rate=self.commission_rate,
            rebalance_threshold=config.rebalance_threshold,
            use_shrinkage=config.use_shrinkage
        )

        # Run backtest
        results = strategy.run_backtest(start_date=self.start_date, verbose=False)

        # Store
        self.strategies[version_name] = strategy
        self.results[version_name] = results

        if verbose:
            print(f"   Final Value: ¥{results['final_value']:,.0f}")
            print(f"   Annual Return: {results['metrics']['annual_return']:.2%}")
            print(f"   Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")

        return results

    def run_all_versions(
        self,
        versions: Optional[List[str]] = None,
        verbose: bool = True
    ):
        """
        Run backtests for all specified versions.

        Args:
            versions: List of version names (default: all predefined versions)
            verbose: Print progress messages
        """
        if versions is None:
            versions = list(VERSION_CONFIGS.keys())

        if verbose:
            print_section("Running Backtests for All Versions")

        for version in versions:
            self.run_version(version, verbose=verbose)

        if verbose:
            print("\n✓ All backtests complete")

    def print_comparison(self):
        """Print comparison table for all run versions."""
        if not self.results:
            print("No results available. Run backtests first.")
            return

        print_section("Performance Comparison")

        comparison_df = print_comparison_table(
            self.results,
            self.strategies
        )

        return comparison_df

    def print_incremental_improvements(self):
        """Print incremental improvements between versions."""
        if len(self.results) < 2:
            print("Need at least 2 versions to compare.")
            return

        print_section("Incremental Improvements")

        versions = list(self.results.keys())

        # Compare consecutive versions
        for i in range(len(versions) - 1):
            baseline = versions[i]
            improved = versions[i + 1]

            print_improvement_summary(
                self.results[baseline],
                self.strategies[baseline].portfolio,
                self.results[improved],
                self.strategies[improved].portfolio,
                baseline_name=baseline,
                improved_name=improved
            )

        # Compare first to last
        if len(versions) > 2:
            print_improvement_summary(
                self.results[versions[0]],
                self.strategies[versions[0]].portfolio,
                self.results[versions[-1]],
                self.strategies[versions[-1]].portfolio,
                baseline_name=f"{versions[0]} (Baseline)",
                improved_name=f"{versions[-1]} (Combined)"
            )

    def print_ranking(self, metric: str = 'sharpe_ratio'):
        """Print version ranking by specified metric."""
        if not self.results:
            print("No results available.")
            return

        metric_labels = {
            'sharpe_ratio': 'Sharpe Ratio',
            'annual_return': 'Annual Return',
            'final_value': 'Final Value',
            'calmar_ratio': 'Calmar Ratio'
        }

        label = metric_labels.get(metric, metric.replace('_', ' ').title())
        print_version_ranking(self.results, metric=metric, metric_label=label)

    def get_equity_curves(self) -> Dict[str, pd.Series]:
        """Get equity curves for all versions."""
        return {
            version: results['equity_curve']
            for version, results in self.results.items()
        }

    def get_summary_dict(self) -> Dict[str, Dict]:
        """Get summary dictionaries for all versions."""
        summaries = {}
        for version, results in self.results.items():
            summaries[version] = create_summary_dict(
                results,
                self.strategies[version].portfolio
            )
        return summaries

    def calculate_improvements(self) -> List[Dict]:
        """
        Calculate improvement statistics between versions.

        Returns:
            List of improvement dictionaries
        """
        if len(self.results) < 2:
            return []

        improvements = []
        versions = list(self.results.keys())

        for i in range(len(versions) - 1):
            from_ver = versions[i]
            to_ver = versions[i + 1]

            from_val = self.results[from_ver]['final_value']
            to_val = self.results[to_ver]['final_value']

            gain = to_val - from_val
            gain_pct = (gain / from_val) * 100

            improvement = {
                'from_version': from_ver,
                'to_version': to_ver,
                'gain': gain,
                'gain_pct': gain_pct,
                'from_value': from_val,
                'to_value': to_val
            }

            # Add feature description
            if to_ver == 'v1.1':
                improvement['feature'] = 'Adaptive rebalancing reduces costs'
            elif to_ver == 'v1.2':
                improvement['feature'] = 'Covariance shrinkage improves robustness'

            improvements.append(improvement)

        return improvements

    def print_summary(self):
        """Print comprehensive summary with insights and recommendations."""
        if not self.results:
            print("No results available.")
            return

        print_section("Summary & Recommendations")

        # Print ranking
        self.print_ranking(metric='sharpe_ratio')

        # Calculate improvements
        improvements = self.calculate_improvements()

        # Find best version
        best_version = max(
            self.results.items(),
            key=lambda x: x[1]['metrics']['sharpe_ratio']
        )[0]
        best_metrics = self.results[best_version]['metrics']

        # Print insights
        print_key_insights(improvements, best_version, best_metrics)

    def generate_report(self) -> str:
        """
        Generate a text report of the comparison.

        Returns:
            Formatted report string
        """
        if not self.results:
            return "No results available."

        lines = []
        lines.append("="*70)
        lines.append("ALL WEATHER STRATEGY - VERSION COMPARISON REPORT")
        lines.append("="*70)
        lines.append(f"\nPeriod: {self.start_date} to {self.prices.index[-1].date()}")
        lines.append(f"Initial Capital: ¥{self.initial_capital:,.0f}\n")

        # Add summary statistics for each version
        for version, results in self.results.items():
            config = VERSION_CONFIGS.get(version)
            lines.append(f"\n{version}: {config.description if config else ''}")
            lines.append(f"  Final Value: ¥{results['final_value']:,.0f}")
            lines.append(f"  Annual Return: {results['metrics']['annual_return']:.2%}")
            lines.append(f"  Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
            lines.append(f"  Max Drawdown: {results['metrics']['max_drawdown']:.2%}")
            lines.append(f"  Rebalances: {results['rebalances_executed']}")

        lines.append("\n" + "="*70)

        return "\n".join(lines)
