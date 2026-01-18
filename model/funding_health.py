"""
Funding Environment Health Assessment Module
Integrates multiple data sources to assess AI funding sustainability
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    PROCESSED_DATA_DIR, MARKET_DATA_DIR,
    WARNING_THRESHOLDS_CREDIT, WARNING_THRESHOLDS_EQUITY, WARNING_THRESHOLDS_COMPANY,
    RISK_WEIGHTS, ALERT_LEVELS
)


class AlertLevel(Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"


@dataclass
class IndicatorAssessment:
    """Assessment result for a single indicator"""
    name: str
    category: str
    value: float
    score: float  # 0-100, higher = healthier
    alert_level: str
    threshold_yellow: float
    threshold_orange: float
    threshold_red: float
    interpretation: str
    trend: str = None
    week_change: float = None


@dataclass
class CategoryAssessment:
    """Assessment result for a category of indicators"""
    category: str
    score: float
    alert_level: str
    indicators: List[Dict]
    summary: str


@dataclass
class FundingHealthReport:
    """Complete funding health assessment report"""
    timestamp: str
    overall_score: float
    alert_level: str
    alert_description: str

    credit_market: Dict
    equity_market: Dict
    company_fundamentals: Dict

    triggered_warnings: List[Dict]
    key_findings: List[str]
    recommendations: List[str]


class FundingHealthAssessor:
    """Assesses overall funding environment health for AI sector"""

    def __init__(self):
        self.credit_thresholds = WARNING_THRESHOLDS_CREDIT
        self.equity_thresholds = WARNING_THRESHOLDS_EQUITY
        self.company_thresholds = WARNING_THRESHOLDS_COMPANY
        self.weights = RISK_WEIGHTS
        self.alert_levels = ALERT_LEVELS

    def load_market_data(self) -> Dict:
        """Load market data from saved files"""
        market_data = {}

        # Load credit market data
        credit_file = MARKET_DATA_DIR / "credit_market_data.json"
        if credit_file.exists():
            with open(credit_file, "r", encoding="utf-8") as f:
                market_data["credit"] = json.load(f)

        # Load market indicators
        market_file = MARKET_DATA_DIR / "market_indicators.json"
        if market_file.exists():
            with open(market_file, "r", encoding="utf-8") as f:
                market_data["market"] = json.load(f)

        # Load company data
        risk_file = PROCESSED_DATA_DIR / "risk_assessment.json"
        if risk_file.exists():
            with open(risk_file, "r", encoding="utf-8") as f:
                market_data["company"] = json.load(f)

        # Load consolidated company data
        consolidated_file = PROCESSED_DATA_DIR / "consolidated_data.json"
        if consolidated_file.exists():
            with open(consolidated_file, "r", encoding="utf-8") as f:
                market_data["consolidated"] = json.load(f)

        return market_data

    def assess_credit_market(self, credit_data: Dict) -> CategoryAssessment:
        """
        Assess credit market health

        Args:
            credit_data: Credit market data dictionary

        Returns:
            CategoryAssessment for credit market
        """
        indicators = []
        scores = []

        credit_market = credit_data.get("credit_market", {})

        # High Yield Spread
        hy_data = credit_market.get("BAMLH0A0HYM2", {})
        if hy_data and hy_data.get("latest"):
            value = hy_data["latest"]["value"]
            thresholds = self.credit_thresholds["high_yield_spread"]
            score, alert = self._calculate_score_inverse(value, thresholds)
            changes = hy_data.get("changes", {})

            indicators.append(asdict(IndicatorAssessment(
                name="High Yield Bond Spread",
                category="credit",
                value=value,
                score=score,
                alert_level=alert,
                threshold_yellow=thresholds["yellow"],
                threshold_orange=thresholds["orange"],
                threshold_red=thresholds["red"],
                interpretation=self._interpret_spread(value, "high_yield"),
                trend="up" if changes.get("1w_change", 0) > 0 else "down",
                week_change=changes.get("1w_change"),
            )))
            scores.append(score)

        # Investment Grade Spread
        ig_data = credit_market.get("BAMLC0A0CM", {})
        if ig_data and ig_data.get("latest"):
            value = ig_data["latest"]["value"]
            thresholds = self.credit_thresholds["investment_grade_spread"]
            score, alert = self._calculate_score_inverse(value, thresholds)
            changes = ig_data.get("changes", {})

            indicators.append(asdict(IndicatorAssessment(
                name="Investment Grade Spread",
                category="credit",
                value=value,
                score=score,
                alert_level=alert,
                threshold_yellow=thresholds["yellow"],
                threshold_orange=thresholds["orange"],
                threshold_red=thresholds["red"],
                interpretation=self._interpret_spread(value, "ig"),
                trend="up" if changes.get("1w_change", 0) > 0 else "down",
                week_change=changes.get("1w_change"),
            )))
            scores.append(score)

        # TED Spread
        ted_data = credit_market.get("TEDRATE", {})
        if ted_data and ted_data.get("latest"):
            value = ted_data["latest"]["value"]
            thresholds = self.credit_thresholds["ted_spread"]
            score, alert = self._calculate_score_inverse(value, thresholds)

            indicators.append(asdict(IndicatorAssessment(
                name="TED Spread (Interbank Risk)",
                category="credit",
                value=value,
                score=score,
                alert_level=alert,
                threshold_yellow=thresholds["yellow"],
                threshold_orange=thresholds["orange"],
                threshold_red=thresholds["red"],
                interpretation="Low interbank risk" if value < 0.35 else "Elevated interbank risk",
            )))
            scores.append(score)

        # Yield Curve
        yc_data = credit_market.get("T10Y2Y", {})
        if yc_data and yc_data.get("latest"):
            value = yc_data["latest"]["value"]
            thresholds = self.credit_thresholds["yield_curve_10y2y"]
            # Yield curve is special - positive is good, negative is bad
            score, alert = self._calculate_score_yield_curve(value, thresholds)

            indicators.append(asdict(IndicatorAssessment(
                name="Yield Curve (10Y-2Y)",
                category="credit",
                value=value,
                score=score,
                alert_level=alert,
                threshold_yellow=thresholds["yellow"],
                threshold_orange=thresholds["orange"],
                threshold_red=thresholds["red"],
                interpretation=self._interpret_yield_curve(value),
            )))
            scores.append(score)

        # Calculate category score
        category_score = sum(scores) / len(scores) if scores else 50
        category_alert = self._score_to_alert(category_score)

        return CategoryAssessment(
            category="credit_market",
            score=round(category_score, 1),
            alert_level=category_alert,
            indicators=indicators,
            summary=self._summarize_credit(category_score, indicators),
        )

    def assess_equity_market(self, market_data: Dict) -> CategoryAssessment:
        """
        Assess equity market health

        Args:
            market_data: Market indicators data dictionary

        Returns:
            CategoryAssessment for equity market
        """
        indicators = []
        scores = []

        # VIX Assessment
        vix_data = market_data.get("vix", {})
        vix_stats = vix_data.get("statistics", {})
        if vix_stats and vix_stats.get("current"):
            value = vix_stats["current"]
            thresholds = self.equity_thresholds["vix"]
            score, alert = self._calculate_score_inverse(value, thresholds)

            indicators.append(asdict(IndicatorAssessment(
                name="VIX (Volatility Index)",
                category="equity",
                value=value,
                score=score,
                alert_level=alert,
                threshold_yellow=thresholds["yellow"],
                threshold_orange=thresholds["orange"],
                threshold_red=thresholds["red"],
                interpretation=self._interpret_vix(value),
                week_change=vix_stats.get("week_change"),
            )))
            scores.append(score)

        # AI Stocks Performance
        ai_stocks = market_data.get("ai_stocks", {})
        ai_agg = ai_stocks.get("aggregate", {})
        if ai_agg and ai_agg.get("avg_1w_return") is not None:
            value = ai_agg["avg_1w_return"]
            thresholds = self.equity_thresholds["ai_stocks_weekly_drawdown"]
            score, alert = self._calculate_score_drawdown(value, thresholds)

            indicators.append(asdict(IndicatorAssessment(
                name="AI Stocks Avg Weekly Return",
                category="equity",
                value=value,
                score=score,
                alert_level=alert,
                threshold_yellow=thresholds["yellow"],
                threshold_orange=thresholds["orange"],
                threshold_red=thresholds["red"],
                interpretation="Positive momentum" if value > 0 else "Negative momentum",
            )))
            scores.append(score)

        # Tech ETF Performance
        etfs = market_data.get("etfs", {})
        tech_etfs = ["QQQ", "SMH", "XLK"]
        tech_returns = []
        for etf in tech_etfs:
            etf_data = etfs.get(etf, {})
            perf = etf_data.get("performance", {})
            if perf.get("1w_return") is not None:
                tech_returns.append(perf["1w_return"])

        if tech_returns:
            avg_tech_return = sum(tech_returns) / len(tech_returns)
            thresholds = self.equity_thresholds["tech_etf_weekly_drawdown"]
            score, alert = self._calculate_score_drawdown(avg_tech_return, thresholds)

            indicators.append(asdict(IndicatorAssessment(
                name="Tech ETF Avg Weekly Return",
                category="equity",
                value=avg_tech_return,
                score=score,
                alert_level=alert,
                threshold_yellow=thresholds["yellow"],
                threshold_orange=thresholds["orange"],
                threshold_red=thresholds["red"],
                interpretation="Tech sector healthy" if avg_tech_return > -2 else "Tech sector weak",
            )))
            scores.append(score)

        # IPO Market (using IPO ETF as proxy)
        ipo_data = etfs.get("IPO", {})
        ipo_perf = ipo_data.get("performance", {})
        if ipo_perf.get("1m_return") is not None:
            value = ipo_perf["1m_return"]
            # IPO market: positive return = open window
            score = max(0, min(100, 50 + value * 5))  # Scale: -10% = 0, +10% = 100
            alert = self._score_to_alert(score)

            indicators.append(asdict(IndicatorAssessment(
                name="IPO ETF Monthly Return",
                category="equity",
                value=value,
                score=score,
                alert_level=alert,
                threshold_yellow=-5,
                threshold_orange=-10,
                threshold_red=-20,
                interpretation="IPO window open" if value > -5 else "IPO window narrowing",
            )))
            scores.append(score)

        # Tech Sentiment (relative strength)
        rel_strength = market_data.get("relative_strength", {})
        tech_sent = rel_strength.get("tech_sentiment", {})
        if tech_sent.get("sentiment_score") is not None:
            value = tech_sent["sentiment_score"]
            score = value  # Already 0-100

            indicators.append(asdict(IndicatorAssessment(
                name="Tech Relative Strength",
                category="equity",
                value=value,
                score=score,
                alert_level=self._score_to_alert(score),
                threshold_yellow=40,
                threshold_orange=30,
                threshold_red=20,
                interpretation=tech_sent.get("interpretation", "neutral"),
            )))
            scores.append(score)

        # Calculate category score
        category_score = sum(scores) / len(scores) if scores else 50
        category_alert = self._score_to_alert(category_score)

        return CategoryAssessment(
            category="equity_market",
            score=round(category_score, 1),
            alert_level=category_alert,
            indicators=indicators,
            summary=self._summarize_equity(category_score, indicators),
        )

    def assess_company_fundamentals(self, company_data: Dict, consolidated: Dict) -> CategoryAssessment:
        """
        Assess company-level fundamentals

        Args:
            company_data: Risk assessment data
            consolidated: Consolidated company data

        Returns:
            CategoryAssessment for company fundamentals
        """
        indicators = []
        scores = []
        warnings = []

        company_profiles = company_data.get("company_profiles", [])
        companies = consolidated.get("companies", {})

        for profile in company_profiles:
            company_name = profile.get("company_name")
            ticker = profile.get("ticker")

            # Get additional data from consolidated
            company_detail = companies.get(company_name, {})
            yahoo_metrics = company_detail.get("yahoo_metrics", {})

            # Debt to Cash Ratio
            debt_to_cash = yahoo_metrics.get("debt_to_cash_ratio")
            if debt_to_cash is not None:
                thresholds = self.company_thresholds["debt_to_cash"]
                score, alert = self._calculate_score_inverse(debt_to_cash, thresholds)

                if alert in ["ORANGE", "RED"]:
                    warnings.append({
                        "company": company_name,
                        "indicator": "Debt to Cash Ratio",
                        "value": debt_to_cash,
                        "alert": alert,
                    })

                indicators.append({
                    "company": company_name,
                    "ticker": ticker,
                    "indicator": "Debt to Cash Ratio",
                    "value": debt_to_cash,
                    "score": score,
                    "alert_level": alert,
                })
                scores.append(score)

            # Overall company risk score (invert - lower original score = healthier)
            company_risk = profile.get("overall_risk_score", 50)
            company_health = 100 - company_risk

            indicators.append({
                "company": company_name,
                "ticker": ticker,
                "indicator": "Overall Health Score",
                "value": company_health,
                "score": company_health,
                "alert_level": self._score_to_alert(company_health),
            })
            scores.append(company_health)

        # Calculate category score
        category_score = sum(scores) / len(scores) if scores else 50
        category_alert = self._score_to_alert(category_score)

        # Count companies by risk level
        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for profile in company_profiles:
            level = profile.get("risk_level", "MEDIUM")
            risk_counts[level] = risk_counts.get(level, 0) + 1

        return CategoryAssessment(
            category="company_fundamentals",
            score=round(category_score, 1),
            alert_level=category_alert,
            indicators=indicators,
            summary=f"{risk_counts['LOW']} healthy, {risk_counts['MEDIUM']} caution, {risk_counts['HIGH']} at risk",
        )

    def _calculate_score_inverse(self, value: float, thresholds: Dict) -> Tuple[float, str]:
        """Calculate score where lower value is better"""
        yellow = thresholds["yellow"]
        orange = thresholds["orange"]
        red = thresholds["red"]

        if value >= red:
            return 0, "RED"
        elif value >= orange:
            # Linear interpolation between orange (30) and red (0)
            score = 30 * (red - value) / (red - orange)
            return score, "ORANGE"
        elif value >= yellow:
            # Linear interpolation between yellow (55) and orange (30)
            score = 30 + 25 * (orange - value) / (orange - yellow)
            return score, "YELLOW"
        else:
            # Linear interpolation between 0 (100) and yellow (55)
            score = 55 + 45 * (yellow - value) / yellow if yellow > 0 else 100
            return min(100, score), "GREEN"

    def _calculate_score_drawdown(self, value: float, thresholds: Dict) -> Tuple[float, str]:
        """Calculate score for drawdown (negative values)"""
        # Thresholds are negative (e.g., -5, -10, -20)
        yellow = thresholds["yellow"]
        orange = thresholds["orange"]
        red = thresholds["red"]

        if value <= red:
            return 0, "RED"
        elif value <= orange:
            score = 30 * (value - red) / (orange - red)
            return score, "ORANGE"
        elif value <= yellow:
            score = 30 + 25 * (value - orange) / (yellow - orange)
            return score, "YELLOW"
        else:
            # Positive or slightly negative
            score = min(100, 55 + 45 * (value - yellow) / (10 - yellow))
            return score, "GREEN"

    def _calculate_score_yield_curve(self, value: float, thresholds: Dict) -> Tuple[float, str]:
        """Calculate score for yield curve (positive is good)"""
        if value <= thresholds["red"]:
            return 0, "RED"
        elif value <= thresholds["orange"]:
            return 30, "ORANGE"
        elif value <= thresholds["yellow"]:
            return 45, "YELLOW"
        elif value <= 0:
            return 55, "YELLOW"
        else:
            # Positive slope
            score = min(100, 60 + value * 40)
            return score, "GREEN"

    def _score_to_alert(self, score: float) -> str:
        """Convert score to alert level"""
        if score >= 70:
            return "GREEN"
        elif score >= 55:
            return "YELLOW"
        elif score >= 40:
            return "ORANGE"
        else:
            return "RED"

    def _interpret_spread(self, value: float, spread_type: str) -> str:
        """Interpret credit spread value"""
        if spread_type == "high_yield":
            if value < 3.5:
                return "Very low risk premium, favorable conditions"
            elif value < 4.5:
                return "Normal risk premium"
            elif value < 6:
                return "Elevated risk premium, caution advised"
            else:
                return "High risk premium, stressed conditions"
        else:  # investment grade
            if value < 1.2:
                return "Very tight spreads, strong demand"
            elif value < 2:
                return "Normal spreads"
            else:
                return "Wide spreads, credit concerns"

    def _interpret_yield_curve(self, value: float) -> str:
        """Interpret yield curve value"""
        if value > 0.5:
            return "Normal upward slope, healthy"
        elif value > 0:
            return "Slightly positive, watchful"
        elif value > -0.3:
            return "Flat to slightly inverted, caution"
        else:
            return "Inverted curve, recession signal"

    def _interpret_vix(self, value: float) -> str:
        """Interpret VIX value"""
        if value < 15:
            return "Very low volatility, complacent market"
        elif value < 20:
            return "Normal volatility"
        elif value < 25:
            return "Elevated volatility, uncertainty"
        elif value < 30:
            return "High volatility, fear present"
        else:
            return "Very high volatility, panic levels"

    def _summarize_credit(self, score: float, indicators: List) -> str:
        """Generate credit market summary"""
        if score >= 75:
            return "Credit markets healthy, funding conditions favorable"
        elif score >= 55:
            return "Credit markets stable with some pressure points"
        elif score >= 40:
            return "Credit stress emerging, monitor closely"
        else:
            return "Credit markets stressed, funding conditions challenging"

    def _summarize_equity(self, score: float, indicators: List) -> str:
        """Generate equity market summary"""
        if score >= 75:
            return "Risk appetite strong, equity markets supportive"
        elif score >= 55:
            return "Market sentiment cautious but stable"
        elif score >= 40:
            return "Risk-off sentiment, equity weakness"
        else:
            return "Significant market stress, risk aversion high"

    def generate_report(self) -> FundingHealthReport:
        """
        Generate comprehensive funding health report

        Returns:
            FundingHealthReport with all assessments
        """
        # Load all data
        data = self.load_market_data()

        # Assess each category
        credit_assessment = None
        equity_assessment = None
        company_assessment = None

        if data.get("credit"):
            credit_assessment = self.assess_credit_market(data["credit"])

        if data.get("market"):
            equity_assessment = self.assess_equity_market(data["market"])

        if data.get("company") and data.get("consolidated"):
            company_assessment = self.assess_company_fundamentals(
                data["company"], data["consolidated"]
            )

        # Calculate overall score
        scores = []
        weights_used = []

        if credit_assessment:
            scores.append(credit_assessment.score * self.weights["credit_market"])
            weights_used.append(self.weights["credit_market"])

        if equity_assessment:
            scores.append(equity_assessment.score * self.weights["equity_market"])
            weights_used.append(self.weights["equity_market"])

        if company_assessment:
            scores.append(company_assessment.score * self.weights["company_fundamentals"])
            weights_used.append(self.weights["company_fundamentals"])

        overall_score = sum(scores) / sum(weights_used) if weights_used else 50
        overall_alert = self._score_to_alert(overall_score)

        # Collect triggered warnings
        triggered_warnings = []
        for cat in [credit_assessment, equity_assessment, company_assessment]:
            if cat:
                for ind in cat.indicators:
                    if ind.get("alert_level") in ["ORANGE", "RED"]:
                        triggered_warnings.append({
                            "category": cat.category,
                            "indicator": ind.get("name") or ind.get("indicator"),
                            "value": ind.get("value"),
                            "alert": ind.get("alert_level"),
                        })

        # Generate findings and recommendations
        key_findings = self._generate_findings(
            credit_assessment, equity_assessment, company_assessment
        )
        recommendations = self._generate_recommendations(
            overall_score, triggered_warnings
        )

        return FundingHealthReport(
            timestamp=datetime.now().isoformat(),
            overall_score=round(overall_score, 1),
            alert_level=overall_alert,
            alert_description=self.alert_levels[overall_alert]["description"],
            credit_market=asdict(credit_assessment) if credit_assessment else {},
            equity_market=asdict(equity_assessment) if equity_assessment else {},
            company_fundamentals=asdict(company_assessment) if company_assessment else {},
            triggered_warnings=triggered_warnings,
            key_findings=key_findings,
            recommendations=recommendations,
        )

    def _generate_findings(self, credit, equity, company) -> List[str]:
        """Generate key findings from assessments"""
        findings = []

        if credit and credit.score >= 70:
            findings.append("Credit markets providing favorable funding conditions")
        elif credit and credit.score < 50:
            findings.append("Credit market stress may limit funding access")

        if equity and equity.score >= 70:
            findings.append("Strong risk appetite supports AI sector valuations")
        elif equity and equity.score < 50:
            findings.append("Weak equity sentiment may pressure AI funding")

        if company:
            if company.score >= 70:
                findings.append("AI company fundamentals remain healthy")
            elif company.score < 50:
                findings.append("Some AI companies showing funding stress")

        return findings

    def _generate_recommendations(self, score: float, warnings: List) -> List[str]:
        """Generate recommendations based on assessment"""
        recommendations = []

        if score >= 70:
            recommendations.append("Current funding environment supports continued AI investment")
            recommendations.append("Maintain standard monitoring cadence")
        elif score >= 55:
            recommendations.append("Monitor warning indicators closely")
            recommendations.append("Consider reviewing risk exposure")
        elif score >= 40:
            recommendations.append("Elevated caution warranted")
            recommendations.append("Review funding contingency plans")
        else:
            recommendations.append("High alert - significant funding risk present")
            recommendations.append("Consider defensive positioning")

        # Specific warnings
        if any(w["category"] == "credit_market" and w["alert"] == "RED" for w in warnings):
            recommendations.append("Credit market stress requires immediate attention")

        return recommendations

    def save_report(self, report: FundingHealthReport, filename: str = "funding_health_report.json"):
        """Save report to file"""
        output_path = PROCESSED_DATA_DIR / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)

        print(f"Report saved to {output_path}")
        return output_path


def main():
    """Generate funding health report"""
    print("=" * 60)
    print("Funding Environment Health Assessment")
    print("=" * 60)

    assessor = FundingHealthAssessor()
    report = assessor.generate_report()
    assessor.save_report(report)

    # Print summary
    print(f"\n{'=' * 60}")
    print("FUNDING HEALTH REPORT")
    print("=" * 60)

    print(f"\nOverall Score: {report.overall_score}/100")
    print(f"Alert Level: {report.alert_level}")
    print(f"Status: {report.alert_description}")

    if report.credit_market:
        print(f"\nCredit Market: {report.credit_market.get('score', 'N/A')}/100 ({report.credit_market.get('alert_level', 'N/A')})")

    if report.equity_market:
        print(f"Equity Market: {report.equity_market.get('score', 'N/A')}/100 ({report.equity_market.get('alert_level', 'N/A')})")

    if report.company_fundamentals:
        print(f"Company Fundamentals: {report.company_fundamentals.get('score', 'N/A')}/100 ({report.company_fundamentals.get('alert_level', 'N/A')})")

    if report.triggered_warnings:
        print(f"\nTriggered Warnings ({len(report.triggered_warnings)}):")
        for w in report.triggered_warnings:
            print(f"  [{w['alert']}] {w['indicator']}: {w['value']:.2f}")

    print("\nKey Findings:")
    for finding in report.key_findings:
        print(f"  • {finding}")

    print("\nRecommendations:")
    for rec in report.recommendations:
        print(f"  • {rec}")

    return report


if __name__ == "__main__":
    main()
