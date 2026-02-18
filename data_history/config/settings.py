"""
Configuration settings for 90s IT Bubble Historical Validation
Mirrors the main config/settings.py but adapted for 1995-2003 period
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
HISTORY_ROOT = Path(__file__).parent.parent

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
DATA_DIR = HISTORY_ROOT
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MARKET_DATA_DIR = DATA_DIR / "market"
COMPILED_DATA_DIR = DATA_DIR / "compiled"

# API Configuration
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
WRDS_API_TOKEN = os.environ.get("WRDS_API_TOKEN", "")

# =============================================================================
# HISTORICAL PERIOD CONFIGURATION
# =============================================================================

# Study period: IT/Telecom Bubble (1995-2003)
HISTORY_START_DATE = "1995-01-01"
HISTORY_END_DATE = "2003-12-31"
BUBBLE_PEAK_DATE = "2000-03-10"  # NASDAQ peak

# Phase definitions
PHASES = {
    "buildup": {"start": "1995-01-01", "end": "1999-12-31", "label": "Bubble Build-up"},
    "peak": {"start": "2000-01-01", "end": "2000-12-31", "label": "Peak & Initial Crash"},
    "crash": {"start": "2001-01-01", "end": "2002-12-31", "label": "Crash & Fallout"},
    "recovery": {"start": "2003-01-01", "end": "2003-12-31", "label": "Early Recovery"},
}

# =============================================================================
# TARGET COMPANIES - 90s IT Infrastructure Players
# Analogous to today's AI infrastructure companies
# =============================================================================

# Companies with SEC CIK numbers (for those that still file)
TARGET_COMPANIES = {
    "Cisco": "0000858877",       # Network infrastructure (like Nvidia for AI)
    "Intel": "0000050863",       # Chip maker (like AMD/Intel today)
    "Microsoft": "0000789019",   # Software platform
    "Oracle": "0001341439",      # Enterprise database/software
    "Sun Microsystems": "0000709519",  # Servers (acquired by Oracle 2010)
    "Lucent": "0001108524",      # Telecom equipment (merged into Nokia)
}

# Yahoo Finance tickers (for historical stock prices)
YAHOO_TICKERS_HISTORY = {
    "Cisco": "CSCO",
    "Intel": "INTC",
    "Microsoft": "MSFT",
    "Oracle": "ORCL",
    # Sun Microsystems: traded as SUNW, then JAVA (delisted 2010)
    # Lucent: traded as LU (delisted 2006)
    # Nortel: traded as NT (delisted 2009)
}

# Full company list with notes
COMPANY_NOTES = {
    "Cisco": "Dominant network equipment maker. The 'Nvidia of the 90s'. IPO 1990, peak market cap ~$555B.",
    "Intel": "Dominant processor maker. Fueled the PC revolution. Peak market cap ~$509B in 2000.",
    "Microsoft": "Dominant software platform. Windows/Office monopoly. Peak market cap ~$613B in 1999.",
    "Oracle": "Dominant database/enterprise software. Peak market cap ~$228B in 2000.",
    "Sun Microsystems": "Server/workstation maker. 'We put the dot in .com'. Peak cap ~$200B, crashed to $3B.",
    "Lucent": "Spun off from AT&T 1996. Telecom equipment. Peak cap ~$258B, crashed to $6B.",
}

# =============================================================================
# FRED SERIES - Historical Macro Indicators (available for 1990s)
# =============================================================================

FRED_SERIES = {
    "FEDFUNDS": "Federal Funds Rate",
    "BAA10Y": "Baa Corporate Bond Spread",
    "GDP": "US GDP",
    "SP500": "S&P 500 Index",
    "NASDAQCOM": "NASDAQ Composite Index",
}

FRED_CREDIT_SERIES = {
    "DFF": "Federal Funds Effective Rate (Daily)",
    "DGS10": "10-Year Treasury Rate",
    "DGS2": "2-Year Treasury Rate",
    "T10Y2Y": "10Y-2Y Treasury Spread (Yield Curve)",
    "T10Y3M": "10Y-3M Treasury Spread",
    "TEDRATE": "TED Spread (Interbank Lending Risk)",
    "BAMLC0A0CM": "Investment Grade Corporate Bond Spread",
    "BAMLH0A0HYM2": "High Yield Bond Spread",
}

# Market ETFs available in 1990s-2000s
MARKET_TICKERS = {
    "SPY": "S&P 500 ETF (from 1993)",
    "QQQ": "NASDAQ 100 ETF (from 1999 as QQQ)",
    "^IXIC": "NASDAQ Composite Index",
    "^GSPC": "S&P 500 Index",
    "^VIX": "CBOE Volatility Index",
    "XLK": "Technology Select Sector (from 1998)",
}

# Semiconductor companies of the 90s
SEMICONDUCTOR_TICKERS_90S = ["INTC", "TXN", "MOT", "AMD", "AMAT", "LRCX"]

# =============================================================================
# RISK THRESHOLDS (same as main project for comparison)
# =============================================================================

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

RISK_LEVELS = {
    "LOW": {"label": "Low Risk", "color": "#28a745"},
    "MEDIUM": {"label": "Medium Risk", "color": "#ffc107"},
    "HIGH": {"label": "High Risk", "color": "#dc3545"},
}

WARNING_THRESHOLDS_CREDIT = {
    "high_yield_spread": {"yellow": 4.0, "orange": 5.5, "red": 7.0},
    "investment_grade_spread": {"yellow": 1.5, "orange": 2.5, "red": 3.5},
    "ted_spread": {"yellow": 0.35, "orange": 0.50, "red": 0.75},
    "yield_curve_10y2y": {"yellow": -0.20, "orange": -0.50, "red": -0.75},
}

WARNING_THRESHOLDS_EQUITY = {
    "vix": {"yellow": 22, "orange": 28, "red": 35},
    "nasdaq_weekly_drawdown": {"yellow": -5, "orange": -10, "red": -20},
    "tech_weekly_drawdown": {"yellow": -4, "orange": -8, "red": -15},
}

RISK_WEIGHTS = {
    "credit_market": 0.30,
    "equity_market": 0.25,
    "company_fundamentals": 0.30,
    "supply_demand": 0.15,
}

ALERT_LEVELS = {
    "GREEN": {"label": "Normal", "description": "Funding environment healthy", "score_max": 40},
    "YELLOW": {"label": "Watch", "description": "Early warning signals present", "score_max": 55},
    "ORANGE": {"label": "Warning", "description": "Multiple risk indicators elevated", "score_max": 70},
    "RED": {"label": "Danger", "description": "High systemic risk detected", "score_max": 100},
}
