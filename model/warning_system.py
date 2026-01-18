"""
Early Warning System Module
Monitors multiple indicators and generates alerts for AI funding risks
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    PROCESSED_DATA_DIR, MARKET_DATA_DIR,
    WARNING_THRESHOLDS_CREDIT, WARNING_THRESHOLDS_EQUITY, WARNING_THRESHOLDS_COMPANY,
    ALERT_LEVELS
)


class AlertSeverity(Enum):
    GREEN = 1
    YELLOW = 2
    ORANGE = 3
    RED = 4


@dataclass
class WarningSignal:
    """Individual warning signal"""
    signal_id: str
    category: str  # credit, equity, company, supply_demand
    name: str
    description: str
    current_value: float
    threshold_yellow: float
    threshold_orange: float
    threshold_red: float
    severity: str
    triggered: bool
    trend: str = "stable"  # improving, stable, deteriorating
    week_change: float = None
    message: str = ""


@dataclass
class WarningDashboard:
    """Complete warning system dashboard"""
    timestamp: str
    overall_status: str  # GREEN, YELLOW, ORANGE, RED
    overall_score: float
    status_message: str

    signals_summary: Dict
    active_warnings: List[Dict]
    watch_list: List[Dict]
    all_signals: List[Dict]

    trend_analysis: Dict
    recommendations: List[str]


class EarlyWarningSystem:
    """Monitors and generates early warnings for AI funding risks"""

    # Signal definitions with metadata
    SIGNAL_DEFINITIONS = {
        # Credit Market Signals
        "HY_SPREAD": {
            "category": "credit",
            "name": "High Yield Bond Spread",
            "description": "Spread between high-yield corporate bonds and treasuries",
            "data_path": ["credit", "credit_market", "BAMLH0A0HYM2"],
            "thresholds": WARNING_THRESHOLDS_CREDIT["high_yield_spread"],
            "inverse": True,  # Higher is worse
        },
        "IG_SPREAD": {
            "category": "credit",
            "name": "Investment Grade Spread",
            "description": "Spread for investment-grade corporate bonds",
            "data_path": ["credit", "credit_market", "BAMLC0A0CM"],
            "thresholds": WARNING_THRESHOLDS_CREDIT["investment_grade_spread"],
            "inverse": True,
        },
        "TED_SPREAD": {
            "category": "credit",
            "name": "TED Spread",
            "description": "Interbank lending risk indicator",
            "data_path": ["credit", "credit_market", "TEDRATE"],
            "thresholds": WARNING_THRESHOLDS_CREDIT["ted_spread"],
            "inverse": True,
        },
        "YIELD_CURVE": {
            "category": "credit",
            "name": "Yield Curve (10Y-2Y)",
            "description": "Treasury yield curve slope",
            "data_path": ["credit", "credit_market", "T10Y2Y"],
            "thresholds": WARNING_THRESHOLDS_CREDIT["yield_curve_10y2y"],
            "inverse": False,  # Negative is bad
            "special": "yield_curve",
        },

        # Equity Market Signals
        "VIX": {
            "category": "equity",
            "name": "VIX Volatility Index",
            "description": "Market fear gauge",
            "data_path": ["market", "vix", "statistics"],
            "value_key": "current",
            "thresholds": WARNING_THRESHOLDS_EQUITY["vix"],
            "inverse": True,
        },
        "AI_STOCKS_RETURN": {
            "category": "equity",
            "name": "AI Stocks Weekly Return",
            "description": "Average weekly return of major AI companies",
            "data_path": ["market", "ai_stocks", "aggregate"],
            "value_key": "avg_1w_return",
            "thresholds": WARNING_THRESHOLDS_EQUITY["ai_stocks_weekly_drawdown"],
            "inverse": False,  # Negative is bad
            "special": "drawdown",
        },
        "TECH_ETF_RETURN": {
            "category": "equity",
            "name": "Tech ETF Weekly Return",
            "description": "Technology sector ETF performance",
            "data_path": ["market", "etfs", "QQQ", "performance"],
            "value_key": "1w_return",
            "thresholds": WARNING_THRESHOLDS_EQUITY["tech_etf_weekly_drawdown"],
            "inverse": False,
            "special": "drawdown",
        },

        # Company-Level Signals (aggregated)
        "COMPANY_RISK_AVG": {
            "category": "company",
            "name": "Avg Company Risk Score",
            "description": "Average risk score across AI companies",
            "data_path": ["company", "company_profiles"],
            "special": "company_risk",
            "thresholds": {"yellow": 45, "orange": 55, "red": 65},
            "inverse": True,
        },
        "HIGH_RISK_COUNT": {
            "category": "company",
            "name": "High Risk Companies",
            "description": "Number of companies with elevated risk",
            "data_path": ["company", "company_profiles"],
            "special": "high_risk_count",
            "thresholds": {"yellow": 1, "orange": 2, "red": 3},
            "inverse": True,
        },
    }

    def __init__(self):
        self.signals = {}
        self.data = {}

    def load_data(self) -> Dict:
        """Load all required data"""
        data = {}

        # Credit market data
        credit_file = MARKET_DATA_DIR / "credit_market_data.json"
        if credit_file.exists():
            with open(credit_file, "r", encoding="utf-8") as f:
                data["credit"] = json.load(f)

        # Market indicators
        market_file = MARKET_DATA_DIR / "market_indicators.json"
        if market_file.exists():
            with open(market_file, "r", encoding="utf-8") as f:
                data["market"] = json.load(f)

        # Company risk assessment
        risk_file = PROCESSED_DATA_DIR / "risk_assessment.json"
        if risk_file.exists():
            with open(risk_file, "r", encoding="utf-8") as f:
                data["company"] = json.load(f)

        # Supply demand analysis
        sd_file = PROCESSED_DATA_DIR / "supply_demand_analysis.json"
        if sd_file.exists():
            with open(sd_file, "r", encoding="utf-8") as f:
                data["supply_demand"] = json.load(f)

        # Funding health report
        health_file = PROCESSED_DATA_DIR / "funding_health_report.json"
        if health_file.exists():
            with open(health_file, "r", encoding="utf-8") as f:
                data["funding_health"] = json.load(f)

        self.data = data
        return data

    def _get_nested_value(self, data: Dict, path: List[str], default=None):
        """Get value from nested dictionary using path"""
        current = data
        for key in path:
            if isinstance(current, dict):
                current = current.get(key, default)
            else:
                return default
            if current is None:
                return default
        return current

    def evaluate_signal(self, signal_id: str, definition: Dict) -> Optional[WarningSignal]:
        """
        Evaluate a single warning signal

        Args:
            signal_id: Signal identifier
            definition: Signal definition dictionary

        Returns:
            WarningSignal or None if data unavailable
        """
        # Get the data
        data_path = definition.get("data_path", [])
        raw_data = self._get_nested_value(self.data, data_path)

        if raw_data is None:
            return None

        # Extract the value
        if definition.get("special") == "company_risk":
            # Calculate average company risk
            if isinstance(raw_data, list):
                scores = [p.get("overall_risk_score", 50) for p in raw_data]
                value = sum(scores) / len(scores) if scores else 50
            else:
                return None
        elif definition.get("special") == "high_risk_count":
            # Count high-risk companies
            if isinstance(raw_data, list):
                value = sum(1 for p in raw_data if p.get("risk_level") in ["MEDIUM", "HIGH"])
            else:
                return None
        elif definition.get("value_key"):
            if isinstance(raw_data, dict):
                value = raw_data.get(definition["value_key"])
            else:
                value = raw_data
        else:
            # Standard FRED-style data
            if isinstance(raw_data, dict) and "latest" in raw_data:
                value = raw_data["latest"].get("value")
            elif isinstance(raw_data, dict):
                value = raw_data.get("value")
            else:
                value = raw_data

        if value is None:
            return None

        # Get thresholds
        thresholds = definition.get("thresholds", {})
        yellow = thresholds.get("yellow", 0)
        orange = thresholds.get("orange", 0)
        red = thresholds.get("red", 0)

        # Determine severity
        severity, triggered = self._calculate_severity(
            value, yellow, orange, red,
            inverse=definition.get("inverse", False),
            special=definition.get("special")
        )

        # Get trend data if available
        trend = "stable"
        week_change = None
        if isinstance(raw_data, dict):
            changes = raw_data.get("changes", {})
            week_change = changes.get("1w_change")
            if week_change:
                if abs(week_change) < 0.1:
                    trend = "stable"
                elif definition.get("inverse"):
                    trend = "deteriorating" if week_change > 0 else "improving"
                else:
                    trend = "improving" if week_change > 0 else "deteriorating"

        # Generate message
        message = self._generate_signal_message(
            definition["name"], value, severity, thresholds, definition.get("inverse")
        )

        return WarningSignal(
            signal_id=signal_id,
            category=definition["category"],
            name=definition["name"],
            description=definition["description"],
            current_value=round(value, 3) if isinstance(value, float) else value,
            threshold_yellow=yellow,
            threshold_orange=orange,
            threshold_red=red,
            severity=severity,
            triggered=triggered,
            trend=trend,
            week_change=round(week_change, 3) if week_change else None,
            message=message,
        )

    def _calculate_severity(
        self,
        value: float,
        yellow: float,
        orange: float,
        red: float,
        inverse: bool = False,
        special: str = None
    ) -> Tuple[str, bool]:
        """Calculate severity level for a value"""

        if special == "yield_curve":
            # Yield curve: negative is bad
            if value <= red:
                return "RED", True
            elif value <= orange:
                return "ORANGE", True
            elif value <= yellow:
                return "YELLOW", True
            else:
                return "GREEN", False

        elif special == "drawdown":
            # Drawdown: negative values, more negative is worse
            if value <= red:
                return "RED", True
            elif value <= orange:
                return "ORANGE", True
            elif value <= yellow:
                return "YELLOW", True
            else:
                return "GREEN", False

        elif inverse:
            # Higher value is worse
            if value >= red:
                return "RED", True
            elif value >= orange:
                return "ORANGE", True
            elif value >= yellow:
                return "YELLOW", True
            else:
                return "GREEN", False
        else:
            # Lower value is worse
            if value <= red:
                return "RED", True
            elif value <= orange:
                return "ORANGE", True
            elif value <= yellow:
                return "YELLOW", True
            else:
                return "GREEN", False

    def _generate_signal_message(
        self,
        name: str,
        value: float,
        severity: str,
        thresholds: Dict,
        inverse: bool
    ) -> str:
        """Generate human-readable message for signal"""
        if severity == "GREEN":
            return f"{name} at normal levels ({value:.2f})"
        elif severity == "YELLOW":
            return f"{name} approaching concern levels ({value:.2f})"
        elif severity == "ORANGE":
            return f"{name} at warning levels ({value:.2f}) - monitor closely"
        else:  # RED
            return f"{name} at critical levels ({value:.2f}) - immediate attention required"

    def evaluate_all_signals(self) -> Dict[str, WarningSignal]:
        """Evaluate all defined warning signals"""
        self.signals = {}

        for signal_id, definition in self.SIGNAL_DEFINITIONS.items():
            signal = self.evaluate_signal(signal_id, definition)
            if signal:
                self.signals[signal_id] = signal

        return self.signals

    def calculate_overall_status(self) -> Tuple[str, float, str]:
        """
        Calculate overall warning status

        Returns:
            Tuple of (status, score, message)
        """
        if not self.signals:
            return "GREEN", 100, "No data available"

        # Count signals by severity
        severity_counts = {"GREEN": 0, "YELLOW": 0, "ORANGE": 0, "RED": 0}
        for signal in self.signals.values():
            severity_counts[signal.severity] += 1

        total = sum(severity_counts.values())

        # Calculate weighted score (0-100, higher is better)
        weights = {"GREEN": 100, "YELLOW": 65, "ORANGE": 35, "RED": 10}
        score = sum(severity_counts[s] * weights[s] for s in severity_counts) / total if total > 0 else 50

        # Determine overall status
        if severity_counts["RED"] >= 2:
            status = "RED"
            message = "Multiple critical warnings - high funding risk"
        elif severity_counts["RED"] >= 1 or severity_counts["ORANGE"] >= 3:
            status = "ORANGE"
            message = "Significant warnings detected - elevated risk"
        elif severity_counts["ORANGE"] >= 1 or severity_counts["YELLOW"] >= 3:
            status = "YELLOW"
            message = "Some warning signals present - monitor closely"
        else:
            status = "GREEN"
            message = "All systems normal - funding environment healthy"

        return status, round(score, 1), message

    def generate_dashboard(self) -> WarningDashboard:
        """
        Generate complete warning dashboard

        Returns:
            WarningDashboard with all warning information
        """
        self.load_data()
        self.evaluate_all_signals()
        status, score, message = self.calculate_overall_status()

        # Categorize signals
        active_warnings = []
        watch_list = []
        all_signals = []

        for signal in self.signals.values():
            signal_dict = asdict(signal)
            all_signals.append(signal_dict)

            if signal.severity in ["RED", "ORANGE"]:
                active_warnings.append(signal_dict)
            elif signal.severity == "YELLOW":
                watch_list.append(signal_dict)

        # Sort by severity
        severity_order = {"RED": 0, "ORANGE": 1, "YELLOW": 2, "GREEN": 3}
        active_warnings.sort(key=lambda x: severity_order.get(x["severity"], 3))
        watch_list.sort(key=lambda x: severity_order.get(x["severity"], 3))

        # Summary by category
        signals_summary = {
            "total": len(self.signals),
            "by_severity": {
                "RED": sum(1 for s in self.signals.values() if s.severity == "RED"),
                "ORANGE": sum(1 for s in self.signals.values() if s.severity == "ORANGE"),
                "YELLOW": sum(1 for s in self.signals.values() if s.severity == "YELLOW"),
                "GREEN": sum(1 for s in self.signals.values() if s.severity == "GREEN"),
            },
            "by_category": {
                "credit": sum(1 for s in self.signals.values() if s.category == "credit" and s.triggered),
                "equity": sum(1 for s in self.signals.values() if s.category == "equity" and s.triggered),
                "company": sum(1 for s in self.signals.values() if s.category == "company" and s.triggered),
            },
        }

        # Trend analysis
        improving = sum(1 for s in self.signals.values() if s.trend == "improving")
        deteriorating = sum(1 for s in self.signals.values() if s.trend == "deteriorating")
        trend_analysis = {
            "improving_count": improving,
            "deteriorating_count": deteriorating,
            "overall_trend": "improving" if improving > deteriorating else (
                "deteriorating" if deteriorating > improving else "stable"
            ),
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(status, active_warnings, watch_list)

        return WarningDashboard(
            timestamp=datetime.now().isoformat(),
            overall_status=status,
            overall_score=score,
            status_message=message,
            signals_summary=signals_summary,
            active_warnings=active_warnings,
            watch_list=watch_list,
            all_signals=all_signals,
            trend_analysis=trend_analysis,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        status: str,
        active_warnings: List,
        watch_list: List
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if status == "RED":
            recommendations.append("HIGH ALERT: Review all funding positions immediately")
            recommendations.append("Consider defensive measures for AI investments")
        elif status == "ORANGE":
            recommendations.append("Elevated monitoring recommended")
            recommendations.append("Review contingency funding plans")
        elif status == "YELLOW":
            recommendations.append("Continue normal monitoring with increased attention")
        else:
            recommendations.append("Funding environment healthy - maintain standard monitoring")

        # Specific recommendations based on warnings
        credit_warnings = [w for w in active_warnings if w.get("category") == "credit"]
        if credit_warnings:
            recommendations.append("Credit market stress detected - review debt refinancing plans")

        equity_warnings = [w for w in active_warnings if w.get("category") == "equity"]
        if equity_warnings:
            recommendations.append("Market sentiment weak - equity financing may be challenging")

        company_warnings = [w for w in active_warnings if w.get("category") == "company"]
        if company_warnings:
            recommendations.append("Some companies showing stress - review individual positions")

        return recommendations

    def save_dashboard(self, dashboard: WarningDashboard, filename: str = "warning_dashboard.json"):
        """Save dashboard to file"""
        output_path = PROCESSED_DATA_DIR / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(dashboard), f, indent=2, ensure_ascii=False)

        print(f"Dashboard saved to {output_path}")
        return output_path

    def print_dashboard(self, dashboard: WarningDashboard):
        """Print dashboard summary to console"""
        # Use ASCII-safe symbols to avoid encoding issues on Windows
        status_symbols = {
            "GREEN": "[OK]",
            "YELLOW": "[!]",
            "ORANGE": "[!!]",
            "RED": "[!!!]"
        }

        print("\n" + "=" * 70)
        print("AI FUNDING RISK EARLY WARNING DASHBOARD")
        print("=" * 70)

        print(f"\nTimestamp: {dashboard.timestamp}")
        print(f"\nOverall Status: {status_symbols.get(dashboard.overall_status, '[?]')} {dashboard.overall_status}")
        print(f"Health Score: {dashboard.overall_score}/100")
        print(f"Status: {dashboard.status_message}")

        # Summary
        summary = dashboard.signals_summary
        print(f"\nSignal Summary ({summary['total']} total):")
        for sev, count in summary["by_severity"].items():
            if count > 0:
                print(f"  {status_symbols.get(sev, '[?]')} {sev}: {count}")

        # Active warnings
        if dashboard.active_warnings:
            print(f"\n** ACTIVE WARNINGS ({len(dashboard.active_warnings)}):")
            for w in dashboard.active_warnings:
                symbol = status_symbols.get(w["severity"], "[?]")
                print(f"  {symbol} [{w['category'].upper()}] {w['name']}: {w['current_value']}")
                print(f"      {w['message']}")

        # Watch list
        if dashboard.watch_list:
            print(f"\n>> WATCH LIST ({len(dashboard.watch_list)}):")
            for w in dashboard.watch_list:
                print(f"  [!] [{w['category'].upper()}] {w['name']}: {w['current_value']}")

        # Trend
        trend = dashboard.trend_analysis
        print(f"\nTrend Analysis:")
        print(f"  Improving: {trend['improving_count']} | Deteriorating: {trend['deteriorating_count']}")
        print(f"  Overall Trend: {trend['overall_trend'].upper()}")

        # Recommendations
        print("\n-- Recommendations:")
        for rec in dashboard.recommendations:
            print(f"  * {rec}")

        print("\n" + "=" * 70)


def main():
    """Run early warning system"""
    print("=" * 60)
    print("Early Warning System - AI Funding Risk Monitor")
    print("=" * 60)

    system = EarlyWarningSystem()
    dashboard = system.generate_dashboard()
    system.save_dashboard(dashboard)
    system.print_dashboard(dashboard)

    return dashboard


if __name__ == "__main__":
    main()
