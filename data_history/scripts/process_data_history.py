"""
Data Processing Module for 90s IT Bubble Historical Validation
Consolidates compiled financial data, FRED macro data, and Yahoo stock data
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR, COMPILED_DATA_DIR, MARKET_DATA_DIR


class HistoryDataProcessor:
    """Processes historical data for 90s IT bubble analysis"""

    def __init__(self):
        self.raw_dir = RAW_DATA_DIR
        self.processed_dir = PROCESSED_DATA_DIR
        self.compiled_dir = COMPILED_DATA_DIR
        self.market_dir = MARKET_DATA_DIR
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_json(self, filename: str, directory: Path = None) -> Optional[Dict]:
        """Load JSON file"""
        if directory is None:
            directory = self.raw_dir
        filepath = directory / filename
        if not filepath.exists():
            print(f"File not found: {filepath}")
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, data: Dict, filename: str):
        """Save data to processed directory"""
        filepath = self.processed_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved: {filepath}")

    def process_compiled_financials(self, compiled_data: Dict) -> Dict[str, Dict]:
        """Process compiled historical financial data into analysis-ready format"""
        processed = {}

        for company_name, company_data in compiled_data.get("companies", {}).items():
            annual_data = company_data.get("annual_data", [])
            if not annual_data:
                continue

            # Sort by year (most recent first)
            annual_data = sorted(annual_data, key=lambda x: x["year"], reverse=True)

            # Calculate derived metrics for each year
            yearly_metrics = []
            for i, year_data in enumerate(annual_data):
                metrics = {
                    "year": year_data["year"],
                    "revenue_M": year_data.get("revenue", 0),
                    "capex_M": year_data.get("capex", 0),
                    "operating_cashflow_M": year_data.get("operating_cashflow", 0),
                    "long_term_debt_M": year_data.get("long_term_debt", 0),
                    "total_cash_M": year_data.get("total_cash", 0),
                    "net_income_M": year_data.get("net_income", 0),
                    "market_cap_peak_M": year_data.get("market_cap_peak", 0),
                    "employees": year_data.get("employees", 0),
                }

                # Capex to cash flow ratio
                ocf = year_data.get("operating_cashflow", 0)
                capex = year_data.get("capex", 0)
                if ocf > 0 and capex > 0:
                    metrics["capex_to_cashflow_ratio"] = round(capex / ocf, 3)
                else:
                    metrics["capex_to_cashflow_ratio"] = None

                # Debt to revenue ratio
                revenue = year_data.get("revenue", 0)
                debt = year_data.get("long_term_debt", 0)
                if revenue > 0:
                    metrics["debt_to_revenue_ratio"] = round(debt / revenue, 3)
                else:
                    metrics["debt_to_revenue_ratio"] = None

                # Debt to cash ratio
                cash = year_data.get("total_cash", 0)
                if cash > 0 and debt > 0:
                    metrics["debt_to_cash_ratio"] = round(debt / cash, 3)
                else:
                    metrics["debt_to_cash_ratio"] = 0

                # YoY growth rates (need previous year)
                if i < len(annual_data) - 1:
                    prev = annual_data[i + 1]

                    prev_rev = prev.get("revenue", 0)
                    if prev_rev > 0:
                        metrics["revenue_growth_yoy"] = round(
                            (revenue - prev_rev) / prev_rev * 100, 2
                        )
                    else:
                        metrics["revenue_growth_yoy"] = None

                    prev_capex = prev.get("capex", 0)
                    if prev_capex > 0:
                        metrics["capex_growth_yoy"] = round(
                            (capex - prev_capex) / prev_capex * 100, 2
                        )
                    else:
                        metrics["capex_growth_yoy"] = None

                    prev_debt = prev.get("long_term_debt", 0)
                    if prev_debt > 0 and debt > 0:
                        metrics["debt_growth_yoy"] = round(
                            (debt - prev_debt) / prev_debt * 100, 2
                        )
                    else:
                        metrics["debt_growth_yoy"] = None

                    # Revenue per employee growth
                    prev_emp = prev.get("employees", 0)
                    emp = year_data.get("employees", 0)
                    if prev_emp > 0 and emp > 0 and prev_rev > 0 and revenue > 0:
                        prev_rev_per_emp = prev_rev / prev_emp
                        rev_per_emp = revenue / emp
                        metrics["revenue_per_employee_growth_yoy"] = round(
                            (rev_per_emp - prev_rev_per_emp) / prev_rev_per_emp * 100, 2
                        )
                    else:
                        metrics["revenue_per_employee_growth_yoy"] = None

                    # Capex efficiency: revenue growth vs capex growth
                    rev_growth = metrics.get("revenue_growth_yoy")
                    capex_growth = metrics.get("capex_growth_yoy")
                    if rev_growth is not None and capex_growth is not None and capex_growth != 0:
                        metrics["capex_efficiency"] = round(rev_growth / capex_growth, 3)
                    else:
                        metrics["capex_efficiency"] = None

                    # Debt growth vs revenue growth
                    debt_growth = metrics.get("debt_growth_yoy")
                    if debt_growth is not None and rev_growth is not None and rev_growth != 0:
                        metrics["debt_to_revenue_growth_ratio"] = round(
                            debt_growth / rev_growth, 3
                        )
                    else:
                        metrics["debt_to_revenue_growth_ratio"] = None
                else:
                    # First year - no previous data
                    metrics["revenue_growth_yoy"] = None
                    metrics["capex_growth_yoy"] = None
                    metrics["debt_growth_yoy"] = None
                    metrics["capex_efficiency"] = None
                    metrics["debt_to_revenue_growth_ratio"] = None
                    metrics["revenue_per_employee_growth_yoy"] = None

                yearly_metrics.append(metrics)

            processed[company_name] = {
                "company": company_name,
                "ticker": company_data.get("ticker"),
                "notes": company_data.get("notes"),
                "yearly_metrics": yearly_metrics,
            }

        return processed

    def process_fred_data(self, fred_data: Dict) -> Dict[str, Dict]:
        """Process FRED macro data for the historical period"""
        processed = {}
        for series_id, data in fred_data.items():
            observations = data.get("observations", [])
            if not observations:
                continue

            latest = observations[-1] if observations else None
            recent = observations[-12:]
            if len(recent) >= 2:
                first_val = recent[0].get("value", 0)
                last_val = recent[-1].get("value", 0)
                trend_pct = ((last_val - first_val) / abs(first_val)) * 100 if first_val != 0 else 0
            else:
                trend_pct = 0

            processed[series_id] = {
                "description": data.get("description"),
                "latest_value": latest.get("value") if latest else None,
                "latest_date": latest.get("date") if latest else None,
                "trend_pct": round(trend_pct, 2),
                "observation_count": len(observations),
            }

        return processed

    def create_consolidated_dataset(self) -> Dict:
        """Load and consolidate all data sources"""
        print("Loading data files...")

        # Load compiled financial data
        compiled_data = self.load_json("historical_financials.json", self.compiled_dir)
        # Load FRED macro data
        fred_macro = self.load_json("fred_macro_history.json")
        # Load FRED credit data
        fred_credit = self.load_json("fred_credit_history.json", self.market_dir)
        # Load Yahoo stock data
        yahoo_stocks = self.load_json("yahoo_stock_history.json")
        # Load market indices
        market_indices = self.load_json("market_indices_history.json", self.market_dir)

        consolidated = {
            "metadata": {
                "description": "90s IT Bubble Historical Data - Consolidated",
                "period": "1995-2003",
                "created_at": datetime.now().isoformat(),
                "sources": {
                    "compiled_financials": compiled_data is not None,
                    "fred_macro": fred_macro is not None,
                    "fred_credit": fred_credit is not None,
                    "yahoo_stocks": yahoo_stocks is not None,
                    "market_indices": market_indices is not None,
                },
            },
            "companies": {},
            "macro_indicators": {},
            "market_data": {},
        }

        # Process compiled financials
        if compiled_data:
            print("Processing compiled financial data...")
            processed_financials = self.process_compiled_financials(compiled_data)
            for company_name, data in processed_financials.items():
                consolidated["companies"][company_name] = {
                    "financials": data,
                    "stock_data": None,
                }

        # Add Yahoo stock data
        if yahoo_stocks:
            print("Adding stock price data...")
            for company_name, stock_data in yahoo_stocks.items():
                if company_name in consolidated["companies"]:
                    consolidated["companies"][company_name]["stock_data"] = stock_data

        # Process FRED data
        if fred_macro:
            print("Processing FRED macro data...")
            consolidated["macro_indicators"] = self.process_fred_data(fred_macro)

        if fred_credit:
            print("Processing FRED credit data...")
            credit_processed = self.process_fred_data(fred_credit)
            consolidated["macro_indicators"].update(credit_processed)

        # Add market data
        if market_indices:
            consolidated["market_data"] = market_indices

        return consolidated

    def generate_yearly_summary(self, consolidated: Dict) -> Dict:
        """Generate year-by-year summary across all companies"""
        companies = consolidated.get("companies", {})

        yearly_summary = {}

        for company_name, company_data in companies.items():
            financials = company_data.get("financials", {})
            if not financials:
                continue

            for metrics in financials.get("yearly_metrics", []):
                year = metrics["year"]
                if year not in yearly_summary:
                    yearly_summary[year] = {
                        "year": year,
                        "total_revenue_M": 0,
                        "total_capex_M": 0,
                        "total_operating_cashflow_M": 0,
                        "total_debt_M": 0,
                        "total_cash_M": 0,
                        "total_market_cap_peak_M": 0,
                        "total_employees": 0,
                        "companies": {},
                    }

                yearly_summary[year]["total_revenue_M"] += metrics.get("revenue_M", 0)
                yearly_summary[year]["total_capex_M"] += metrics.get("capex_M", 0)
                yearly_summary[year]["total_operating_cashflow_M"] += max(0, metrics.get("operating_cashflow_M", 0))
                yearly_summary[year]["total_debt_M"] += metrics.get("long_term_debt_M", 0)
                yearly_summary[year]["total_cash_M"] += metrics.get("total_cash_M", 0)
                yearly_summary[year]["total_market_cap_peak_M"] += metrics.get("market_cap_peak_M", 0)
                yearly_summary[year]["total_employees"] += metrics.get("employees", 0)

                yearly_summary[year]["companies"][company_name] = {
                    "revenue_M": metrics.get("revenue_M"),
                    "capex_M": metrics.get("capex_M"),
                    "capex_to_cashflow_ratio": metrics.get("capex_to_cashflow_ratio"),
                    "revenue_growth_yoy": metrics.get("revenue_growth_yoy"),
                    "capex_growth_yoy": metrics.get("capex_growth_yoy"),
                }

        # Calculate aggregate ratios
        for year, data in yearly_summary.items():
            total_ocf = data["total_operating_cashflow_M"]
            total_capex = data["total_capex_M"]
            total_rev = data["total_revenue_M"]
            total_debt = data["total_debt_M"]

            data["aggregate_capex_to_cashflow"] = (
                round(total_capex / total_ocf, 3) if total_ocf > 0 else None
            )
            data["aggregate_debt_to_revenue"] = (
                round(total_debt / total_rev, 3) if total_rev > 0 else None
            )
            # Convert to billions for display
            data["total_revenue_B"] = round(total_rev / 1000, 2)
            data["total_capex_B"] = round(total_capex / 1000, 2)
            data["total_market_cap_peak_T"] = round(data["total_market_cap_peak_M"] / 1e6, 2)

        # Sort by year
        sorted_summary = dict(sorted(yearly_summary.items()))
        return sorted_summary

    def generate_risk_timeline(self, yearly_summary: Dict) -> List[Dict]:
        """Generate risk score timeline showing how risk evolved through the bubble"""
        from data_history.config.settings import RISK_THRESHOLDS

        timeline = []
        years = sorted(yearly_summary.keys())

        prev_year_data = None
        for year in years:
            data = yearly_summary[year]

            capex_to_cf = data.get("aggregate_capex_to_cashflow")
            debt_to_rev = data.get("aggregate_debt_to_revenue")

            # Calculate risk scores using same thresholds as main project
            consumption_score = 20  # Default LOW
            if capex_to_cf is not None:
                if capex_to_cf >= RISK_THRESHOLDS["capex_to_cashflow"]["warning"]:
                    consumption_score = 80
                elif capex_to_cf >= RISK_THRESHOLDS["capex_to_cashflow"]["normal"]:
                    progress = (capex_to_cf - 0.70) / 0.20
                    consumption_score = 30 + progress * 40
                else:
                    consumption_score = 20

            # Calculate YoY capex growth across aggregate
            capex_growth_score = 50  # Default MEDIUM
            if prev_year_data:
                prev_capex = prev_year_data.get("total_capex_M", 0)
                curr_capex = data.get("total_capex_M", 0)
                if prev_capex > 0:
                    capex_growth = (curr_capex - prev_capex) / prev_capex * 100
                    if capex_growth > 50:
                        capex_growth_score = 80
                    elif capex_growth > 30:
                        capex_growth_score = 50
                    else:
                        capex_growth_score = 20

            # Supply score based on debt levels
            supply_score = 20
            if debt_to_rev is not None:
                if debt_to_rev > 0.5:
                    supply_score = 60
                elif debt_to_rev > 0.3:
                    supply_score = 40

            # Overall risk score
            overall = consumption_score * 0.40 + capex_growth_score * 0.30 + supply_score * 0.30

            if overall < 40:
                risk_level = "LOW"
            elif overall < 65:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"

            timeline.append({
                "year": year,
                "overall_risk_score": round(overall, 1),
                "risk_level": risk_level,
                "consumption_score": round(consumption_score, 1),
                "capex_growth_score": round(capex_growth_score, 1),
                "supply_score": round(supply_score, 1),
                "capex_to_cashflow": capex_to_cf,
                "total_capex_B": data.get("total_capex_B"),
                "total_revenue_B": data.get("total_revenue_B"),
                "total_market_cap_T": data.get("total_market_cap_peak_T"),
            })

            prev_year_data = data

        return timeline

    def run(self) -> Dict:
        """Run the full data processing pipeline"""
        print("=" * 60)
        print("Historical Data Processing Pipeline (1995-2003)")
        print("=" * 60)

        consolidated = self.create_consolidated_dataset()
        self.save_json(consolidated, "consolidated_history.json")

        # Generate yearly summary
        print("\nGenerating yearly summary...")
        yearly_summary = self.generate_yearly_summary(consolidated)
        self.save_json(yearly_summary, "yearly_summary.json")

        # Generate risk timeline
        print("Generating risk timeline...")
        risk_timeline = self.generate_risk_timeline(yearly_summary)
        self.save_json({"timeline": risk_timeline}, "risk_timeline.json")

        # Generate comparison summary
        print("Generating comparison data...")
        comparison = self.generate_comparison_summary(yearly_summary, risk_timeline)
        self.save_json(comparison, "bubble_comparison.json")

        print("\nProcessing complete!")
        return consolidated

    def generate_comparison_summary(self, yearly_summary: Dict, risk_timeline: List[Dict]) -> Dict:
        """Generate a summary comparing 90s IT bubble with current AI bubble"""
        # Find key years
        pre_bubble = yearly_summary.get(1996, {})
        peak = yearly_summary.get(2000, {})
        trough = yearly_summary.get(2002, {})

        comparison = {
            "title": "90s IT Bubble vs Current AI Bubble - Comparative Analysis",
            "generated_at": datetime.now().isoformat(),
            "it_bubble_summary": {
                "period": "1995-2003",
                "peak_year": 2000,
                "peak_nasdaq": 5048.62,
                "pre_bubble_aggregate_capex_B": pre_bubble.get("total_capex_B"),
                "peak_aggregate_capex_B": peak.get("total_capex_B"),
                "capex_growth_pre_to_peak": None,
                "peak_aggregate_revenue_B": peak.get("total_revenue_B"),
                "peak_market_cap_T": peak.get("total_market_cap_peak_T"),
                "peak_capex_to_cashflow": peak.get("aggregate_capex_to_cashflow"),
                "trough_year": 2002,
                "trough_aggregate_revenue_B": trough.get("total_revenue_B"),
                "revenue_decline_peak_to_trough_pct": None,
            },
            "risk_timeline": risk_timeline,
            "key_findings": [],
            "validation_against_ai_bubble": {
                "similarities": [],
                "differences": [],
                "warning_signals_that_preceded_crash": [],
            }
        }

        # Calculate capex growth pre-bubble to peak
        pre_capex = pre_bubble.get("total_capex_B", 0)
        peak_capex = peak.get("total_capex_B", 0)
        if pre_capex and pre_capex > 0:
            comparison["it_bubble_summary"]["capex_growth_pre_to_peak"] = round(
                (peak_capex - pre_capex) / pre_capex * 100, 1
            )

        # Revenue decline
        peak_rev = peak.get("total_revenue_B", 0)
        trough_rev = trough.get("total_revenue_B", 0)
        if peak_rev and peak_rev > 0 and trough_rev:
            comparison["it_bubble_summary"]["revenue_decline_peak_to_trough_pct"] = round(
                (trough_rev - peak_rev) / peak_rev * 100, 1
            )

        # Key findings
        findings = []

        # Check capex trajectory
        capex_trajectory = []
        for year in sorted(yearly_summary.keys()):
            capex_trajectory.append({
                "year": year,
                "capex_B": yearly_summary[year].get("total_capex_B"),
                "capex_to_cf": yearly_summary[year].get("aggregate_capex_to_cashflow"),
            })
        comparison["capex_trajectory"] = capex_trajectory

        # Identify when risk crossed thresholds
        for item in risk_timeline:
            if item["risk_level"] == "HIGH":
                findings.append(
                    f"Risk reached HIGH level in {item['year']} "
                    f"(score: {item['overall_risk_score']}/100)"
                )
                break

        # Capex acceleration
        for i in range(1, len(capex_trajectory)):
            prev = capex_trajectory[i - 1]["capex_B"]
            curr = capex_trajectory[i]["capex_B"]
            if prev and curr and prev > 0:
                growth = (curr - prev) / prev * 100
                if growth > 40:
                    findings.append(
                        f"Capex accelerated {growth:.0f}% in {capex_trajectory[i]['year']}"
                    )

        comparison["key_findings"] = findings

        # Warning signals
        comparison["validation_against_ai_bubble"]["warning_signals_that_preceded_crash"] = [
            "Capex growth consistently outpacing revenue growth (1998-2001)",
            "Aggregate capex-to-cashflow ratio rising above 0.50 threshold",
            "Massive employee hiring despite slowing revenue growth",
            "Companies funding capex through debt issuance rather than operations",
            "Market cap disconnection from fundamental metrics",
            "Credit spreads initially tight then rapidly widening in 2001-2002",
        ]

        comparison["validation_against_ai_bubble"]["similarities"] = [
            "Dominant infrastructure companies spending heavily on buildout",
            "Market expects exponential growth to justify capex",
            "Low interest rates enabling cheap debt financing",
            "High capex-to-cashflow ratios across sector leaders",
            "Revenue growth strong but potentially unsustainable",
        ]

        comparison["validation_against_ai_bubble"]["differences"] = [
            "90s IT companies had lower profit margins than current AI leaders",
            "Current AI companies (except Oracle) carry less debt relative to cash",
            "90s capex was more hardware-intensive (factories, fiber optic cables)",
            "Current AI companies are more profitable and cash-flow positive",
            "Market concentration is higher in current AI wave (fewer dominant players)",
        ]

        return comparison


def main():
    """Main function to run data processing"""
    processor = HistoryDataProcessor()
    consolidated = processor.run()

    companies = consolidated.get("companies", {})
    print(f"\nProcessed data for {len(companies)} companies")
    return consolidated


if __name__ == "__main__":
    main()
