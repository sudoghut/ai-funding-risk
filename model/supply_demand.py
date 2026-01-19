"""
Supply-Demand Balance Analysis Module
Analyzes the balance between AI capital demand and funding supply
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import PROCESSED_DATA_DIR, MARKET_DATA_DIR


@dataclass
class DemandMetrics:
    """AI sector capital demand metrics"""
    total_capex_B: float
    total_operating_cf_B: float
    capex_to_cf_ratio: float
    capex_growth_rate: float
    implied_annual_demand_B: float
    demand_intensity: str  # low, moderate, high, very_high


@dataclass
class SupplyMetrics:
    """Capital supply metrics"""
    total_cash_holdings_B: float
    total_free_cashflow_B: float
    total_debt_capacity_B: float  # Estimated from debt/cash ratios
    market_cap_total_T: float
    implied_funding_capacity_B: float
    supply_conditions: str  # tight, neutral, favorable


@dataclass
class BalanceAnalysis:
    """Supply-demand balance analysis"""
    demand: Dict
    supply: Dict
    balance_ratio: float  # supply / demand, >1 means surplus
    sustainability_score: float  # 0-100
    runway_years: float  # How long current supply can meet demand growth
    gap_annual_B: float  # Positive = surplus, negative = deficit
    trend: str  # improving, stable, deteriorating
    critical_year: Optional[int]
    findings: List[str]


class SupplyDemandAnalyzer:
    """Analyzes supply-demand dynamics for AI funding"""

    def __init__(self):
        self.base_year = datetime.now().year

    def load_data(self) -> Dict:
        """Load required data files"""
        data = {}

        # Load consolidated company data
        consolidated_file = PROCESSED_DATA_DIR / "consolidated_data.json"
        if consolidated_file.exists():
            with open(consolidated_file, "r", encoding="utf-8") as f:
                data["consolidated"] = json.load(f)

        # Load scenario projections
        scenario_file = PROCESSED_DATA_DIR / "scenario_projections.json"
        if scenario_file.exists():
            with open(scenario_file, "r", encoding="utf-8") as f:
                data["scenarios"] = json.load(f)

        # Load market data
        market_file = MARKET_DATA_DIR / "market_indicators.json"
        if market_file.exists():
            with open(market_file, "r", encoding="utf-8") as f:
                data["market"] = json.load(f)

        # Load credit market data
        credit_file = MARKET_DATA_DIR / "credit_market_data.json"
        if credit_file.exists():
            with open(credit_file, "r", encoding="utf-8") as f:
                data["credit"] = json.load(f)

        return data

    def _calculate_aggregate_growth_rate(self, consolidated: Dict, metric_key: str = "capex") -> float:
        """
        Calculate aggregate growth rate from Yahoo Finance historical data by summing
        all companies' values and computing YoY change on the total.

        Uses Yahoo Finance annual cashflow data which provides accurate calendar-year
        aligned data across all companies, avoiding fiscal year mismatch issues.

        Args:
            consolidated: Consolidated company data
            metric_key: 'capex' or 'ocf'

        Returns:
            Aggregate growth rate based on total values
        """
        companies = consolidated.get("companies", {})

        # Collect yearly totals from Yahoo Finance historical data
        yearly_totals = {}

        for company_name, company_data in companies.items():
            yahoo_hist = company_data.get("yahoo_historical", {})

            if metric_key == "capex":
                data = yahoo_hist.get("capex", [])
            elif metric_key == "ocf":
                data = yahoo_hist.get("ocf", [])
            else:
                data = []

            # Aggregate by calendar year
            for item in data:
                year = item.get("year")
                value = item.get("value", 0)
                if year and value > 0:
                    if year not in yearly_totals:
                        yearly_totals[year] = 0
                    yearly_totals[year] += value  # Already in billions

        # Get complete years with substantial data
        # For OCF: >$200B (6 companies should have ~$250B+)
        # For CapEx: >$90B (5-6 companies should have ~$100B+)
        current_year = self.base_year
        threshold = 200 if metric_key == "ocf" else 90
        complete_years = sorted([y for y in yearly_totals.keys()
                                 if y < current_year and yearly_totals[y] > threshold], reverse=True)

        if len(complete_years) < 2:
            return 0.30  # Fallback default

        # Calculate average growth rate over recent years
        growth_rates = []
        for i in range(min(3, len(complete_years) - 1)):  # Up to 3 years of growth
            curr_year = complete_years[i]
            prev_year = complete_years[i + 1]
            curr_val = yearly_totals[curr_year]
            prev_val = yearly_totals[prev_year]
            if prev_val > 0:
                growth = (curr_val - prev_val) / prev_val
                growth_rates.append(growth)

        if not growth_rates:
            return 0.30  # Fallback default

        # Return average of recent growth rates
        avg_growth = sum(growth_rates) / len(growth_rates)
        return round(avg_growth, 3)

    def _calculate_historical_growth_rate(self, consolidated: Dict, metric_key: str = "capex") -> float:
        """
        Calculate historical growth rate - now uses aggregate method for consistency
        with historical data display.

        Args:
            consolidated: Consolidated company data
            metric_key: 'capex', 'revenue', or 'fcf'

        Returns:
            Aggregate growth rate based on actual historical data
        """
        if metric_key == "capex":
            return self._calculate_aggregate_growth_rate(consolidated, "capex")
        elif metric_key == "ocf":
            return self._calculate_aggregate_growth_rate(consolidated, "ocf")
        else:
            # Fallback to original weighted average for other metrics
            growth_rates = []
            weights = []

            for company_name, company_data in consolidated.get("companies", {}).items():
                derived = company_data.get("derived_metrics", {})
                yahoo = company_data.get("yahoo_metrics", {})

                if metric_key == "revenue":
                    growth = derived.get("revenue_growth_yoy")
                else:
                    growth = None

                weight = yahoo.get("market_cap_B", 100)

                if growth is not None and -100 < growth < 500:
                    growth_rates.append(growth / 100)
                    weights.append(weight)

            if not growth_rates:
                return 0.25

            total_weight = sum(weights)
            weighted_avg = sum(g * w for g, w in zip(growth_rates, weights)) / total_weight
            return round(weighted_avg, 3)

    def _calculate_fcf_growth_rate(self, consolidated: Dict) -> float:
        """
        Calculate supply growth rate using aggregate OCF growth.

        Uses operating cash flow as the base for supply capacity growth,
        calculated as total OCF YoY change across all companies.
        """
        # Use aggregate OCF growth for consistency with historical data
        return self._calculate_aggregate_growth_rate(consolidated, "ocf")

    def calculate_demand_metrics(self, consolidated: Dict) -> DemandMetrics:
        """
        Calculate AI sector capital demand metrics

        Args:
            consolidated: Consolidated company data

        Returns:
            DemandMetrics with demand analysis
        """
        companies = consolidated.get("companies", {})

        total_capex = 0
        total_operating_cf = 0
        capex_values = []
        cf_values = []

        for company_name, company_data in companies.items():
            yahoo = company_data.get("yahoo_metrics", {})

            # Get operating cash flow
            op_cf = yahoo.get("operating_cashflow_B")
            if op_cf:
                total_operating_cf += op_cf
                cf_values.append(op_cf)

            # Estimate capex from free cash flow difference
            free_cf = yahoo.get("free_cashflow_B")
            if op_cf and free_cf:
                estimated_capex = op_cf - free_cf
                if estimated_capex > 0:
                    total_capex += estimated_capex
                    capex_values.append(estimated_capex)

        # Calculate ratios
        capex_to_cf = total_capex / total_operating_cf if total_operating_cf > 0 else 0

        # Calculate growth rate from actual historical data instead of hardcoding
        capex_growth = self._calculate_historical_growth_rate(consolidated, "capex")

        # Calculate implied annual demand
        # Current capex + projected growth
        implied_demand = total_capex * (1 + capex_growth)

        # Determine demand intensity
        if capex_to_cf > 0.8:
            intensity = "very_high"
        elif capex_to_cf > 0.6:
            intensity = "high"
        elif capex_to_cf > 0.4:
            intensity = "moderate"
        else:
            intensity = "low"

        return DemandMetrics(
            total_capex_B=round(total_capex, 2),
            total_operating_cf_B=round(total_operating_cf, 2),
            capex_to_cf_ratio=round(capex_to_cf, 3),
            capex_growth_rate=capex_growth,
            implied_annual_demand_B=round(implied_demand, 2),
            demand_intensity=intensity,
        )

    def calculate_supply_metrics(self, consolidated: Dict, credit_data: Dict) -> SupplyMetrics:
        """
        Calculate capital supply metrics

        Args:
            consolidated: Consolidated company data
            credit_data: Credit market data

        Returns:
            SupplyMetrics with supply analysis
        """
        companies = consolidated.get("companies", {})

        total_cash = 0
        total_fcf = 0
        total_debt = 0
        total_market_cap = 0

        for company_name, company_data in companies.items():
            yahoo = company_data.get("yahoo_metrics", {})

            cash = yahoo.get("total_cash_B")
            if cash:
                total_cash += cash

            fcf = yahoo.get("free_cashflow_B")
            if fcf and fcf > 0:
                total_fcf += fcf

            debt = yahoo.get("total_debt_B")
            if debt:
                total_debt += debt

            mc = yahoo.get("market_cap_B")
            if mc:
                total_market_cap += mc

        # Estimate debt capacity based on current leverage
        # Assume companies could increase debt to 1.5x current levels sustainably
        debt_capacity = total_debt * 0.5  # Additional capacity

        # Calculate implied funding capacity
        # = Current cash + Annual FCF + Debt capacity + Potential equity raises (1% of market cap)
        equity_raise_capacity = total_market_cap * 0.01  # Conservative 1% dilution
        implied_capacity = total_cash + total_fcf + debt_capacity + equity_raise_capacity

        # Determine supply conditions based on credit market
        credit_health = credit_data.get("health_assessment", {}).get("composite_score", 50)

        if credit_health >= 70:
            conditions = "favorable"
        elif credit_health >= 50:
            conditions = "neutral"
        else:
            conditions = "tight"

        return SupplyMetrics(
            total_cash_holdings_B=round(total_cash, 2),
            total_free_cashflow_B=round(total_fcf, 2),
            total_debt_capacity_B=round(debt_capacity, 2),
            market_cap_total_T=round(total_market_cap / 1000, 2),
            implied_funding_capacity_B=round(implied_capacity, 2),
            supply_conditions=conditions,
        )

    def analyze_balance(
        self,
        demand: DemandMetrics,
        supply: SupplyMetrics,
        scenarios: Dict = None,
        consolidated: Dict = None
    ) -> BalanceAnalysis:
        """
        Analyze supply-demand balance

        Args:
            demand: Demand metrics
            supply: Supply metrics
            scenarios: Scenario projections (optional)
            consolidated: Consolidated data for calculating supply growth

        Returns:
            BalanceAnalysis with complete analysis
        """
        # Calculate balance ratio
        balance_ratio = supply.implied_funding_capacity_B / demand.implied_annual_demand_B if demand.implied_annual_demand_B > 0 else 1

        # Calculate annual gap
        gap = supply.implied_funding_capacity_B - demand.implied_annual_demand_B

        # Calculate runway (years until supply exhausted at current growth)
        # Use historical data to calculate supply growth instead of hardcoding
        if consolidated:
            supply_growth = self._calculate_fcf_growth_rate(consolidated)
        else:
            supply_growth = 0.12  # Fallback only if no data
        demand_growth = demand.capex_growth_rate

        if demand_growth > supply_growth:
            # Calculate years until crossover
            current_supply = supply.implied_funding_capacity_B
            current_demand = demand.implied_annual_demand_B

            years = 0
            while current_supply > current_demand and years < 10:
                years += 1
                current_supply *= (1 + supply_growth)
                current_demand *= (1 + demand_growth)

            runway = years if years < 10 else None
        else:
            runway = None  # Sustainable indefinitely

        # Calculate sustainability score
        # Based on: balance ratio, runway, supply conditions
        base_score = min(100, balance_ratio * 50)  # 2x coverage = 100

        # Adjust for supply conditions
        condition_adj = {"favorable": 10, "neutral": 0, "tight": -15}
        base_score += condition_adj.get(supply.supply_conditions, 0)

        # Adjust for demand intensity
        intensity_adj = {"low": 10, "moderate": 0, "high": -10, "very_high": -20}
        base_score += intensity_adj.get(demand.demand_intensity, 0)

        sustainability_score = max(0, min(100, base_score))

        # Determine trend
        if gap > 50:  # $50B surplus
            trend = "improving"
        elif gap > -20:  # Small deficit
            trend = "stable"
        else:
            trend = "deteriorating"

        # Find critical year from scenarios
        critical_year = None
        if scenarios:
            scenario_list = scenarios.get("scenarios", [])
            base_case = next((s for s in scenario_list if s.get("scenario_name") == "Base Case"), None)
            if base_case:
                critical_year = base_case.get("critical_year")

        # Generate findings
        findings = self._generate_findings(demand, supply, balance_ratio, runway, gap)

        return BalanceAnalysis(
            demand=asdict(demand),
            supply=asdict(supply),
            balance_ratio=round(balance_ratio, 2),
            sustainability_score=round(sustainability_score, 1),
            runway_years=runway,
            gap_annual_B=round(gap, 2),
            trend=trend,
            critical_year=critical_year,
            findings=findings,
        )

    def _generate_findings(
        self,
        demand: DemandMetrics,
        supply: SupplyMetrics,
        balance_ratio: float,
        runway: Optional[float],
        gap: float
    ) -> List[str]:
        """Generate key findings from analysis"""
        findings = []

        # Balance assessment
        if balance_ratio >= 1.5:
            findings.append(f"Strong funding surplus: supply is {balance_ratio:.1f}x demand")
        elif balance_ratio >= 1.0:
            findings.append(f"Adequate funding: supply slightly exceeds demand ({balance_ratio:.1f}x)")
        else:
            findings.append(f"Funding pressure: demand exceeds available supply ({balance_ratio:.1f}x)")

        # Demand intensity
        if demand.demand_intensity in ["high", "very_high"]:
            findings.append(f"High capital intensity: Capex consuming {demand.capex_to_cf_ratio*100:.0f}% of operating cash flow")

        # Supply conditions
        if supply.supply_conditions == "favorable":
            findings.append("Credit markets supportive of corporate financing")
        elif supply.supply_conditions == "tight":
            findings.append("Credit conditions may constrain external funding")

        # Runway warning
        if runway and runway < 3:
            findings.append(f"Warning: At current trajectory, funding gap emerges in ~{runway:.0f} years")

        # Gap assessment
        if gap < 0:
            findings.append(f"Annual funding gap of ${abs(gap):.0f}B requires attention")
        elif gap > 100:
            findings.append(f"Comfortable funding buffer of ${gap:.0f}B annually")

        return findings

    def calculate_historical_supply_demand(self, consolidated: Dict) -> List[Dict]:
        """
        Calculate historical supply-demand data from SEC filings

        Args:
            consolidated: Consolidated company data

        Returns:
            List of historical yearly data with actual growth rates
        """
        companies = consolidated.get("companies", {})

        # Collect annual data by calendar year from Yahoo Finance historical data
        yearly_capex = {}  # year -> total capex
        yearly_ocf = {}    # year -> total operating cash flow

        for company_name, company_data in companies.items():
            yahoo_hist = company_data.get("yahoo_historical", {})

            # Get CapEx data from Yahoo historical
            capex_data = yahoo_hist.get("capex", [])
            for item in capex_data:
                year = item.get("year")
                value = item.get("value", 0)
                if year and value > 0:
                    if year not in yearly_capex:
                        yearly_capex[year] = 0
                    yearly_capex[year] += value  # Already in billions

            # Get Operating Cash Flow data from Yahoo historical
            ocf_data = yahoo_hist.get("ocf", [])
            for item in ocf_data:
                year = item.get("year")
                value = item.get("value", 0)
                if year and value > 0:
                    if year not in yearly_ocf:
                        yearly_ocf[year] = 0
                    yearly_ocf[year] += value  # Already in billions

        # Build historical records for recent years
        current_year = self.base_year
        historical = []

        # Get sorted years that have both capex and ocf data
        common_years = sorted(set(yearly_capex.keys()) & set(yearly_ocf.keys()), reverse=True)

        # Take recent complete years with substantial data
        # CapEx threshold: >$90B (5-6 companies)
        # OCF threshold: >$200B (6 companies)
        # This ensures we're comparing years with similar company coverage
        recent_years = [y for y in common_years
                        if y < current_year
                        and yearly_capex.get(y, 0) > 90
                        and yearly_ocf.get(y, 0) > 200][:5]  # Up to 5 years of history
        recent_years = sorted(recent_years)  # Sort ascending

        prev_demand = None
        prev_supply = None

        for year in recent_years:
            demand = yearly_capex.get(year, 0)
            # Supply approximation: OCF + estimated debt/equity capacity
            # Use a multiplier similar to how implied_funding_capacity is calculated
            ocf = yearly_ocf.get(year, 0)
            supply = ocf * 1.6  # Approximate total capacity

            # Calculate YoY growth rates
            demand_growth = None
            supply_growth = None
            if prev_demand and prev_demand > 0:
                demand_growth = round((demand - prev_demand) / prev_demand * 100, 1)
            if prev_supply and prev_supply > 0:
                supply_growth = round((supply - prev_supply) / prev_supply * 100, 1)

            gap = supply - demand
            balance_ratio = supply / demand if demand > 0 else 1

            historical.append({
                "year": year,
                "demand_B": round(demand, 1),
                "supply_B": round(supply, 1),
                "gap_B": round(gap, 1),
                "balance_ratio": round(balance_ratio, 2),
                "status": "surplus" if gap > 0 else "deficit",
                "risk_level": "LOW" if balance_ratio > 1.2 else ("MEDIUM" if balance_ratio > 0.9 else "HIGH"),
                "demand_growth_pct": demand_growth,
                "supply_growth_pct": supply_growth,
                "is_historical": True
            })

            prev_demand = demand
            prev_supply = supply

        return historical

    def project_balance(
        self,
        demand: DemandMetrics,
        supply: SupplyMetrics,
        years: int = 5,
        demand_growth: float = None,
        supply_growth: float = None,
        consolidated: Dict = None,
        historical: List[Dict] = None
    ) -> List[Dict]:
        """
        Project supply-demand balance over multiple years, starting from
        the last historical year's data.

        Args:
            demand: Current demand metrics
            supply: Current supply metrics
            years: Years to project
            demand_growth: Demand growth rate (defaults to demand.capex_growth_rate)
            supply_growth: Supply growth rate (calculated from historical data if None)
            consolidated: Consolidated data for calculating supply growth
            historical: Historical data to continue from

        Returns:
            List of yearly projections
        """
        if demand_growth is None:
            demand_growth = demand.capex_growth_rate

        # Calculate supply growth from historical data if not provided
        if supply_growth is None:
            if consolidated:
                supply_growth = self._calculate_fcf_growth_rate(consolidated)
            else:
                supply_growth = 0.12  # Fallback default

        projections = []

        # Start from the last historical data point if available
        if historical and len(historical) > 0:
            last_hist = historical[-1]
            start_year = last_hist["year"] + 1
            current_demand = last_hist["demand_B"] * (1 + demand_growth)
            current_supply = last_hist["supply_B"] * (1 + supply_growth)
        else:
            # Fallback to original behavior
            start_year = self.base_year
            current_demand = demand.implied_annual_demand_B
            current_supply = supply.implied_funding_capacity_B

        for year in range(years + 1):
            projection_year = start_year + year

            balance_ratio = current_supply / current_demand if current_demand > 0 else 1
            gap = current_supply - current_demand

            # Show projected growth rate for all years
            proj_demand_growth = round(demand_growth * 100, 1)
            proj_supply_growth = round(supply_growth * 100, 1)

            projections.append({
                "year": projection_year,
                "demand_B": round(current_demand, 1),
                "supply_B": round(current_supply, 1),
                "gap_B": round(gap, 1),
                "balance_ratio": round(balance_ratio, 2),
                "status": "surplus" if gap > 0 else "deficit",
                "risk_level": "LOW" if balance_ratio > 1.2 else ("MEDIUM" if balance_ratio > 0.9 else "HIGH"),
                "demand_growth_pct": proj_demand_growth,
                "supply_growth_pct": proj_supply_growth,
                "is_historical": False
            })

            # Project forward
            current_demand *= (1 + demand_growth)
            current_supply *= (1 + supply_growth)

        return projections

    def run_analysis(self) -> Dict:
        """
        Run complete supply-demand analysis

        Returns:
            Complete analysis results
        """
        print("=" * 60)
        print("Supply-Demand Balance Analysis")
        print("=" * 60)

        data = self.load_data()

        if not data.get("consolidated"):
            print("Error: Consolidated data not found. Run data processing first.")
            return {}

        # Calculate metrics
        print("\nCalculating demand metrics...")
        demand = self.calculate_demand_metrics(data["consolidated"])
        print(f"  Total Capex: ${demand.total_capex_B:.1f}B")
        print(f"  Capex/CF Ratio: {demand.capex_to_cf_ratio:.1%}")
        print(f"  Demand Growth Rate: {demand.capex_growth_rate:.1%} (from historical data)")
        print(f"  Demand Intensity: {demand.demand_intensity}")

        print("\nCalculating supply metrics...")
        credit_data = data.get("credit", {})
        supply = self.calculate_supply_metrics(data["consolidated"], credit_data)
        supply_growth = self._calculate_fcf_growth_rate(data["consolidated"])
        print(f"  Total Cash Holdings: ${supply.total_cash_holdings_B:.1f}B")
        print(f"  Annual FCF: ${supply.total_free_cashflow_B:.1f}B")
        print(f"  Implied Capacity: ${supply.implied_funding_capacity_B:.1f}B")
        print(f"  Supply Growth Rate: {supply_growth:.1%} (from historical data)")
        print(f"  Supply Conditions: {supply.supply_conditions}")

        print("\nAnalyzing balance...")
        # Pass consolidated data for calculating supply growth from historical data
        balance = self.analyze_balance(demand, supply, data.get("scenarios"), data["consolidated"])

        print("\nCalculating historical data...")
        historical = self.calculate_historical_supply_demand(data["consolidated"])

        print("\nProjecting forward...")
        # Pass historical data to continue projection from last historical year
        projections = self.project_balance(
            demand, supply, years=5,
            consolidated=data["consolidated"],
            historical=historical
        )

        result = {
            "timestamp": datetime.now().isoformat(),
            "demand_metrics": asdict(demand),
            "supply_metrics": asdict(supply),
            "balance_analysis": asdict(balance),
            "historical": historical,
            "projections": projections,
        }

        return result

    def save_analysis(self, analysis: Dict, filename: str = "supply_demand_analysis.json"):
        """Save analysis to file"""
        output_path = PROCESSED_DATA_DIR / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        print(f"\nAnalysis saved to {output_path}")
        return output_path


def main():
    """Run supply-demand analysis"""
    analyzer = SupplyDemandAnalyzer()
    analysis = analyzer.run_analysis()

    if analysis:
        analyzer.save_analysis(analysis)

        # Print summary
        print("\n" + "=" * 60)
        print("SUPPLY-DEMAND ANALYSIS SUMMARY")
        print("=" * 60)

        balance = analysis.get("balance_analysis", {})
        print(f"\nBalance Ratio: {balance.get('balance_ratio', 'N/A')}x")
        print(f"Sustainability Score: {balance.get('sustainability_score', 'N/A')}/100")
        print(f"Annual Gap: ${balance.get('gap_annual_B', 0):+.1f}B")
        print(f"Trend: {balance.get('trend', 'N/A').upper()}")

        if balance.get("critical_year"):
            print(f"Critical Year: {balance['critical_year']}")

        print("\nKey Findings:")
        for finding in balance.get("findings", []):
            print(f"  • {finding}")

        print("\n5-Year Projection:")
        print(f"{'Year':<6} {'Demand':>10} {'Supply':>10} {'Gap':>10} {'Status':>10}")
        print("-" * 50)
        for proj in analysis.get("projections", []):
            print(f"{proj['year']:<6} ${proj['demand_B']:>8.0f}B ${proj['supply_B']:>8.0f}B ${proj['gap_B']:>+8.0f}B {proj['status']:>10}")

    return analysis


if __name__ == "__main__":
    main()
