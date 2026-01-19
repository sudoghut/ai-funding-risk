# AI Funding Risk Early Warning System

A comprehensive, automated system for monitoring AI industry funding chain risks with real-time early warning capabilities.

## Overview

This system evaluates whether AI infrastructure investment levels are sustainable by analyzing:

- **Consumption Side**: Capital expenditure (Capex) trends of major tech companies
- **Supply Side**: Macroeconomic funding conditions, credit markets, institutional capital
- **Efficiency**: Return on investment metrics (revenue growth vs. spending growth)
- **Market Signals**: Equity sentiment, VIX, tech sector performance

### Core Formula

```
Risk Signal = f(Capital Consumption Rate, Funding Supply Capability, Capital Efficiency, Market Sentiment)
```

## Features

- **Multi-Source Data Collection**: SEC EDGAR, FRED, Yahoo Finance, Credit Markets
- **Early Warning System**: Real-time signal monitoring with GREEN/YELLOW/ORANGE/RED alerts
- **Supply-Demand Analysis**: Balance ratio tracking with multi-year projections
- **Scenario Simulation**: Project future funding sustainability under 5 scenarios
- **Company Risk Profiling**: Individual risk scores with data quality indicators
- **Visualization Dashboard**: Interactive HTML reports and charts

## Installation

```bash
# Clone the repository
git clone https://github.com/sudoghut/ai-funding-risk.git
cd ai-funding-risk

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

- `requests` - HTTP requests for SEC and FRED APIs
- `yfinance` - Yahoo Finance data
- `matplotlib` - Visualization (optional but recommended)

## Configuration

### FRED API Key

Get a free API key from [FRED](https://fred.stlouisfed.org/docs/api/api_key.html), then:

**Option 1**: Create a `.env` file in the project root:
```
FRED_API_KEY=your_api_key_here
```

**Option 2**: Set environment variable:
```bash
# Windows
set FRED_API_KEY=your_api_key_here

# Linux/Mac
export FRED_API_KEY=your_api_key_here
```

## Usage

### Run Complete Pipeline (Recommended)

```bash
python run_warning_system.py
```

This will execute the full 5-phase pipeline:
1. **Data Collection**: SEC, FRED, Credit Markets, Yahoo Finance, Market Indicators
2. **Data Processing**: Consolidation and metric calculation
3. **Risk Analysis**: Risk assessment, scenario simulation, supply-demand analysis
4. **Early Warning**: Signal monitoring and alert generation
5. **Visualization**: HTML dashboards and charts

### Alternative: Legacy Pipeline

```bash
python main.py
```

### Command Line Options

```bash
python main.py --fetch-only      # Only fetch new data
python main.py --analyze-only    # Only run analysis (use cached data)
python main.py --visualize-only  # Only generate visualizations
python main.py --skip-fred       # Skip FRED data (if no API key)
```

### Run Individual Components

```bash
# Fetch data
python scripts/fetch_sec.py
python scripts/fetch_fred.py
python scripts/fetch_yahoo.py
python scripts/fetch_credit_market.py
python scripts/fetch_market_data.py

# Process data
python scripts/process_data.py

# Run analysis
python model/risk_calculator.py
python model/scenario_simulator.py
python model/supply_demand.py
python model/funding_health.py
python model/warning_system.py

# Generate visualizations
python visualization/dashboard.py
```

## Project Structure

```
ai-funding-risk/
├── config/
│   └── settings.py              # Configuration and thresholds
├── scripts/
│   ├── fetch_sec.py             # SEC EDGAR API fetcher
│   ├── fetch_fred.py            # FRED macroeconomic data
│   ├── fetch_yahoo.py           # Yahoo Finance data
│   ├── fetch_credit_market.py   # Credit market indicators
│   ├── fetch_market_data.py     # Market sentiment data
│   └── process_data.py          # Data consolidation
├── model/
│   ├── risk_calculator.py       # Risk scoring engine
│   ├── scenario_simulator.py    # Future projections
│   ├── supply_demand.py         # Supply-demand balance analysis
│   ├── funding_health.py        # Funding environment health
│   └── warning_system.py        # Early warning signal generator
├── visualization/
│   └── dashboard.py             # Charts and HTML reports
├── data/
│   ├── raw/                     # API responses (JSON)
│   ├── processed/               # Consolidated analysis
│   └── market/                  # Market indicator data
├── run_warning_system.py        # Full pipeline orchestrator
├── main.py                      # Legacy pipeline
├── requirements.txt
└── .env                         # API keys (not in git)
```

## Data Sources

| Source | Data | Update Frequency |
|--------|------|------------------|
| SEC EDGAR | Company financials (Capex, Cash Flow, Debt, Revenue) | Quarterly |
| FRED | Macroeconomic & credit indicators | Daily/Monthly |
| Yahoo Finance | Real-time market data, company metrics | Real-time |
| Credit Markets | Spreads, yield curves, bank lending | Daily/Weekly |

### Target Companies

- Amazon (AMZN)
- Microsoft (MSFT)
- Alphabet/Google (GOOG)
- Meta (META)
- Oracle (ORCL)
- Nvidia (NVDA)

### Key Indicators

**Credit Market:**
- High Yield Bond Spread (BAMLH0A0HYM2)
- Investment Grade Spread (BAMLC0A0CM)
- 10Y-2Y Treasury Spread (Yield Curve)
- Federal Funds Rate

**Equity Market:**
- VIX Volatility Index
- Tech ETF Performance (XLK, SMH, SOXX)
- AI Stock Sentiment

**Company Level:**
- Capex to Cash Flow Ratio
- Debt to Cash Ratio
- Revenue Growth vs Debt Growth

## Risk Assessment Framework

### Alert Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| GREEN | 0-40 | Funding environment healthy |
| YELLOW | 40-55 | Early warning signals present |
| ORANGE | 55-70 | Multiple risk indicators elevated |
| RED | 70-100 | High systemic risk detected |

### Risk Thresholds

| Metric | Normal | Warning | Danger |
|--------|--------|---------|--------|
| Capex/Cash Flow | <70% | 70-90% | >90% |
| Debt/Cash Ratio | <3.0x | 3.0-5.0x | >7.0x |
| High Yield Spread | <4% | 4-5.5% | >7% |
| VIX | <22 | 22-28 | >35 |

### Risk Levels (Company)

- **LOW** (Score < 40): Sustainable funding profile
- **MEDIUM** (Score 40-65): Monitor key indicators
- **HIGH** (Score > 65): Elevated risk, potential funding stress

## Scenario Simulation

The model simulates five standard scenarios:

1. **Historical Trend**: Actual historical growth rates continue
2. **Base Case**: Moderate growth assumptions
3. **Optimistic**: Strong revenue growth, favorable rates
4. **Pessimistic**: Slowing revenue, rising rates
5. **AI Winter**: Severe slowdown with continued capex commitments

### Custom Scenarios

```python
from model.scenario_simulator import ScenarioSimulator, ScenarioParameters

simulator = ScenarioSimulator()
data = simulator.load_baseline_data()
baseline = simulator.get_aggregate_baseline(data)

custom_params = ScenarioParameters(
    capex_growth_rate=0.25,      # 25% annual capex growth
    revenue_growth_rate=0.10,    # 10% revenue growth
    interest_rate=5.5,           # Interest rate assumption
    debt_growth_rate=0.15,       # 15% debt growth
    years_to_simulate=5          # 5-year projection
)

result = simulator.simulate_scenario(baseline, custom_params, "Custom Scenario")
```

## Output Files

After running the pipeline:

| File | Description |
|------|-------------|
| `data/raw/*.json` | Raw API responses |
| `data/market/*.json` | Market indicator data |
| `data/processed/consolidated_data.json` | Merged dataset |
| `data/processed/risk_assessment.json` | Risk scores with data quality |
| `data/processed/scenario_projections.json` | Scenario results |
| `data/processed/supply_demand_analysis.json` | Supply-demand balance |
| `data/processed/funding_health_report.json` | Funding environment health |
| `data/processed/warning_dashboard.json` | Early warning signals |
| `data/visualization/output/warning_dashboard.html` | Interactive warning dashboard |
| `data/visualization/output/risk_report.html` | Risk analysis report |
| `data/visualization/output/*.png` | Chart images |

## Sample Output

```
======================================================================
AI FUNDING RISK EARLY WARNING DASHBOARD
======================================================================

Overall Status: [OK] GREEN
Health Score: 95.6/100
Status: All systems normal - funding environment healthy

Signal Summary (8 total):
  [!] YELLOW: 1
  [OK] GREEN: 7

============================================================
RISK ASSESSMENT SUMMARY
============================================================

Overall Risk Score: 36.0/100
Risk Level: LOW
Data Completeness: 90%

Category Scores:
  Consumption (Capex pressure): 46.7/100
  Supply (Funding availability): 30.0/100
  Efficiency (ROI on spending): 31.6/100

------------------------------------------------------------
COMPANY RISK PROFILES
------------------------------------------------------------
Company         Ticker   Score    Level     Quality
------------------------------------------------------------
Amazon          AMZN     36.6     LOW       medium
Microsoft       MSFT     27.0     LOW       high
Alphabet        GOOG     30.5     LOW       high
Meta            META     28.0     LOW       high
Oracle          ORCL     69.9     HIGH      medium
Nvidia          NVDA     25.9     LOW       high

============================================================
SUPPLY-DEMAND ANALYSIS
============================================================

Balance Ratio: 1.84x
Sustainability Score: 92.2/100
Annual Gap: +$478B (surplus)
Trend: IMPROVING

5-Year Projection:
Year       Demand     Supply        Gap     Status
--------------------------------------------------
2026   $     566B $    1044B $    +478B    surplus
2027   $     708B $    1170B $    +462B    surplus
2028   $     885B $    1310B $    +425B    surplus
2029   $    1106B $    1467B $    +361B    surplus
2030   $    1383B $    1643B $    +260B    surplus
```

## Limitations

- SEC data may lag by several weeks after filing
- Different companies use different XBRL tags (e.g., Nvidia uses `PaymentsToAcquireProductiveAssets` for Capex)
- Yahoo Finance data is unofficial and may have gaps
- Some FRED series may be discontinued or unavailable
- Risk thresholds are configurable assumptions, not absolute truths
- Model focuses on major tech companies, not the entire AI ecosystem

## Data Quality

The system tracks data quality at multiple levels:
- **Indicator Level**: `is_estimated` flag shows when default values are used
- **Company Level**: Quality rating (high/medium/low) based on missing indicators
- **System Level**: Overall data completeness percentage

Current typical completeness: **~90%** (3/30 indicators estimated)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests at [GitHub](https://github.com/sudoghut/ai-funding-risk).
