"""
Data Processing Module
Consolidates and processes data from all sources for risk analysis
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR, TARGET_COMPANIES, SEC_METRIC_NAMES

# Minimum acceptable date for data (filter out stale data older than 5 years)
MIN_DATA_YEAR = datetime.now().year - 5


class DataProcessor:
    """Processes and consolidates data from multiple sources"""

    def __init__(self):
        self.raw_dir = RAW_DATA_DIR
        self.processed_dir = PROCESSED_DATA_DIR
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_json(self, filename: str, directory: Path = None) -> Optional[Dict]:
        """Load JSON file from raw data directory"""
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

    def _extract_year_from_date(self, date_str: str) -> Optional[int]:
        """Extract year from date string (YYYY-MM-DD format)"""
        if date_str and len(date_str) >= 4:
            try:
                return int(date_str[:4])
            except ValueError:
                return None
        return None

    def _filter_recent_data(self, values: List[Dict], min_year: int = None) -> List[Dict]:
        """Filter out stale data older than min_year using fiscal_year"""
        if min_year is None:
            min_year = MIN_DATA_YEAR

        filtered = []
        for v in values:
            # Use fiscal_year as the primary year identifier
            fiscal_year = v.get("fiscal_year")
            if fiscal_year and fiscal_year >= min_year:
                filtered.append(v)
        return filtered

    def process_sec_data(self, sec_data: Dict) -> Dict[str, Dict]:
        """
        Process SEC data to extract key financial metrics

        Args:
            sec_data: Raw SEC data

        Returns:
            Processed metrics per company
        """
        processed = {}

        for company_name, data in sec_data.items():
            metrics = data.get("metrics", {})
            company_metrics = {"company": company_name, "cik": data.get("cik")}

            # Process each metric
            for metric_name, values in metrics.items():
                if not values:
                    continue

                # Sort by fiscal_year (most recent first) for consistent year alignment
                # This ensures all companies are compared on the same fiscal year basis
                sorted_values = sorted(
                    values, key=lambda x: x.get("fiscal_year", 0), reverse=True
                )

                # Filter out stale data (older than MIN_DATA_YEAR)
                recent_values = self._filter_recent_data(sorted_values)

                # If no recent data, fall back to all data but log warning
                if not recent_values:
                    recent_values = sorted_values
                    if sorted_values:
                        oldest_fy = sorted_values[-1].get("fiscal_year", "unknown")
                        print(f"  [WARNING] {company_name}/{metric_name}: No recent data, using stale data from FY{oldest_fy}")

                # Get recent annual values (last 10 years for better historical coverage)
                annual_values = [v for v in recent_values if v.get("form") == "10-K"][:10]

                # Get recent quarterly values (last 8 quarters)
                quarterly_values = [v for v in recent_values if v.get("form") == "10-Q"][:8]

                # Use friendly name if available (e.g., PaymentsToAcquire... -> CapitalExpenditures)
                output_name = SEC_METRIC_NAMES.get(metric_name, metric_name)

                # Use fiscal_year as the primary year identifier for consistency
                # This aligns data across companies with different fiscal year end dates
                company_metrics[output_name] = {
                    "annual": [
                        {
                            "year": v.get("fiscal_year"),
                            "date": v.get("end_date"),
                            "value": v.get("value"),
                        }
                        for v in annual_values
                    ],
                    "quarterly": [
                        {
                            "year": v.get("fiscal_year"),
                            "period": v.get("fiscal_period"),
                            "date": v.get("end_date"),
                            "value": v.get("value"),
                        }
                        for v in quarterly_values
                    ],
                }

            processed[company_name] = company_metrics

        return processed

    def _select_most_recent_capex(self, data: Dict) -> Dict:
        """
        Select the Capex data source with the most recent date.

        Some companies (e.g., Nvidia, Amazon) have both CapitalExpenditures and
        CapitalExpenditures_Alt fields. The primary field may contain stale data
        (e.g., 2011) while the Alt field has current data (e.g., 2024-2025).

        This method compares the most recent date in each field and returns
        the one with newer data.
        """
        primary = data.get("CapitalExpenditures", {})
        alt = data.get("CapitalExpenditures_Alt", {})

        primary_annual = primary.get("annual", [])
        alt_annual = alt.get("annual", [])

        # If only one has data, use that
        if not primary_annual and not alt_annual:
            return {}
        if not primary_annual:
            return alt
        if not alt_annual:
            return primary

        # Both have data - compare most recent dates
        def get_latest_date(annual_list: List[Dict]) -> str:
            if not annual_list:
                return ""
            dates = [item.get("date", "") for item in annual_list if item.get("date")]
            return max(dates) if dates else ""

        primary_latest = get_latest_date(primary_annual)
        alt_latest = get_latest_date(alt_annual)

        # Return the one with more recent data
        if alt_latest > primary_latest:
            return alt
        return primary

    def calculate_derived_metrics(self, sec_processed: Dict, yahoo_data: Dict = None) -> Dict[str, Dict]:
        """
        Calculate derived financial metrics

        Args:
            sec_processed: Processed SEC data
            yahoo_data: Optional Yahoo Finance data for fallback/validation

        Returns:
            Dictionary with derived metrics per company
        """
        derived = {}

        # Map company names to tickers for Yahoo data lookup
        company_to_ticker = {
            "Amazon": "AMZN", "Microsoft": "MSFT", "Alphabet": "GOOG",
            "Meta": "META", "Oracle": "ORCL", "Nvidia": "NVDA"
        }

        for company_name, data in sec_processed.items():
            company_derived = {"company": company_name, "data_quality_notes": []}

            # Get Yahoo data for this company if available
            ticker = company_to_ticker.get(company_name)
            yahoo_company = yahoo_data.get(ticker, {}).get("info", {}) if yahoo_data and ticker else {}

            # Get latest values (use friendly names from SEC_METRIC_NAMES mapping)
            # Choose Capex field with most recent data (fixes issue where primary field has stale data)
            # Nvidia and Amazon have both CapitalExpenditures (old) and CapitalExpenditures_Alt (current)
            capex_data = self._select_most_recent_capex(data)
            cashflow_data = data.get("OperatingCashFlow", {}) or data.get("NetCashProvidedByUsedInOperatingActivities", {})
            revenue_data = data.get("Revenues", {})
            debt_data = data.get("LongTermDebt", {})

            # Calculate Capex to Cash Flow ratio
            capex_annual = capex_data.get("annual", [])
            cashflow_annual = cashflow_data.get("annual", [])

            if capex_annual and cashflow_annual:
                # Get most recent values
                latest_capex = abs(capex_annual[0].get("value", 0)) if capex_annual else 0
                latest_cashflow = cashflow_annual[0].get("value", 0) if cashflow_annual else 0

                if latest_cashflow > 0:
                    company_derived["capex_to_cashflow_ratio"] = round(
                        latest_capex / latest_cashflow, 3
                    )
                else:
                    company_derived["capex_to_cashflow_ratio"] = None

                company_derived["latest_capex"] = latest_capex
                company_derived["latest_operating_cashflow"] = latest_cashflow

            # Calculate year-over-year growth rates
            def calc_yoy_growth(values: List[Dict]) -> Optional[float]:
                if len(values) >= 2:
                    current = values[0].get("value", 0)
                    previous = values[1].get("value", 0)
                    if previous and previous != 0:
                        return round(((current - previous) / abs(previous)) * 100, 2)
                return None

            # Revenue growth - use Yahoo fallback if SEC data is missing or stale
            revenue_annual = revenue_data.get("annual", [])
            sec_revenue = revenue_annual[0].get("value") if revenue_annual else None
            sec_revenue_date = revenue_annual[0].get("date", "") if revenue_annual else ""
            sec_revenue_year = self._extract_year_from_date(sec_revenue_date)

            # Check if SEC revenue is missing or stale (>3 years old) - fallback to Yahoo
            is_stale = sec_revenue_year and sec_revenue_year < (datetime.now().year - 3)
            use_yahoo_revenue = (sec_revenue is None or is_stale) and yahoo_company.get("revenue")

            if use_yahoo_revenue:
                yahoo_revenue = yahoo_company.get("revenue")
                company_derived["latest_revenue"] = yahoo_revenue
                company_derived["revenue_source"] = "yahoo"
                # Use Yahoo's revenue growth if available
                if yahoo_company.get("revenue_growth"):
                    company_derived["revenue_growth_yoy"] = round(yahoo_company["revenue_growth"] * 100, 2)
                else:
                    company_derived["revenue_growth_yoy"] = None
                reason = "stale" if is_stale else "missing"
                company_derived["data_quality_notes"].append(
                    f"SEC revenue {reason} ({sec_revenue_date}), using Yahoo Finance: ${yahoo_revenue/1e9:.1f}B"
                )
            else:
                company_derived["revenue_growth_yoy"] = calc_yoy_growth(revenue_annual)
                if revenue_annual:
                    company_derived["latest_revenue"] = revenue_annual[0].get("value")
                    company_derived["revenue_source"] = "sec"

            # Debt growth - use Yahoo fallback if SEC data is missing or zero
            debt_annual = debt_data.get("annual", [])
            sec_debt = debt_annual[0].get("value") if debt_annual else None

            # Check if SEC debt is missing or zero - fallback to Yahoo
            if (sec_debt is None or sec_debt == 0) and yahoo_company.get("total_debt"):
                yahoo_debt = yahoo_company.get("total_debt")
                company_derived["latest_debt"] = yahoo_debt
                company_derived["debt_source"] = "yahoo"
                company_derived["data_quality_notes"].append(
                    f"SEC debt missing/zero, using Yahoo Finance: ${yahoo_debt/1e9:.1f}B"
                )
                # Cannot calculate growth without historical SEC data
                company_derived["debt_growth_yoy"] = None
            else:
                company_derived["debt_growth_yoy"] = calc_yoy_growth(debt_annual)
                if debt_annual:
                    company_derived["latest_debt"] = debt_annual[0].get("value")
                    company_derived["debt_source"] = "sec"

            # Capex growth
            company_derived["capex_growth_yoy"] = calc_yoy_growth(capex_annual)

            # Debt to revenue growth ratio
            revenue_growth = company_derived.get("revenue_growth_yoy")
            debt_growth = company_derived.get("debt_growth_yoy")
            if revenue_growth and debt_growth and revenue_growth != 0:
                company_derived["debt_to_revenue_growth_ratio"] = round(
                    debt_growth / revenue_growth, 3
                )

            # Capex efficiency: Revenue growth / Capex growth
            capex_growth = company_derived.get("capex_growth_yoy")
            if revenue_growth and capex_growth and capex_growth != 0:
                company_derived["capex_efficiency"] = round(
                    revenue_growth / capex_growth, 3
                )

            derived[company_name] = company_derived

        return derived

    def process_fred_data(self, fred_data: Dict) -> Dict[str, Dict]:
        """
        Process FRED macroeconomic data

        Args:
            fred_data: Raw FRED data

        Returns:
            Processed macro indicators
        """
        processed = {}

        for series_id, data in fred_data.items():
            observations = data.get("observations", [])

            if not observations:
                continue

            # Get latest value
            latest = observations[-1] if observations else None

            # Calculate recent trend (last 12 observations or available)
            recent = observations[-12:]
            if len(recent) >= 2:
                first_val = recent[0].get("value", 0)
                last_val = recent[-1].get("value", 0)
                if first_val != 0:
                    trend_pct = ((last_val - first_val) / abs(first_val)) * 100
                else:
                    trend_pct = 0
            else:
                trend_pct = 0

            processed[series_id] = {
                "description": data.get("description"),
                "latest_value": latest.get("value") if latest else None,
                "latest_date": latest.get("date") if latest else None,
                "trend_pct": round(trend_pct, 2),
                "trend_direction": "up" if trend_pct > 1 else ("down" if trend_pct < -1 else "stable"),
                "observation_count": len(observations),
            }

        return processed

    def process_yahoo_data(self, yahoo_data: Dict) -> Dict[str, Dict]:
        """
        Process Yahoo Finance data

        Args:
            yahoo_data: Raw Yahoo data

        Returns:
            Processed market metrics per company
        """
        processed = {}

        for ticker, data in yahoo_data.items():
            info = data.get("info", {})

            if not info:
                continue

            # Extract key metrics, converting to billions where appropriate
            def to_billions(value):
                if value is not None:
                    return round(value / 1e9, 2)
                return None

            processed[ticker] = {
                "name": info.get("name"),
                "market_cap_B": to_billions(info.get("market_cap")),
                "total_debt_B": to_billions(info.get("total_debt")),
                "total_cash_B": to_billions(info.get("total_cash")),
                "free_cashflow_B": to_billions(info.get("free_cashflow")),
                "operating_cashflow_B": to_billions(info.get("operating_cashflow")),
                "revenue_B": to_billions(info.get("revenue")),
                "revenue_growth": info.get("revenue_growth"),
                "profit_margins": info.get("profit_margins"),
                "pe_ratio": info.get("pe_ratio"),
                "beta": info.get("beta"),
                "debt_to_cash_ratio": (
                    round(info.get("total_debt", 0) / info.get("total_cash", 1), 2)
                    if info.get("total_cash") and info.get("total_debt")
                    else None
                ),
            }

        return processed

    def create_consolidated_dataset(self) -> Dict:
        """
        Load and consolidate all data sources into a single dataset

        Returns:
            Consolidated dataset for risk analysis
        """
        print("Loading raw data files...")

        # Load raw data
        sec_data = self.load_json("sec_company_data.json")
        fred_data = self.load_json("fred_series_data.json")
        yahoo_data = self.load_json("yahoo_company_data.json")

        consolidated = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "sources": {
                    "sec": sec_data is not None,
                    "fred": fred_data is not None,
                    "yahoo": yahoo_data is not None,
                },
            },
            "companies": {},
            "macro_indicators": {},
        }

        # Process SEC data (with Yahoo data available for fallback)
        if sec_data:
            print("Processing SEC data...")
            sec_processed = self.process_sec_data(sec_data)
            # Pass Yahoo data for fallback when SEC data is missing
            derived_metrics = self.calculate_derived_metrics(sec_processed, yahoo_data)

            for company_name in sec_processed:
                consolidated["companies"][company_name] = {
                    "sec_metrics": sec_processed.get(company_name),
                    "derived_metrics": derived_metrics.get(company_name),
                }

        # Process FRED data
        if fred_data:
            print("Processing FRED data...")
            consolidated["macro_indicators"] = self.process_fred_data(fred_data)

        # Process Yahoo data and merge with companies
        if yahoo_data:
            print("Processing Yahoo Finance data...")
            yahoo_processed = self.process_yahoo_data(yahoo_data)

            # Map tickers to company names
            ticker_to_company = {
                "AMZN": "Amazon",
                "MSFT": "Microsoft",
                "GOOG": "Alphabet",
                "META": "Meta",
                "ORCL": "Oracle",
                "NVDA": "Nvidia",
            }

            for ticker, metrics in yahoo_processed.items():
                company_name = ticker_to_company.get(ticker)
                if company_name:
                    if company_name not in consolidated["companies"]:
                        consolidated["companies"][company_name] = {}
                    consolidated["companies"][company_name]["yahoo_metrics"] = metrics
                    consolidated["companies"][company_name]["ticker"] = ticker

        return consolidated

    def run(self) -> Dict:
        """
        Run the full data processing pipeline

        Returns:
            Consolidated dataset
        """
        print("=" * 60)
        print("Data Processing Pipeline")
        print("=" * 60)

        # Create consolidated dataset
        consolidated = self.create_consolidated_dataset()

        # Save consolidated data
        self.save_json(consolidated, "consolidated_data.json")

        # Generate summary statistics
        summary = self.generate_summary(consolidated)
        self.save_json(summary, "data_summary.json")

        print("\nProcessing complete!")
        return consolidated

    def generate_summary(self, consolidated: Dict) -> Dict:
        """Generate summary statistics from consolidated data"""
        companies = consolidated.get("companies", {})
        macro = consolidated.get("macro_indicators", {})

        summary = {
            "generated_at": datetime.now().isoformat(),
            "company_count": len(companies),
            "companies": [],
            "aggregate_metrics": {},
            "macro_summary": {},
        }

        total_capex = 0
        total_cashflow = 0
        total_debt = 0
        total_revenue = 0

        for company_name, data in companies.items():
            derived = data.get("derived_metrics", {})
            yahoo = data.get("yahoo_metrics", {})

            # Calculate capex from Yahoo Finance data (operating_cashflow - free_cashflow)
            # This is more reliable and consistent with supply_demand.py
            yahoo_op_cf = yahoo.get("operating_cashflow_B")
            yahoo_free_cf = yahoo.get("free_cashflow_B")
            estimated_capex_B = None
            if yahoo_op_cf is not None and yahoo_free_cf is not None:
                estimated_capex_B = round(yahoo_op_cf - yahoo_free_cf, 2)
                if estimated_capex_B < 0:
                    estimated_capex_B = None  # Invalid

            # Use Yahoo-derived capex/cashflow ratio if available
            capex_to_cashflow = None
            if estimated_capex_B and yahoo_op_cf and yahoo_op_cf > 0:
                capex_to_cashflow = round(estimated_capex_B / yahoo_op_cf, 3)
            elif derived.get("capex_to_cashflow_ratio"):
                capex_to_cashflow = derived.get("capex_to_cashflow_ratio")

            company_summary = {
                "name": company_name,
                "ticker": data.get("ticker"),
                "capex_to_cashflow": capex_to_cashflow,
                "capex_B": estimated_capex_B,
                "revenue_growth_yoy": derived.get("revenue_growth_yoy"),
                "debt_growth_yoy": derived.get("debt_growth_yoy"),
                "market_cap_B": yahoo.get("market_cap_B"),
            }
            summary["companies"].append(company_summary)

            # Aggregate - use Yahoo data for consistency with supply_demand.py
            if estimated_capex_B and estimated_capex_B > 0:
                total_capex += estimated_capex_B
            elif derived.get("latest_capex"):
                total_capex += abs(derived["latest_capex"]) / 1e9  # Convert to billions

            if yahoo_op_cf and yahoo_op_cf > 0:
                total_cashflow += yahoo_op_cf
            elif derived.get("latest_operating_cashflow"):
                total_cashflow += derived["latest_operating_cashflow"] / 1e9

            if yahoo.get("total_debt_B"):
                total_debt += yahoo.get("total_debt_B")
            elif derived.get("latest_debt"):
                total_debt += derived["latest_debt"] / 1e9

            if yahoo.get("revenue_B"):
                total_revenue += yahoo.get("revenue_B")
            elif derived.get("latest_revenue"):
                total_revenue += derived["latest_revenue"] / 1e9

        # Calculate aggregate metrics (values already in billions from Yahoo)
        summary["aggregate_metrics"] = {
            "total_capex_B": round(total_capex, 2),
            "total_operating_cashflow_B": round(total_cashflow, 2),
            "total_debt_B": round(total_debt, 2),
            "total_revenue_B": round(total_revenue, 2),
            "aggregate_capex_to_cashflow": (
                round(total_capex / total_cashflow, 3) if total_cashflow > 0 else None
            ),
        }

        # Macro summary
        for series_id, data in macro.items():
            summary["macro_summary"][series_id] = {
                "description": data.get("description"),
                "latest_value": data.get("latest_value"),
                "trend": data.get("trend_direction"),
            }

        return summary


def main():
    """Main function to run data processing"""
    processor = DataProcessor()
    consolidated = processor.run()

    # Print summary
    companies = consolidated.get("companies", {})
    print(f"\nProcessed data for {len(companies)} companies")

    return consolidated


if __name__ == "__main__":
    main()
