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

# Yahoo Finance Tickers
YAHOO_TICKERS = ["AMZN", "MSFT", "GOOG", "META", "ORCL", "NVDA"]

# FRED Series IDs
FRED_SERIES = {
    "FEDFUNDS": "Federal Funds Rate",
    "BAA10Y": "Baa Corporate Bond Spread",
    "BAMLH0A0HYM2": "High Yield Bond Spread",
    "GDP": "US GDP",
    "BOGZ1FL664090005Q": "Nonfinancial Corporate Debt",
    "SP500": "S&P 500 Index",
}

# SEC Financial Metrics to Extract
SEC_METRICS = [
    "CapitalExpenditures",
    "NetCashProvidedByUsedInOperatingActivities",
    "LongTermDebt",
    "Revenues",
    "PropertyPlantAndEquipmentNet",
]

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
