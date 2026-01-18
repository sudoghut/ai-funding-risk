"""
Market Data Fetcher
Fetches ETF, VIX, and market sentiment data from Yahoo Finance
For AI Funding Risk Early Warning System
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    MARKET_ETFS, SEMICONDUCTOR_TICKERS, YAHOO_TICKERS,
    RAW_DATA_DIR, MARKET_DATA_DIR
)

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("Required packages not installed. Run: pip install yfinance pandas")
    sys.exit(1)


class MarketDataFetcher:
    """Fetches market indicators for funding environment assessment"""

    def __init__(self):
        self.etf_tickers = MARKET_ETFS
        self.semiconductor_tickers = SEMICONDUCTOR_TICKERS
        self.ai_company_tickers = YAHOO_TICKERS

    def fetch_price_history(
        self,
        ticker: str,
        period: str = "3mo",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical price data for a ticker

        Args:
            ticker: Stock/ETF ticker symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)
            if hist.empty:
                return None
            return hist
        except Exception as e:
            print(f"Error fetching history for {ticker}: {e}")
            return None

    def fetch_current_quote(self, ticker: str) -> Optional[Dict]:
        """
        Fetch current quote and key statistics

        Args:
            ticker: Stock/ETF ticker symbol

        Returns:
            Dictionary with current quote data
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                "ticker": ticker,
                "name": info.get("longName") or info.get("shortName", ticker),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "avg_volume": info.get("averageVolume"),
                "avg_volume_10d": info.get("averageVolume10days"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "50_day_avg": info.get("fiftyDayAverage"),
                "200_day_avg": info.get("twoHundredDayAverage"),
                "market_cap": info.get("marketCap"),
                "total_assets": info.get("totalAssets"),  # For ETFs
                "ytd_return": info.get("ytdReturn"),
                "beta": info.get("beta") or info.get("beta3Year"),
                "fetch_time": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching quote for {ticker}: {e}")
            return None

    def fetch_vix_data(self) -> Dict:
        """
        Fetch VIX (Volatility Index) data

        Returns:
            Dictionary with VIX current and historical data
        """
        print("Fetching VIX data...")

        result = {
            "current": self.fetch_current_quote("^VIX"),
            "history": None,
            "statistics": {},
        }

        # Get historical data for trend analysis
        hist = self.fetch_price_history("^VIX", period="6mo", interval="1d")
        if hist is not None and not hist.empty:
            # Convert to serializable format
            history_data = []
            for date, row in hist.iterrows():
                history_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
                    "high": float(row["High"]) if pd.notna(row["High"]) else None,
                    "low": float(row["Low"]) if pd.notna(row["Low"]) else None,
                })
            result["history"] = history_data[-90:]  # Last 90 days

            # Calculate statistics
            closes = hist["Close"].dropna()
            if len(closes) > 0:
                result["statistics"] = {
                    "current": float(closes.iloc[-1]),
                    "avg_30d": float(closes.tail(30).mean()),
                    "avg_90d": float(closes.mean()),
                    "max_30d": float(closes.tail(30).max()),
                    "min_30d": float(closes.tail(30).min()),
                    "percentile_current": float((closes < closes.iloc[-1]).sum() / len(closes) * 100),
                    "week_change": float((closes.iloc[-1] / closes.iloc[-5] - 1) * 100) if len(closes) >= 5 else None,
                    "month_change": float((closes.iloc[-1] / closes.iloc[-22] - 1) * 100) if len(closes) >= 22 else None,
                }

        return result

    def fetch_etf_data(self) -> Dict[str, Dict]:
        """
        Fetch data for all configured ETFs

        Returns:
            Dictionary mapping ETF tickers to their data
        """
        print("Fetching ETF market data...")
        all_data = {}

        for ticker, description in self.etf_tickers.items():
            if ticker == "^VIX":
                continue  # VIX handled separately

            print(f"  Fetching {ticker} ({description})...")

            etf_data = {
                "ticker": ticker,
                "description": description,
                "quote": self.fetch_current_quote(ticker),
                "performance": {},
                "fund_flow_proxy": {},
            }

            # Get historical data for performance calculation
            hist = self.fetch_price_history(ticker, period="6mo", interval="1d")
            if hist is not None and not hist.empty:
                closes = hist["Close"].dropna()
                volumes = hist["Volume"].dropna()

                if len(closes) > 0:
                    current = closes.iloc[-1]

                    # Calculate returns over different periods
                    etf_data["performance"] = {
                        "1d_return": float((current / closes.iloc[-2] - 1) * 100) if len(closes) >= 2 else None,
                        "1w_return": float((current / closes.iloc[-5] - 1) * 100) if len(closes) >= 5 else None,
                        "1m_return": float((current / closes.iloc[-22] - 1) * 100) if len(closes) >= 22 else None,
                        "3m_return": float((current / closes.iloc[-66] - 1) * 100) if len(closes) >= 66 else None,
                        "ytd_return": etf_data["quote"].get("ytd_return") if etf_data["quote"] else None,
                    }

                    # Volume analysis as proxy for fund flows
                    if len(volumes) >= 22:
                        avg_volume_1m = volumes.tail(22).mean()
                        avg_volume_3m = volumes.mean()
                        recent_volume = volumes.tail(5).mean()

                        etf_data["fund_flow_proxy"] = {
                            "recent_vs_1m_avg": float((recent_volume / avg_volume_1m - 1) * 100),
                            "recent_vs_3m_avg": float((recent_volume / avg_volume_3m - 1) * 100),
                            "volume_trend": "increasing" if recent_volume > avg_volume_1m else "decreasing",
                        }

            all_data[ticker] = etf_data

        return all_data

    def fetch_ai_stocks_performance(self) -> Dict:
        """
        Fetch performance data for AI-related stocks

        Returns:
            Dictionary with AI stocks performance metrics
        """
        print("Fetching AI stocks performance...")

        stocks_data = {}

        # Core AI companies
        for ticker in self.ai_company_tickers:
            print(f"  Fetching {ticker}...")

            quote = self.fetch_current_quote(ticker)
            hist = self.fetch_price_history(ticker, period="3mo", interval="1d")

            stock_data = {
                "ticker": ticker,
                "quote": quote,
                "performance": {},
            }

            if hist is not None and not hist.empty:
                closes = hist["Close"].dropna()
                if len(closes) > 0:
                    current = closes.iloc[-1]
                    stock_data["performance"] = {
                        "1d_return": float((current / closes.iloc[-2] - 1) * 100) if len(closes) >= 2 else None,
                        "1w_return": float((current / closes.iloc[-5] - 1) * 100) if len(closes) >= 5 else None,
                        "1m_return": float((current / closes.iloc[-22] - 1) * 100) if len(closes) >= 22 else None,
                        "from_52w_high": float((current / quote.get("52_week_high", current) - 1) * 100) if quote else None,
                    }

            stocks_data[ticker] = stock_data

        # Calculate aggregate metrics
        performances = []
        for ticker, data in stocks_data.items():
            if data.get("performance", {}).get("1w_return") is not None:
                performances.append(data["performance"]["1w_return"])

        aggregate = {
            "avg_1w_return": sum(performances) / len(performances) if performances else None,
            "max_1w_return": max(performances) if performances else None,
            "min_1w_return": min(performances) if performances else None,
            "stocks_positive": sum(1 for p in performances if p > 0),
            "stocks_negative": sum(1 for p in performances if p < 0),
        }

        return {
            "stocks": stocks_data,
            "aggregate": aggregate,
            "fetch_time": datetime.now().isoformat(),
        }

    def fetch_semiconductor_demand(self) -> Dict:
        """
        Fetch semiconductor stocks data as AI infrastructure demand proxy

        Returns:
            Dictionary with semiconductor sector metrics
        """
        print("Fetching semiconductor demand indicators...")

        stocks_data = {}

        for ticker in self.semiconductor_tickers:
            print(f"  Fetching {ticker}...")

            quote = self.fetch_current_quote(ticker)
            hist = self.fetch_price_history(ticker, period="3mo", interval="1d")

            stock_data = {
                "ticker": ticker,
                "name": quote.get("name") if quote else ticker,
                "market_cap": quote.get("market_cap") if quote else None,
                "performance": {},
            }

            if hist is not None and not hist.empty:
                closes = hist["Close"].dropna()
                if len(closes) > 0:
                    current = closes.iloc[-1]
                    stock_data["performance"] = {
                        "1w_return": float((current / closes.iloc[-5] - 1) * 100) if len(closes) >= 5 else None,
                        "1m_return": float((current / closes.iloc[-22] - 1) * 100) if len(closes) >= 22 else None,
                        "3m_return": float((current / closes.iloc[0] - 1) * 100) if len(closes) >= 1 else None,
                    }

            stocks_data[ticker] = stock_data

        # Calculate sector aggregate
        performances_1w = [d["performance"].get("1w_return") for d in stocks_data.values()
                          if d.get("performance", {}).get("1w_return") is not None]
        performances_1m = [d["performance"].get("1m_return") for d in stocks_data.values()
                          if d.get("performance", {}).get("1m_return") is not None]

        return {
            "stocks": stocks_data,
            "sector_aggregate": {
                "avg_1w_return": sum(performances_1w) / len(performances_1w) if performances_1w else None,
                "avg_1m_return": sum(performances_1m) / len(performances_1m) if performances_1m else None,
                "total_market_cap_T": sum(d.get("market_cap", 0) or 0 for d in stocks_data.values()) / 1e12,
            },
            "fetch_time": datetime.now().isoformat(),
        }

    def calculate_relative_strength(self, etf_data: Dict) -> Dict:
        """
        Calculate relative strength of AI/Tech vs broader market

        Args:
            etf_data: ETF data dictionary

        Returns:
            Dictionary with relative strength metrics
        """
        spy_data = etf_data.get("SPY", {}).get("performance", {})

        comparisons = {}
        tech_etfs = ["QQQ", "XLK", "SMH", "ARKK", "BOTZ", "AIQ"]

        for etf in tech_etfs:
            if etf in etf_data:
                etf_perf = etf_data[etf].get("performance", {})

                comparisons[etf] = {
                    "name": etf_data[etf].get("description"),
                    "1w_return": etf_perf.get("1w_return"),
                    "1m_return": etf_perf.get("1m_return"),
                    "vs_spy_1w": (etf_perf.get("1w_return") or 0) - (spy_data.get("1w_return") or 0),
                    "vs_spy_1m": (etf_perf.get("1m_return") or 0) - (spy_data.get("1m_return") or 0),
                }

        # Determine overall tech sentiment
        outperforming = sum(1 for c in comparisons.values() if (c.get("vs_spy_1w") or 0) > 0)
        total = len(comparisons)

        return {
            "comparisons": comparisons,
            "tech_sentiment": {
                "etfs_outperforming_spy": outperforming,
                "etfs_total": total,
                "sentiment_score": outperforming / total * 100 if total > 0 else 50,
                "interpretation": "bullish" if outperforming > total / 2 else "bearish",
            },
        }

    def fetch_all_market_data(self) -> Dict:
        """
        Fetch all market data for comprehensive analysis

        Returns:
            Complete market data dictionary
        """
        print("=" * 60)
        print("Market Data Fetcher - Funding Environment Assessment")
        print("=" * 60)

        # Fetch all data components
        vix_data = self.fetch_vix_data()
        etf_data = self.fetch_etf_data()
        ai_stocks = self.fetch_ai_stocks_performance()
        semiconductor = self.fetch_semiconductor_demand()

        # Calculate relative strength
        relative_strength = self.calculate_relative_strength(etf_data)

        return {
            "vix": vix_data,
            "etfs": etf_data,
            "ai_stocks": ai_stocks,
            "semiconductor": semiconductor,
            "relative_strength": relative_strength,
            "fetch_time": datetime.now().isoformat(),
        }

    def save_data(self, data: Dict, filename: str, directory: Path = None):
        """Save data to JSON file"""
        if directory is None:
            directory = MARKET_DATA_DIR

        output_path = directory / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        print(f"Data saved to {output_path}")
        return output_path


def main():
    """Main function to fetch and save market data"""
    fetcher = MarketDataFetcher()

    # Fetch all market data
    market_data = fetcher.fetch_all_market_data()

    # Save to file
    fetcher.save_data(market_data, "market_indicators.json")

    # Print summary
    print("\n" + "=" * 60)
    print("Market Data Summary")
    print("=" * 60)

    # VIX Summary
    vix_stats = market_data.get("vix", {}).get("statistics", {})
    if vix_stats:
        print(f"\nVIX (Volatility Index):")
        print(f"  Current: {vix_stats.get('current', 'N/A'):.2f}")
        print(f"  30-Day Avg: {vix_stats.get('avg_30d', 'N/A'):.2f}")
        print(f"  Week Change: {vix_stats.get('week_change', 'N/A'):.1f}%")

    # Tech Sentiment
    tech_sent = market_data.get("relative_strength", {}).get("tech_sentiment", {})
    if tech_sent:
        print(f"\nTech Sentiment:")
        print(f"  ETFs Outperforming SPY: {tech_sent.get('etfs_outperforming_spy')}/{tech_sent.get('etfs_total')}")
        print(f"  Sentiment: {tech_sent.get('interpretation', 'N/A').upper()}")

    # AI Stocks
    ai_agg = market_data.get("ai_stocks", {}).get("aggregate", {})
    if ai_agg:
        print(f"\nAI Stocks (6 Major Companies):")
        print(f"  Avg 1-Week Return: {ai_agg.get('avg_1w_return', 0):.2f}%")
        print(f"  Positive/Negative: {ai_agg.get('stocks_positive')}/{ai_agg.get('stocks_negative')}")

    # Semiconductor
    semi_agg = market_data.get("semiconductor", {}).get("sector_aggregate", {})
    if semi_agg:
        print(f"\nSemiconductor Sector (AI Infrastructure):")
        print(f"  Avg 1-Week Return: {semi_agg.get('avg_1w_return', 0):.2f}%")
        print(f"  Total Market Cap: ${semi_agg.get('total_market_cap_T', 0):.2f}T")

    return market_data


if __name__ == "__main__":
    main()
