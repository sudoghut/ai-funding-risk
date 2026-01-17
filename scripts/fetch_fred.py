"""
FRED API Data Fetcher
Fetches macroeconomic data from Federal Reserve Economic Data (FRED)
"""
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import FRED_API_KEY, FRED_SERIES, RAW_DATA_DIR


class FREDFetcher:
    """Fetches macroeconomic data from FRED API"""

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: str = None):
        self.api_key = (api_key or FRED_API_KEY).strip()
        if not self.api_key:
            raise ValueError(
                "FRED API key required. Set FRED_API_KEY environment variable "
                "or pass api_key parameter. Get a free key at: "
                "https://fred.stlouisfed.org/docs/api/api_key.html"
            )

    def fetch_series(
        self,
        series_id: str,
        start_date: str = None,
        end_date: str = None,
        frequency: str = None,
    ) -> Optional[Dict]:
        """
        Fetch a single FRED series

        Args:
            series_id: FRED series identifier
            start_date: Start date (YYYY-MM-DD), defaults to 5 years ago
            end_date: End date (YYYY-MM-DD), defaults to today
            frequency: Data frequency (d, w, m, q, a), optional

        Returns:
            Dictionary with series data or None if error
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date,
        }

        if frequency:
            params["frequency"] = frequency

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            observations = data.get("observations", [])

            # Parse and clean the data
            cleaned_data = []
            for obs in observations:
                value = obs.get("value", ".")
                if value != ".":  # FRED uses "." for missing values
                    try:
                        cleaned_data.append({
                            "date": obs.get("date"),
                            "value": float(value),
                        })
                    except ValueError:
                        continue

            return {
                "series_id": series_id,
                "description": FRED_SERIES.get(series_id, "Unknown"),
                "observations": cleaned_data,
                "count": len(cleaned_data),
                "start_date": start_date,
                "end_date": end_date,
                "fetch_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            print(f"Error fetching series {series_id}: {e}")
            return None

    def fetch_all_series(self, start_date: str = None) -> Dict[str, Dict]:
        """
        Fetch all configured FRED series

        Args:
            start_date: Start date for all series

        Returns:
            Dictionary mapping series IDs to their data
        """
        all_data = {}

        for series_id, description in FRED_SERIES.items():
            print(f"Fetching {series_id} ({description})...")

            data = self.fetch_series(series_id, start_date=start_date)
            if data:
                all_data[series_id] = data
                print(f"  Retrieved {data['count']} observations")
            else:
                print(f"  Failed to fetch data")

        return all_data

    def get_latest_values(self, all_data: Dict) -> Dict[str, Dict]:
        """
        Extract the most recent value for each series

        Args:
            all_data: Full series data dictionary

        Returns:
            Dictionary with latest values and metadata
        """
        latest = {}

        for series_id, data in all_data.items():
            observations = data.get("observations", [])
            if observations:
                # Get the most recent observation
                most_recent = observations[-1]
                latest[series_id] = {
                    "description": data.get("description"),
                    "latest_date": most_recent.get("date"),
                    "latest_value": most_recent.get("value"),
                    "observation_count": len(observations),
                }

        return latest

    def calculate_trends(self, all_data: Dict, periods: int = 4) -> Dict[str, Dict]:
        """
        Calculate trends for each series

        Args:
            all_data: Full series data dictionary
            periods: Number of recent periods to analyze

        Returns:
            Dictionary with trend analysis
        """
        trends = {}

        for series_id, data in all_data.items():
            observations = data.get("observations", [])
            if len(observations) >= periods:
                recent = observations[-periods:]
                values = [obs["value"] for obs in recent]

                first_value = values[0]
                last_value = values[-1]

                if first_value != 0:
                    change_pct = ((last_value - first_value) / abs(first_value)) * 100
                else:
                    change_pct = 0

                trends[series_id] = {
                    "description": data.get("description"),
                    "current_value": last_value,
                    "previous_value": first_value,
                    "change_pct": round(change_pct, 2),
                    "trend": "up" if change_pct > 0 else ("down" if change_pct < 0 else "flat"),
                    "periods_analyzed": periods,
                }

        return trends

    def save_data(self, data: Dict, filename: str):
        """Save data to JSON file"""
        output_path = RAW_DATA_DIR / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Data saved to {output_path}")


def main():
    """Main function to fetch and save FRED data"""
    print("=" * 60)
    print("FRED API Data Fetcher")
    print("=" * 60)

    try:
        fetcher = FREDFetcher()
    except ValueError as e:
        print(f"\nError: {e}")
        print("\nTo set your API key, run:")
        print('  set FRED_API_KEY=your_api_key_here  (Windows)')
        print('  export FRED_API_KEY=your_api_key_here  (Linux/Mac)')
        return None

    # Fetch all series data
    print("\nFetching macroeconomic data...")
    all_data = fetcher.fetch_all_series()

    # Save full historical data
    fetcher.save_data(all_data, "fred_series_data.json")

    # Extract and save latest values
    latest_data = fetcher.get_latest_values(all_data)
    fetcher.save_data(latest_data, "fred_latest_values.json")

    # Calculate and save trends
    trends = fetcher.calculate_trends(all_data)
    fetcher.save_data(trends, "fred_trends.json")

    print("\nFetch complete!")
    print(f"Series processed: {len(all_data)}")

    return all_data


if __name__ == "__main__":
    main()
