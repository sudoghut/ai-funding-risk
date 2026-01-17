# AI Funding Risk Assessment Model

A sustainable, automated model for assessing AI industry funding chain risks by comparing capital consumption rates against funding supply capabilities.

## Overview

This model evaluates whether current AI infrastructure investment levels are sustainable by analyzing:

- **Consumption Side**: Capital expenditure (Capex) trends of major tech companies
- **Supply Side**: Macroeconomic funding conditions (interest rates, credit spreads)
- **Efficiency**: Return on investment metrics (revenue growth vs. spending growth)

### Core Formula

```
Risk Signal = f(Capital Consumption Rate, Funding Supply Capability, Capital Efficiency)
```

## Features

- **Multi-Source Data Collection**: SEC EDGAR, FRED, Yahoo Finance
- **Automated Risk Scoring**: Company-level and systemic risk assessment
- **Scenario Simulation**: Project future funding sustainability under different assumptions
- **Visualization Dashboard**: Charts and HTML reports

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-funding-risk.git
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

### Run Complete Pipeline

```bash
python main.py
```

This will:
1. Fetch data from all sources
2. Process and consolidate data
3. Calculate risk scores
4. Run scenario simulations
5. Generate visualizations and reports

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

# Process data
python scripts/process_data.py

# Run analysis
python model/risk_calculator.py
python model/scenario_simulator.py

# Generate visualizations
python visualization/dashboard.py
```

## Project Structure

```
ai-funding-risk/
├── config/
│   └── settings.py          # Configuration and thresholds
├── scripts/
│   ├── fetch_sec.py         # SEC EDGAR API fetcher
│   ├── fetch_fred.py        # FRED macroeconomic data
│   ├── fetch_yahoo.py       # Yahoo Finance data
│   └── process_data.py      # Data consolidation
├── model/
│   ├── risk_calculator.py   # Risk scoring engine
│   └── scenario_simulator.py # Future projections
├── visualization/
│   └── dashboard.py         # Charts and HTML reports
├── data/
│   ├── raw/                 # API responses (JSON)
│   └── processed/           # Consolidated analysis
├── main.py                  # Pipeline orchestrator
├── requirements.txt
└── .env                     # API keys (not in git)
```

## Data Sources

| Source | Data | Update Frequency |
|--------|------|------------------|
| SEC EDGAR | Company financials (10-K, 10-Q) | Quarterly |
| FRED | Macroeconomic indicators | Daily/Monthly |
| Yahoo Finance | Real-time market data | Real-time |

### Target Companies

- Amazon (AMZN)
- Microsoft (MSFT)
- Alphabet/Google (GOOG)
- Meta (META)
- Oracle (ORCL)
- Nvidia (NVDA)

### Macroeconomic Indicators

- Federal Funds Rate (FEDFUNDS)
- Baa Corporate Bond Spread (BAA10Y)
- High Yield Bond Spread (BAMLH0A0HYM2)
- US GDP
- Nonfinancial Corporate Debt
- S&P 500 Index

## Risk Assessment Framework

### Risk Thresholds

| Metric | Normal | Warning | Danger |
|--------|--------|---------|--------|
| Capex/Cash Flow | <70% | 70-90% | >90% |
| Debt/Revenue Growth | <1.0x | 1.0-1.5x | >1.5x |
| Interest Rate | <4% | 4-6% | >6% |
| Credit Spread | <2% | 2-4% | >4% |

### Risk Levels

- **LOW** (Score < 40): Sustainable funding environment
- **MEDIUM** (Score 40-65): Monitor key indicators
- **HIGH** (Score > 65): Elevated risk, potential funding stress

## Scenario Simulation

The model simulates four standard scenarios:

1. **Base Case**: Current growth trends continue
2. **Optimistic**: Strong revenue growth, favorable rates
3. **Pessimistic**: Slowing revenue, rising rates
4. **AI Winter**: Severe slowdown with continued capex commitments

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
| `data/processed/consolidated_data.json` | Merged dataset |
| `data/processed/risk_assessment.json` | Risk scores |
| `data/processed/scenario_projections.json` | Scenario results |
| `visualization/output/risk_report.html` | Interactive HTML report |
| `visualization/output/*.png` | Chart images |

## Sample Output

```
============================================================
RISK ASSESSMENT SUMMARY
============================================================

Overall Risk Score: 37.3/100
Risk Level: LOW

Category Scores:
  Consumption (Capex pressure): 50.0/100
  Supply (Funding availability): 30.0/100
  Efficiency (ROI on spending): 31.6/100

------------------------------------------------------------
COMPANY RISK PROFILES
------------------------------------------------------------
Company         Ticker   Score    Level
------------------------------------------------------------
Amazon          AMZN     39.5     LOW
Microsoft       MSFT     30.5     LOW
Alphabet        GOOG     30.5     LOW
Meta            META     34.5     LOW
Oracle          ORCL     59.4     MEDIUM
Nvidia          NVDA     30.5     LOW
```

## Limitations

- SEC data may lag by several weeks after filing
- Yahoo Finance data is unofficial and may have gaps
- Risk thresholds are configurable assumptions, not absolute truths
- Model focuses on major tech companies, not the entire AI ecosystem

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
