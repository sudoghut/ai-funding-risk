"""
WRDS Compustat Data Fetcher
Fetches historical financial data from Wharton Research Data Services REST API

Uses the WRDS REST API at wrds-api.wharton.upenn.edu with Token authentication.
Queries Compustat Annual Fundamentals (comp.funda) for 90s IT bubble companies.
"""
import json
import os
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import WRDS_API_TOKEN, RAW_DATA_DIR, COMPILED_DATA_DIR

WRDS_API_BASE = "https://wrds-api.wharton.upenn.edu"

# Target companies for 90s IT bubble analysis
# Note: WRDS Compustat uses different tickers for some historical companies
# Sun Microsystems is listed as JAVA.1, Lucent as LU.1 in WRDS REST API
WRDS_TARGETS = {
    "CSCO": {"name": "Cisco Systems", "wrds_tic": "CSCO"},
    "INTC": {"name": "Intel Corporation", "wrds_tic": "INTC"},
    "MSFT": {"name": "Microsoft Corporation", "wrds_tic": "MSFT"},
    "ORCL": {"name": "Oracle Corporation", "wrds_tic": "ORCL"},
    "SUNW": {"name": "Sun Microsystems", "wrds_tic": None, "wrds_gvkey": "012136"},
    "LU":   {"name": "Lucent Technologies", "wrds_tic": None, "wrds_gvkey": "062599"},
}

# Key Compustat fields
FIELDS_OF_INTEREST = [
    "gvkey", "datadate", "conm", "tic", "fyear", "fyr",
    "capx", "oancf", "revt", "sale", "dltt", "che", "ni",
    "emp", "csho", "prcc_f", "at", "seq",
    "indfmt", "datafmt", "popsrc", "consol",
]


class WRDSFetcher:
    """Fetches historical data from WRDS Compustat via REST API"""

    def __init__(self, api_token: str = None):
        self.token = api_token or WRDS_API_TOKEN
        if not self.token:
            raise ValueError("WRDS_API_TOKEN not set in .env")
        self.headers = {"Authorization": f"Token {self.token}"}
        self.base_url = f"{WRDS_API_BASE}/data/comp.funda/"

    def test_connection(self) -> bool:
        """Test WRDS API connectivity"""
        try:
            resp = requests.get(
                f"{WRDS_API_BASE}/data/",
                headers=self.headers,
                timeout=10
            )
            if resp.status_code == 200:
                print("WRDS API connection successful!")
                return True
            else:
                print(f"WRDS API error: {resp.status_code}")
                return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def fetch_company_data(self, ticker: str = None, gvkey: str = None,
                           start_year: int = 1995, end_year: int = 2003) -> List[Dict]:
        """Fetch annual financial data for a single company from Compustat.
        Can search by ticker or gvkey (for historical companies with changed tickers).
        """
        all_results = []
        params = {
            "fyear__gte": start_year,
            "fyear__lte": end_year,
            "indfmt": "INDL",
            "datafmt": "STD",
            "popsrc": "D",
            "consol": "C",
            "limit": 100,
        }
        if gvkey:
            params["gvkey"] = gvkey
        elif ticker:
            params["tic"] = ticker

        url = self.base_url
        while url:
            try:
                resp = requests.get(
                    url,
                    headers=self.headers,
                    params=params if url == self.base_url else None,
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()

                results = data.get("results", [])
                for record in results:
                    filtered = {}
                    for field in FIELDS_OF_INTEREST:
                        val = record.get(field)
                        if val is not None and field not in [
                            "gvkey", "datadate", "conm", "tic",
                            "indfmt", "datafmt", "popsrc", "consol"
                        ]:
                            try:
                                filtered[field] = float(val) if val != "" else None
                            except (ValueError, TypeError):
                                filtered[field] = val
                        else:
                            filtered[field] = val
                    all_results.append(filtered)

                url = data.get("next")
                params = None  # next URL has params

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {ticker}: {e}")
                break

        return all_results

    def fetch_all_companies(self) -> Dict[str, Dict]:
        """Fetch data for all target companies"""
        all_data = {}

        for ticker, info in WRDS_TARGETS.items():
            company_name = info["name"]
            wrds_tic = info.get("wrds_tic")
            wrds_gvkey = info.get("wrds_gvkey")
            print(f"Fetching {company_name} ({ticker})...")
            records = self.fetch_company_data(ticker=wrds_tic, gvkey=wrds_gvkey)

            if records:
                years_data = {}
                for record in records:
                    fyear = record.get("fyear")
                    if not fyear:
                        continue
                    year_key = int(fyear)
                    # Skip duplicate records without revenue (WRDS sometimes returns
                    # multiple records per year, prefer the one with revenue data)
                    if year_key in years_data and not record.get("revt"):
                        continue
                    years_data[year_key] = {
                        "fiscal_year": year_key,
                        "datadate": record.get("datadate"),
                        "revenue": record.get("revt"),
                        "sales": record.get("sale"),
                        "capex": record.get("capx"),
                        "operating_cashflow": record.get("oancf"),
                        "long_term_debt": record.get("dltt"),
                        "cash_and_equivalents": record.get("che"),
                        "net_income": record.get("ni"),
                        "employees_thousands": record.get("emp"),
                        "shares_outstanding_M": record.get("csho"),
                        "stock_price_fy_close": record.get("prcc_f"),
                        "total_assets": record.get("at"),
                        "stockholders_equity": record.get("seq"),
                    }

                    csho = record.get("csho")
                    prcc = record.get("prcc_f")
                    if csho and prcc:
                        years_data[year_key]["market_cap"] = round(csho * prcc, 2)

                all_data[ticker] = {
                    "company_name": company_name,
                    "ticker": ticker,
                    "gvkey": records[0].get("gvkey") if records else None,
                    "years_available": sorted(years_data.keys()),
                    "annual_data": years_data,
                }
                print(f"  Got {len(years_data)} years: {sorted(years_data.keys())}")
            else:
                print(f"  No data found")

        return all_data

    def save_data(self, data: Dict, filename: str):
        """Save data to JSON file"""
        output_path = RAW_DATA_DIR / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"Data saved to {output_path}")

    def update_compiled_data(self, wrds_data: Dict):
        """Update compiled historical data with actual WRDS Compustat values"""
        compiled_file = COMPILED_DATA_DIR / "historical_financials.json"
        if not compiled_file.exists():
            print("Compiled data file not found - skipping update")
            return

        with open(compiled_file, "r", encoding="utf-8") as f:
            compiled = json.load(f)

        ticker_to_company = {
            "CSCO": "Cisco", "INTC": "Intel", "MSFT": "Microsoft",
            "ORCL": "Oracle", "SUNW": "Sun Microsystems", "LU": "Lucent",
        }

        updated_count = 0
        for ticker, company_data in wrds_data.items():
            company_name = ticker_to_company.get(ticker)
            if not company_name or company_name not in compiled.get("companies", {}):
                continue

            compiled_company = compiled["companies"][company_name]
            wrds_years = company_data.get("annual_data", {})

            for i, annual in enumerate(compiled_company.get("annual_data", [])):
                year = annual["year"]
                # Handle both int and string keys (JSON may deserialize as strings)
                if year in wrds_years or str(year) in wrds_years:
                    w = wrds_years.get(year) or wrds_years.get(str(year))
                    if w.get("revenue"):
                        compiled_company["annual_data"][i]["revenue"] = w["revenue"]
                    if w.get("capex"):
                        compiled_company["annual_data"][i]["capex"] = w["capex"]
                    if w.get("operating_cashflow"):
                        compiled_company["annual_data"][i]["operating_cashflow"] = w["operating_cashflow"]
                    if w.get("long_term_debt") is not None:
                        compiled_company["annual_data"][i]["long_term_debt"] = w["long_term_debt"]
                    if w.get("cash_and_equivalents"):
                        compiled_company["annual_data"][i]["total_cash"] = w["cash_and_equivalents"]
                    if w.get("net_income"):
                        compiled_company["annual_data"][i]["net_income"] = w["net_income"]
                    if w.get("employees_thousands"):
                        compiled_company["annual_data"][i]["employees"] = int(w["employees_thousands"] * 1000)
                    if w.get("market_cap"):
                        compiled_company["annual_data"][i]["market_cap_peak"] = w["market_cap"]
                    updated_count += 1

        compiled["metadata"]["wrds_updated"] = True
        compiled["metadata"]["wrds_update_time"] = datetime.now().isoformat()
        compiled["metadata"]["wrds_records_updated"] = updated_count

        with open(compiled_file, "w", encoding="utf-8") as f:
            json.dump(compiled, f, indent=2, ensure_ascii=False)
        print(f"Updated {updated_count} records in compiled data with WRDS values")


def main():
    """Main function to fetch WRDS Compustat data"""
    print("=" * 60)
    print("WRDS Compustat Data Fetcher (1995-2003)")
    print("=" * 60)

    try:
        fetcher = WRDSFetcher()
    except ValueError as e:
        print(f"Error: {e}")
        return None

    if not fetcher.test_connection():
        print("Cannot connect to WRDS API")
        return None

    print("\nFetching Compustat annual data...")
    data = fetcher.fetch_all_companies()

    if data:
        fetcher.save_data({
            "metadata": {
                "source": "WRDS Compustat Annual Fundamentals (comp.funda)",
                "period": "1995-2003",
                "fetched_at": datetime.now().isoformat(),
                "companies": len(data),
            },
            "companies": data,
        }, "wrds_compustat_data.json")

        print("\nUpdating compiled data with WRDS values...")
        fetcher.update_compiled_data(data)

    print("\nWRDS fetch complete!")
    return data


if __name__ == "__main__":
    main()
