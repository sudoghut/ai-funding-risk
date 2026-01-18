"""
Risk Calculator Module
Calculates funding risk scores based on consumption vs. supply metrics
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import RISK_THRESHOLDS, RISK_LEVELS, PROCESSED_DATA_DIR


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class RiskIndicator:
    """Individual risk indicator with score and details"""
    name: str
    category: str  # "consumption", "supply", "efficiency"
    value: Optional[float]
    threshold_low: float
    threshold_high: float
    risk_level: str
    score: float  # 0-100, higher = more risk
    description: str
    is_estimated: bool = False  # True if value is null and score is default


@dataclass
class CompanyRiskProfile:
    """Risk profile for a single company"""
    company_name: str
    ticker: str
    overall_risk_score: float
    risk_level: str
    indicators: List[Dict]
    summary: str
    data_quality: str = "high"  # high, medium, low
    missing_indicators: int = 0


@dataclass
class SystemicRiskAssessment:
    """Overall AI funding ecosystem risk assessment"""
    assessment_date: str
    overall_risk_score: float
    risk_level: str
    consumption_score: float
    supply_score: float
    efficiency_score: float
    company_profiles: List[Dict]
    macro_factors: Dict
    key_findings: List[str]
    recommendations: List[str]
    data_quality_summary: Dict = None  # Summary of data quality across companies


class RiskCalculator:
    """Calculates AI funding risk based on multiple indicators"""

    def __init__(self):
        self.thresholds = RISK_THRESHOLDS
        self.processed_dir = PROCESSED_DATA_DIR

    def load_consolidated_data(self) -> Optional[Dict]:
        """Load consolidated data from processing step"""
        filepath = self.processed_dir / "consolidated_data.json"
        if not filepath.exists():
            print(f"Consolidated data not found: {filepath}")
            print("Run scripts/process_data.py first")
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def calculate_indicator_score(
        self,
        value: Optional[float],
        threshold_normal: float,
        threshold_warning: float,
        inverse: bool = False
    ) -> Tuple[float, str, bool]:
        """
        Calculate risk score for a single indicator

        Args:
            value: The metric value
            threshold_normal: Below this = low risk
            threshold_warning: Above this = high risk
            inverse: If True, lower values = higher risk

        Returns:
            Tuple of (score 0-100, risk_level string, is_estimated bool)
        """
        if value is None:
            # Return estimated flag to indicate low confidence
            return 50.0, "MEDIUM", True  # Unknown = medium risk, is_estimated=True

        if inverse:
            # For inverse metrics, flip the logic
            if value > threshold_normal:
                return 20.0, "LOW", False
            elif value > threshold_warning:
                # Linear interpolation in warning zone
                range_size = threshold_normal - threshold_warning
                if range_size != 0:
                    progress = (threshold_normal - value) / range_size
                    score = 30 + (progress * 40)
                else:
                    score = 50
                return score, "MEDIUM", False
            else:
                return 80.0, "HIGH", False
        else:
            # Normal logic: higher value = higher risk
            if value < threshold_normal:
                return 20.0, "LOW", False
            elif value < threshold_warning:
                # Linear interpolation in warning zone
                range_size = threshold_warning - threshold_normal
                if range_size != 0:
                    progress = (value - threshold_normal) / range_size
                    score = 30 + (progress * 40)
                else:
                    score = 50
                return score, "MEDIUM", False
            else:
                return 80.0, "HIGH", False

    def assess_company_risk(
        self, company_name: str, company_data: Dict
    ) -> CompanyRiskProfile:
        """
        Calculate risk profile for a single company

        Args:
            company_name: Company identifier
            company_data: Company data from consolidated dataset

        Returns:
            CompanyRiskProfile with detailed assessment
        """
        indicators = []
        derived = company_data.get("derived_metrics", {})
        yahoo = company_data.get("yahoo_metrics", {})
        ticker = company_data.get("ticker", "")
        missing_count = 0

        # 1. Capex to Cash Flow Ratio (Consumption indicator)
        capex_ratio = derived.get("capex_to_cashflow_ratio")
        score, level, is_estimated = self.calculate_indicator_score(
            capex_ratio,
            self.thresholds["capex_to_cashflow"]["normal"],
            self.thresholds["capex_to_cashflow"]["warning"]
        )
        if is_estimated:
            missing_count += 1
        indicators.append(RiskIndicator(
            name="Capex to Cash Flow Ratio",
            category="consumption",
            value=capex_ratio,
            threshold_low=self.thresholds["capex_to_cashflow"]["normal"],
            threshold_high=self.thresholds["capex_to_cashflow"]["warning"],
            risk_level=level,
            score=score,
            description="Capital expenditure as percentage of operating cash flow",
            is_estimated=is_estimated
        ))

        # 2. Debt to Revenue Growth Ratio
        debt_rev_ratio = derived.get("debt_to_revenue_growth_ratio")
        score, level, is_estimated = self.calculate_indicator_score(
            debt_rev_ratio,
            self.thresholds["debt_to_revenue_growth"]["normal"],
            self.thresholds["debt_to_revenue_growth"]["warning"]
        )
        if is_estimated:
            missing_count += 1
        indicators.append(RiskIndicator(
            name="Debt vs Revenue Growth",
            category="efficiency",
            value=debt_rev_ratio,
            threshold_low=self.thresholds["debt_to_revenue_growth"]["normal"],
            threshold_high=self.thresholds["debt_to_revenue_growth"]["warning"],
            risk_level=level,
            score=score,
            description="Debt growth relative to revenue growth",
            is_estimated=is_estimated
        ))

        # 3. Capex Growth Rate (Higher = more aggressive spending)
        capex_growth = derived.get("capex_growth_yoy")
        score, level, is_estimated = self.calculate_indicator_score(capex_growth, 30, 50)
        if is_estimated:
            missing_count += 1
        indicators.append(RiskIndicator(
            name="Capex Growth Rate",
            category="consumption",
            value=capex_growth,
            threshold_low=30,
            threshold_high=50,
            risk_level=level,
            score=score,
            description="Year-over-year growth in capital expenditure (%)",
            is_estimated=is_estimated
        ))

        # 4. Revenue Growth (positive signal - inverse scoring)
        revenue_growth = derived.get("revenue_growth_yoy")
        score, level, is_estimated = self.calculate_indicator_score(
            revenue_growth, 10, 5, inverse=True
        )
        if is_estimated:
            missing_count += 1
        indicators.append(RiskIndicator(
            name="Revenue Growth",
            category="efficiency",
            value=revenue_growth,
            threshold_low=10,
            threshold_high=5,
            risk_level=level,
            score=score,
            description="Year-over-year revenue growth (%)",
            is_estimated=is_estimated
        ))

        # 5. Debt to Cash Ratio (from Yahoo)
        debt_cash_ratio = yahoo.get("debt_to_cash_ratio")
        score, level, is_estimated = self.calculate_indicator_score(debt_cash_ratio, 3, 5)
        if is_estimated:
            missing_count += 1
        indicators.append(RiskIndicator(
            name="Debt to Cash Ratio",
            category="supply",
            value=debt_cash_ratio,
            threshold_low=3,
            threshold_high=5,
            risk_level=level,
            score=score,
            description="Total debt relative to total cash holdings",
            is_estimated=is_estimated
        ))

        # Calculate overall score (weighted average)
        weights = {
            "consumption": 0.35,
            "supply": 0.35,
            "efficiency": 0.30
        }

        category_scores = {"consumption": [], "supply": [], "efficiency": []}
        for ind in indicators:
            category_scores[ind.category].append(ind.score)

        weighted_score = 0
        for category, scores in category_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                weighted_score += avg_score * weights[category]

        # Determine overall risk level
        if weighted_score < 40:
            overall_level = "LOW"
        elif weighted_score < 65:
            overall_level = "MEDIUM"
        else:
            overall_level = "HIGH"

        # Determine data quality based on missing indicators
        total_indicators = len(indicators)
        if missing_count == 0:
            data_quality = "high"
        elif missing_count <= 2:
            data_quality = "medium"
        else:
            data_quality = "low"

        # Generate summary
        high_risk_indicators = [i for i in indicators if i.risk_level == "HIGH"]
        quality_note = f" (data quality: {data_quality}, {missing_count}/{total_indicators} estimated)" if missing_count > 0 else ""

        if high_risk_indicators:
            summary = f"Elevated risk due to: {', '.join([i.name for i in high_risk_indicators])}{quality_note}"
        elif weighted_score < 40:
            summary = f"Healthy financial position with sustainable spending patterns{quality_note}"
        else:
            summary = f"Moderate risk profile - monitor key indicators{quality_note}"

        return CompanyRiskProfile(
            company_name=company_name,
            ticker=ticker,
            overall_risk_score=round(weighted_score, 1),
            risk_level=overall_level,
            indicators=[asdict(i) for i in indicators],
            summary=summary,
            data_quality=data_quality,
            missing_indicators=missing_count
        )

    def assess_macro_environment(self, macro_data: Dict) -> Dict:
        """
        Assess macroeconomic funding environment

        Args:
            macro_data: Macro indicators from consolidated data

        Returns:
            Dictionary with macro risk factors
        """
        macro_assessment = {
            "indicators": {},
            "overall_funding_environment": "neutral",
            "risk_factors": []
        }

        # Interest rate assessment
        fed_funds = macro_data.get("FEDFUNDS", {})
        if fed_funds:
            rate = fed_funds.get("latest_value", 0)
            score, level, _ = self.calculate_indicator_score(
                rate,
                self.thresholds["interest_rate"]["normal"],
                self.thresholds["interest_rate"]["warning"]
            )
            macro_assessment["indicators"]["interest_rate"] = {
                "value": rate,
                "risk_level": level,
                "score": score,
                "description": "Federal Funds Rate affects borrowing costs"
            }
            if level == "HIGH":
                macro_assessment["risk_factors"].append(
                    f"High interest rates ({rate}%) increase funding costs"
                )

        # Credit spread assessment (BAA - 10Y spread)
        baa_spread = macro_data.get("BAA10Y", {})
        if baa_spread:
            spread = baa_spread.get("latest_value", 0)
            score, level, _ = self.calculate_indicator_score(
                spread,
                self.thresholds["credit_spread"]["normal"],
                self.thresholds["credit_spread"]["warning"]
            )
            macro_assessment["indicators"]["credit_spread"] = {
                "value": spread,
                "risk_level": level,
                "score": score,
                "description": "Corporate bond spread indicates credit risk premium"
            }
            if level == "HIGH":
                macro_assessment["risk_factors"].append(
                    f"Wide credit spreads ({spread}%) signal risk aversion"
                )

        # High yield spread
        hy_spread = macro_data.get("BAMLH0A0HYM2", {})
        if hy_spread:
            spread = hy_spread.get("latest_value", 0)
            # High yield considered elevated if >4%, high risk if >6%
            score, level, _ = self.calculate_indicator_score(spread, 4, 6)
            macro_assessment["indicators"]["high_yield_spread"] = {
                "value": spread,
                "risk_level": level,
                "score": score,
                "description": "High yield bond spread indicates market risk appetite"
            }

        # Determine overall environment
        high_risk_count = sum(
            1 for ind in macro_assessment["indicators"].values()
            if ind.get("risk_level") == "HIGH"
        )
        if high_risk_count >= 2:
            macro_assessment["overall_funding_environment"] = "restrictive"
        elif high_risk_count == 1:
            macro_assessment["overall_funding_environment"] = "cautious"
        else:
            macro_assessment["overall_funding_environment"] = "favorable"

        return macro_assessment

    def generate_systemic_assessment(self, data: Dict) -> SystemicRiskAssessment:
        """
        Generate comprehensive systemic risk assessment

        Args:
            data: Consolidated data from all sources

        Returns:
            SystemicRiskAssessment with full analysis
        """
        companies = data.get("companies", {})
        macro = data.get("macro_indicators", {})

        # Assess each company
        company_profiles = []
        consumption_scores = []
        supply_scores = []
        efficiency_scores = []

        for company_name, company_data in companies.items():
            profile = self.assess_company_risk(company_name, company_data)
            company_profiles.append(asdict(profile))

            # Extract category scores
            for indicator in profile.indicators:
                if indicator["category"] == "consumption":
                    consumption_scores.append(indicator["score"])
                elif indicator["category"] == "supply":
                    supply_scores.append(indicator["score"])
                elif indicator["category"] == "efficiency":
                    efficiency_scores.append(indicator["score"])

        # Calculate aggregate scores
        consumption_score = (
            sum(consumption_scores) / len(consumption_scores)
            if consumption_scores else 50
        )
        supply_score = (
            sum(supply_scores) / len(supply_scores)
            if supply_scores else 50
        )
        efficiency_score = (
            sum(efficiency_scores) / len(efficiency_scores)
            if efficiency_scores else 50
        )

        # Assess macro environment
        macro_assessment = self.assess_macro_environment(macro)

        # Calculate overall risk score
        # Weight: 40% consumption, 30% supply, 20% efficiency, 10% macro
        macro_score = 50  # Default
        if macro_assessment["indicators"]:
            macro_score = sum(
                ind["score"] for ind in macro_assessment["indicators"].values()
            ) / len(macro_assessment["indicators"])

        overall_score = (
            consumption_score * 0.40 +
            supply_score * 0.30 +
            efficiency_score * 0.20 +
            macro_score * 0.10
        )

        # Determine risk level
        if overall_score < 40:
            risk_level = "LOW"
        elif overall_score < 65:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # Generate data quality summary
        total_companies = len(company_profiles)
        high_quality = sum(1 for p in company_profiles if p.get("data_quality") == "high")
        medium_quality = sum(1 for p in company_profiles if p.get("data_quality") == "medium")
        low_quality = sum(1 for p in company_profiles if p.get("data_quality") == "low")
        total_missing = sum(p.get("missing_indicators", 0) for p in company_profiles)
        total_indicators = total_companies * 5  # 5 indicators per company

        data_quality_summary = {
            "overall_quality": "high" if high_quality > total_companies / 2 else ("medium" if low_quality < total_companies / 2 else "low"),
            "companies_by_quality": {
                "high": high_quality,
                "medium": medium_quality,
                "low": low_quality,
            },
            "total_missing_values": total_missing,
            "total_indicators": total_indicators,
            "data_completeness_pct": round((1 - total_missing / total_indicators) * 100, 1) if total_indicators > 0 else 0,
            "confidence_note": "Scores with missing data use neutral estimates (50) and may not reflect actual risk" if total_missing > 0 else "All indicators have actual data"
        }

        # Generate key findings
        key_findings = self._generate_key_findings(
            company_profiles, macro_assessment, consumption_score, supply_score
        )

        # Add data quality finding if needed
        if data_quality_summary["data_completeness_pct"] < 80:
            key_findings.insert(0, f"Data quality note: {data_quality_summary['data_completeness_pct']}% data completeness - {total_missing} indicators estimated")

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, key_findings, macro_assessment
        )

        return SystemicRiskAssessment(
            assessment_date=datetime.now().isoformat(),
            overall_risk_score=round(overall_score, 1),
            risk_level=risk_level,
            consumption_score=round(consumption_score, 1),
            supply_score=round(supply_score, 1),
            efficiency_score=round(efficiency_score, 1),
            company_profiles=company_profiles,
            macro_factors=macro_assessment,
            key_findings=key_findings,
            recommendations=recommendations,
            data_quality_summary=data_quality_summary
        )

    def _generate_key_findings(
        self,
        company_profiles: List[Dict],
        macro_assessment: Dict,
        consumption_score: float,
        supply_score: float
    ) -> List[str]:
        """Generate key findings from the assessment"""
        findings = []

        # High-risk companies
        high_risk_companies = [
            p["company_name"] for p in company_profiles
            if p["risk_level"] == "HIGH"
        ]
        if high_risk_companies:
            findings.append(
                f"High risk identified for: {', '.join(high_risk_companies)}"
            )

        # Load supply-demand analysis for cross-validation if available
        supply_demand_file = self.processed_dir / "supply_demand_analysis.json"
        supply_demand_data = None
        if supply_demand_file.exists():
            try:
                with open(supply_demand_file, "r", encoding="utf-8") as f:
                    supply_demand_data = json.load(f)
            except Exception:
                pass

        # Use supply-demand analysis if available for accurate assessment
        if supply_demand_data:
            balance = supply_demand_data.get("balance_analysis", {})
            balance_ratio = balance.get("balance_ratio", 1.0)
            gap = balance.get("gap_annual_B", 0)

            if balance_ratio >= 1.5:
                findings.append(
                    f"Strong funding surplus: supply is {balance_ratio:.1f}x demand (gap: +${gap:.0f}B)"
                )
            elif balance_ratio >= 1.0:
                findings.append(
                    f"Adequate funding balance: supply meets demand ({balance_ratio:.1f}x)"
                )
            else:
                findings.append(
                    f"Funding pressure: demand exceeds supply ({balance_ratio:.1f}x, gap: ${gap:.0f}B)"
                )
        else:
            # Fallback to risk score comparison
            # Note: These are RISK scores (higher = more risky), not actual amounts
            # consumption_score > supply_score means consumption is riskier
            if consumption_score > supply_score + 15:
                findings.append(
                    "Elevated consumption risk relative to supply risk indicators"
                )
            elif supply_score > consumption_score + 15:
                findings.append(
                    "Supply risk elevated - monitor funding availability"
                )

        # Macro environment
        env = macro_assessment.get("overall_funding_environment", "neutral")
        if env == "restrictive":
            findings.append(
                "Macroeconomic environment is restrictive for new funding"
            )
        elif env == "favorable":
            findings.append(
                "Favorable macroeconomic conditions support continued investment"
            )

        # Specific macro risks
        findings.extend(macro_assessment.get("risk_factors", []))

        # Aggregate capex trends
        high_capex_growth = [
            p["company_name"] for p in company_profiles
            if any(
                i["name"] == "Capex Growth Rate" and i["risk_level"] == "HIGH"
                for i in p["indicators"]
            )
        ]
        if len(high_capex_growth) >= 3:
            findings.append(
                f"Multiple companies with aggressive capex growth: {', '.join(high_capex_growth)}"
            )

        if not findings:
            findings.append("No significant risk factors identified")

        return findings

    def _generate_recommendations(
        self,
        risk_level: str,
        key_findings: List[str],
        macro_assessment: Dict
    ) -> List[str]:
        """Generate recommendations based on assessment"""
        recommendations = []

        if risk_level == "HIGH":
            recommendations.append(
                "Consider reducing exposure to highest-risk companies"
            )
            recommendations.append(
                "Monitor debt levels and cash flow coverage closely"
            )
            recommendations.append(
                "Evaluate sustainability of current investment pace"
            )
        elif risk_level == "MEDIUM":
            recommendations.append(
                "Maintain diversified exposure across AI infrastructure players"
            )
            recommendations.append(
                "Monitor quarterly earnings for deterioration in key metrics"
            )
        else:
            recommendations.append(
                "Current funding environment appears sustainable"
            )
            recommendations.append(
                "Continue monitoring for early warning signs"
            )

        # Macro-specific recommendations
        env = macro_assessment.get("overall_funding_environment", "neutral")
        if env == "restrictive":
            recommendations.append(
                "Rising rates may pressure companies with high debt levels"
            )

        return recommendations

    def run_assessment(self) -> Optional[SystemicRiskAssessment]:
        """
        Run complete risk assessment

        Returns:
            SystemicRiskAssessment or None if data not available
        """
        print("=" * 60)
        print("AI Funding Risk Assessment")
        print("=" * 60)

        # Load data
        data = self.load_consolidated_data()
        if data is None:
            return None

        # Generate assessment
        print("\nAnalyzing risk indicators...")
        assessment = self.generate_systemic_assessment(data)

        # Save results
        output_path = self.processed_dir / "risk_assessment.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(assessment), f, indent=2, ensure_ascii=False)
        print(f"\nAssessment saved to {output_path}")

        return assessment

    def print_assessment_summary(self, assessment: SystemicRiskAssessment):
        """Print a formatted summary of the assessment"""
        print("\n" + "=" * 60)
        print("RISK ASSESSMENT SUMMARY")
        print("=" * 60)

        # Overall score
        print(f"\nOverall Risk Score: {assessment.overall_risk_score}/100")
        print(f"Risk Level: {assessment.risk_level}")

        # Category scores
        print(f"\nCategory Scores:")
        print(f"  Consumption (Capex pressure): {assessment.consumption_score}/100")
        print(f"  Supply (Funding availability): {assessment.supply_score}/100")
        print(f"  Efficiency (ROI on spending): {assessment.efficiency_score}/100")

        # Macro environment
        macro_env = assessment.macro_factors.get("overall_funding_environment", "unknown")
        print(f"\nMacro Environment: {macro_env.upper()}")

        # Company profiles
        print("\n" + "-" * 60)
        print("COMPANY RISK PROFILES")
        print("-" * 60)
        print(f"{'Company':<15} {'Ticker':<8} {'Score':<8} {'Level':<10}")
        print("-" * 60)
        for profile in assessment.company_profiles:
            print(
                f"{profile['company_name']:<15} "
                f"{profile['ticker']:<8} "
                f"{profile['overall_risk_score']:<8} "
                f"{profile['risk_level']:<10}"
            )

        # Key findings
        print("\n" + "-" * 60)
        print("KEY FINDINGS")
        print("-" * 60)
        for finding in assessment.key_findings:
            print(f"  * {finding}")

        # Recommendations
        print("\n" + "-" * 60)
        print("RECOMMENDATIONS")
        print("-" * 60)
        for rec in assessment.recommendations:
            print(f"  * {rec}")

        print("\n" + "=" * 60)


def main():
    """Main function to run risk assessment"""
    calculator = RiskCalculator()
    assessment = calculator.run_assessment()

    if assessment:
        calculator.print_assessment_summary(assessment)

    return assessment


if __name__ == "__main__":
    main()
