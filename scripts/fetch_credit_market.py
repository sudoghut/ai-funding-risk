"""
Credit Market Data Fetcher
Fetches daily/weekly credit market indicators from FRED
For AI Funding Risk Early Warning System
"""
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    FRED_API_KEY, FRED_CREDIT_SERIES, FRED_SUPPLY_SERIES,
    RAW_DATA_DIR, MARKET_DATA_DIR
)


class CreditMarketFetcher:
    """Fetches credit market and capital supply indicators from FRED"""

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: str = None):
        self.api_key = (api_key or FRED_API_KEY).strip()
        if not self.api_key:
            raise ValueError(
                "FRED API key required. Set FRED_API_KEY environment variable. "
                "Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html"
            )

    def fetch_series(
        self,
        series_id: str,
        description: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> Optional[Dict]:
        """
        Fetch a single FRED series with daily data where available

        Args:
            series_id: FRED series identifier
            description: Human-readable description
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary with series data or None if error
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

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

            # Parse and clean the data
            cleaned_data = []
            for obs in observations:
                value = obs.get("value", ".")
                if value != ".":
                    try:
                        cleaned_data.append({
                            "date": obs.get("date"),
                            "value": float(value),
                        })
                    except ValueError:
                        continue

            if not cleaned_data:
                return None

            # Calculate statistics
            values = [d["value"] for d in cleaned_data]
            recent_values = values[-30:] if len(values) >= 30 else values

            return {
                "series_id": series_id,
                "description": description or series_id,
                "observations": cleaned_data,
                "count": len(cleaned_data),
                "latest": {
                    "date": cleaned_data[-1]["date"],
                    "value": cleaned_data[-1]["value"],
                },
                "statistics": {
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "recent_mean": sum(recent_values) / len(recent_values),
                    "current_vs_mean": (cleaned_data[-1]["value"] - sum(values) / len(values)),
                },
                "changes": self._calculate_changes(cleaned_data),
                "start_date": start_date,
                "end_date": end_date,
                "fetch_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            print(f"Error fetching series {series_id}: {e}")
            return None

    def _calculate_changes(self, data: List[Dict]) -> Dict:
        """Calculate period-over-period changes"""
        if len(data) < 2:
            return {}

        current = data[-1]["value"]
        changes = {}

        # 1-day change (if daily data)
        if len(data) >= 2:
            changes["1d_change"] = current - data[-2]["value"]
            changes["1d_change_pct"] = (current / data[-2]["value"] - 1) * 100 if data[-2]["value"] != 0 else 0

        # 1-week change (5 trading days)
        if len(data) >= 5:
            changes["1w_change"] = current - data[-5]["value"]
            changes["1w_change_pct"] = (current / data[-5]["value"] - 1) * 100 if data[-5]["value"] != 0 else 0

        # 1-month change (~22 trading days)
        if len(data) >= 22:
            changes["1m_change"] = current - data[-22]["value"]
            changes["1m_change_pct"] = (current / data[-22]["value"] - 1) * 100 if data[-22]["value"] != 0 else 0

        # 3-month change (~66 trading days)
        if len(data) >= 66:
            changes["3m_change"] = current - data[-66]["value"]
            changes["3m_change_pct"] = (current / data[-66]["value"] - 1) * 100 if data[-66]["value"] != 0 else 0

        return changes

    def fetch_credit_market_data(self) -> Dict[str, Dict]:
        """
        Fetch all credit market indicators

        Returns:
            Dictionary mapping series IDs to their data
        """
        print("Fetching credit market indicators...")
        all_data = {}

        for series_id, description in FRED_CREDIT_SERIES.items():
            print(f"  Fetching {series_id} ({description})...")
            data = self.fetch_series(series_id, description)
            if data:
                all_data[series_id] = data
                print(f"    Latest: {data['latest']['value']:.3f} ({data['latest']['date']})")
            else:
                print(f"    Failed to fetch data")

        return all_data

    def fetch_supply_indicators(self) -> Dict[str, Dict]:
        """
        Fetch capital supply indicators (institutional assets, etc.)

        Returns:
            Dictionary mapping series IDs to their data
        """
        print("Fetching capital supply indicators...")
        all_data = {}

        # These are typically quarterly, so fetch more history
        start_date = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")

        for series_id, description in FRED_SUPPLY_SERIES.items():
            print(f"  Fetching {series_id} ({description})...")
            data = self.fetch_series(series_id, description, start_date=start_date)
            if data:
                all_data[series_id] = data
                latest_val = data['latest']['value']
                # Format large numbers
                if latest_val > 1e6:
                    print(f"    Latest: {latest_val/1e6:.2f}T ({data['latest']['date']})")
                else:
                    print(f"    Latest: {latest_val:.2f} ({data['latest']['date']})")
            else:
                print(f"    Failed to fetch data")

        return all_data

    def calculate_credit_health_score(self, credit_data: Dict) -> Dict:
        """
        Calculate credit market health score based on indicators

        Args:
            credit_data: Credit market data dictionary

        Returns:
            Dictionary with health score and component analysis
        """
        scores = {}
        details = {}

        # High Yield Spread (lower is better)
        hy_data = credit_data.get("BAMLH0A0HYM2", {})
        if hy_data and hy_data.get("latest"):
            hy_spread = hy_data["latest"]["value"]
            # Score: 100 at 2%, 50 at 5%, 0 at 8%
            hy_score = max(0, min(100, 100 - (hy_spread - 2) * (100 / 6)))
            scores["high_yield_spread"] = hy_score
            details["high_yield_spread"] = {
                "value": hy_spread,
                "score": hy_score,
                "interpretation": "healthy" if hy_spread < 4 else ("caution" if hy_spread < 6 else "stressed"),
            }

        # Investment Grade Spread
        ig_data = credit_data.get("BAMLC0A0CM", {})
        if ig_data and ig_data.get("latest"):
            ig_spread = ig_data["latest"]["value"]
            ig_score = max(0, min(100, 100 - (ig_spread - 1) * (100 / 3)))
            scores["ig_spread"] = ig_score
            details["ig_spread"] = {
                "value": ig_spread,
                "score": ig_score,
                "interpretation": "healthy" if ig_spread < 1.5 else ("caution" if ig_spread < 2.5 else "stressed"),
            }

        # TED Spread (interbank lending risk)
        ted_data = credit_data.get("TEDRATE", {})
        if ted_data and ted_data.get("latest"):
            ted_spread = ted_data["latest"]["value"]
            ted_score = max(0, min(100, 100 - ted_spread * (100 / 1)))
            scores["ted_spread"] = ted_score
            details["ted_spread"] = {
                "value": ted_spread,
                "score": ted_score,
                "interpretation": "healthy" if ted_spread < 0.35 else ("caution" if ted_spread < 0.5 else "stressed"),
            }

        # Yield Curve (10Y-2Y) - positive is better
        yc_data = credit_data.get("T10Y2Y", {})
        if yc_data and yc_data.get("latest"):
            yc_spread = yc_data["latest"]["value"]
            # Score: 100 at +1%, 50 at 0%, 0 at -1%
            yc_score = max(0, min(100, 50 + yc_spread * 50))
            scores["yield_curve"] = yc_score
            details["yield_curve"] = {
                "value": yc_spread,
                "score": yc_score,
                "interpretation": "normal" if yc_spread > 0 else ("flat" if yc_spread > -0.2 else "inverted"),
            }

        # Federal Funds Rate (context-dependent, lower generally better for borrowing)
        ff_data = credit_data.get("DFF", {})
        if ff_data and ff_data.get("latest"):
            ff_rate = ff_data["latest"]["value"]
            ff_score = max(0, min(100, 100 - (ff_rate - 2) * (100 / 6)))
            scores["fed_funds"] = ff_score
            details["fed_funds"] = {
                "value": ff_rate,
                "score": ff_score,
                "interpretation": "accommodative" if ff_rate < 3 else ("neutral" if ff_rate < 5 else "restrictive"),
            }

        # Calculate composite score
        if scores:
            weights = {
                "high_yield_spread": 0.30,
                "ig_spread": 0.20,
                "ted_spread": 0.15,
                "yield_curve": 0.20,
                "fed_funds": 0.15,
            }

            composite = sum(scores.get(k, 50) * weights.get(k, 0) for k in weights)
            composite /= sum(weights.get(k, 0) for k in weights if k in scores)
        else:
            composite = 50

        return {
            "composite_score": round(composite, 1),
            "health_status": "healthy" if composite >= 70 else ("caution" if composite >= 50 else "stressed"),
            "component_scores": scores,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

    def fetch_all_data(self) -> Dict:
        """
        Fetch all credit market and supply data

        Returns:
            Complete credit market data dictionary
        """
        print("=" * 60)
        print("Credit Market Data Fetcher")
        print("=" * 60)

        credit_data = self.fetch_credit_market_data()
        supply_data = self.fetch_supply_indicators()
        health_score = self.calculate_credit_health_score(credit_data)

        return {
            "credit_market": credit_data,
            "capital_supply": supply_data,
            "health_assessment": health_score,
            "fetch_time": datetime.now().isoformat(),
        }

    def save_data(self, data: Dict, filename: str, directory: Path = None):
        """Save data to JSON file"""
        if directory is None:
            directory = MARKET_DATA_DIR

        output_path = directory / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Data saved to {output_path}")
        return output_path


def main():
    """Main function to fetch and save credit market data"""
    try:
        fetcher = CreditMarketFetcher()
    except ValueError as e:
        print(f"\nError: {e}")
        return None

    # Fetch all data
    all_data = fetcher.fetch_all_data()

    # Save to file
    fetcher.save_data(all_data, "credit_market_data.json")

    # Print summary
    print("\n" + "=" * 60)
    print("Credit Market Summary")
    print("=" * 60)

    health = all_data.get("health_assessment", {})
    print(f"\nComposite Health Score: {health.get('composite_score', 'N/A')}/100")
    print(f"Status: {health.get('health_status', 'N/A').upper()}")

    print("\nComponent Scores:")
    for component, score in health.get("component_scores", {}).items():
        detail = health.get("details", {}).get(component, {})
        value = detail.get("value", "N/A")
        interp = detail.get("interpretation", "N/A")
        print(f"  {component}: {score:.0f}/100 (value: {value:.3f}, {interp})")

    return all_data


if __name__ == "__main__":
    main()
