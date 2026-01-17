"""
Yahoo Finance Data Fetcher
Fetches real-time market data and financials from Yahoo Finance
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import YAHOO_TICKERS, RAW_DATA_DIR

try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed. Run: pip install yfinance")
    sys.exit(1)


class YahooFetcher:
    """Fetches financial data from Yahoo Finance"""

    def __init__(self, tickers: List[str] = None):
        self.tickers = tickers or YAHOO_TICKERS

    def fetch_company_info(self, ticker: str) -> Optional[Dict]:
        """
        Fetch company information and key metrics

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with company info or None if error
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract key financial metrics
            return {
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "total_debt": info.get("totalDebt"),
                "total_cash": info.get("totalCash"),
                "free_cashflow": info.get("freeCashflow"),
                "operating_cashflow": info.get("operatingCashflow"),
                "revenue": info.get("totalRevenue"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_margins": info.get("profitMargins"),
                "current_price": info.get("currentPrice"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "beta": info.get("beta"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "enterprise_value": info.get("enterpriseValue"),
                "fetch_time": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching info for {ticker}: {e}")
            return None

    def fetch_cashflow(self, ticker: str, quarterly: bool = True) -> Optional[Dict]:
        """
        Fetch cash flow statement data

        Args:
            ticker: Stock ticker symbol
            quarterly: If True, fetch quarterly data; otherwise annual

        Returns:
            Dictionary with cash flow data
        """
        try:
            stock = yf.Ticker(ticker)

            if quarterly:
                cf = stock.quarterly_cashflow
            else:
                cf = stock.cashflow

            if cf.empty:
                return None

            # Convert to dictionary format
            cf_dict = {}
            for col in cf.columns:
                col_str = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)
                cf_dict[col_str] = {}
                for idx in cf.index:
                    value = cf.loc[idx, col]
                    if value is not None and str(value) != 'nan':
                        cf_dict[col_str][idx] = float(value)

            return {
                "ticker": ticker,
                "period_type": "quarterly" if quarterly else "annual",
                "data": cf_dict,
                "periods": list(cf_dict.keys()),
                "fetch_time": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching cashflow for {ticker}: {e}")
            return None

    def fetch_balance_sheet(self, ticker: str, quarterly: bool = True) -> Optional[Dict]:
        """
        Fetch balance sheet data

        Args:
            ticker: Stock ticker symbol
            quarterly: If True, fetch quarterly data; otherwise annual

        Returns:
            Dictionary with balance sheet data
        """
        try:
            stock = yf.Ticker(ticker)

            if quarterly:
                bs = stock.quarterly_balance_sheet
            else:
                bs = stock.balance_sheet

            if bs.empty:
                return None

            # Convert to dictionary format
            bs_dict = {}
            for col in bs.columns:
                col_str = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)
                bs_dict[col_str] = {}
                for idx in bs.index:
                    value = bs.loc[idx, col]
                    if value is not None and str(value) != 'nan':
                        bs_dict[col_str][idx] = float(value)

            return {
                "ticker": ticker,
                "period_type": "quarterly" if quarterly else "annual",
                "data": bs_dict,
                "periods": list(bs_dict.keys()),
                "fetch_time": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching balance sheet for {ticker}: {e}")
            return None

    def fetch_financials(self, ticker: str, quarterly: bool = True) -> Optional[Dict]:
        """
        Fetch income statement data

        Args:
            ticker: Stock ticker symbol
            quarterly: If True, fetch quarterly data; otherwise annual

        Returns:
            Dictionary with income statement data
        """
        try:
            stock = yf.Ticker(ticker)

            if quarterly:
                fin = stock.quarterly_financials
            else:
                fin = stock.financials

            if fin.empty:
                return None

            # Convert to dictionary format
            fin_dict = {}
            for col in fin.columns:
                col_str = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)
                fin_dict[col_str] = {}
                for idx in fin.index:
                    value = fin.loc[idx, col]
                    if value is not None and str(value) != 'nan':
                        fin_dict[col_str][idx] = float(value)

            return {
                "ticker": ticker,
                "period_type": "quarterly" if quarterly else "annual",
                "data": fin_dict,
                "periods": list(fin_dict.keys()),
                "fetch_time": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}")
            return None

    def fetch_all_companies(self) -> Dict[str, Dict]:
        """
        Fetch comprehensive data for all target companies

        Returns:
            Dictionary mapping tickers to their financial data
        """
        all_data = {}

        for ticker in self.tickers:
            print(f"Fetching data for {ticker}...")

            company_data = {
                "ticker": ticker,
                "info": self.fetch_company_info(ticker),
                "quarterly_cashflow": self.fetch_cashflow(ticker, quarterly=True),
                "annual_cashflow": self.fetch_cashflow(ticker, quarterly=False),
                "quarterly_balance_sheet": self.fetch_balance_sheet(ticker, quarterly=True),
                "quarterly_financials": self.fetch_financials(ticker, quarterly=True),
                "fetch_time": datetime.now().isoformat(),
            }

            all_data[ticker] = company_data

            # Print summary
            info = company_data.get("info", {})
            if info:
                market_cap = info.get("market_cap")
                if market_cap:
                    print(f"  Market Cap: ${market_cap / 1e9:.1f}B")

        return all_data

    def get_key_metrics_summary(self, all_data: Dict) -> Dict[str, Dict]:
        """
        Extract key metrics summary for quick analysis

        Args:
            all_data: Full company data dictionary

        Returns:
            Dictionary with key metrics per company
        """
        summary = {}

        for ticker, data in all_data.items():
            info = data.get("info", {})
            if info:
                summary[ticker] = {
                    "name": info.get("name"),
                    "market_cap_billions": (
                        info.get("market_cap", 0) / 1e9
                        if info.get("market_cap")
                        else None
                    ),
                    "total_debt_billions": (
                        info.get("total_debt", 0) / 1e9
                        if info.get("total_debt")
                        else None
                    ),
                    "free_cashflow_billions": (
                        info.get("free_cashflow", 0) / 1e9
                        if info.get("free_cashflow")
                        else None
                    ),
                    "operating_cashflow_billions": (
                        info.get("operating_cashflow", 0) / 1e9
                        if info.get("operating_cashflow")
                        else None
                    ),
                    "revenue_billions": (
                        info.get("revenue", 0) / 1e9
                        if info.get("revenue")
                        else None
                    ),
                    "revenue_growth_pct": (
                        info.get("revenue_growth", 0) * 100
                        if info.get("revenue_growth")
                        else None
                    ),
                    "profit_margin_pct": (
                        info.get("profit_margins", 0) * 100
                        if info.get("profit_margins")
                        else None
                    ),
                    "pe_ratio": info.get("pe_ratio"),
                    "beta": info.get("beta"),
                }

        return summary

    def save_data(self, data: Dict, filename: str):
        """Save data to JSON file"""
        output_path = RAW_DATA_DIR / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        print(f"Data saved to {output_path}")


def main():
    """Main function to fetch and save Yahoo Finance data"""
    print("=" * 60)
    print("Yahoo Finance Data Fetcher")
    print("=" * 60)

    fetcher = YahooFetcher()

    # Fetch all company data
    print("\nFetching company financial data...")
    all_data = fetcher.fetch_all_companies()

    # Save full data
    fetcher.save_data(all_data, "yahoo_company_data.json")

    # Extract and save key metrics summary
    summary = fetcher.get_key_metrics_summary(all_data)
    fetcher.save_data(summary, "yahoo_summary.json")

    print("\nFetch complete!")
    print(f"Companies processed: {len(all_data)}")

    # Print summary table
    print("\n" + "=" * 60)
    print("Key Metrics Summary")
    print("=" * 60)
    print(f"{'Ticker':<8} {'Market Cap':>12} {'Revenue':>12} {'FCF':>12} {'Debt':>12}")
    print("-" * 60)
    for ticker, metrics in summary.items():
        mc = f"${metrics['market_cap_billions']:.0f}B" if metrics.get('market_cap_billions') else "N/A"
        rev = f"${metrics['revenue_billions']:.0f}B" if metrics.get('revenue_billions') else "N/A"
        fcf = f"${metrics['free_cashflow_billions']:.0f}B" if metrics.get('free_cashflow_billions') else "N/A"
        debt = f"${metrics['total_debt_billions']:.0f}B" if metrics.get('total_debt_billions') else "N/A"
        print(f"{ticker:<8} {mc:>12} {rev:>12} {fcf:>12} {debt:>12}")

    return all_data


if __name__ == "__main__":
    main()
