"""
AI Funding Risk Early Warning System - Main Entry Point
Runs the complete warning system pipeline
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    FRED_API_KEY, RAW_DATA_DIR, PROCESSED_DATA_DIR, MARKET_DATA_DIR
)


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
        import pandas
    except ImportError:
        missing.append("pandas")

    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False

    return True


def run_data_collection(skip_fred: bool = False):
    """Run all data collection modules"""
    print("\n" + "=" * 70)
    print("PHASE 1: DATA COLLECTION")
    print("=" * 70)

    results = {"success": [], "failed": []}

    # 1. Original SEC data fetch
    print("\n[1/5] Fetching SEC company data...")
    try:
        from scripts.fetch_sec import main as fetch_sec
        fetch_sec()
        results["success"].append("SEC")
    except Exception as e:
        print(f"  Error: {e}")
        results["failed"].append("SEC")

    # 2. Original FRED data
    if not skip_fred and FRED_API_KEY:
        print("\n[2/5] Fetching FRED macro data...")
        try:
            from scripts.fetch_fred import main as fetch_fred
            fetch_fred()
            results["success"].append("FRED (macro)")
        except Exception as e:
            print(f"  Error: {e}")
            results["failed"].append("FRED (macro)")

        # 3. Extended credit market data
        print("\n[3/5] Fetching credit market data...")
        try:
            from scripts.fetch_credit_market import main as fetch_credit
            fetch_credit()
            results["success"].append("Credit Market")
        except Exception as e:
            print(f"  Error: {e}")
            results["failed"].append("Credit Market")
    else:
        print("\n[2-3/5] Skipping FRED data (no API key or --skip-fred)")
        results["failed"].append("FRED (skipped)")

    # 4. Yahoo Finance company data
    print("\n[4/5] Fetching Yahoo Finance company data...")
    try:
        from scripts.fetch_yahoo import main as fetch_yahoo
        fetch_yahoo()
        results["success"].append("Yahoo (companies)")
    except Exception as e:
        print(f"  Error: {e}")
        results["failed"].append("Yahoo (companies)")

    # 5. Market indicators (ETFs, VIX, etc.)
    print("\n[5/5] Fetching market indicators...")
    try:
        from scripts.fetch_market import main as fetch_market
        fetch_market()
        results["success"].append("Market Indicators")
    except Exception as e:
        print(f"  Error: {e}")
        results["failed"].append("Market Indicators")

    print(f"\nData collection complete:")
    print(f"  Success: {len(results['success'])} - {', '.join(results['success'])}")
    print(f"  Failed: {len(results['failed'])} - {', '.join(results['failed']) if results['failed'] else 'None'}")

    return len(results["failed"]) == 0


def run_data_processing():
    """Run data processing"""
    print("\n" + "=" * 70)
    print("PHASE 2: DATA PROCESSING")
    print("=" * 70)

    try:
        from scripts.process_data import main as process_data
        process_data()
        return True
    except Exception as e:
        print(f"Error in data processing: {e}")
        return False


def run_risk_analysis():
    """Run risk analysis modules"""
    print("\n" + "=" * 70)
    print("PHASE 3: RISK ANALYSIS")
    print("=" * 70)

    results = {"success": [], "failed": []}

    # 1. Original risk calculator
    print("\n[1/4] Running risk assessment...")
    try:
        from model.risk_calculator import main as run_risk
        run_risk()
        results["success"].append("Risk Assessment")
    except Exception as e:
        print(f"  Error: {e}")
        results["failed"].append("Risk Assessment")

    # 2. Scenario simulation
    print("\n[2/4] Running scenario simulation...")
    try:
        from model.scenario_simulator import main as run_scenarios
        run_scenarios()
        results["success"].append("Scenario Simulation")
    except Exception as e:
        print(f"  Error: {e}")
        results["failed"].append("Scenario Simulation")

    # 3. Supply-demand analysis
    print("\n[3/4] Running supply-demand analysis...")
    try:
        from model.supply_demand import main as run_supply_demand
        run_supply_demand()
        results["success"].append("Supply-Demand")
    except Exception as e:
        print(f"  Error: {e}")
        results["failed"].append("Supply-Demand")

    # 4. Funding health assessment
    print("\n[4/4] Running funding health assessment...")
    try:
        from model.funding_health import main as run_funding_health
        run_funding_health()
        results["success"].append("Funding Health")
    except Exception as e:
        print(f"  Error: {e}")
        results["failed"].append("Funding Health")

    print(f"\nRisk analysis complete:")
    print(f"  Success: {len(results['success'])} - {', '.join(results['success'])}")
    print(f"  Failed: {len(results['failed'])} - {', '.join(results['failed']) if results['failed'] else 'None'}")

    return len(results["failed"]) == 0


def run_warning_system():
    """Run the early warning system"""
    print("\n" + "=" * 70)
    print("PHASE 4: EARLY WARNING SYSTEM")
    print("=" * 70)

    try:
        from model.warning_system import main as run_warnings
        dashboard = run_warnings()
        return dashboard
    except Exception as e:
        print(f"Error in warning system: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_visualization():
    """Generate visualization and reports"""
    print("\n" + "=" * 70)
    print("PHASE 5: VISUALIZATION")
    print("=" * 70)

    try:
        from visualization.dashboard import main as run_dashboard
        run_dashboard()
        return True
    except Exception as e:
        print(f"Error in visualization: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI Funding Risk Early Warning System"
    )
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="Only fetch data, don't run analysis"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only run analysis using cached data"
    )
    parser.add_argument(
        "--warning-only",
        action="store_true",
        help="Only run warning system using cached data"
    )
    parser.add_argument(
        "--skip-fred",
        action="store_true",
        help="Skip FRED data fetching"
    )
    parser.add_argument(
        "--skip-viz",
        action="store_true",
        help="Skip visualization generation"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("AI FUNDING RISK EARLY WARNING SYSTEM")
    print("=" * 70)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Ensure directories exist
    for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MARKET_DATA_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Execute pipeline based on arguments
    if args.warning_only:
        dashboard = run_warning_system()
        if dashboard:
            print("\n[OK] Warning system completed successfully")
        else:
            print("\n[ERROR] Warning system failed")
            sys.exit(1)

    elif args.analyze_only:
        success = run_risk_analysis()
        if success:
            dashboard = run_warning_system()
            if not args.skip_viz:
                run_visualization()
            print("\n[OK] Analysis completed successfully")
        else:
            print("\n[ERROR] Analysis failed")
            sys.exit(1)

    elif args.fetch_only:
        success = run_data_collection(skip_fred=args.skip_fred)
        if success:
            print("\n[OK] Data collection completed successfully")
        else:
            print("\n[WARN] Data collection completed with some failures")

    else:
        # Full pipeline
        print("\nRunning full pipeline...")

        # Phase 1: Data Collection
        data_success = run_data_collection(skip_fred=args.skip_fred)

        # Phase 2: Data Processing
        if not run_data_processing():
            print("\n[ERROR] Data processing failed")
            sys.exit(1)

        # Phase 3: Risk Analysis
        if not run_risk_analysis():
            print("\n[WARN] Some risk analysis modules failed")

        # Phase 4: Warning System
        dashboard = run_warning_system()

        # Phase 5: Visualization (optional)
        if not args.skip_viz:
            run_visualization()

        # Final summary
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)

        if dashboard:
            print(f"\n[STATUS] Overall Status: {dashboard.overall_status}")
            print(f"[SCORE] Health Score: {dashboard.overall_score}/100")
            print(f"[INFO] {dashboard.status_message}")

            if dashboard.active_warnings:
                print(f"\n[ALERT] Active Warnings: {len(dashboard.active_warnings)}")
                for w in dashboard.active_warnings[:3]:  # Show top 3
                    print(f"   * {w['name']}: {w['message']}")

        print("\n[OK] All systems completed")
        print(f"\nOutput files saved to:")
        print(f"  - {PROCESSED_DATA_DIR}")
        print(f"  - {MARKET_DATA_DIR}")


if __name__ == "__main__":
    main()
