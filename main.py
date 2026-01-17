"""
AI Funding Risk Assessment Model - Main Entry Point

This script orchestrates the complete pipeline:
1. Fetch data from SEC EDGAR, FRED, and Yahoo Finance
2. Process and consolidate data
3. Calculate risk scores
4. Run scenario simulations
5. Generate visualizations and reports

Usage:
    python main.py                    # Run complete pipeline
    python main.py --fetch-only       # Only fetch new data
    python main.py --analyze-only     # Only run analysis (use cached data)
    python main.py --help             # Show help
"""
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR, FRED_API_KEY


def check_dependencies():
    """Check if required packages are installed"""
    missing = []

    try:
        import requests
    except ImportError:
        missing.append("requests")

    try:
        import yfinance
    except ImportError:
        missing.append("yfinance")

    try:
        import matplotlib
    except ImportError:
        print("Warning: matplotlib not installed. Charts will be skipped.")
        print("Install with: pip install matplotlib")

    if missing:
        print("Missing required packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstall with: pip install " + " ".join(missing))
        return False

    return True


def fetch_data(skip_fred: bool = False):
    """Fetch data from all sources"""
    print("\n" + "=" * 60)
    print("STEP 1: Fetching Data")
    print("=" * 60)

    # Create data directories
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch SEC data
    print("\n--- SEC EDGAR Data ---")
    try:
        from scripts.fetch_sec import SECFetcher
        sec_fetcher = SECFetcher()
        sec_data = sec_fetcher.fetch_all_companies()
        sec_fetcher.save_data(sec_data, "sec_company_data.json")
        print(f"SEC: Fetched data for {len(sec_data)} companies")
    except Exception as e:
        print(f"SEC fetch error: {e}")

    # Fetch FRED data
    if not skip_fred:
        print("\n--- FRED Data ---")
        if not FRED_API_KEY:
            print("FRED API key not set. Skipping FRED data.")
            print("Set FRED_API_KEY environment variable to enable.")
        else:
            try:
                from scripts.fetch_fred import FREDFetcher
                fred_fetcher = FREDFetcher()
                fred_data = fred_fetcher.fetch_all_series()
                fred_fetcher.save_data(fred_data, "fred_series_data.json")
                print(f"FRED: Fetched {len(fred_data)} series")
            except Exception as e:
                print(f"FRED fetch error: {e}")
    else:
        print("\n--- FRED Data ---")
        print("Skipped (--skip-fred flag)")

    # Fetch Yahoo Finance data
    print("\n--- Yahoo Finance Data ---")
    try:
        from scripts.fetch_yahoo import YahooFetcher
        yahoo_fetcher = YahooFetcher()
        yahoo_data = yahoo_fetcher.fetch_all_companies()
        yahoo_fetcher.save_data(yahoo_data, "yahoo_company_data.json")
        print(f"Yahoo: Fetched data for {len(yahoo_data)} companies")
    except Exception as e:
        print(f"Yahoo fetch error: {e}")


def process_data():
    """Process and consolidate all data"""
    print("\n" + "=" * 60)
    print("STEP 2: Processing Data")
    print("=" * 60)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from scripts.process_data import DataProcessor
        processor = DataProcessor()
        consolidated = processor.run()
        print(f"Processed data for {len(consolidated.get('companies', {}))} companies")
        return True
    except Exception as e:
        print(f"Data processing error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_analysis():
    """Run risk analysis and scenario simulation"""
    print("\n" + "=" * 60)
    print("STEP 3: Risk Analysis")
    print("=" * 60)

    # Risk calculation
    try:
        from model.risk_calculator import RiskCalculator
        calculator = RiskCalculator()
        assessment = calculator.run_assessment()

        if assessment:
            calculator.print_assessment_summary(assessment)
        else:
            print("Could not generate assessment - check if data files exist")
            return False
    except Exception as e:
        print(f"Risk calculation error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Scenario simulation
    print("\n" + "=" * 60)
    print("STEP 4: Scenario Simulation")
    print("=" * 60)

    try:
        from model.scenario_simulator import ScenarioSimulator
        simulator = ScenarioSimulator()
        scenarios = simulator.run_standard_scenarios()

        if scenarios:
            simulator.save_scenarios(scenarios)
            simulator.print_scenario_summary(scenarios)
    except Exception as e:
        print(f"Scenario simulation error: {e}")
        import traceback
        traceback.print_exc()

    return True


def generate_visualizations():
    """Generate charts and reports"""
    print("\n" + "=" * 60)
    print("STEP 5: Generating Visualizations")
    print("=" * 60)

    try:
        from visualization.dashboard import RiskDashboard
        dashboard = RiskDashboard()
        dashboard.generate_all()
        return True
    except Exception as e:
        print(f"Visualization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_full_pipeline(skip_fred: bool = False):
    """Run the complete pipeline"""
    print("=" * 60)
    print("AI FUNDING RISK ASSESSMENT MODEL")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Check dependencies
    if not check_dependencies():
        return False

    # Run pipeline steps
    fetch_data(skip_fred=skip_fred)
    if not process_data():
        print("\nPipeline stopped due to data processing error")
        return False

    if not run_analysis():
        print("\nPipeline stopped due to analysis error")
        return False

    generate_visualizations()

    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  Raw data: {RAW_DATA_DIR}")
    print(f"  Processed data: {PROCESSED_DATA_DIR}")
    print(f"  Visualizations: {PROJECT_ROOT / 'visualization' / 'output'}")

    report_path = PROJECT_ROOT / 'visualization' / 'output' / 'risk_report.html'
    if report_path.exists():
        print(f"\nOpen the report in your browser:")
        print(f"  {report_path}")

    return True


def main():
    """Main entry point with CLI argument handling"""
    parser = argparse.ArgumentParser(
        description="AI Funding Risk Assessment Model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Run complete pipeline
  python main.py --fetch-only       Only fetch new data
  python main.py --analyze-only     Only run analysis (use cached data)
  python main.py --skip-fred        Skip FRED data (if no API key)
        """
    )

    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="Only fetch data, skip analysis and visualization"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only run analysis using existing data"
    )
    parser.add_argument(
        "--visualize-only",
        action="store_true",
        help="Only generate visualizations using existing analysis"
    )
    parser.add_argument(
        "--skip-fred",
        action="store_true",
        help="Skip FRED data fetching (useful if no API key)"
    )

    args = parser.parse_args()

    if args.fetch_only:
        if not check_dependencies():
            return
        fetch_data(skip_fred=args.skip_fred)
    elif args.analyze_only:
        if not check_dependencies():
            return
        process_data()
        run_analysis()
        generate_visualizations()
    elif args.visualize_only:
        generate_visualizations()
    else:
        run_full_pipeline(skip_fred=args.skip_fred)


if __name__ == "__main__":
    main()
