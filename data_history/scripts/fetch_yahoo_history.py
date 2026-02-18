"""
Yahoo Finance Historical Data Fetcher (1995-2003)
Fetches historical stock prices and market data for 90s IT bubble analysis
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    YAHOO_TICKERS_HISTORY, MARKET_TICKERS, SEMICONDUCTOR_TICKERS_90S,
    RAW_DATA_DIR, MARKET_DATA_DIR,
    HISTORY_START_DATE, HISTORY_END_DATE,
)

try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed. Run: pip install yfinance")
    sys.exit(1)


class YahooHistoryFetcher:
    """Fetches historical stock and market data from Yahoo Finance"""

    def __init__(self):
        self.start_date = HISTORY_START_DATE
        self.end_date = HISTORY_END_DATE

    def fetch_stock_history(self, ticker: str) -> Optional[Dict]:
        """Fetch historical stock price data for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=self.start_date, end=self.end_date, auto_adjust=True)

            if hist.empty:
                return None

            # Convert to list of records
            records = []
            for date, row in hist.iterrows():
                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(float(row.get("Open", 0)), 4),
                    "high": round(float(row.get("High", 0)), 4),
                    "low": round(float(row.get("Low", 0)), 4),
                    "close": round(float(row.get("Close", 0)), 4),
                    "volume": int(row.get("Volume", 0)),
                })

            # Calculate key metrics
            if len(records) > 0:
                prices = [r["close"] for r in records if r["close"] > 0]
                peak_price = max(prices) if prices else 0
                peak_date = records[prices.index(peak_price)]["date"] if prices else None
                trough_price = min(prices[prices.index(peak_price):]) if prices and prices.index(peak_price) < len(prices) - 1 else peak_price
                drawdown = ((trough_price - peak_price) / peak_price * 100) if peak_price > 0 else 0

                # Monthly closing prices for charting
                monthly = {}
                for r in records:
                    month_key = r["date"][:7]  # YYYY-MM
                    monthly[month_key] = r["close"]

                return {
                    "ticker": ticker,
                    "period": f"{self.start_date} to {self.end_date}",
                    "total_trading_days": len(records),
                    "peak_price": round(peak_price, 4),
                    "peak_date": peak_date,
                    "trough_price_after_peak": round(trough_price, 4),
                    "peak_to_trough_drawdown_pct": round(drawdown, 2),
                    "first_price": records[0]["close"],
                    "last_price": records[-1]["close"],
                    "total_return_pct": round(
                        (records[-1]["close"] - records[0]["close"]) / records[0]["close"] * 100, 2
                    ),
                    "monthly_closes": monthly,
                    "fetch_time": datetime.now().isoformat(),
                }
            return None
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def fetch_all_company_stocks(self) -> Dict[str, Dict]:
        """Fetch historical stock data for all target companies"""
        all_data = {}
        for company, ticker in YAHOO_TICKERS_HISTORY.items():
            print(f"Fetching {company} ({ticker})...")
            data = self.fetch_stock_history(ticker)
            if data:
                all_data[company] = data
                print(f"  Peak: ${data['peak_price']:.2f} on {data['peak_date']}")
                print(f"  Drawdown: {data['peak_to_trough_drawdown_pct']:.1f}%")
            else:
                print(f"  No data available")
        return all_data

    def fetch_market_indices(self) -> Dict[str, Dict]:
        """Fetch historical market index data"""
        all_data = {}
        for ticker, description in MARKET_TICKERS.items():
            print(f"Fetching {ticker} ({description})...")
            data = self.fetch_stock_history(ticker)
            if data:
                all_data[ticker] = data
                data["description"] = description
                print(f"  Trading days: {data['total_trading_days']}")
            else:
                print(f"  No data available")
        return all_data

    def fetch_semiconductor_stocks(self) -> Dict[str, Dict]:
        """Fetch semiconductor stock data"""
        all_data = {}
        for ticker in SEMICONDUCTOR_TICKERS_90S:
            print(f"Fetching {ticker}...")
            data = self.fetch_stock_history(ticker)
            if data:
                all_data[ticker] = data
                print(f"  Drawdown: {data['peak_to_trough_drawdown_pct']:.1f}%")
            else:
                print(f"  No data available")
        return all_data

    def save_data(self, data: Dict, filename: str, directory: Path = None):
        """Save data to JSON file"""
        if directory is None:
            directory = RAW_DATA_DIR
        output_path = directory / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"Data saved to {output_path}")


def main():
    """Fetch and save historical Yahoo Finance data"""
    print("=" * 60)
    print("Yahoo Finance Historical Data Fetcher (1995-2003)")
    print("=" * 60)

    fetcher = YahooHistoryFetcher()

    # Fetch company stock data
    print("\nFetching company stock histories...")
    company_data = fetcher.fetch_all_company_stocks()
    fetcher.save_data(company_data, "yahoo_stock_history.json")

    # Fetch market indices
    print("\nFetching market indices...")
    market_data = fetcher.fetch_market_indices()
    fetcher.save_data(market_data, "market_indices_history.json", MARKET_DATA_DIR)

    # Fetch semiconductor stocks
    print("\nFetching semiconductor stocks...")
    semi_data = fetcher.fetch_semiconductor_stocks()
    fetcher.save_data(semi_data, "semiconductor_history.json", MARKET_DATA_DIR)

    print(f"\nFetch complete!")
    print(f"  Companies: {len(company_data)}")
    print(f"  Market indices: {len(market_data)}")
    print(f"  Semiconductors: {len(semi_data)}")

    return {"companies": company_data, "market": market_data, "semiconductors": semi_data}


if __name__ == "__main__":
    main()
