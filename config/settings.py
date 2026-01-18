"""
Configuration settings for AI Funding Risk Assessment Model
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Load .env file if exists
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MARKET_DATA_DIR = DATA_DIR / "market"

# API Configuration
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")  # Set via environment variable or .env file

# SEC EDGAR Configuration
SEC_USER_AGENT = "AI-Funding-Risk-Model research@example.com"  # Required by SEC
SEC_BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts"
SEC_RATE_LIMIT = 10  # requests per second

# Target Companies (CIK numbers)
TARGET_COMPANIES = {
    "Amazon": "0001018724",
    "Microsoft": "0000789019",
    "Alphabet": "0001652044",
    "Meta": "0001326801",
    "Oracle": "0001341439",
    "Nvidia": "0001045810",
}

# Yahoo Finance Tickers - Core AI Companies
YAHOO_TICKERS = ["AMZN", "MSFT", "GOOG", "META", "ORCL", "NVDA"]

# Yahoo Finance Tickers - Market Indicators (ETFs, Indices, Semiconductor)
MARKET_ETFS = {
    # Major Indices
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF",
    # Volatility
    "^VIX": "CBOE Volatility Index",
    # Technology/AI ETFs
    "XLK": "Technology Select Sector",
    "SMH": "VanEck Semiconductor ETF",
    "SOXX": "iShares Semiconductor ETF",
    "IGV": "iShares Software ETF",
    "ARKK": "ARK Innovation ETF",
    "BOTZ": "Global X Robotics & AI ETF",
    "AIQ": "Global X AI & Technology ETF",
    # IPO Market
    "IPO": "Renaissance IPO ETF",
    # Growth vs Value
    "VUG": "Vanguard Growth ETF",
    "VTV": "Vanguard Value ETF",
}

# Semiconductor/AI Infrastructure Companies (for demand signal)
SEMICONDUCTOR_TICKERS = ["NVDA", "AMD", "INTC", "ASML", "AMAT", "LRCX", "TSM"]

# FRED Series IDs - Original Macro Indicators
FRED_SERIES = {
    "FEDFUNDS": "Federal Funds Rate",
    "BAA10Y": "Baa Corporate Bond Spread",
    "BAMLH0A0HYM2": "High Yield Bond Spread",
    "GDP": "US GDP",
    "BOGZ1FL664090005Q": "Nonfinancial Corporate Debt",
    "SP500": "S&P 500 Index",
}

# FRED Series - Extended Credit Market Indicators (Daily/Weekly frequency)
FRED_CREDIT_SERIES = {
    # Daily Credit Spreads
    "BAMLC0A0CM": "Investment Grade Corporate Bond Spread",
    "BAMLC0A4CBBB": "BBB Corporate Bond Spread",
    "BAMLH0A0HYM2": "High Yield Bond Spread",
    "TEDRATE": "TED Spread (Interbank Lending Risk)",
    # Daily Interest Rates
    "DFF": "Federal Funds Effective Rate (Daily)",
    "DGS10": "10-Year Treasury Rate",
    "DGS2": "2-Year Treasury Rate",
    "T10Y2Y": "10Y-2Y Treasury Spread (Yield Curve)",
    "T10Y3M": "10Y-3M Treasury Spread",
    # Weekly Bank Lending
    "TOTCI": "Commercial and Industrial Loans",
    "BUSLOANS": "Commercial and Industrial Loans at All Commercial Banks",
}

# FRED Series - Institutional Capital Supply Indicators (Monthly/Quarterly)
FRED_SUPPLY_SERIES = {
    # Institutional Assets
    "BOGZ1FL594090005Q": "Pension Funds Total Financial Assets",
    "BOGZ1FL654090005Q": "Mutual Funds Total Financial Assets",
    "BOGZ1FL544090005Q": "Life Insurance Companies Total Financial Assets",
    # Corporate Cash
    "BOGZ1LM103020005Q": "Nonfinancial Corporate Liquid Assets",
    # Credit Market
    "CORGDPUSQ163S": "Corporate Debt to GDP Ratio",
    "NCBCMDPMVCE": "Nonfinancial Corporate Business Credit Market Instruments",
}

# SEC Financial Metrics to Extract
# Note: Different companies use different XBRL tags for Capex:
#   - PaymentsToAcquirePropertyPlantAndEquipment (most common)
#   - PaymentsToAcquireProductiveAssets (Nvidia uses this)
SEC_METRICS = [
    "PaymentsToAcquirePropertyPlantAndEquipment",  # Capital Expenditures (common)
    "PaymentsToAcquireProductiveAssets",  # Capital Expenditures (alternative - Nvidia)
    "NetCashProvidedByUsedInOperatingActivities",
    "LongTermDebt",
    "Revenues",
    "PropertyPlantAndEquipmentNet",
]

# Mapping of SEC XBRL tags to friendly names for output
SEC_METRIC_NAMES = {
    "PaymentsToAcquirePropertyPlantAndEquipment": "CapitalExpenditures",
    "PaymentsToAcquireProductiveAssets": "CapitalExpenditures_Alt",  # Alternative Capex tag
    "NetCashProvidedByUsedInOperatingActivities": "OperatingCashFlow",
    "LongTermDebt": "LongTermDebt",
    "Revenues": "Revenues",
    "PropertyPlantAndEquipmentNet": "PropertyPlantAndEquipmentNet",
}

# Risk Thresholds
RISK_THRESHOLDS = {
    "capex_to_cashflow": {
        "normal": 0.70,
        "warning": 0.90,
        "danger": float("inf"),
    },
    "debt_to_revenue_growth": {
        "normal": 1.0,
        "warning": 1.5,
        "danger": float("inf"),
    },
    "interest_rate": {
        "normal": 4.0,
        "warning": 6.0,
        "danger": float("inf"),
    },
    "credit_spread": {
        "normal": 2.0,
        "warning": 4.0,
        "danger": float("inf"),
    },
}

# Risk Level Definitions
RISK_LEVELS = {
    "LOW": {"label": "Low Risk", "color": "#28a745"},
    "MEDIUM": {"label": "Medium Risk", "color": "#ffc107"},
    "HIGH": {"label": "High Risk", "color": "#dc3545"},
}

# =============================================================================
# WARNING SYSTEM CONFIGURATION
# =============================================================================

# Warning Thresholds - Credit Market
WARNING_THRESHOLDS_CREDIT = {
    "high_yield_spread": {
        "yellow": 4.0,    # Concern level
        "orange": 5.5,    # Warning level
        "red": 7.0,       # Danger level
    },
    "investment_grade_spread": {
        "yellow": 1.5,
        "orange": 2.5,
        "red": 3.5,
    },
    "ted_spread": {
        "yellow": 0.35,
        "orange": 0.50,
        "red": 0.75,
    },
    "yield_curve_10y2y": {
        "yellow": -0.20,   # Slight inversion
        "orange": -0.50,   # Moderate inversion
        "red": -0.75,      # Deep inversion
    },
}

# Warning Thresholds - Equity Market
WARNING_THRESHOLDS_EQUITY = {
    "vix": {
        "yellow": 22,
        "orange": 28,
        "red": 35,
    },
    "ai_stocks_weekly_drawdown": {  # Percentage
        "yellow": -5,
        "orange": -10,
        "red": -20,
    },
    "tech_etf_weekly_drawdown": {
        "yellow": -4,
        "orange": -8,
        "red": -15,
    },
}

# Warning Thresholds - Company Level
WARNING_THRESHOLDS_COMPANY = {
    "capex_to_cashflow": {
        "yellow": 0.70,
        "orange": 0.85,
        "red": 0.95,
    },
    "debt_to_cash": {
        "yellow": 3.0,
        "orange": 5.0,
        "red": 7.0,
    },
    "debt_growth_vs_revenue_growth": {
        "yellow": 1.0,
        "orange": 1.3,
        "red": 1.5,
    },
}

# Composite Risk Weights
RISK_WEIGHTS = {
    "credit_market": 0.30,      # Credit conditions weight
    "equity_market": 0.25,      # Market sentiment weight
    "company_fundamentals": 0.30,  # Company health weight
    "supply_demand": 0.15,      # Supply-demand balance weight
}

# Alert Levels
ALERT_LEVELS = {
    "GREEN": {"label": "Normal", "description": "Funding environment healthy", "score_max": 40},
    "YELLOW": {"label": "Watch", "description": "Early warning signals present", "score_max": 55},
    "ORANGE": {"label": "Warning", "description": "Multiple risk indicators elevated", "score_max": 70},
    "RED": {"label": "Danger", "description": "High systemic risk detected", "score_max": 100},
}
