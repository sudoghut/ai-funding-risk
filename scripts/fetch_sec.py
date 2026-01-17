"""
SEC EDGAR Data Fetcher
Fetches financial data from SEC EDGAR API for target companies
"""
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    SEC_BASE_URL,
    SEC_USER_AGENT,
    SEC_RATE_LIMIT,
    TARGET_COMPANIES,
    SEC_METRICS,
    RAW_DATA_DIR,
)


class SECFetcher:
    """Fetches company financial data from SEC EDGAR API"""

    def __init__(self):
        self.base_url = SEC_BASE_URL
        self.headers = {"User-Agent": SEC_USER_AGENT}
        self.rate_limit = SEC_RATE_LIMIT
        self.last_request_time = 0

    def _rate_limit_wait(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_request_time = time.time()

    def fetch_company_facts(self, cik: str) -> Optional[Dict]:
        """
        Fetch all company facts from SEC EDGAR

        Args:
            cik: Company CIK number (with leading zeros)

        Returns:
            Dictionary of company facts or None if error
        """
        self._rate_limit_wait()

        url = f"{self.base_url}/CIK{cik}.json"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for CIK {cik}: {e}")
            return None

    def extract_metric(
        self,
        facts: Dict,
        metric_name: str,
        form_types: List[str] = ["10-K", "10-Q"]
    ) -> List[Dict]:
        """
        Extract specific metric from company facts

        Args:
            facts: Company facts dictionary
            metric_name: Name of the metric to extract (e.g., 'CapitalExpenditures')
            form_types: List of form types to include

        Returns:
            List of data points with dates and values
        """
        results = []

        try:
            us_gaap = facts.get("facts", {}).get("us-gaap", {})
            metric_data = us_gaap.get(metric_name, {})
            units = metric_data.get("units", {})

            # Most financial metrics are in USD
            usd_data = units.get("USD", [])

            for entry in usd_data:
                form_type = entry.get("form", "")
                if form_type in form_types:
                    results.append({
                        "end_date": entry.get("end"),
                        "value": entry.get("val"),
                        "form": form_type,
                        "fiscal_year": entry.get("fy"),
                        "fiscal_period": entry.get("fp"),
                        "filed": entry.get("filed"),
                    })
        except Exception as e:
            print(f"Error extracting {metric_name}: {e}")

        return results

    def fetch_all_companies(self) -> Dict[str, Dict]:
        """
        Fetch data for all target companies

        Returns:
            Dictionary mapping company names to their financial data
        """
        all_data = {}

        for company_name, cik in TARGET_COMPANIES.items():
            print(f"Fetching data for {company_name} (CIK: {cik})...")

            facts = self.fetch_company_facts(cik)
            if facts is None:
                continue

            company_data = {
                "cik": cik,
                "entity_name": facts.get("entityName", company_name),
                "metrics": {},
                "fetch_time": datetime.now().isoformat(),
            }

            for metric in SEC_METRICS:
                metric_values = self.extract_metric(facts, metric)
                if metric_values:
                    company_data["metrics"][metric] = metric_values

            all_data[company_name] = company_data
            print(f"  Retrieved {len(company_data['metrics'])} metrics")

        return all_data

    def get_latest_values(self, all_data: Dict) -> Dict[str, Dict]:
        """
        Extract the most recent value for each metric per company

        Args:
            all_data: Full company data dictionary

        Returns:
            Dictionary with latest values only
        """
        latest = {}

        for company, data in all_data.items():
            latest[company] = {"cik": data["cik"], "metrics": {}}

            for metric, values in data.get("metrics", {}).items():
                if values:
                    # Sort by end_date descending and take the most recent
                    sorted_values = sorted(
                        values,
                        key=lambda x: x.get("end_date", ""),
                        reverse=True
                    )
                    # Get most recent annual (10-K) and quarterly (10-Q)
                    annual = next(
                        (v for v in sorted_values if v.get("form") == "10-K"),
                        None
                    )
                    quarterly = next(
                        (v for v in sorted_values if v.get("form") == "10-Q"),
                        None
                    )

                    latest[company]["metrics"][metric] = {
                        "latest_annual": annual,
                        "latest_quarterly": quarterly,
                    }

        return latest

    def save_data(self, data: Dict, filename: str):
        """Save data to JSON file"""
        output_path = RAW_DATA_DIR / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Data saved to {output_path}")


def main():
    """Main function to fetch and save SEC data"""
    print("=" * 60)
    print("SEC EDGAR Data Fetcher")
    print("=" * 60)

    fetcher = SECFetcher()

    # Fetch all company data
    print("\nFetching company financial data...")
    all_data = fetcher.fetch_all_companies()

    # Save full historical data
    fetcher.save_data(all_data, "sec_company_data.json")

    # Extract and save latest values
    latest_data = fetcher.get_latest_values(all_data)
    fetcher.save_data(latest_data, "sec_latest_values.json")

    print("\nFetch complete!")
    print(f"Companies processed: {len(all_data)}")

    return all_data


if __name__ == "__main__":
    main()
