"""
Visualization Dashboard for 90s IT Bubble Historical Validation
Generates charts comparing 90s IT bubble with current AI funding risk
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import PROCESSED_DATA_DIR, COMPILED_DATA_DIR, PHASES

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("matplotlib not installed - charts will be skipped")


# Color scheme
COLORS = {
    "Cisco": "#049fd9",
    "Intel": "#0071c5",
    "Microsoft": "#00a4ef",
    "Oracle": "#f80000",
    "Sun Microsystems": "#8b5cf6",
    "Lucent": "#e67e22",
    # Risk levels
    "LOW": "#28a745",
    "MEDIUM": "#ffc107",
    "HIGH": "#dc3545",
    # Phases
    "buildup": "#a8d5e2",
    "peak": "#ffd700",
    "crash": "#ff6b6b",
    "recovery": "#90ee90",
}

OUTPUT_DIR = Path(__file__).parent / "output"


def load_json(filename: str, directory: Path = PROCESSED_DATA_DIR) -> Optional[Dict]:
    filepath = directory / filename
    if not filepath.exists():
        print(f"Not found: {filepath}")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_capex_trajectory(yearly_summary: Dict):
    """Plot aggregate capex and revenue trajectory (1995-2003)"""
    if not HAS_MATPLOTLIB:
        return

    years = sorted(yearly_summary.keys(), key=int)
    capex = [yearly_summary[y].get("total_capex_B", 0) for y in years]
    revenue = [yearly_summary[y].get("total_revenue_B", 0) for y in years]
    capex_to_cf = [yearly_summary[y].get("aggregate_capex_to_cashflow", 0) for y in years]
    years_int = [int(y) for y in years]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={"height_ratios": [3, 2]})

    # Add phase backgrounds
    for phase_name, phase in PHASES.items():
        start_year = int(phase["start"][:4])
        end_year = int(phase["end"][:4]) + 0.5
        for ax in [ax1, ax2]:
            ax.axvspan(start_year - 0.5, end_year, alpha=0.1,
                      color=COLORS.get(phase_name, "#cccccc"),
                      label=phase["label"] if ax == ax1 else None)

    # Top: Capex and Revenue bars
    bar_width = 0.35
    x_pos = range(len(years_int))

    bars1 = ax1.bar([x - bar_width/2 for x in x_pos], capex, bar_width,
                    label="Aggregate CapEx ($B)", color="#dc3545", alpha=0.8)
    bars2 = ax1.bar([x + bar_width/2 for x in x_pos], revenue, bar_width,
                    label="Aggregate Revenue ($B)", color="#28a745", alpha=0.8)

    ax1.set_ylabel("Billions USD", fontsize=12)
    ax1.set_title("90s IT Bubble: Aggregate CapEx vs Revenue (6 Companies)", fontsize=14, fontweight="bold")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(years_int)
    ax1.legend(loc="upper left")
    ax1.grid(axis="y", alpha=0.3)

    # Add value labels
    for bar in bars1:
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f"${bar.get_height():.1f}",
                ha="center", va="bottom", fontsize=8)

    # Bottom: Capex/CF ratio
    colors_cf = []
    for v in capex_to_cf:
        if v and v >= 0.90:
            colors_cf.append(COLORS["HIGH"])
        elif v and v >= 0.70:
            colors_cf.append(COLORS["MEDIUM"])
        else:
            colors_cf.append(COLORS["LOW"])

    ax2.bar(x_pos, [v if v else 0 for v in capex_to_cf], color=colors_cf, alpha=0.8)
    ax2.axhline(y=0.70, color="orange", linestyle="--", alpha=0.7, label="Warning (0.70)")
    ax2.axhline(y=0.90, color="red", linestyle="--", alpha=0.7, label="Danger (0.90)")
    ax2.set_ylabel("Ratio", fontsize=12)
    ax2.set_title("Aggregate CapEx / Operating Cash Flow Ratio", fontsize=12)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(years_int)
    ax2.legend(loc="upper left")
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    output_path = OUTPUT_DIR / "capex_trajectory_90s.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_company_comparison(yearly_summary: Dict):
    """Plot individual company capex-to-cashflow ratios over time"""
    if not HAS_MATPLOTLIB:
        return

    fig, ax = plt.subplots(figsize=(14, 8))

    years = sorted(yearly_summary.keys(), key=int)
    years_int = [int(y) for y in years]

    for company_name in ["Cisco", "Intel", "Microsoft", "Oracle", "Sun Microsystems", "Lucent"]:
        ratios = []
        for y in years:
            company_data = yearly_summary[y].get("companies", {}).get(company_name, {})
            ratio = company_data.get("capex_to_cashflow_ratio")
            ratios.append(ratio)

        # Filter out None values for plotting
        valid_years = [yr for yr, r in zip(years_int, ratios) if r is not None]
        valid_ratios = [r for r in ratios if r is not None]

        if valid_years:
            ax.plot(valid_years, valid_ratios, "o-",
                   label=company_name, color=COLORS.get(company_name, "#333"),
                   linewidth=2, markersize=6)

    ax.axhline(y=0.70, color="orange", linestyle="--", alpha=0.7, label="Warning")
    ax.axhline(y=0.90, color="red", linestyle="--", alpha=0.7, label="Danger")

    # Add crash marker
    ax.axvline(x=2000.2, color="gray", linestyle=":", alpha=0.5)
    ax.text(2000.3, ax.get_ylim()[1] * 0.95, "NASDAQ Peak\nMar 2000",
            fontsize=9, color="gray", va="top")

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("CapEx / Operating Cash Flow Ratio", fontsize=12)
    ax.set_title("90s IT Bubble: Company CapEx Intensity (CapEx/OCF)", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", ncol=2)
    ax.grid(alpha=0.3)
    ax.set_xlim(1994.5, 2004)

    plt.tight_layout()
    output_path = OUTPUT_DIR / "company_comparison_90s.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_risk_timeline(risk_timeline: List[Dict]):
    """Plot risk score evolution through the bubble"""
    if not HAS_MATPLOTLIB:
        return

    years = [item["year"] for item in risk_timeline]
    scores = [item["overall_risk_score"] for item in risk_timeline]
    consumption = [item["consumption_score"] for item in risk_timeline]
    capex_growth = [item["capex_growth_score"] for item in risk_timeline]
    supply = [item["supply_score"] for item in risk_timeline]

    fig, ax = plt.subplots(figsize=(12, 7))

    # Background zones
    ax.axhspan(0, 40, alpha=0.1, color="green", label="LOW Risk Zone")
    ax.axhspan(40, 65, alpha=0.1, color="orange", label="MEDIUM Risk Zone")
    ax.axhspan(65, 100, alpha=0.1, color="red", label="HIGH Risk Zone")

    # Plot scores
    ax.plot(years, scores, "o-", color="#333", linewidth=3, markersize=8, label="Overall Risk Score", zorder=5)
    ax.plot(years, consumption, "s--", color="#dc3545", linewidth=1.5, markersize=5,
            label="Consumption (CapEx Pressure)", alpha=0.7)
    ax.plot(years, capex_growth, "^--", color="#fd7e14", linewidth=1.5, markersize=5,
            label="CapEx Growth Rate", alpha=0.7)
    ax.plot(years, supply, "D--", color="#0d6efd", linewidth=1.5, markersize=5,
            label="Supply (Debt Level)", alpha=0.7)

    # Annotate key events
    ax.annotate("NASDAQ Peak\n(5,048)", xy=(2000, scores[years.index(2000)] if 2000 in years else 50),
                xytext=(2000.5, 85), fontsize=9,
                arrowprops=dict(arrowstyle="->", color="gray"),
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.5))

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Risk Score (0-100)", fontsize=12)
    ax.set_title("90s IT Bubble: Risk Score Evolution (1996-2003)", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_xlim(min(years) - 0.5, max(years) + 0.5)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    output_path = OUTPUT_DIR / "risk_timeline_90s.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_revenue_vs_capex_growth(yearly_summary: Dict):
    """Plot revenue growth vs capex growth to show divergence"""
    if not HAS_MATPLOTLIB:
        return

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    axes = axes.flatten()

    companies = ["Cisco", "Intel", "Microsoft", "Oracle", "Sun Microsystems", "Lucent"]

    for idx, company in enumerate(companies):
        ax = axes[idx]
        years_data = []

        for year_str in sorted(yearly_summary.keys(), key=int):
            company_data = yearly_summary[year_str].get("companies", {}).get(company, {})
            rev_growth = company_data.get("revenue_growth_yoy")
            capex_growth = company_data.get("capex_growth_yoy")
            if rev_growth is not None and capex_growth is not None:
                years_data.append({
                    "year": int(year_str),
                    "rev_growth": rev_growth,
                    "capex_growth": capex_growth,
                })

        if years_data:
            years = [d["year"] for d in years_data]
            rev = [d["rev_growth"] for d in years_data]
            capex = [d["capex_growth"] for d in years_data]

            ax.bar([y - 0.15 for y in years], rev, 0.3,
                   label="Revenue Growth %", color="#28a745", alpha=0.8)
            ax.bar([y + 0.15 for y in years], capex, 0.3,
                   label="CapEx Growth %", color="#dc3545", alpha=0.8)

            ax.axhline(y=0, color="black", linewidth=0.5)
            ax.axvline(x=2000.5, color="gray", linestyle=":", alpha=0.5)

        ax.set_title(company, fontsize=12, fontweight="bold", color=COLORS.get(company, "#333"))
        ax.set_ylabel("YoY Growth %")
        if idx == 0:
            ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    plt.suptitle("90s IT Bubble: Revenue vs CapEx Growth by Company",
                fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    output_path = OUTPUT_DIR / "revenue_vs_capex_growth_90s.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_market_cap_vs_fundamentals(yearly_summary: Dict):
    """Plot market cap vs fundamental metrics to show valuation disconnect"""
    if not HAS_MATPLOTLIB:
        return

    years = sorted(yearly_summary.keys(), key=int)
    years_int = [int(y) for y in years]

    market_caps = [yearly_summary[y].get("total_market_cap_peak_T", 0) for y in years]
    revenues = [yearly_summary[y].get("total_revenue_B", 0) for y in years]

    # Calculate price/sales ratio
    ps_ratios = []
    for mc, rev in zip(market_caps, revenues):
        if rev > 0 and mc > 0:
            ps_ratios.append(round(mc * 1000 / rev, 1))  # T to B conversion
        else:
            ps_ratios.append(0)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9))

    # Market Cap and Revenue
    ax1_twin = ax1.twinx()
    line1 = ax1.plot(years_int, market_caps, "o-", color="#8b5cf6", linewidth=2.5,
                     markersize=8, label="Total Peak Market Cap ($T)")
    line2 = ax1_twin.plot(years_int, revenues, "s-", color="#28a745", linewidth=2,
                          markersize=6, label="Total Revenue ($B)")

    ax1.set_ylabel("Market Cap ($T)", fontsize=12, color="#8b5cf6")
    ax1_twin.set_ylabel("Revenue ($B)", fontsize=12, color="#28a745")
    ax1.set_title("90s IT Bubble: Market Cap vs Revenue", fontsize=14, fontweight="bold")

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left")
    ax1.grid(alpha=0.3)

    # Price/Sales Ratio
    colors_ps = ["#dc3545" if ps > 15 else "#ffc107" if ps > 8 else "#28a745" for ps in ps_ratios]
    ax2.bar(years_int, ps_ratios, color=colors_ps, alpha=0.8)
    ax2.axhline(y=10, color="orange", linestyle="--", alpha=0.7, label="Elevated P/S (10x)")
    ax2.set_ylabel("Price/Sales Ratio", fontsize=12)
    ax2.set_title("Aggregate Price/Sales Ratio", fontsize=12)
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)

    # Add value labels
    for i, (year, ps) in enumerate(zip(years_int, ps_ratios)):
        ax2.text(year, ps + 0.3, f"{ps:.1f}x", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    output_path = OUTPUT_DIR / "market_cap_vs_fundamentals_90s.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def generate_html_report(yearly_summary: Dict, risk_timeline: List[Dict], comparison: Dict):
    """Generate HTML comparison report"""
    # Build company table rows
    company_rows = ""
    for year_str in sorted(yearly_summary.keys(), key=int):
        data = yearly_summary[year_str]
        capex_cf = data.get("aggregate_capex_to_cashflow")
        risk_item = next((r for r in risk_timeline if r["year"] == int(year_str)), {})
        risk_level = risk_item.get("risk_level", "N/A")
        risk_score = risk_item.get("overall_risk_score", "N/A")

        risk_color = COLORS.get(risk_level, "#333")

        company_rows += f"""
        <tr>
            <td><strong>{year_str}</strong></td>
            <td>${data.get('total_revenue_B', 0):.1f}B</td>
            <td>${data.get('total_capex_B', 0):.1f}B</td>
            <td>{f'{capex_cf:.3f}' if capex_cf else 'N/A'}</td>
            <td>${data.get('total_market_cap_peak_T', 0):.2f}T</td>
            <td style="color: {risk_color}; font-weight: bold;">{risk_level} ({risk_score})</td>
        </tr>
        """

    # Warning signals
    warnings_html = ""
    for signal in comparison.get("validation_against_ai_bubble", {}).get("warning_signals_that_preceded_crash", []):
        warnings_html += f"<li>{signal}</li>"

    similarities_html = ""
    for s in comparison.get("validation_against_ai_bubble", {}).get("similarities", []):
        similarities_html += f"<li>{s}</li>"

    differences_html = ""
    for d in comparison.get("validation_against_ai_bubble", {}).get("differences", []):
        differences_html += f"<li>{d}</li>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>90s IT Bubble - Historical Validation Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; border-bottom: 3px solid #8b5cf6; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background: #8b5cf6; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f8f9fa; }}
        .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
        .chart-grid img {{ width: 100%; border-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.15); }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; }}
        .danger {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; }}
        .success {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 10px 0; }}
        .comparison {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .comparison > div {{ padding: 15px; border-radius: 8px; }}
        .similarities {{ background: #e8f5e9; }}
        .differences {{ background: #e3f2fd; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>90s IT Bubble Historical Validation</h1>
        <p>Validating AI Funding Risk Early Warning System against the 1995-2003 IT/Telecom Bubble</p>

        <div class="card">
            <h2>Yearly Aggregate Metrics (6 IT Infrastructure Companies)</h2>
            <table>
                <tr>
                    <th>Year</th>
                    <th>Total Revenue</th>
                    <th>Total CapEx</th>
                    <th>CapEx/OCF</th>
                    <th>Peak Market Cap</th>
                    <th>Risk Level</th>
                </tr>
                {company_rows}
            </table>
        </div>

        <div class="card">
            <h2>Charts</h2>
            <div class="chart-grid">
                <div><img src="output/capex_trajectory_90s.png" alt="CapEx Trajectory"></div>
                <div><img src="output/risk_timeline_90s.png" alt="Risk Timeline"></div>
                <div><img src="output/company_comparison_90s.png" alt="Company Comparison"></div>
                <div><img src="output/market_cap_vs_fundamentals_90s.png" alt="Market Cap vs Fundamentals"></div>
            </div>
            <div style="margin-top: 15px;">
                <img src="output/revenue_vs_capex_growth_90s.png" alt="Revenue vs CapEx Growth" style="width: 100%;">
            </div>
        </div>

        <div class="card">
            <h2>Warning Signals That Preceded the 2000 Crash</h2>
            <div class="danger">
                <ul>{warnings_html}</ul>
            </div>
        </div>

        <div class="card">
            <h2>Comparison with Current AI Bubble</h2>
            <div class="comparison">
                <div class="similarities">
                    <h3>Similarities</h3>
                    <ul>{similarities_html}</ul>
                </div>
                <div class="differences">
                    <h3>Differences</h3>
                    <ul>{differences_html}</ul>
                </div>
            </div>
        </div>

        <div class="card">
            <p style="text-align: center; color: #999; font-size: 12px;">
                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
                AI Funding Risk Early Warning System - Historical Validation Module
            </p>
        </div>
    </div>
</body>
</html>"""

    output_path = OUTPUT_DIR.parent / "historical_validation_report.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {output_path}")


def main():
    """Generate all visualizations"""
    print("=" * 60)
    print("Historical Validation Dashboard Generator")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    yearly_summary = load_json("yearly_summary.json")
    risk_data = load_json("risk_timeline.json")
    comparison = load_json("bubble_comparison.json")

    if not yearly_summary:
        print("Error: yearly_summary.json not found. Run process_data_history.py first.")
        return

    risk_timeline = risk_data.get("timeline", []) if risk_data else []

    # Generate charts
    print("\nGenerating charts...")
    plot_capex_trajectory(yearly_summary)
    plot_company_comparison(yearly_summary)
    if risk_timeline:
        plot_risk_timeline(risk_timeline)
    plot_revenue_vs_capex_growth(yearly_summary)
    plot_market_cap_vs_fundamentals(yearly_summary)

    # Generate HTML report
    print("\nGenerating HTML report...")
    generate_html_report(yearly_summary, risk_timeline, comparison or {})

    print("\nVisualization complete!")


if __name__ == "__main__":
    main()
