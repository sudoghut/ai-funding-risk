"""
FRED Historical Data Fetcher (1995-2003)
Fetches macroeconomic data from the 90s IT Bubble period
"""
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    FRED_API_KEY, FRED_SERIES, FRED_CREDIT_SERIES,
    RAW_DATA_DIR, MARKET_DATA_DIR,
    HISTORY_START_DATE, HISTORY_END_DATE,
)


class FREDHistoryFetcher:
    """Fetches 1995-2003 macroeconomic data from FRED API"""

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: str = None):
        self.api_key = (api_key or FRED_API_KEY).strip()
        if not self.api_key:
            raise ValueError("FRED API key required")

    def fetch_series(self, series_id: str, start_date: str = None, end_date: str = None) -> Optional[Dict]:
        """Fetch a single FRED series for the historical period"""
        if start_date is None:
            start_date = HISTORY_START_DATE
        if end_date is None:
            end_date = HISTORY_END_DATE

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date,
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            observations = data.get("observations", [])
            cleaned = []
            for obs in observations:
                value = obs.get("value", ".")
                if value != ".":
                    try:
                        cleaned.append({"date": obs.get("date"), "value": float(value)})
                    except ValueError:
                        continue

            # Merge description from both dictionaries
            all_series = {**FRED_SERIES, **FRED_CREDIT_SERIES}

            return {
                "series_id": series_id,
                "description": all_series.get(series_id, "Unknown"),
                "observations": cleaned,
                "count": len(cleaned),
                "start_date": start_date,
                "end_date": end_date,
                "fetch_time": datetime.now().isoformat(),
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching series {series_id}: {e}")
            return None

    def fetch_all_macro_series(self) -> Dict[str, Dict]:
        """Fetch all macro series for historical period"""
        all_data = {}
        for series_id, description in FRED_SERIES.items():
            print(f"Fetching {series_id} ({description})...")
            data = self.fetch_series(series_id)
            if data:
                all_data[series_id] = data
                print(f"  Retrieved {data['count']} observations")
            else:
                print(f"  Failed to fetch data")
        return all_data

    def fetch_all_credit_series(self) -> Dict[str, Dict]:
        """Fetch all credit market series for historical period"""
        all_data = {}
        for series_id, description in FRED_CREDIT_SERIES.items():
            print(f"Fetching {series_id} ({description})...")
            data = self.fetch_series(series_id)
            if data:
                all_data[series_id] = data
                print(f"  Retrieved {data['count']} observations")
            else:
                print(f"  No data available for this period")
        return all_data

    def get_yearly_averages(self, all_data: Dict) -> Dict[str, Dict]:
        """Calculate yearly averages for each series"""
        yearly = {}
        for series_id, data in all_data.items():
            yearly[series_id] = {"description": data.get("description"), "years": {}}
            for obs in data.get("observations", []):
                year = obs["date"][:4]
                if year not in yearly[series_id]["years"]:
                    yearly[series_id]["years"][year] = {"values": [], "count": 0}
                yearly[series_id]["years"][year]["values"].append(obs["value"])
                yearly[series_id]["years"][year]["count"] += 1

            # Calculate averages
            for year, info in yearly[series_id]["years"].items():
                values = info["values"]
                info["average"] = round(sum(values) / len(values), 4)
                info["min"] = round(min(values), 4)
                info["max"] = round(max(values), 4)
                del info["values"]  # Remove raw values to save space

        return yearly

    def save_data(self, data: Dict, filename: str, directory: Path = None):
        """Save data to JSON file"""
        if directory is None:
            directory = RAW_DATA_DIR
        output_path = directory / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {output_path}")


def main():
    """Fetch and save historical FRED data"""
    print("=" * 60)
    print("FRED Historical Data Fetcher (1995-2003)")
    print("=" * 60)

    try:
        fetcher = FREDHistoryFetcher()
    except ValueError as e:
        print(f"Error: {e}")
        return None

    # Fetch macro series
    print("\nFetching macroeconomic data (1995-2003)...")
    macro_data = fetcher.fetch_all_macro_series()
    fetcher.save_data(macro_data, "fred_macro_history.json")

    # Fetch credit market series
    print("\nFetching credit market data (1995-2003)...")
    credit_data = fetcher.fetch_all_credit_series()
    fetcher.save_data(credit_data, "fred_credit_history.json", MARKET_DATA_DIR)

    # Calculate yearly averages
    all_data = {**macro_data, **credit_data}
    yearly = fetcher.get_yearly_averages(all_data)
    fetcher.save_data(yearly, "fred_yearly_averages.json")

    print(f"\nFetch complete! Series retrieved: {len(all_data)}")
    return all_data


if __name__ == "__main__":
    main()
