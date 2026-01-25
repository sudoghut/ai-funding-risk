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

    def calculate_derived_metrics(
        self, sec_processed: Dict, yahoo_data: Dict = None, yahoo_historical: Dict = None
    ) -> Dict[str, Dict]:
        """
        Calculate derived financial metrics using Yahoo Finance as primary data source.

        Yahoo data is preferred because:
        1. Calendar-year aligned (avoids fiscal year mismatch issues)
        2. More up-to-date TTM (trailing twelve months) data
        3. Consistent across all companies

        SEC data is used as fallback when Yahoo data is unavailable.

        Args:
            sec_processed: Processed SEC data (fallback)
            yahoo_data: Yahoo Finance current data (primary for latest values)
            yahoo_historical: Yahoo Finance historical data (primary for YoY growth)

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

            # Get Yahoo data for this company
            ticker = company_to_ticker.get(company_name)
            yahoo_company = yahoo_data.get(ticker, {}).get("info", {}) if yahoo_data and ticker else {}
            yahoo_hist = yahoo_historical.get(ticker, {}) if yahoo_historical and ticker else {}

            # Get SEC data as fallback
            capex_data = self._select_most_recent_capex(data)
            cashflow_data = data.get("OperatingCashFlow", {}) or data.get("NetCashProvidedByUsedInOperatingActivities", {})
            revenue_data = data.get("Revenues", {})
            debt_data = data.get("LongTermDebt", {})

            capex_annual = capex_data.get("annual", [])
            cashflow_annual = cashflow_data.get("annual", [])

            # Calculate Capex to Cash Flow ratio using Yahoo data (primary)
            yahoo_op_cf = yahoo_company.get("operating_cashflow")
            yahoo_free_cf = yahoo_company.get("free_cashflow")

            if yahoo_op_cf and yahoo_free_cf:
                # CapEx = Operating Cash Flow - Free Cash Flow
                latest_capex = yahoo_op_cf - yahoo_free_cf
                latest_cashflow = yahoo_op_cf
                if latest_cashflow > 0 and latest_capex > 0:
                    company_derived["capex_to_cashflow_ratio"] = round(
                        latest_capex / latest_cashflow, 3
                    )
                    company_derived["latest_capex"] = latest_capex
                    company_derived["latest_operating_cashflow"] = latest_cashflow
                    company_derived["capex_source"] = "yahoo"
            elif capex_annual and cashflow_annual:
                # Fallback to SEC data
                latest_capex = abs(capex_annual[0].get("value", 0)) if capex_annual else 0
                latest_cashflow = cashflow_annual[0].get("value", 0) if cashflow_annual else 0
                if latest_cashflow > 0:
                    company_derived["capex_to_cashflow_ratio"] = round(
                        latest_capex / latest_cashflow, 3
                    )
                company_derived["latest_capex"] = latest_capex
                company_derived["latest_operating_cashflow"] = latest_cashflow
                company_derived["capex_source"] = "sec"

            # Helper to calculate YoY growth from Yahoo historical data
            def calc_yahoo_yoy_growth(hist_list: List[Dict]) -> Optional[float]:
                if len(hist_list) >= 2:
                    current = hist_list[0].get("value", 0)
                    previous = hist_list[1].get("value", 0)
                    if previous and previous != 0:
                        return round(((current - previous) / abs(previous)) * 100, 2)
                return None

            # Helper for SEC fallback
            def calc_sec_yoy_growth(values: List[Dict]) -> Optional[float]:
                if len(values) >= 2:
                    current = values[0].get("value", 0)
                    previous = values[1].get("value", 0)
                    if previous and previous != 0:
                        return round(((current - previous) / abs(previous)) * 100, 2)
                return None

            # Revenue - Yahoo as primary source
            yahoo_revenue_hist = yahoo_hist.get("revenue", [])
            if yahoo_revenue_hist:
                # Use Yahoo historical data for growth calculation
                company_derived["latest_revenue"] = yahoo_revenue_hist[0].get("value", 0) * 1e9  # Convert back to raw
                company_derived["revenue_growth_yoy"] = calc_yahoo_yoy_growth(yahoo_revenue_hist)
                company_derived["revenue_source"] = "yahoo"
            elif yahoo_company.get("revenue"):
                # Fallback to Yahoo info (no historical growth)
                company_derived["latest_revenue"] = yahoo_company.get("revenue")
                if yahoo_company.get("revenue_growth"):
                    company_derived["revenue_growth_yoy"] = round(yahoo_company["revenue_growth"] * 100, 2)
                company_derived["revenue_source"] = "yahoo_info"
            else:
                # Fallback to SEC data
                revenue_annual = revenue_data.get("annual", [])
                if revenue_annual:
                    company_derived["latest_revenue"] = revenue_annual[0].get("value")
                    company_derived["revenue_growth_yoy"] = calc_sec_yoy_growth(revenue_annual)
                    company_derived["revenue_source"] = "sec"
                    company_derived["data_quality_notes"].append("Using SEC revenue data (Yahoo unavailable)")

            # Debt - Yahoo as primary source
            yahoo_debt_hist = yahoo_hist.get("debt", [])
            if yahoo_debt_hist:
                # Use Yahoo historical data for growth calculation
                company_derived["latest_debt"] = yahoo_debt_hist[0].get("value", 0) * 1e9  # Convert back to raw
                company_derived["debt_growth_yoy"] = calc_yahoo_yoy_growth(yahoo_debt_hist)
                company_derived["debt_source"] = "yahoo"
            elif yahoo_company.get("total_debt"):
                # Fallback to Yahoo info (no historical growth)
                company_derived["latest_debt"] = yahoo_company.get("total_debt")
                company_derived["debt_growth_yoy"] = None
                company_derived["debt_source"] = "yahoo_info"
            else:
                # Fallback to SEC data
                debt_annual = debt_data.get("annual", [])
                if debt_annual:
                    company_derived["latest_debt"] = debt_annual[0].get("value")
                    company_derived["debt_growth_yoy"] = calc_sec_yoy_growth(debt_annual)
                    company_derived["debt_source"] = "sec"
                    company_derived["data_quality_notes"].append("Using SEC debt data (Yahoo unavailable)")

            # Capex growth - use Yahoo historical if available
            yahoo_capex_hist = yahoo_hist.get("capex", [])
            if yahoo_capex_hist:
                company_derived["capex_growth_yoy"] = calc_yahoo_yoy_growth(yahoo_capex_hist)
            else:
                company_derived["capex_growth_yoy"] = calc_sec_yoy_growth(capex_annual)

            # Derived ratios
            revenue_growth = company_derived.get("revenue_growth_yoy")
            debt_growth = company_derived.get("debt_growth_yoy")
            capex_growth = company_derived.get("capex_growth_yoy")

            # Debt to revenue growth ratio
            if revenue_growth and debt_growth and revenue_growth != 0:
                company_derived["debt_to_revenue_growth_ratio"] = round(
                    debt_growth / revenue_growth, 3
                )

            # Capex efficiency: Revenue growth / Capex growth
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

    def process_yahoo_historical_data(self, yahoo_data: Dict) -> Dict[str, Dict]:
        """
        Process Yahoo Finance historical data to extract calendar-year aligned
        CapEx, OCF, Revenue, and Debt time series.

        This data is used for historical trend analysis to avoid fiscal year mismatch
        issues that occur with SEC data.

        Args:
            yahoo_data: Raw Yahoo data with annual_cashflow, annual_financials, annual_balance_sheet

        Returns:
            Dictionary mapping tickers to historical metrics by calendar year
        """
        processed = {}

        for ticker, data in yahoo_data.items():
            capex_history = []
            ocf_history = []
            revenue_history = []
            debt_history = []
            ocf_breakdown_history = []
            funding_sources_history = []

            # Process cashflow data (CapEx, OCF, OCF Breakdown, Funding Sources)
            annual_cf = data.get("annual_cashflow", {})
            if annual_cf and annual_cf.get("data"):
                cf_data = annual_cf["data"]
                for period, values in cf_data.items():
                    try:
                        year = int(period[:4])
                    except (ValueError, TypeError):
                        continue

                    # Get CapEx (stored as negative in Yahoo, we want absolute value)
                    capex = values.get("Capital Expenditure", 0)
                    if capex:
                        capex_history.append({
                            "year": year,
                            "period": period,
                            "value": round(abs(capex) / 1e9, 2)  # Convert to billions
                        })

                    # Get Operating Cash Flow
                    ocf = values.get("Operating Cash Flow", 0)
                    if ocf:
                        ocf_history.append({
                            "year": year,
                            "period": period,
                            "value": round(ocf / 1e9, 2)  # Convert to billions
                        })

                    # OCF Breakdown (components that make up OCF)
                    net_income = values.get("Net Income From Continuing Operations", 0)
                    depreciation = values.get("Depreciation And Amortization", 0)
                    stock_comp = values.get("Stock Based Compensation", 0)
                    working_capital = values.get("Change In Working Capital", 0)
                    deferred_tax = values.get("Deferred Income Tax", 0)

                    # Calculate "Other" as the difference
                    known_components = (net_income or 0) + (depreciation or 0) + (stock_comp or 0) + (working_capital or 0) + (deferred_tax or 0)
                    other = (ocf or 0) - known_components

                    ocf_breakdown_history.append({
                        "year": year,
                        "period": period,
                        "net_income": round((net_income or 0) / 1e9, 2),
                        "depreciation": round((depreciation or 0) / 1e9, 2),
                        "stock_compensation": round((stock_comp or 0) / 1e9, 2),
                        "working_capital": round((working_capital or 0) / 1e9, 2),
                        "deferred_tax": round((deferred_tax or 0) / 1e9, 2),
                        "other": round(other / 1e9, 2),
                        "total_ocf": round((ocf or 0) / 1e9, 2)
                    })

                    # Funding Sources (how CapEx is financed)
                    free_cashflow = values.get("Free Cash Flow", 0)
                    debt_issuance = values.get("Long Term Debt Issuance", 0) or 0
                    debt_payment = values.get("Long Term Debt Payments", 0) or 0
                    net_debt = values.get("Net Long Term Debt Issuance", 0) or 0
                    stock_issuance = values.get("Common Stock Issuance", 0) or values.get("Issuance Of Capital Stock", 0) or 0
                    stock_repurchase = values.get("Repurchase Of Capital Stock", 0) or 0
                    dividends = values.get("Cash Dividends Paid", 0) or 0

                    funding_sources_history.append({
                        "year": year,
                        "period": period,
                        "capex": round(abs(capex or 0) / 1e9, 2),
                        "ocf": round((ocf or 0) / 1e9, 2),
                        "free_cashflow": round((free_cashflow or 0) / 1e9, 2),
                        "debt_issuance": round((debt_issuance or 0) / 1e9, 2),
                        "debt_payment": round(abs(debt_payment or 0) / 1e9, 2),
                        "net_debt_financing": round((net_debt or 0) / 1e9, 2),
                        "stock_issuance": round((stock_issuance or 0) / 1e9, 2),
                        "stock_repurchase": round(abs(stock_repurchase or 0) / 1e9, 2),
                        "dividends": round(abs(dividends or 0) / 1e9, 2)
                    })

            # Process financials data (Revenue)
            annual_fin = data.get("annual_financials", {})
            if annual_fin and annual_fin.get("data"):
                fin_data = annual_fin["data"]
                for period, values in fin_data.items():
                    try:
                        year = int(period[:4])
                    except (ValueError, TypeError):
                        continue

                    revenue = values.get("Total Revenue", 0)
                    if revenue and revenue > 0:
                        revenue_history.append({
                            "year": year,
                            "period": period,
                            "value": round(revenue / 1e9, 2)  # Convert to billions
                        })

            # Process balance sheet data (Debt, Cash)
            annual_bs = data.get("annual_balance_sheet", {})
            if annual_bs and annual_bs.get("data"):
                bs_data = annual_bs["data"]
                for period, values in bs_data.items():
                    try:
                        year = int(period[:4])
                    except (ValueError, TypeError):
                        continue

                    debt = values.get("Total Debt", 0)
                    if debt is not None:  # Allow 0 debt
                        debt_history.append({
                            "year": year,
                            "period": period,
                            "value": round(debt / 1e9, 2) if debt else 0  # Convert to billions
                        })

            # Sort all by year descending
            capex_history.sort(key=lambda x: x["year"], reverse=True)
            ocf_history.sort(key=lambda x: x["year"], reverse=True)
            revenue_history.sort(key=lambda x: x["year"], reverse=True)
            debt_history.sort(key=lambda x: x["year"], reverse=True)
            ocf_breakdown_history.sort(key=lambda x: x["year"], reverse=True)
            funding_sources_history.sort(key=lambda x: x["year"], reverse=True)

            processed[ticker] = {
                "capex": capex_history,
                "ocf": ocf_history,
                "revenue": revenue_history,
                "debt": debt_history,
                "ocf_breakdown": ocf_breakdown_history,
                "funding_sources": funding_sources_history
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

        # Process Yahoo data first (primary data source)
        yahoo_processed = {}
        yahoo_historical = {}
        ticker_to_company = {
            "AMZN": "Amazon",
            "MSFT": "Microsoft",
            "GOOG": "Alphabet",
            "META": "Meta",
            "ORCL": "Oracle",
            "NVDA": "Nvidia",
        }

        if yahoo_data:
            print("Processing Yahoo Finance data (primary source)...")
            yahoo_processed = self.process_yahoo_data(yahoo_data)
            yahoo_historical = self.process_yahoo_historical_data(yahoo_data)

        # Process SEC data (with Yahoo as primary, SEC as fallback)
        if sec_data:
            print("Processing SEC data (fallback source)...")
            sec_processed = self.process_sec_data(sec_data)
            # Pass Yahoo data as primary source, SEC as fallback
            derived_metrics = self.calculate_derived_metrics(
                sec_processed, yahoo_data, yahoo_historical
            )

            for company_name in sec_processed:
                consolidated["companies"][company_name] = {
                    "sec_metrics": sec_processed.get(company_name),
                    "derived_metrics": derived_metrics.get(company_name),
                }

        # Process FRED data
        if fred_data:
            print("Processing FRED data...")
            consolidated["macro_indicators"] = self.process_fred_data(fred_data)

        # Merge Yahoo data with companies
        if yahoo_data:
            for ticker, metrics in yahoo_processed.items():
                company_name = ticker_to_company.get(ticker)
                if company_name:
                    if company_name not in consolidated["companies"]:
                        consolidated["companies"][company_name] = {}
                    consolidated["companies"][company_name]["yahoo_metrics"] = metrics
                    consolidated["companies"][company_name]["ticker"] = ticker

                    # Add Yahoo historical data for calendar-year aligned analysis
                    if ticker in yahoo_historical:
                        consolidated["companies"][company_name]["yahoo_historical"] = yahoo_historical[ticker]

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
