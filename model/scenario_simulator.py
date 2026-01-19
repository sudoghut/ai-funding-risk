"""
Scenario Simulator Module
Allows simulation of future funding scenarios with adjustable parameters
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import PROCESSED_DATA_DIR, RISK_THRESHOLDS


@dataclass
class ScenarioParameters:
    """Parameters for scenario simulation"""
    capex_growth_rate: float  # Annual growth rate (e.g., 0.20 = 20%)
    revenue_growth_rate: float
    interest_rate: float
    debt_growth_rate: float
    years_to_simulate: int


@dataclass
class YearProjection:
    """Projection for a single year"""
    year: int
    capex: float
    revenue: float
    operating_cashflow: float
    debt: float
    capex_to_cashflow_ratio: float
    debt_to_revenue_ratio: float
    risk_level: str
    alerts: List[str]


@dataclass
class ScenarioResult:
    """Complete scenario simulation result"""
    scenario_name: str
    parameters: Dict
    base_year: int
    projections: List[Dict]
    critical_year: Optional[int]  # Year when risk becomes HIGH
    summary: str
    warnings: List[str]


class ScenarioSimulator:
    """Simulates future funding scenarios for AI companies"""

    def __init__(self):
        self.processed_dir = PROCESSED_DATA_DIR
        self.thresholds = RISK_THRESHOLDS
        self.raw_dir = PROCESSED_DATA_DIR.parent / "raw"

    def load_baseline_data(self) -> Optional[Dict]:
        """Load consolidated data for baseline values"""
        filepath = self.processed_dir / "consolidated_data.json"
        if not filepath.exists():
            print(f"Consolidated data not found: {filepath}")
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_aggregate_baseline(self, data: Dict) -> Dict:
        """
        Calculate aggregate baseline values from all companies

        Args:
            data: Consolidated data

        Returns:
            Dictionary with aggregate baseline values
        """
        companies = data.get("companies", {})

        total_capex = 0
        total_revenue = 0
        total_cashflow = 0
        total_debt = 0
        count = 0

        for company_name, company_data in companies.items():
            # Try SEC derived metrics first, then fall back to Yahoo
            derived = company_data.get("derived_metrics", {})
            yahoo = company_data.get("yahoo_metrics", {})

            # Get capex from SEC or estimate from Yahoo free cash flow
            capex = derived.get("latest_capex")
            if not capex and yahoo:
                # Estimate capex as operating cashflow - free cashflow (approximation)
                ocf = yahoo.get("operating_cashflow_B")
                fcf = yahoo.get("free_cashflow_B")
                if ocf is not None and fcf is not None:
                    capex = (ocf - fcf) * 1e9  # Convert back from billions

            # Get revenue - prefer SEC, fallback to Yahoo
            revenue = derived.get("latest_revenue")
            if not revenue and yahoo:
                rev_b = yahoo.get("revenue_B")
                if rev_b is not None:
                    revenue = rev_b * 1e9

            # Get cashflow - prefer SEC, fallback to Yahoo
            cashflow = derived.get("latest_operating_cashflow")
            if not cashflow and yahoo:
                ocf_b = yahoo.get("operating_cashflow_B")
                if ocf_b is not None:
                    cashflow = ocf_b * 1e9

            # Get debt - prefer SEC, fallback to Yahoo
            debt = derived.get("latest_debt")
            if not debt and yahoo:
                debt_b = yahoo.get("total_debt_B")
                if debt_b is not None:
                    debt = debt_b * 1e9

            if capex and revenue and cashflow:
                total_capex += abs(capex)
                total_revenue += revenue
                total_cashflow += cashflow
                total_debt += debt if debt else 0
                count += 1

        # Convert to billions
        return {
            "capex_B": round(total_capex / 1e9, 2),
            "revenue_B": round(total_revenue / 1e9, 2),
            "operating_cashflow_B": round(total_cashflow / 1e9, 2),
            "debt_B": round(total_debt / 1e9, 2),
            "company_count": count,
            "capex_to_cashflow_ratio": (
                round(total_capex / total_cashflow, 3)
                if total_cashflow > 0 else None
            ),
        }

    def calculate_historical_growth_rates(self, data: Dict) -> Dict:
        """
        Calculate historical growth rates from SEC and Yahoo data

        Args:
            data: Consolidated data

        Returns:
            Dictionary with average historical growth rates
        """
        companies = data.get("companies", {})

        revenue_growth_rates = []
        debt_growth_rates = []
        capex_growth_rates = []

        for company_name, company_data in companies.items():
            sec_metrics = company_data.get("sec_metrics", {})
            derived = company_data.get("derived_metrics", {})
            yahoo = company_data.get("yahoo_metrics", {})

            # Get revenue growth from derived metrics or Yahoo
            rev_growth = derived.get("revenue_growth_yoy")
            if rev_growth is None and yahoo:
                rev_growth_pct = yahoo.get("revenue_growth")
                if rev_growth_pct is not None:
                    rev_growth = rev_growth_pct * 100  # Convert to percentage

            if rev_growth is not None:
                revenue_growth_rates.append(rev_growth)

            # Get debt growth from derived metrics
            debt_growth = derived.get("debt_growth_yoy")
            if debt_growth is not None:
                debt_growth_rates.append(debt_growth)

            # Get capex growth from derived metrics
            capex_growth = derived.get("capex_growth_yoy")
            if capex_growth is not None:
                capex_growth_rates.append(capex_growth)

            # Calculate capex growth from Yahoo historical data (calendar-year aligned)
            yahoo_hist = company_data.get("yahoo_historical", {})
            if yahoo_hist:
                capex_data = yahoo_hist.get("capex", [])
                if len(capex_data) >= 2:
                    # Calculate YoY growth from most recent years
                    latest = capex_data[0].get("value", 0)
                    prev = capex_data[1].get("value", 0)
                    if prev > 0 and latest > 0:
                        yoy_growth = ((latest - prev) / prev) * 100
                        if -50 < yoy_growth < 200:  # Reasonable bounds
                            capex_growth_rates.append(yoy_growth)

        # Calculate averages (default to conservative estimates if no data)
        def safe_average(values, default):
            if values:
                # Remove outliers (values > 100% or < -50%)
                filtered = [v for v in values if -50 < v < 100]
                if filtered:
                    return sum(filtered) / len(filtered)
            return default

        avg_revenue_growth = safe_average(revenue_growth_rates, 10.0)
        avg_debt_growth = safe_average(debt_growth_rates, 12.0)
        avg_capex_growth = safe_average(capex_growth_rates, 18.0)

        # Get current interest rate from FRED data if available
        current_interest_rate = 5.0  # Default
        macro = data.get("macro_indicators", {})
        if macro:
            fed_funds = macro.get("FEDFUNDS", {})
            if fed_funds and fed_funds.get("latest_value"):
                current_interest_rate = fed_funds["latest_value"]

        return {
            "revenue_growth": round(avg_revenue_growth, 2),
            "debt_growth": round(avg_debt_growth, 2),
            "capex_growth": round(avg_capex_growth, 2),
            "interest_rate": round(current_interest_rate, 2),
            "data_points": {
                "revenue_samples": len(revenue_growth_rates),
                "debt_samples": len(debt_growth_rates),
                "capex_samples": len(capex_growth_rates),
            }
        }

    def simulate_scenario(
        self,
        baseline: Dict,
        params: ScenarioParameters,
        scenario_name: str = "Custom Scenario"
    ) -> ScenarioResult:
        """
        Simulate future years based on growth assumptions

        Args:
            baseline: Baseline values (in billions)
            params: Scenario parameters
            scenario_name: Name for this scenario

        Returns:
            ScenarioResult with year-by-year projections
        """
        projections = []
        warnings = []
        critical_year = None

        current_year = datetime.now().year
        capex = baseline["capex_B"]
        revenue = baseline["revenue_B"]
        cashflow = baseline["operating_cashflow_B"]
        debt = baseline["debt_B"]

        # Estimate cashflow growth based on revenue growth (simplified)
        cashflow_margin = cashflow / revenue if revenue > 0 else 0.15

        for year_offset in range(params.years_to_simulate + 1):
            year = current_year + year_offset
            alerts = []

            # Project values (year 0 = baseline)
            if year_offset > 0:
                capex *= (1 + params.capex_growth_rate)
                revenue *= (1 + params.revenue_growth_rate)
                debt *= (1 + params.debt_growth_rate)
                # Cashflow grows with revenue but may compress under higher interest
                interest_impact = max(0, params.interest_rate - 4) * 0.02
                cashflow = revenue * (cashflow_margin - interest_impact)

            # Calculate ratios
            capex_to_cf = capex / cashflow if cashflow > 0 else float('inf')
            debt_to_rev = debt / revenue if revenue > 0 else float('inf')

            # Determine risk level
            if capex_to_cf >= self.thresholds["capex_to_cashflow"]["warning"]:
                risk_level = "HIGH"
                alerts.append("Capex exceeds sustainable cash flow coverage")
                if critical_year is None:
                    critical_year = year
            elif capex_to_cf >= self.thresholds["capex_to_cashflow"]["normal"]:
                risk_level = "MEDIUM"
                alerts.append("Capex approaching cash flow limits")
            else:
                risk_level = "LOW"

            # Check debt sustainability
            if debt_to_rev > 1.5:
                if risk_level != "HIGH":
                    risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
                alerts.append(f"High debt-to-revenue ratio: {debt_to_rev:.2f}x")

            # Check for negative cashflow scenario
            if cashflow <= 0:
                risk_level = "HIGH"
                alerts.append("Operating cashflow turned negative")
                if critical_year is None:
                    critical_year = year

            projection = YearProjection(
                year=year,
                capex=round(capex, 2),
                revenue=round(revenue, 2),
                operating_cashflow=round(cashflow, 2),
                debt=round(debt, 2),
                capex_to_cashflow_ratio=round(capex_to_cf, 3),
                debt_to_revenue_ratio=round(debt_to_rev, 3),
                risk_level=risk_level,
                alerts=alerts
            )
            projections.append(asdict(projection))

        # Generate summary
        final_year = projections[-1]
        if critical_year:
            summary = (
                f"Risk threshold breached in {critical_year}. "
                f"Final capex-to-cashflow ratio: {final_year['capex_to_cashflow_ratio']:.2f}"
            )
            warnings.append(f"Critical year identified: {critical_year}")
        else:
            summary = (
                f"Scenario remains sustainable through {current_year + params.years_to_simulate}. "
                f"Final capex-to-cashflow ratio: {final_year['capex_to_cashflow_ratio']:.2f}"
            )

        # Add warnings for concerning trends
        baseline_ratio = projections[0]["capex_to_cashflow_ratio"]
        final_ratio = projections[-1]["capex_to_cashflow_ratio"]
        ratio_change = ((final_ratio - baseline_ratio) / baseline_ratio) * 100 if baseline_ratio > 0 else 0

        if ratio_change > 50:
            warnings.append(
                f"Capex-to-cashflow ratio increases {ratio_change:.0f}% over projection period"
            )

        return ScenarioResult(
            scenario_name=scenario_name,
            parameters=asdict(params),
            base_year=current_year,
            projections=projections,
            critical_year=critical_year,
            summary=summary,
            warnings=warnings
        )

    def run_standard_scenarios(self) -> List[ScenarioResult]:
        """
        Run a set of standard scenarios (base, optimistic, pessimistic)

        Returns:
            List of scenario results
        """
        data = self.load_baseline_data()
        if data is None:
            return []

        baseline = self.get_aggregate_baseline(data)
        ratio = baseline.get('capex_to_cashflow_ratio')
        ratio_str = f"{ratio:.2f}" if ratio is not None else "N/A"
        print(f"Baseline: Capex ${baseline['capex_B']}B, "
              f"Cashflow ${baseline['operating_cashflow_B']}B, "
              f"Ratio {ratio_str}")

        # Calculate historical growth rates
        historical_rates = self.calculate_historical_growth_rates(data)
        print(f"Historical Growth Rates: Revenue {historical_rates['revenue_growth']:.1f}%, "
              f"Capex {historical_rates['capex_growth']:.1f}%, "
              f"Debt {historical_rates['debt_growth']:.1f}%")

        scenarios = []

        # Historical Trend: Based on actual historical data
        historical_params = ScenarioParameters(
            capex_growth_rate=historical_rates["capex_growth"] / 100,
            revenue_growth_rate=historical_rates["revenue_growth"] / 100,
            interest_rate=historical_rates["interest_rate"],
            debt_growth_rate=historical_rates["debt_growth"] / 100,
            years_to_simulate=5
        )
        scenarios.append(self.simulate_scenario(
            baseline, historical_params, "Historical Trend"
        ))

        # Base Case: Current growth continues
        base_params = ScenarioParameters(
            capex_growth_rate=0.20,  # 20% annual capex growth
            revenue_growth_rate=0.12,  # 12% revenue growth
            interest_rate=5.0,
            debt_growth_rate=0.15,
            years_to_simulate=5
        )
        scenarios.append(self.simulate_scenario(
            baseline, base_params, "Base Case"
        ))

        # Optimistic: Strong revenue growth
        optimistic_params = ScenarioParameters(
            capex_growth_rate=0.15,
            revenue_growth_rate=0.20,
            interest_rate=4.0,
            debt_growth_rate=0.10,
            years_to_simulate=5
        )
        scenarios.append(self.simulate_scenario(
            baseline, optimistic_params, "Optimistic"
        ))

        # Pessimistic: Slowing revenue, high rates
        pessimistic_params = ScenarioParameters(
            capex_growth_rate=0.25,
            revenue_growth_rate=0.05,
            interest_rate=6.5,
            debt_growth_rate=0.20,
            years_to_simulate=5
        )
        scenarios.append(self.simulate_scenario(
            baseline, pessimistic_params, "Pessimistic"
        ))

        # AI Winter: Severe slowdown
        ai_winter_params = ScenarioParameters(
            capex_growth_rate=0.30,  # Committed projects continue
            revenue_growth_rate=-0.05,  # Revenue decline
            interest_rate=7.0,
            debt_growth_rate=0.25,
            years_to_simulate=5
        )
        scenarios.append(self.simulate_scenario(
            baseline, ai_winter_params, "AI Winter"
        ))

        return scenarios

    def save_scenarios(self, scenarios: List[ScenarioResult]):
        """Save scenario results to file"""
        output_path = self.processed_dir / "scenario_projections.json"

        output_data = {
            "generated_at": datetime.now().isoformat(),
            "scenarios": [asdict(s) for s in scenarios]
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\nScenarios saved to {output_path}")

    def print_scenario_summary(self, scenarios: List[ScenarioResult]):
        """Print formatted summary of all scenarios"""
        print("\n" + "=" * 70)
        print("SCENARIO SIMULATION RESULTS")
        print("=" * 70)

        for scenario in scenarios:
            print(f"\n{scenario.scenario_name}")
            print("-" * 40)

            # Parameters
            params = scenario.parameters
            print(f"Parameters:")
            print(f"  Capex Growth: {params['capex_growth_rate']*100:.0f}%/year")
            print(f"  Revenue Growth: {params['revenue_growth_rate']*100:.0f}%/year")
            print(f"  Interest Rate: {params['interest_rate']:.1f}%")
            print(f"  Debt Growth: {params['debt_growth_rate']*100:.0f}%/year")

            # Projections table
            print(f"\n{'Year':<6} {'Capex':>10} {'Revenue':>10} {'Cashflow':>10} "
                  f"{'Cap/CF':>8} {'Risk':>8}")
            print("-" * 60)

            for p in scenario.projections:
                print(f"{p['year']:<6} "
                      f"${p['capex']:>8.0f}B "
                      f"${p['revenue']:>8.0f}B "
                      f"${p['operating_cashflow']:>8.0f}B "
                      f"{p['capex_to_cashflow_ratio']:>7.2f} "
                      f"{p['risk_level']:>8}")

            # Summary
            print(f"\nSummary: {scenario.summary}")

            if scenario.warnings:
                print("Warnings:")
                for w in scenario.warnings:
                    print(f"  ! {w}")

        print("\n" + "=" * 70)


def main():
    """Main function to run scenario simulations"""
    print("=" * 60)
    print("Scenario Simulation")
    print("=" * 60)

    simulator = ScenarioSimulator()

    # Run standard scenarios
    scenarios = simulator.run_standard_scenarios()

    if scenarios:
        # Save results
        simulator.save_scenarios(scenarios)

        # Print summary
        simulator.print_scenario_summary(scenarios)

    return scenarios


if __name__ == "__main__":
    main()
