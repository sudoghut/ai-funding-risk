"""
90s IT Bubble Historical Validation - Main Pipeline
Validates AI Funding Risk conclusions against the 1995-2003 IT/Telecom Bubble
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR, MARKET_DATA_DIR, COMPILED_DATA_DIR


def check_dependencies():
    """Check if required packages are installed"""
    missing = []
    for pkg in ["requests", "yfinance", "pandas"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    return True


def run_compile_data():
    """Phase 1a: Compile historical financial data"""
    print("\n" + "=" * 70)
    print("PHASE 1a: COMPILE HISTORICAL FINANCIAL DATA")
    print("=" * 70)
    try:
        from scripts.compile_historical_data import main as compile_data
        compile_data()
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_fetch_fred():
    """Phase 1b: Fetch FRED historical macro data"""
    print("\n" + "=" * 70)
    print("PHASE 1b: FETCH FRED HISTORICAL DATA (1995-2003)")
    print("=" * 70)
    try:
        from scripts.fetch_fred_history import main as fetch_fred
        fetch_fred()
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_fetch_yahoo():
    """Phase 1c: Fetch Yahoo Finance historical stock data"""
    print("\n" + "=" * 70)
    print("PHASE 1c: FETCH YAHOO FINANCE HISTORICAL DATA (1995-2003)")
    print("=" * 70)
    try:
        from scripts.fetch_yahoo_history import main as fetch_yahoo
        fetch_yahoo()
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_process_data():
    """Phase 2: Process and consolidate all data"""
    print("\n" + "=" * 70)
    print("PHASE 2: DATA PROCESSING & CONSOLIDATION")
    print("=" * 70)
    try:
        from scripts.process_data_history import main as process_data
        process_data()
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_visualization():
    """Phase 3: Generate visualizations and report"""
    print("\n" + "=" * 70)
    print("PHASE 3: VISUALIZATION & REPORT GENERATION")
    print("=" * 70)
    try:
        from visualization.dashboard_history import main as generate_viz
        generate_viz()
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_final_summary():
    """Print final validation summary"""
    import json

    print("\n" + "=" * 70)
    print("HISTORICAL VALIDATION SUMMARY")
    print("=" * 70)

    # Load results
    risk_file = PROCESSED_DATA_DIR / "risk_timeline.json"
    comparison_file = PROCESSED_DATA_DIR / "bubble_comparison.json"

    if risk_file.exists():
        with open(risk_file, "r", encoding="utf-8") as f:
            risk_data = json.load(f)

        timeline = risk_data.get("timeline", [])
        print("\nRisk Score Timeline (90s IT Bubble):")
        print(f"{'Year':<6} {'Score':>8} {'Level':>8} {'CapEx/CF':>10} {'CapEx $B':>10}")
        print("-" * 50)
        for item in timeline:
            capex_cf = item.get("capex_to_cashflow")
            cf_str = f"{capex_cf:.3f}" if capex_cf else "N/A"
            print(f"{item['year']:<6} {item['overall_risk_score']:>7.1f} {item['risk_level']:>8} "
                  f"{cf_str:>10} ${item.get('total_capex_B', 0):>8.1f}")

    if comparison_file.exists():
        with open(comparison_file, "r", encoding="utf-8") as f:
            comparison = json.load(f)

        summary = comparison.get("it_bubble_summary", {})
        print(f"\n{'='*50}")
        print("IT BUBBLE KEY METRICS:")
        print(f"  Peak Year: {summary.get('peak_year')}")
        print(f"  Peak CapEx: ${summary.get('peak_aggregate_capex_B', 0):.1f}B")
        print(f"  Peak Revenue: ${summary.get('peak_aggregate_revenue_B', 0):.1f}B")
        print(f"  Peak CapEx/CF: {summary.get('peak_capex_to_cashflow', 'N/A')}")
        print(f"  Peak Market Cap: ${summary.get('peak_market_cap_T', 0):.2f}T")

        capex_growth = summary.get('capex_growth_pre_to_peak')
        if capex_growth:
            print(f"  CapEx Growth (1996-2000): {capex_growth:.1f}%")

        rev_decline = summary.get('revenue_decline_peak_to_trough_pct')
        if rev_decline:
            print(f"  Revenue Decline (2000-2002): {rev_decline:.1f}%")

        print(f"\nWARNING SIGNALS BEFORE CRASH:")
        for signal in comparison.get("validation_against_ai_bubble", {}).get(
            "warning_signals_that_preceded_crash", []
        ):
            print(f"  * {signal}")

        print(f"\nVALIDATION CONCLUSIONS:")
        findings = comparison.get("key_findings", [])
        for f in findings:
            print(f"  * {f}")

    print(f"\n{'='*70}")
    print("Output files:")
    print(f"  Data:   {PROCESSED_DATA_DIR}/")
    print(f"  Report: data_history/visualization/historical_validation_report.html")
    print(f"  Charts: data_history/visualization/output/")
    print(f"{'='*70}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="90s IT Bubble Historical Validation Pipeline"
    )
    parser.add_argument("--compile-only", action="store_true",
                       help="Only compile financial data")
    parser.add_argument("--skip-fetch", action="store_true",
                       help="Skip data fetching (use cached data)")
    parser.add_argument("--skip-viz", action="store_true",
                       help="Skip visualization generation")
    args = parser.parse_args()

    print("=" * 70)
    print("90s IT BUBBLE HISTORICAL VALIDATION")
    print("AI Funding Risk Early Warning System")
    print("=" * 70)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not check_dependencies():
        sys.exit(1)

    # Ensure directories exist
    for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MARKET_DATA_DIR, COMPILED_DATA_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

    if args.compile_only:
        run_compile_data()
        sys.exit(0)

    # Phase 1: Data Collection
    run_compile_data()

    if not args.skip_fetch:
        run_fetch_fred()
        run_fetch_yahoo()

    # Phase 2: Data Processing
    if not run_process_data():
        print("\n[ERROR] Data processing failed")
        sys.exit(1)

    # Phase 3: Visualization
    if not args.skip_viz:
        run_visualization()

    # Final Summary
    print_final_summary()

    print("\n[OK] Historical validation complete!")


if __name__ == "__main__":
    main()
