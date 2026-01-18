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

        # Estimate growth rate from scenarios or use default
        capex_growth = 0.25  # Default 25% growth assumption

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
        scenarios: Dict = None
    ) -> BalanceAnalysis:
        """
        Analyze supply-demand balance

        Args:
            demand: Demand metrics
            supply: Supply metrics
            scenarios: Scenario projections (optional)

        Returns:
            BalanceAnalysis with complete analysis
        """
        # Calculate balance ratio
        balance_ratio = supply.implied_funding_capacity_B / demand.implied_annual_demand_B if demand.implied_annual_demand_B > 0 else 1

        # Calculate annual gap
        gap = supply.implied_funding_capacity_B - demand.implied_annual_demand_B

        # Calculate runway (years until supply exhausted at current growth)
        # Simplified model: supply grows at ~12%, demand at ~25%
        supply_growth = 0.12
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

    def project_balance(
        self,
        demand: DemandMetrics,
        supply: SupplyMetrics,
        years: int = 5,
        demand_growth: float = None,
        supply_growth: float = 0.12
    ) -> List[Dict]:
        """
        Project supply-demand balance over multiple years

        Args:
            demand: Current demand metrics
            supply: Current supply metrics
            years: Years to project
            demand_growth: Demand growth rate (defaults to demand.capex_growth_rate)
            supply_growth: Supply growth rate

        Returns:
            List of yearly projections
        """
        if demand_growth is None:
            demand_growth = demand.capex_growth_rate

        projections = []
        current_demand = demand.implied_annual_demand_B
        current_supply = supply.implied_funding_capacity_B

        for year in range(years + 1):
            projection_year = self.base_year + year

            balance_ratio = current_supply / current_demand if current_demand > 0 else 1
            gap = current_supply - current_demand

            projections.append({
                "year": projection_year,
                "demand_B": round(current_demand, 1),
                "supply_B": round(current_supply, 1),
                "gap_B": round(gap, 1),
                "balance_ratio": round(balance_ratio, 2),
                "status": "surplus" if gap > 0 else "deficit",
                "risk_level": "LOW" if balance_ratio > 1.2 else ("MEDIUM" if balance_ratio > 0.9 else "HIGH"),
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
        print(f"  Demand Intensity: {demand.demand_intensity}")

        print("\nCalculating supply metrics...")
        credit_data = data.get("credit", {})
        supply = self.calculate_supply_metrics(data["consolidated"], credit_data)
        print(f"  Total Cash Holdings: ${supply.total_cash_holdings_B:.1f}B")
        print(f"  Annual FCF: ${supply.total_free_cashflow_B:.1f}B")
        print(f"  Implied Capacity: ${supply.implied_funding_capacity_B:.1f}B")
        print(f"  Supply Conditions: {supply.supply_conditions}")

        print("\nAnalyzing balance...")
        balance = self.analyze_balance(demand, supply, data.get("scenarios"))

        print("\nProjecting forward...")
        projections = self.project_balance(demand, supply, years=5)

        result = {
            "timestamp": datetime.now().isoformat(),
            "demand_metrics": asdict(demand),
            "supply_metrics": asdict(supply),
            "balance_analysis": asdict(balance),
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
