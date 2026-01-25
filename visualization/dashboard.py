"""
Visualization Dashboard Module
Generates charts and reports for AI funding risk assessment
Extended to support the Early Warning System
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import PROCESSED_DATA_DIR, MARKET_DATA_DIR, RISK_LEVELS, ALERT_LEVELS

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Install with: pip install matplotlib")


class RiskDashboard:
    """Generates visualizations for risk assessment"""

    def __init__(self, output_dir: Path = None):
        self.processed_dir = PROCESSED_DATA_DIR
        self.output_dir = output_dir or (PROCESSED_DATA_DIR.parent / "visualization" / "output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Color scheme
        self.colors = {
            "LOW": "#28a745",
            "MEDIUM": "#ffc107",
            "HIGH": "#dc3545",
            "primary": "#007bff",
            "secondary": "#6c757d",
            "background": "#f8f9fa",
            # Alert level colors
            "GREEN": "#28a745",
            "YELLOW": "#ffc107",
            "ORANGE": "#fd7e14",
            "RED": "#dc3545",
        }

    def load_assessment(self) -> Optional[Dict]:
        """Load risk assessment data"""
        filepath = self.processed_dir / "risk_assessment.json"
        if not filepath.exists():
            print(f"Risk assessment not found: {filepath}")
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_scenarios(self) -> Optional[Dict]:
        """Load scenario projections"""
        filepath = self.processed_dir / "scenario_projections.json"
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_warning_dashboard(self) -> Optional[Dict]:
        """Load warning system dashboard data"""
        filepath = self.processed_dir / "warning_dashboard.json"
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_funding_health(self) -> Optional[Dict]:
        """Load funding health report"""
        filepath = self.processed_dir / "funding_health_report.json"
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_supply_demand(self) -> Optional[Dict]:
        """Load supply-demand analysis"""
        filepath = self.processed_dir / "supply_demand_analysis.json"
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_credit_market(self) -> Optional[Dict]:
        """Load credit market data"""
        filepath = MARKET_DATA_DIR / "credit_market_data.json"
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_consolidated_data(self) -> Optional[Dict]:
        """Load consolidated company data"""
        filepath = self.processed_dir / "consolidated_data.json"
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def plot_company_risk_comparison(self, assessment: Dict):
        """Create bar chart comparing company risk scores"""
        if not MATPLOTLIB_AVAILABLE:
            print("Skipping plot - matplotlib not available")
            return

        companies = assessment.get("company_profiles", [])
        if not companies:
            return

        # Sort by risk score
        companies_sorted = sorted(companies, key=lambda x: x["overall_risk_score"], reverse=True)

        names = [c["company_name"] for c in companies_sorted]
        scores = [c["overall_risk_score"] for c in companies_sorted]
        levels = [c["risk_level"] for c in companies_sorted]
        colors = [self.colors.get(level, self.colors["secondary"]) for level in levels]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(names, scores, color=colors)

        # Add risk level labels
        for bar, score, level in zip(bars, scores, levels):
            ax.text(score + 1, bar.get_y() + bar.get_height()/2,
                   f'{score:.0f} ({level})', va='center', fontsize=10)

        ax.set_xlabel('Risk Score (0-100)')
        ax.set_title('AI Company Funding Risk Comparison')
        ax.set_xlim(0, 100)

        # Add threshold lines
        ax.axvline(x=40, color=self.colors["LOW"], linestyle='--', alpha=0.5, label='Low threshold')
        ax.axvline(x=65, color=self.colors["HIGH"], linestyle='--', alpha=0.5, label='High threshold')

        ax.legend(loc='lower right')
        plt.tight_layout()

        output_path = self.output_dir / "company_risk_comparison.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path}")

    def plot_risk_breakdown(self, assessment: Dict):
        """Create pie chart showing risk category breakdown"""
        if not MATPLOTLIB_AVAILABLE:
            return

        consumption = assessment.get("consumption_score", 0)
        supply = assessment.get("supply_score", 0)
        efficiency = assessment.get("efficiency_score", 0)

        # Normalize scores to show contribution
        total = consumption + supply + efficiency
        if total == 0:
            return

        sizes = [consumption, supply, efficiency]
        labels = [
            f'Consumption\n({consumption:.0f})',
            f'Supply\n({supply:.0f})',
            f'Efficiency\n({efficiency:.0f})'
        ]
        colors = ['#ff6b6b', '#4dabf7', '#69db7c']

        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 11}
        )

        ax.set_title('Risk Score Contribution by Category', fontsize=14)

        # Add center text with overall score
        overall = assessment.get("overall_risk_score", 0)
        level = assessment.get("risk_level", "MEDIUM")
        ax.text(0, 0, f'{overall:.0f}\n{level}',
               ha='center', va='center', fontsize=20, fontweight='bold')

        plt.tight_layout()

        output_path = self.output_dir / "risk_breakdown.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path}")

    def plot_indicator_heatmap(self, assessment: Dict):
        """Create heatmap of indicators across companies"""
        if not MATPLOTLIB_AVAILABLE:
            return

        companies = assessment.get("company_profiles", [])
        if not companies:
            return

        # Extract indicators
        company_names = []
        indicator_names = set()
        indicator_data = {}

        for company in companies:
            name = company["company_name"]
            company_names.append(name)
            indicator_data[name] = {}

            for indicator in company.get("indicators", []):
                ind_name = indicator["name"]
                indicator_names.add(ind_name)
                indicator_data[name][ind_name] = indicator["score"]

        indicator_names = sorted(list(indicator_names))

        # Create matrix
        matrix = []
        for company in company_names:
            row = [indicator_data[company].get(ind, 50) for ind in indicator_names]
            matrix.append(row)

        fig, ax = plt.subplots(figsize=(12, 8))

        # Create heatmap
        im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=100)

        # Labels
        ax.set_xticks(range(len(indicator_names)))
        ax.set_xticklabels(indicator_names, rotation=45, ha='right', fontsize=9)
        ax.set_yticks(range(len(company_names)))
        ax.set_yticklabels(company_names, fontsize=10)

        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel('Risk Score (0=Low, 100=High)', rotation=-90, va="bottom")

        # Add values to cells
        for i in range(len(company_names)):
            for j in range(len(indicator_names)):
                value = matrix[i][j]
                color = 'white' if value > 50 else 'black'
                ax.text(j, i, f'{value:.0f}', ha='center', va='center', color=color, fontsize=9)

        ax.set_title('Risk Indicator Heatmap by Company', fontsize=14)
        plt.tight_layout()

        output_path = self.output_dir / "indicator_heatmap.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path}")

    def plot_scenario_projections(self, scenarios: Dict):
        """Plot scenario comparison over time"""
        if not MATPLOTLIB_AVAILABLE:
            return

        scenario_list = scenarios.get("scenarios", [])
        if not scenario_list:
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Plot 1: Capex over time
        ax1 = axes[0, 0]
        for scenario in scenario_list:
            years = [p["year"] for p in scenario["projections"]]
            capex = [p["capex"] for p in scenario["projections"]]
            ax1.plot(years, capex, marker='o', label=scenario["scenario_name"])
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Capex ($B)')
        ax1.set_title('Projected Capital Expenditure')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Capex to Cashflow ratio
        ax2 = axes[0, 1]
        for scenario in scenario_list:
            years = [p["year"] for p in scenario["projections"]]
            ratio = [p["capex_to_cashflow_ratio"] for p in scenario["projections"]]
            ax2.plot(years, ratio, marker='o', label=scenario["scenario_name"])
        ax2.axhline(y=0.70, color='green', linestyle='--', alpha=0.5, label='Normal threshold')
        ax2.axhline(y=0.90, color='red', linestyle='--', alpha=0.5, label='Warning threshold')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Capex / Cashflow Ratio')
        ax2.set_title('Funding Sustainability Ratio')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Plot 3: Revenue vs Capex growth
        ax3 = axes[1, 0]
        scenario_names = [s["scenario_name"] for s in scenario_list]
        capex_growth = [s["parameters"]["capex_growth_rate"] * 100 for s in scenario_list]
        revenue_growth = [s["parameters"]["revenue_growth_rate"] * 100 for s in scenario_list]

        x = range(len(scenario_names))
        width = 0.35
        ax3.bar([i - width/2 for i in x], capex_growth, width, label='Capex Growth', color='#ff6b6b')
        ax3.bar([i + width/2 for i in x], revenue_growth, width, label='Revenue Growth', color='#69db7c')
        ax3.set_xlabel('Scenario')
        ax3.set_ylabel('Annual Growth Rate (%)')
        ax3.set_title('Scenario Growth Assumptions')
        ax3.set_xticks(x)
        ax3.set_xticklabels(scenario_names, rotation=15)
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')

        # Plot 4: Risk level progression
        ax4 = axes[1, 1]
        risk_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

        for scenario in scenario_list:
            years = [p["year"] for p in scenario["projections"]]
            risks = [risk_map.get(p["risk_level"], 2) for p in scenario["projections"]]
            ax4.plot(years, risks, marker='s', label=scenario["scenario_name"], linewidth=2)

        ax4.set_yticks([1, 2, 3])
        ax4.set_yticklabels(['LOW', 'MEDIUM', 'HIGH'])
        ax4.set_xlabel('Year')
        ax4.set_ylabel('Risk Level')
        ax4.set_title('Projected Risk Level Over Time')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # Color bands for risk levels
        ax4.axhspan(0.5, 1.5, color=self.colors["LOW"], alpha=0.1)
        ax4.axhspan(1.5, 2.5, color=self.colors["MEDIUM"], alpha=0.1)
        ax4.axhspan(2.5, 3.5, color=self.colors["HIGH"], alpha=0.1)

        plt.tight_layout()

        output_path = self.output_dir / "scenario_projections.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path}")

    def generate_html_report(self, assessment: Dict, scenarios: Dict = None) -> str:
        """Generate HTML report with embedded charts"""
        html_parts = []

        # Header
        html_parts.append("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Funding Risk Assessment Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white;
                    padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #1a1a1a; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #333; margin-top: 30px; }
        .risk-badge { display: inline-block; padding: 5px 15px; border-radius: 20px;
                     font-weight: bold; color: white; }
        .risk-LOW { background: #28a745; }
        .risk-MEDIUM { background: #ffc107; color: #1a1a1a; }
        .risk-HIGH { background: #dc3545; }
        .score-box { background: #f8f9fa; padding: 20px; border-radius: 8px;
                    margin: 20px 0; text-align: center; }
        .score-value { font-size: 48px; font-weight: bold; color: #1a1a1a; }
        .score-label { font-size: 14px; color: #666; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .card { background: #f8f9fa; padding: 15px; border-radius: 8px; }
        .card h3 { margin-top: 0; color: #333; font-size: 16px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
        .finding { padding: 10px; margin: 5px 0; background: #fff3cd;
                  border-left: 4px solid #ffc107; border-radius: 4px; }
        .recommendation { padding: 10px; margin: 5px 0; background: #d4edda;
                         border-left: 4px solid #28a745; border-radius: 4px; }
        .chart-container { margin: 20px 0; text-align: center; }
        .chart-container img { max-width: 100%; height: auto; border-radius: 8px;
                              box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;
                 color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
""")

        # Title and date
        date_str = assessment.get("assessment_date", datetime.now().isoformat())[:10]
        overall_score = assessment.get("overall_risk_score", 0)
        risk_level = assessment.get("risk_level", "MEDIUM")

        html_parts.append(f"""
        <h1>AI Funding Risk Assessment Report</h1>
        <p>Generated: {date_str}</p>

        <div class="score-box">
            <div class="score-value">{overall_score:.0f}</div>
            <div class="score-label">Overall Risk Score (0-100)</div>
            <div style="margin-top: 10px;">
                <span class="risk-badge risk-{risk_level}">{risk_level} RISK</span>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Consumption Score</h3>
                <div style="font-size: 24px; font-weight: bold;">{assessment.get('consumption_score', 0):.0f}</div>
                <div style="color: #666; font-size: 12px;">Capital expenditure pressure</div>
            </div>
            <div class="card">
                <h3>Supply Score</h3>
                <div style="font-size: 24px; font-weight: bold;">{assessment.get('supply_score', 0):.0f}</div>
                <div style="color: #666; font-size: 12px;">Funding availability</div>
            </div>
            <div class="card">
                <h3>Efficiency Score</h3>
                <div style="font-size: 24px; font-weight: bold;">{assessment.get('efficiency_score', 0):.0f}</div>
                <div style="color: #666; font-size: 12px;">Return on investment</div>
            </div>
        </div>
""")

        # Company profiles table
        html_parts.append("""
        <h2>Company Risk Profiles</h2>
        <table>
            <thead>
                <tr>
                    <th>Company</th>
                    <th>Ticker</th>
                    <th>Risk Score</th>
                    <th>Risk Level</th>
                    <th>Summary</th>
                </tr>
            </thead>
            <tbody>
""")

        for company in sorted(assessment.get("company_profiles", []),
                             key=lambda x: x["overall_risk_score"], reverse=True):
            html_parts.append(f"""
                <tr>
                    <td>{company['company_name']}</td>
                    <td>{company['ticker']}</td>
                    <td>{company['overall_risk_score']:.0f}</td>
                    <td><span class="risk-badge risk-{company['risk_level']}">{company['risk_level']}</span></td>
                    <td>{company['summary']}</td>
                </tr>
""")

        html_parts.append("""
            </tbody>
        </table>
""")

        # Key findings
        html_parts.append("""
        <h2>Key Findings</h2>
""")
        for finding in assessment.get("key_findings", []):
            html_parts.append(f'        <div class="finding">{finding}</div>\n')

        # Recommendations
        html_parts.append("""
        <h2>Recommendations</h2>
""")
        for rec in assessment.get("recommendations", []):
            html_parts.append(f'        <div class="recommendation">{rec}</div>\n')

        # Charts section
        html_parts.append("""
        <h2>Visualizations</h2>
""")

        # Check for chart images
        chart_files = [
            ("company_risk_comparison.png", "Company Risk Comparison"),
            ("risk_breakdown.png", "Risk Category Breakdown"),
            ("indicator_heatmap.png", "Indicator Heatmap"),
            ("scenario_projections.png", "Scenario Projections"),
        ]

        for filename, title in chart_files:
            chart_path = self.output_dir / filename
            if chart_path.exists():
                html_parts.append(f"""
        <div class="chart-container">
            <h3>{title}</h3>
            <img src="{filename}" alt="{title}">
        </div>
""")

        # Footer
        html_parts.append("""
        <div class="footer">
            <p>This report is generated automatically based on publicly available financial data.
            It is intended for informational purposes only and should not be considered financial advice.</p>
            <p>Data sources: SEC EDGAR, FRED, Yahoo Finance</p>
        </div>
    </div>
</body>
</html>
""")

        html_content = "".join(html_parts)

        # Save HTML report
        output_path = self.output_dir / "risk_report.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Saved: {output_path}")
        return html_content

    def plot_warning_signals(self, warning_data: Dict):
        """Plot warning signal status overview"""
        if not MATPLOTLIB_AVAILABLE:
            return

        signals = warning_data.get("active_signals", [])
        if not signals:
            return

        # Categorize signals
        categories = {"credit": [], "equity": [], "company": []}
        for signal in signals:
            cat = signal.get("category", "other")
            if cat in categories:
                categories[cat].append(signal)

        # Create subplot for each category
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        level_colors = {
            "GREEN": self.colors["GREEN"],
            "YELLOW": self.colors["YELLOW"],
            "ORANGE": self.colors["ORANGE"],
            "RED": self.colors["RED"],
        }

        for ax, (category, cat_signals) in zip(axes, categories.items()):
            if not cat_signals:
                ax.text(0.5, 0.5, "No signals", ha='center', va='center', fontsize=12)
                ax.set_title(f'{category.upper()} Signals')
                ax.axis('off')
                continue

            names = [s["signal_name"][:20] for s in cat_signals]
            values = [s["current_value"] for s in cat_signals]
            colors = [level_colors.get(s["alert_level"], self.colors["secondary"]) for s in cat_signals]

            bars = ax.barh(names, values, color=colors)

            # Add threshold lines if available
            for i, signal in enumerate(cat_signals):
                if signal.get("threshold"):
                    ax.axvline(x=signal["threshold"], color='red', linestyle='--', alpha=0.5)

            ax.set_title(f'{category.upper()} Signals')
            ax.set_xlabel('Value')

        plt.tight_layout()

        output_path = self.output_dir / "warning_signals.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path}")

    def plot_supply_demand_projection(self, supply_demand: Dict):
        """Plot supply-demand balance projection with historical data"""
        if not MATPLOTLIB_AVAILABLE:
            return

        historical = supply_demand.get("historical", [])
        projections = supply_demand.get("projections", [])
        if not projections:
            return

        # Combine historical and projection data
        hist_years = [h["year"] for h in historical]
        hist_demand = [h["demand_B"] for h in historical]
        hist_supply = [h["supply_B"] for h in historical]
        hist_gap = [h["gap_B"] for h in historical]

        proj_years = [p["year"] for p in projections]
        proj_demand = [p["demand_B"] for p in projections]
        proj_supply = [p["supply_B"] for p in projections]
        proj_gap = [p["gap_B"] for p in projections]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Plot 1: Supply vs Demand
        # Historical data (solid lines with markers)
        if hist_years:
            ax1.plot(hist_years, hist_demand, 'r-o', label='Capital Demand (Historical)', linewidth=2, markersize=8)
            ax1.plot(hist_years, hist_supply, 'g-o', label='Funding Supply (Historical)', linewidth=2, markersize=8)

        # Projection data (dashed lines with different markers)
        ax1.plot(proj_years, proj_demand, 'r--s', label='Capital Demand (Projected)', linewidth=2, markersize=6, alpha=0.7)
        ax1.plot(proj_years, proj_supply, 'g--s', label='Funding Supply (Projected)', linewidth=2, markersize=6, alpha=0.7)

        # Add vertical line to separate historical from projected
        if hist_years and proj_years:
            boundary = (hist_years[-1] + proj_years[0]) / 2
            ax1.axvline(x=boundary, color='gray', linestyle=':', linewidth=2, alpha=0.7)
            ax1.text(boundary, ax1.get_ylim()[1] * 0.95, '  Projected →', fontsize=10, color='gray', va='top')

        # Fill between for projection
        ax1.fill_between(proj_years, proj_demand, proj_supply, alpha=0.2,
                         color='green' if proj_supply[-1] > proj_demand[-1] else 'red')

        ax1.set_xlabel('Year', fontsize=12)
        ax1.set_ylabel('Amount ($B)', fontsize=12)
        ax1.set_title('AI Funding Supply vs Demand: Historical & Projection', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left', fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Gap analysis
        all_years = hist_years + proj_years
        all_gap = hist_gap + proj_gap

        # Different colors for historical vs projected
        colors = []
        for i, g in enumerate(all_gap):
            if i < len(hist_years):
                colors.append('#2ecc71' if g > 0 else '#e74c3c')  # Solid colors for historical
            else:
                colors.append('#27ae60' if g > 0 else '#c0392b')  # Slightly different for projected

        # Different edge styles
        edge_colors = ['black' if i < len(hist_years) else 'gray' for i in range(len(all_gap))]
        line_styles = ['solid' if i < len(hist_years) else 'dashed' for i in range(len(all_gap))]

        bars = ax2.bar(all_years, all_gap, color=colors, alpha=0.7, edgecolor=edge_colors, linewidth=1.5)

        # Add hatching for projected bars
        for i, bar in enumerate(bars):
            if i >= len(hist_years):
                bar.set_hatch('//')

        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

        # Add vertical line separator
        if hist_years and proj_years:
            ax2.axvline(x=boundary, color='gray', linestyle=':', linewidth=2, alpha=0.7)

        ax2.set_xlabel('Year', fontsize=12)
        ax2.set_ylabel('Gap ($B)', fontsize=12)
        ax2.set_title('Funding Gap: Historical & Projected (Positive = Surplus, Negative = Deficit)', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

        # Add legend for bar chart
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2ecc71', edgecolor='black', label='Historical Surplus'),
            Patch(facecolor='#27ae60', edgecolor='gray', hatch='//', label='Projected Surplus'),
        ]
        ax2.legend(handles=legend_elements, loc='upper left', fontsize=10)

        plt.tight_layout()

        output_path = self.output_dir / "supply_demand_projection.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path}")

    def plot_funding_health_gauge(self, funding_health: Dict):
        """Plot funding health as a gauge chart"""
        if not MATPLOTLIB_AVAILABLE:
            return

        overall = funding_health.get("overall_assessment", {})
        score = overall.get("overall_score", 50)
        health_status = overall.get("health_status", "neutral")

        fig, ax = plt.subplots(figsize=(8, 6), subplot_kw={'projection': 'polar'})

        # Create gauge
        theta = score / 100 * 3.14159  # Convert to radians (half circle)

        # Background arc
        theta_bg = [i / 100 * 3.14159 for i in range(101)]
        r_bg = [1] * 101
        ax.plot(theta_bg, r_bg, color='lightgray', linewidth=30, solid_capstyle='round')

        # Colored arc based on score
        if score >= 70:
            color = self.colors["GREEN"]
        elif score >= 50:
            color = self.colors["YELLOW"]
        else:
            color = self.colors["RED"]

        theta_fg = [i / 100 * 3.14159 for i in range(int(score) + 1)]
        r_fg = [1] * (int(score) + 1)
        ax.plot(theta_fg, r_fg, color=color, linewidth=30, solid_capstyle='round')

        # Add needle
        ax.annotate('', xy=(theta, 0.7), xytext=(0, 0),
                   arrowprops=dict(arrowstyle='->', color='black', lw=2))

        # Add score text
        ax.text(3.14159/2, 0.3, f'{score:.0f}', ha='center', va='center',
               fontsize=36, fontweight='bold')
        ax.text(3.14159/2, 0.1, health_status.upper(), ha='center', va='center',
               fontsize=14, color=color)

        # Configure axes
        ax.set_theta_zero_location('W')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 1.2)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['polar'].set_visible(False)

        plt.title('Funding Environment Health Score', fontsize=14, pad=20)
        plt.tight_layout()

        output_path = self.output_dir / "funding_health_gauge.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path}")

    def plot_credit_market_trends(self, credit_data: Dict):
        """Plot credit market indicator trends"""
        if not MATPLOTLIB_AVAILABLE:
            return

        credit_market = credit_data.get("credit_market", {})
        if not credit_market:
            return

        # Select key indicators to plot
        key_series = ["BAMLH0A0HYM2", "BAMLC0A0CM", "T10Y2Y", "DFF"]
        available_series = [s for s in key_series if s in credit_market]

        if not available_series:
            return

        n_series = len(available_series)
        fig, axes = plt.subplots(n_series, 1, figsize=(12, 3 * n_series))
        if n_series == 1:
            axes = [axes]

        for ax, series_id in zip(axes, available_series):
            series_data = credit_market[series_id]
            observations = series_data.get("observations", [])

            if not observations:
                continue

            dates = [obs["date"] for obs in observations]
            values = [obs["value"] for obs in observations]

            ax.plot(dates, values, 'b-', linewidth=1.5)
            ax.fill_between(dates, values, alpha=0.3)

            # Only show every nth label to avoid crowding
            n_labels = min(10, len(dates))
            step = max(1, len(dates) // n_labels)
            ax.set_xticks(dates[::step])
            ax.tick_params(axis='x', rotation=45)

            description = series_data.get("description", series_id)
            latest = series_data.get("latest", {})
            ax.set_title(f'{description} (Latest: {latest.get("value", "N/A"):.3f})')
            ax.grid(True, alpha=0.3)

        plt.tight_layout()

        output_path = self.output_dir / "credit_market_trends.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path}")

    def generate_warning_html_report(self, warning_data: Dict, funding_health: Dict = None,
                                     supply_demand: Dict = None) -> str:
        """Generate HTML report for warning system"""
        html_parts = []

        # Header with warning-specific styles
        html_parts.append("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Funding Risk Early Warning Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               margin: 0; padding: 20px; background: #1a1a2e; color: #eee; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #fff; border-bottom: 2px solid #4dabf7; padding-bottom: 10px; }
        h2 { color: #4dabf7; margin-top: 30px; }
        .alert-panel { padding: 20px; border-radius: 12px; margin: 20px 0;
                      display: flex; align-items: center; gap: 20px; }
        .alert-GREEN { background: linear-gradient(135deg, #28a745, #20c997); }
        .alert-YELLOW { background: linear-gradient(135deg, #ffc107, #fd7e14); color: #1a1a1a; }
        .alert-ORANGE { background: linear-gradient(135deg, #fd7e14, #dc3545); }
        .alert-RED { background: linear-gradient(135deg, #dc3545, #c92a2a); }
        .alert-icon { font-size: 48px; }
        .alert-content { flex: 1; }
        .alert-level { font-size: 24px; font-weight: bold; }
        .alert-description { opacity: 0.9; margin-top: 5px; }
        .score-display { font-size: 36px; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: #16213e; padding: 20px; border-radius: 12px;
               border: 1px solid #0f3460; }
        .card h3 { margin-top: 0; color: #4dabf7; font-size: 16px; }
        .metric { display: flex; justify-content: space-between; padding: 8px 0;
                 border-bottom: 1px solid #0f3460; }
        .metric-name { color: #aaa; }
        .metric-value { font-weight: bold; }
        .signal-list { margin: 0; padding: 0; list-style: none; }
        .signal-item { padding: 10px; margin: 5px 0; border-radius: 8px;
                      background: #0f3460; display: flex; justify-content: space-between;
                      align-items: center; }
        .signal-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px;
                       font-weight: bold; }
        .badge-GREEN { background: #28a745; }
        .badge-YELLOW { background: #ffc107; color: #1a1a1a; }
        .badge-ORANGE { background: #fd7e14; }
        .badge-RED { background: #dc3545; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #0f3460; }
        th { background: #0f3460; color: #4dabf7; font-weight: 600; }
        tr:hover { background: #1f4068; }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .chart-container { margin: 20px 0; background: #16213e; padding: 20px;
                          border-radius: 12px; }
        .chart-container img { max-width: 100%; height: auto; border-radius: 8px; }
        .recommendation { padding: 12px; margin: 8px 0; background: #1f4068;
                         border-left: 4px solid #4dabf7; border-radius: 4px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #0f3460;
                 color: #666; font-size: 12px; text-align: center; }
        .status-row { display: flex; gap: 10px; flex-wrap: wrap; margin: 15px 0; }
        .status-item { background: #0f3460; padding: 8px 16px; border-radius: 8px;
                      display: flex; align-items: center; gap: 8px; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; }
    </style>
</head>
<body>
    <div class="container">
""")

        # Alert level and score
        alert_level = warning_data.get("overall_status", "GREEN")
        # Use overall_score (the actual field name in warning_dashboard.json)
        composite_score = warning_data.get("overall_score", 0)
        level_info = ALERT_LEVELS.get(alert_level, {})

        alert_icons = {"GREEN": "✓", "YELLOW": "⚠", "ORANGE": "⚡", "RED": "🚨"}

        html_parts.append(f"""
        <h1>AI Funding Risk Early Warning Dashboard</h1>
        <p style="color: #aaa;">Generated: {warning_data.get('timestamp', datetime.now().isoformat())[:19]}</p>

        <div class="alert-panel alert-{alert_level}">
            <div class="alert-icon">{alert_icons.get(alert_level, '●')}</div>
            <div class="alert-content">
                <div class="alert-level">{level_info.get('label', alert_level)} - Alert Level</div>
                <div class="alert-description">{level_info.get('description', '')}</div>
            </div>
            <div class="score-display">{composite_score:.0f}/100</div>
        </div>
""")

        # Key metrics grid
        html_parts.append("""
        <div class="grid">
""")

        # Signal summary by category (from signals_summary.by_category)
        signals_summary = warning_data.get("signals_summary", {})
        by_category = signals_summary.get("by_category", {})
        by_severity = signals_summary.get("by_severity", {})

        # Show overall health score card
        health_score_color = "#28a745" if composite_score >= 70 else ("#ffc107" if composite_score >= 50 else "#dc3545")
        html_parts.append(f"""
            <div class="card">
                <h3>OVERALL HEALTH</h3>
                <div style="font-size: 36px; font-weight: bold; color: {health_score_color};">{composite_score:.0f}</div>
                <div style="color: #aaa; font-size: 12px;">Health Score (0-100)</div>
            </div>
""")

        # Show signal counts by severity
        red_count = by_severity.get("RED", 0)
        orange_count = by_severity.get("ORANGE", 0)
        yellow_count = by_severity.get("YELLOW", 0)
        green_count = by_severity.get("GREEN", 0)

        html_parts.append(f"""
            <div class="card">
                <h3>SIGNAL STATUS</h3>
                <div style="display: flex; gap: 10px; justify-content: center; margin: 10px 0;">
                    <span style="color: #dc3545;">RED: {red_count}</span>
                    <span style="color: #fd7e14;">ORANGE: {orange_count}</span>
                    <span style="color: #ffc107;">YELLOW: {yellow_count}</span>
                    <span style="color: #28a745;">GREEN: {green_count}</span>
                </div>
                <div style="color: #aaa; font-size: 12px;">Warning Signals by Severity</div>
            </div>
""")

        # Add funding health if available
        if funding_health:
            overall = funding_health.get("overall_assessment", {})
            health_score = overall.get("overall_score", 50)
            health_status = overall.get("health_status", "neutral")
            status_color = "#28a745" if health_score >= 70 else ("#ffc107" if health_score >= 50 else "#dc3545")
            html_parts.append(f"""
            <div class="card">
                <h3>FUNDING HEALTH</h3>
                <div style="font-size: 36px; font-weight: bold; color: {status_color};">{health_score:.0f}</div>
                <div style="color: #aaa; font-size: 12px;">{health_status.upper()}</div>
            </div>
""")

        # Add supply-demand balance if available
        if supply_demand:
            balance = supply_demand.get("balance_analysis", {})
            balance_ratio = balance.get("balance_ratio", 1.0)
            gap = balance.get("gap_annual_B", 0)
            status_color = "#28a745" if balance_ratio >= 1.0 else "#dc3545"
            html_parts.append(f"""
            <div class="card">
                <h3>SUPPLY/DEMAND BALANCE</h3>
                <div style="font-size: 36px; font-weight: bold; color: {status_color};">{balance_ratio:.2f}x</div>
                <div style="color: #aaa; font-size: 12px;">Annual Gap: ${gap:+.0f}B</div>
            </div>
""")

        html_parts.append("""
        </div>
""")

        # Active signals section
        signals = warning_data.get("active_signals", [])
        elevated_signals = [s for s in signals if s.get("alert_level") not in ["GREEN"]]

        if elevated_signals:
            html_parts.append("""
        <h2>Elevated Warning Signals</h2>
        <table>
            <thead>
                <tr>
                    <th>Signal</th>
                    <th>Category</th>
                    <th>Current Value</th>
                    <th>Threshold</th>
                    <th>Alert Level</th>
                </tr>
            </thead>
            <tbody>
""")
            for signal in sorted(elevated_signals, key=lambda x: {"RED": 0, "ORANGE": 1, "YELLOW": 2}.get(x.get("alert_level"), 3)):
                html_parts.append(f"""
                <tr>
                    <td>{signal.get('signal_name', 'Unknown')}</td>
                    <td>{signal.get('category', 'N/A').upper()}</td>
                    <td>{signal.get('current_value', 'N/A'):.2f if isinstance(signal.get('current_value'), (int, float)) else signal.get('current_value', 'N/A')}</td>
                    <td>{signal.get('threshold', 'N/A'):.2f if isinstance(signal.get('threshold'), (int, float)) else signal.get('threshold', 'N/A')}</td>
                    <td><span class="signal-badge badge-{signal.get('alert_level', 'GREEN')}">{signal.get('alert_level', 'GREEN')}</span></td>
                </tr>
""")
            html_parts.append("""
            </tbody>
        </table>
""")

        # Supply-Demand Projections (with historical data)
        if supply_demand:
            historical = supply_demand.get("historical", [])
            projections = supply_demand.get("projections", [])

            if historical or projections:
                html_parts.append("""
        <h2>Supply-Demand Historical & Projection</h2>
        <p style="color: #aaa; font-size: 0.9em; margin-bottom: 10px;">
            <em>Historical data shows actual YoY growth rates. Projected data uses modeled growth rates.</em>
        </p>
        <table>
            <thead>
                <tr>
                    <th>Year</th>
                    <th>Demand ($B)</th>
                    <th>Supply ($B)</th>
                    <th>Gap ($B)</th>
                    <th>Status</th>
                    <th>Risk Level</th>
                </tr>
            </thead>
            <tbody>
""")
                # Helper function to format value with growth rate
                def format_with_growth(value, growth_pct, is_historical):
                    if growth_pct is not None:
                        growth_str = f"+{growth_pct:.1f}%" if growth_pct >= 0 else f"{growth_pct:.1f}%"
                        label = "actual" if is_historical else "proj"
                        # Use cyan color for historical, gray for projected
                        color = "#4dabf7" if is_historical else "#888"
                        return f"${value:.0f} <span style='color:{color};font-size:0.85em;'>({growth_str} {label})</span>"
                    return f"${value:.0f}"

                # Display historical data first
                for hist in historical:
                    gap_class = "positive" if hist.get("gap_B", 0) > 0 else "negative"
                    demand_str = format_with_growth(hist.get('demand_B', 0), hist.get('demand_growth_pct'), True)
                    supply_str = format_with_growth(hist.get('supply_B', 0), hist.get('supply_growth_pct'), True)
                    html_parts.append(f"""
                <tr style="background-color: #1a3a5c;">
                    <td><strong>{hist.get('year', 'N/A')}</strong> <span style="color:#4dabf7;font-size:0.8em;">(Historical)</span></td>
                    <td>{demand_str}</td>
                    <td>{supply_str}</td>
                    <td class="{gap_class}">${hist.get('gap_B', 0):+.0f}</td>
                    <td>{hist.get('status', 'N/A').upper()}</td>
                    <td><span class="signal-badge badge-{'GREEN' if hist.get('risk_level') == 'LOW' else ('YELLOW' if hist.get('risk_level') == 'MEDIUM' else 'RED')}">{hist.get('risk_level', 'N/A')}</span></td>
                </tr>
""")

                # Add separator row between historical and projected
                if historical and projections:
                    html_parts.append("""
                <tr style="background-color: #0f3460; border-top: 2px solid #4dabf7;">
                    <td colspan="6" style="text-align: center; font-weight: bold; color: #4dabf7; padding: 8px;">
                        ▼ Projected Data ▼
                    </td>
                </tr>
""")

                # Display projected data
                for proj in projections:
                    gap_class = "positive" if proj.get("gap_B", 0) > 0 else "negative"
                    demand_str = format_with_growth(proj.get('demand_B', 0), proj.get('demand_growth_pct'), False)
                    supply_str = format_with_growth(proj.get('supply_B', 0), proj.get('supply_growth_pct'), False)
                    html_parts.append(f"""
                <tr>
                    <td>{proj.get('year', 'N/A')}</td>
                    <td>{demand_str}</td>
                    <td>{supply_str}</td>
                    <td class="{gap_class}">${proj.get('gap_B', 0):+.0f}</td>
                    <td>{proj.get('status', 'N/A').upper()}</td>
                    <td><span class="signal-badge badge-{'GREEN' if proj.get('risk_level') == 'LOW' else ('YELLOW' if proj.get('risk_level') == 'MEDIUM' else 'RED')}">{proj.get('risk_level', 'N/A')}</span></td>
                </tr>
""")
                html_parts.append("""
            </tbody>
        </table>
""")

        # Recommendations
        if funding_health:
            recommendations = funding_health.get("overall_assessment", {}).get("recommendations", [])
            if recommendations:
                html_parts.append("""
        <h2>Recommendations</h2>
""")
                for rec in recommendations:
                    html_parts.append(f'        <div class="recommendation">{rec}</div>\n')

        # Charts section
        html_parts.append("""
        <h2>Visualizations</h2>
""")

        # Check for warning system chart images
        warning_charts = [
            ("warning_signals.png", "Warning Signal Status"),
            ("supply_demand_projection.png", "Supply-Demand Balance Projection"),
            ("funding_health_gauge.png", "Funding Health Score"),
            ("credit_market_trends.png", "Credit Market Trends"),
        ]

        for filename, title in warning_charts:
            chart_path = self.output_dir / filename
            if chart_path.exists():
                html_parts.append(f"""
        <div class="chart-container">
            <h3>{title}</h3>
            <img src="{filename}" alt="{title}">
        </div>
""")

        # Footer
        html_parts.append("""
        <div class="footer">
            <p>AI Funding Risk Early Warning System - Automated Analysis Report</p>
            <p>Data sources: SEC EDGAR, FRED (Federal Reserve), Yahoo Finance</p>
            <p>This report is for informational purposes only and should not be considered financial advice.</p>
        </div>
    </div>
</body>
</html>
""")

        html_content = "".join(html_parts)

        # Save HTML report
        output_path = self.output_dir / "warning_dashboard.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Saved: {output_path}")
        return html_content

    def generate_company_historical_html(self, consolidated_data: Dict) -> str:
        """Generate company historical analysis HTML with category-based charts for OCF breakdown and funding sources"""
        companies_data = consolidated_data.get("companies", {})

        # Company color mapping
        company_colors = {
            "Amazon": "#ff9900",
            "Microsoft": "#00a4ef",
            "Alphabet": "#4285f4",
            "Meta": "#0866ff",
            "Oracle": "#f80000",
            "Nvidia": "#76b900"
        }

        # Build JavaScript data object from consolidated data
        js_data_parts = []
        for company_name, company_info in companies_data.items():
            yahoo_hist = company_info.get("yahoo_historical", {})
            color = company_colors.get(company_name, "#888888")

            # Build capex and ocf by year
            capex_by_year = {}
            ocf_by_year = {}
            for item in yahoo_hist.get("capex", []):
                capex_by_year[item["year"]] = item["value"]
            for item in yahoo_hist.get("ocf", []):
                ocf_by_year[item["year"]] = item["value"]

            # Build OCF breakdown by year
            ocf_breakdown_by_year = {}
            for item in yahoo_hist.get("ocf_breakdown", []):
                year = item["year"]
                ocf_breakdown_by_year[year] = {
                    "netIncome": item.get("net_income", 0),
                    "depreciation": item.get("depreciation", 0),
                    "stockComp": item.get("stock_compensation", 0),
                    "workingCapital": item.get("working_capital", 0),
                    "deferredTax": item.get("deferred_tax", 0),
                    "other": item.get("other", 0)
                }

            # Build funding sources by year
            funding_by_year = {}
            for item in yahoo_hist.get("funding_sources", []):
                year = item["year"]
                funding_by_year[year] = {
                    "capex": item.get("capex", 0),
                    "ocf": item.get("ocf", 0),
                    "fcf": item.get("free_cashflow", 0),
                    "debtIssue": item.get("debt_issuance", 0),
                    "debtPayment": item.get("debt_payment", 0),
                    "stockIssue": item.get("stock_issuance", 0),
                    "buyback": item.get("stock_repurchase", 0),
                    "dividend": item.get("dividends", 0)
                }

            # Format for JavaScript
            capex_js = "{ " + ", ".join([f"{y}: {capex_by_year.get(y) if capex_by_year.get(y) is not None else 'null'}" for y in [2021, 2022, 2023, 2024, 2025]]) + " }"
            ocf_js = "{ " + ", ".join([f"{y}: {ocf_by_year.get(y) if ocf_by_year.get(y) is not None else 'null'}" for y in [2021, 2022, 2023, 2024, 2025]]) + " }"

            # OCF breakdown
            ocf_breakdown_js_parts = []
            for year in [2021, 2022, 2023, 2024, 2025]:
                if year in ocf_breakdown_by_year:
                    b = ocf_breakdown_by_year[year]
                    ocf_breakdown_js_parts.append(
                        f"{year}: {{ netIncome: {b['netIncome']}, depreciation: {b['depreciation']}, "
                        f"stockComp: {b['stockComp']}, workingCapital: {b['workingCapital']}, "
                        f"deferredTax: {b['deferredTax']}, other: {b['other']} }}"
                    )
            ocf_breakdown_js = "{ " + ", ".join(ocf_breakdown_js_parts) + " }"

            # Funding sources
            funding_js_parts = []
            for year in [2021, 2022, 2023, 2024, 2025]:
                if year in funding_by_year:
                    f = funding_by_year[year]
                    funding_js_parts.append(
                        f"{year}: {{ capex: {f['capex']}, ocf: {f['ocf']}, fcf: {f['fcf']}, "
                        f"debtIssue: {f['debtIssue']}, debtPayment: {f['debtPayment']}, stockIssue: {f['stockIssue']}, "
                        f"buyback: {f['buyback']}, dividend: {f['dividend']} }}"
                    )
            funding_js = "{ " + ", ".join(funding_js_parts) + " }"

            js_data_parts.append(f"""            {company_name}: {{
                color: '{color}',
                capex: {capex_js},
                ocf: {ocf_js},
                ocfBreakdown: {ocf_breakdown_js},
                funding: {funding_js}
            }}""")

        company_data_js = ",\n".join(js_data_parts)

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Historical Demand & Supply Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh; padding: 20px; color: #e4e4e4;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        h1 {{ text-align: center; margin-bottom: 10px; color: #4dabf7; font-size: 1.8em; }}
        .subtitle {{ text-align: center; color: #868e96; margin-bottom: 20px; font-size: 0.9em; }}
        .section-title {{
            color: #4dabf7; font-size: 1.3em; margin: 30px 0 15px 0;
            padding-bottom: 10px; border-bottom: 1px solid rgba(77, 171, 247, 0.3);
        }}
        .section-desc {{ color: #868e96; font-size: 0.85em; margin-bottom: 15px; }}
        .subsection-title {{ color: #74c0fc; font-size: 1.1em; margin: 20px 0 10px 0; }}
        .charts-container {{
            display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;
        }}
        .charts-container.three-col {{ grid-template-columns: repeat(3, 1fr); }}
        .chart-box {{
            background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .chart-box.full-width {{ grid-column: 1 / -1; }}
        .chart-title {{
            font-size: 1em; color: #fff; margin-bottom: 15px;
            display: flex; align-items: center; gap: 8px;
        }}
        .chart-title .icon {{ font-size: 1.1em; }}
        .chart-header {{
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;
        }}
        .chart-wrapper {{ height: 280px; position: relative; }}
        .chart-wrapper.tall {{ height: 350px; }}
        .filters {{
            background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px;
            margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);
        }}
        .filter-title {{ font-size: 1em; color: #fff; margin-bottom: 15px; }}
        .filter-groups {{ display: flex; gap: 40px; flex-wrap: wrap; }}
        .filter-group {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }}
        .filter-group-label {{ color: #868e96; font-size: 0.85em; margin-right: 10px; }}
        .filter-btn {{
            padding: 8px 16px; border: none; border-radius: 20px; cursor: pointer;
            font-size: 0.85em; transition: all 0.2s; background: rgba(255,255,255,0.1); color: #e4e4e4;
        }}
        .filter-btn:hover {{ background: rgba(255,255,255,0.2); }}
        .filter-btn.active {{ color: #fff; font-weight: 500; }}
        .filter-btn.amazon.active {{ background: #ff9900; }}
        .filter-btn.microsoft.active {{ background: #00a4ef; }}
        .filter-btn.alphabet.active {{ background: #4285f4; }}
        .filter-btn.meta.active {{ background: #0866ff; }}
        .filter-btn.oracle.active {{ background: #f80000; }}
        .filter-btn.nvidia.active {{ background: #76b900; }}
        .filter-btn.all.active {{ background: #4dabf7; }}
        .company-select {{
            padding: 8px 16px; border-radius: 8px; background: rgba(255,255,255,0.1);
            color: #e4e4e4; border: 1px solid rgba(255,255,255,0.2); font-size: 0.9em; cursor: pointer;
        }}
        .company-select option {{ background: #1a1a2e; color: #e4e4e4; }}
        .data-table {{
            background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px;
            border: 1px solid rgba(255,255,255,0.1); overflow-x: auto; margin-bottom: 20px;
        }}
        .data-table table {{ width: 100%; border-collapse: collapse; font-size: 0.85em; }}
        .data-table th, .data-table td {{
            padding: 10px 12px; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .data-table th {{ color: #4dabf7; font-weight: 600; }}
        .data-table th:first-child, .data-table td:first-child {{ text-align: left; }}
        .data-table tr:hover {{ background: rgba(255,255,255,0.05); }}
        .growth-positive {{ color: #51cf66; }}
        .growth-negative {{ color: #ff6b6b; }}
        .company-legend {{
            display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;
            padding: 15px; background: rgba(255,255,255,0.03); border-radius: 8px;
            margin-bottom: 20px;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 0.85em; }}
        .legend-color {{ width: 12px; height: 12px; border-radius: 2px; }}
        .legend-custom {{
            display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;
            margin-top: 10px; font-size: 0.85em;
        }}
        .table-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
        .table-header h3 {{ color: #4dabf7; margin: 0; }}
        .generated-info {{ text-align: center; color: #868e96; font-size: 0.8em; margin-top: 30px; }}
        .sticky-header {{
            position: sticky; top: 0; z-index: 100;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 15px 0; margin: 0 -20px; padding-left: 20px; padding-right: 20px;
            transition: box-shadow 0.3s ease;
        }}
        .sticky-header.scrolled {{ box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
        /* Cash Flow Framework Diagram Styles */
        .framework-diagram {{
            display: flex; gap: 20px; margin: 20px 0; padding: 20px;
            background: rgba(0,0,0,0.2); border-radius: 12px;
        }}
        .framework-section {{
            flex: 1; padding: 15px; border-radius: 10px;
        }}
        .framework-section.sources {{
            background: linear-gradient(135deg, rgba(81, 207, 102, 0.15) 0%, rgba(81, 207, 102, 0.05) 100%);
            border: 1px solid rgba(81, 207, 102, 0.3);
        }}
        .framework-section.uses {{
            background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, rgba(255, 107, 107, 0.05) 100%);
            border: 1px solid rgba(255, 107, 107, 0.3);
        }}
        .framework-section h4 {{
            color: #4dabf7; font-size: 0.95em; margin-bottom: 15px;
            padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .framework-items {{ display: flex; flex-direction: column; gap: 10px; }}
        .framework-item {{
            display: flex; align-items: center; gap: 10px; padding: 10px;
            background: rgba(255,255,255,0.05); border-radius: 8px;
            border-left: 3px solid #868e96;
            cursor: pointer; transition: all 0.2s ease;
        }}
        .framework-item:hover {{
            background: rgba(255,255,255,0.12);
            transform: translateX(5px);
        }}
        .framework-item::after {{
            content: '→'; margin-left: auto; color: #868e96; font-size: 0.9em;
            opacity: 0; transition: opacity 0.2s;
        }}
        .framework-item:hover::after {{ opacity: 1; }}
        .framework-item.no-chart {{
            cursor: default; opacity: 0.6;
        }}
        .framework-item.no-chart:hover {{
            background: rgba(255,255,255,0.05);
            transform: none;
        }}
        .framework-item.no-chart::after {{ display: none; }}
        .framework-item.primary {{ border-left-color: #51cf66; }}
        .framework-item.secondary {{ border-left-color: #4dabf7; }}
        .framework-item.critical {{ border-left-color: #ff6b6b; }}
        .item-icon {{ font-size: 1.2em; }}
        .item-label {{ font-weight: 600; color: #fff; min-width: 100px; }}
        .item-desc {{ font-size: 0.8em; color: #868e96; }}
        .framework-center {{
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            padding: 20px; min-width: 180px;
        }}
        .balance-symbol {{ font-size: 2.5em; color: #4dabf7; margin-bottom: 15px; }}
        .formula-box {{
            background: rgba(77, 171, 247, 0.15); border: 1px solid rgba(77, 171, 247, 0.4);
            border-radius: 10px; padding: 15px; text-align: center;
            cursor: pointer; transition: all 0.2s ease;
        }}
        .formula-box:hover {{
            background: rgba(77, 171, 247, 0.25);
            transform: scale(1.02);
        }}
        html {{ scroll-behavior: smooth; }}
        .formula-title {{ font-size: 0.8em; color: #74c0fc; margin-bottom: 8px; }}
        .formula {{ font-size: 1.1em; font-weight: 700; color: #4dabf7; font-family: monospace; }}
        .formula-note {{ font-size: 0.75em; color: #868e96; margin-top: 8px; }}
        .framework-insight {{
            margin-top: 15px; padding: 12px 15px; background: rgba(255, 193, 7, 0.1);
            border-left: 3px solid #ffc107; border-radius: 0 8px 8px 0; font-size: 0.85em; color: #e4e4e4;
        }}
        .framework-insight strong {{ color: #ffc107; }}
        .relationship-note {{
            margin: 15px 0 20px 0; padding: 15px; background: rgba(77, 171, 247, 0.1);
            border-radius: 10px; border: 1px solid rgba(77, 171, 247, 0.2);
        }}
        .relationship-note strong {{ color: #4dabf7; }}
        .relationship-note ul {{ margin: 10px 0 0 20px; }}
        .relationship-note li {{ margin: 5px 0; font-size: 0.85em; color: #e4e4e4; }}
        .relationship-note .highlight {{ color: #51cf66; font-weight: 600; font-family: monospace; }}
        @media (max-width: 1400px) {{ .charts-container.three-col {{ grid-template-columns: repeat(2, 1fr); }} }}
        @media (max-width: 1000px) {{
            .charts-container, .charts-container.three-col {{ grid-template-columns: 1fr; }}
            .framework-diagram {{ flex-direction: column; }}
            .framework-center {{ flex-direction: row; gap: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Company Historical Demand & Supply Analysis</h1>
        <p class="subtitle">AI Infrastructure Investment Trends with Financial Breakdown (Calendar Year Aligned)</p>

        <div class="sticky-header" id="stickyHeader">
            <div class="filters">
                <div class="filter-title">Filter Companies</div>
                <div class="filter-groups">
                    <div class="filter-group">
                        <span class="filter-group-label">Quick:</span>
                        <button class="filter-btn all active" onclick="toggleAll()">All Companies</button>
                    </div>
                    <div class="filter-group">
                        <span class="filter-group-label">Select:</span>
                        <button class="filter-btn amazon active" data-company="Amazon" onclick="toggleCompany(this)">Amazon</button>
                        <button class="filter-btn microsoft active" data-company="Microsoft" onclick="toggleCompany(this)">Microsoft</button>
                        <button class="filter-btn alphabet active" data-company="Alphabet" onclick="toggleCompany(this)">Alphabet</button>
                        <button class="filter-btn meta active" data-company="Meta" onclick="toggleCompany(this)">Meta</button>
                        <button class="filter-btn oracle active" data-company="Oracle" onclick="toggleCompany(this)">Oracle</button>
                        <button class="filter-btn nvidia active" data-company="Nvidia" onclick="toggleCompany(this)">Nvidia</button>
                    </div>
                </div>
            </div>
            <div class="company-legend" id="companyLegend"></div>
        </div>

        <h2 class="section-title">1. Demand (CapEx) vs Supply (OCF) Overview</h2>
        <p class="section-desc">Capital expenditure (Demand) and Operating Cash Flow (Supply) trends - Line charts comparing all companies</p>
        <div class="charts-container">
            <div class="chart-box">
                <div class="chart-title"><span class="icon">📈</span> CapEx Trend ($B)</div>
                <div class="chart-wrapper tall"><canvas id="demandChart"></canvas></div>
            </div>
            <div class="chart-box" id="chart-ocf">
                <div class="chart-title"><span class="icon">💰</span> OCF Trend ($B)</div>
                <div class="chart-wrapper tall"><canvas id="supplyChart"></canvas></div>
            </div>
        </div>

        <h2 class="section-title">2. OCF Breakdown - What Generates Cash Flow?</h2>
        <p class="section-desc">OCF (Operating Cash Flow) = Net Income + Non-Cash Adjustments + Working Capital Changes</p>
        <div class="relationship-note" style="margin-top: 10px;">
            <strong>OCF Component Definitions:</strong>
            <ul>
                <li><span class="highlight">Net Income</span> — Profit after all expenses and taxes (cash basis starting point)</li>
                <li><span class="highlight">D&A (Depreciation & Amortization)</span> — Non-cash expense added back; spreads asset costs over time</li>
                <li><span class="highlight">Stock Comp</span> — Stock-based compensation; non-cash expense added back</li>
                <li><span class="highlight">Working Capital</span> — Changes in receivables, payables, inventory (negative = cash used)</li>
                <li><span class="highlight">Deferred Tax</span> — Difference between tax expense and actual tax paid</li>
                <li><span class="highlight">Other</span> — Other non-cash adjustments and reconciling items</li>
            </ul>
        </div>
        <h3 class="subsection-title">2.1 Cross-Company Comparison ($B) - Line Charts</h3>
        <p class="section-desc">Each chart shows absolute values for all companies</p>
        <div class="charts-container three-col">
            <div class="chart-box">
                <div class="chart-title"><span class="icon">💵</span> Net Income ($B)</div>
                <div class="chart-wrapper"><canvas id="netIncomeChart"></canvas></div>
            </div>
            <div class="chart-box">
                <div class="chart-title"><span class="icon">🏭</span> D&A ($B)</div>
                <div class="chart-wrapper"><canvas id="depreciationChart"></canvas></div>
            </div>
            <div class="chart-box">
                <div class="chart-title"><span class="icon">🎁</span> Stock Comp ($B)</div>
                <div class="chart-wrapper"><canvas id="stockCompChart"></canvas></div>
            </div>
            <div class="chart-box">
                <div class="chart-title"><span class="icon">📦</span> Working Capital ($B)</div>
                <div class="chart-wrapper"><canvas id="workingCapitalChart"></canvas></div>
            </div>
            <div class="chart-box">
                <div class="chart-title"><span class="icon">📋</span> Deferred Tax ($B)</div>
                <div class="chart-wrapper"><canvas id="deferredTaxChart"></canvas></div>
            </div>
            <div class="chart-box">
                <div class="chart-title"><span class="icon">📊</span> Other ($B)</div>
                <div class="chart-wrapper"><canvas id="otherChart"></canvas></div>
            </div>
        </div>
        <h3 class="subsection-title">2.2 Within-Company Percentage Breakdown - Stacked Bar Chart</h3>
        <p class="section-desc">Shows each OCF component as percentage of total OCF for the selected company</p>
        <div class="charts-container">
            <div class="chart-box full-width">
                <div class="chart-header">
                    <div class="chart-title"><span class="icon">📊</span> OCF Components % Breakdown by Year</div>
                    <select class="company-select" id="ocfPctCompanySelect" onchange="updateOcfPctChart()">
                        <option value="Amazon">Amazon</option>
                        <option value="Microsoft">Microsoft</option>
                        <option value="Alphabet">Alphabet</option>
                        <option value="Meta">Meta</option>
                        <option value="Oracle">Oracle</option>
                        <option value="Nvidia">Nvidia</option>
                    </select>
                </div>
                <div class="chart-wrapper tall"><canvas id="ocfPctBarChart"></canvas></div>
                <div class="legend-custom">
                    <div class="legend-item"><div class="legend-color" style="background:#51cf66"></div>Net Income</div>
                    <div class="legend-item"><div class="legend-color" style="background:#4dabf7"></div>D&A</div>
                    <div class="legend-item"><div class="legend-color" style="background:#be4bdb"></div>Stock Comp</div>
                    <div class="legend-item"><div class="legend-color" style="background:#fcc419"></div>Working Capital</div>
                    <div class="legend-item"><div class="legend-color" style="background:#ff6b6b"></div>Deferred Tax</div>
                    <div class="legend-item"><div class="legend-color" style="background:#868e96"></div>Other</div>
                </div>
            </div>
        </div>

        <h2 class="section-title">3. Cash Flow Framework - Sources vs Uses</h2>
        <p class="section-desc">Understanding how cash flows through the company: where it comes from (Sources) and where it goes (Uses)</p>
        <div class="chart-box full-width" style="margin-bottom: 20px;">
            <div class="chart-title"><span class="icon">📐</span> Cash Flow Balance Framework</div>
            <div class="framework-diagram">
                <div class="framework-section sources">
                    <h4>SOURCES (Cash Inflows)</h4>
                    <div class="framework-items">
                        <div class="framework-item primary" onclick="scrollToChart('chart-ocf')" title="View OCF Chart">
                            <span class="item-icon">💰</span>
                            <span class="item-label">OCF</span>
                            <span class="item-desc">Operating Cash Flow - cash from business operations</span>
                        </div>
                        <div class="framework-item secondary" onclick="scrollToChart('chart-debt')" title="View Debt Issuance Chart">
                            <span class="item-icon">🏦</span>
                            <span class="item-label">Debt Issuance</span>
                            <span class="item-desc">Long-term debt borrowed when OCF insufficient</span>
                        </div>
                        <div class="framework-item secondary" onclick="scrollToChart('chart-stock-issue')" title="View Stock Issuance Chart">
                            <span class="item-icon">📈</span>
                            <span class="item-label">Stock Issuance</span>
                            <span class="item-desc">New equity raised from investors</span>
                        </div>
                    </div>
                </div>
                <div class="framework-center">
                    <div class="balance-symbol">=</div>
                    <div class="formula-box" onclick="scrollToChart('chart-fcf')" title="View FCF Chart">
                        <div class="formula-title">Key Relationship</div>
                        <div class="formula">FCF = OCF - CapEx</div>
                        <div class="formula-note">Free Cash Flow is what remains after infrastructure investment</div>
                    </div>
                </div>
                <div class="framework-section uses">
                    <h4>USES (Cash Outflows)</h4>
                    <div class="framework-items">
                        <div class="framework-item critical" onclick="scrollToChart('chart-capex')" title="View CapEx Chart">
                            <span class="item-icon">📈</span>
                            <span class="item-label">CapEx</span>
                            <span class="item-desc">Capital Expenditure - investment in infrastructure/AI</span>
                        </div>
                        <div class="framework-item" onclick="scrollToChart('chart-buyback')" title="View Buybacks Chart">
                            <span class="item-icon">🔄</span>
                            <span class="item-label">Buybacks</span>
                            <span class="item-desc">Share repurchases - returning cash to shareholders</span>
                        </div>
                        <div class="framework-item" onclick="scrollToChart('chart-dividend')" title="View Dividends Chart">
                            <span class="item-icon">💎</span>
                            <span class="item-label">Dividends</span>
                            <span class="item-desc">Cash dividends paid to shareholders</span>
                        </div>
                        <div class="framework-item" onclick="scrollToChart('chart-debt-payment')" title="View Debt Repayment Chart">
                            <span class="item-icon">📉</span>
                            <span class="item-label">Debt Repayment</span>
                            <span class="item-desc">Principal repayment of existing debt</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="framework-insight">
                <strong>Key Insight:</strong> When CapEx exceeds OCF (negative FCF), companies must rely on debt or equity issuance to fund growth.
                This dashboard tracks whether AI infrastructure investment (CapEx) is sustainable from operating cash flows (OCF).
            </div>
        </div>

        <h2 class="section-title">4. Funding & Cash Allocation - How is Cash Used?</h2>
        <h3 class="subsection-title">4.1 Cross-Company Comparison ($B) - Line Charts</h3>
        <p class="section-desc">Tracking CapEx (investment demand), FCF (remaining after investment), Debt (external funding), and shareholder returns</p>
        <div class="charts-container three-col" id="section-funding">
            <div class="chart-box" id="chart-capex">
                <div class="chart-title"><span class="icon">📈</span> CapEx ($B)</div>
                <div class="chart-wrapper"><canvas id="capexFundingChart"></canvas></div>
            </div>
            <div class="chart-box" id="chart-fcf">
                <div class="chart-title"><span class="icon">💸</span> Free Cash Flow ($B)</div>
                <div class="chart-wrapper"><canvas id="fcfChart"></canvas></div>
            </div>
            <div class="chart-box" id="chart-debt">
                <div class="chart-title"><span class="icon">🏦</span> Debt Issuance ($B)</div>
                <div class="chart-wrapper"><canvas id="debtChart"></canvas></div>
            </div>
            <div class="chart-box" id="chart-buyback">
                <div class="chart-title"><span class="icon">🔄</span> Stock Buybacks ($B)</div>
                <div class="chart-wrapper"><canvas id="buybackChart"></canvas></div>
            </div>
            <div class="chart-box" id="chart-dividend">
                <div class="chart-title"><span class="icon">💎</span> Dividends ($B)</div>
                <div class="chart-wrapper"><canvas id="dividendChart"></canvas></div>
            </div>
            <div class="chart-box" id="chart-stock-issue">
                <div class="chart-title"><span class="icon">📈</span> Stock Issuance ($B)</div>
                <div class="chart-wrapper"><canvas id="stockIssueChart"></canvas></div>
            </div>
            <div class="chart-box" id="chart-debt-payment">
                <div class="chart-title"><span class="icon">📉</span> Debt Repayment ($B)</div>
                <div class="chart-wrapper"><canvas id="debtPaymentChart"></canvas></div>
            </div>
        </div>
        <div class="relationship-note">
            <strong>Parameter Relationships:</strong>
            <ul>
                <li><span class="highlight">FCF = OCF - CapEx</span> — Free Cash Flow is Operating Cash Flow minus Capital Expenditure</li>
                <li><span class="highlight">If FCF &gt; 0</span> — Company can fund buybacks/dividends from operations</li>
                <li><span class="highlight">If FCF &lt; 0</span> — Company needs debt/equity issuance to fund CapEx</li>
            </ul>
        </div>
        <h3 class="subsection-title" id="fundingPctSection">4.2 Within-Company Percentage Breakdown - Stacked Bar Chart</h3>
        <p class="section-desc">Shows cash allocation as percentage of OCF for the selected company (CapEx + Buybacks + Dividends)</p>
        <div class="charts-container">
            <div class="chart-box full-width">
                <div class="chart-header">
                    <div class="chart-title"><span class="icon">📊</span> Cash Allocation % of OCF by Year</div>
                    <select class="company-select" id="fundingPctCompanySelect" onchange="updateFundingPctChart()">
                        <option value="Amazon">Amazon</option>
                        <option value="Microsoft">Microsoft</option>
                        <option value="Alphabet">Alphabet</option>
                        <option value="Meta">Meta</option>
                        <option value="Oracle">Oracle</option>
                        <option value="Nvidia">Nvidia</option>
                    </select>
                </div>
                <div class="chart-wrapper tall"><canvas id="fundingPctBarChart"></canvas></div>
                <div class="legend-custom">
                    <div class="legend-item"><div class="legend-color" style="background:#4dabf7"></div>CapEx</div>
                    <div class="legend-item"><div class="legend-color" style="background:#be4bdb"></div>Buybacks</div>
                    <div class="legend-item"><div class="legend-color" style="background:#fcc419"></div>Dividends</div>
                </div>
            </div>
        </div>

        <h2 class="section-title">5. Cross-Company Comparison (Latest Year)</h2>
        <p class="section-desc">Stacked bar comparison showing OCF breakdown and capital allocation</p>
        <div class="charts-container">
            <div class="chart-box">
                <div class="chart-title"><span class="icon">📊</span> OCF Components ($B)</div>
                <div class="chart-wrapper tall"><canvas id="ocfComparisonChart"></canvas></div>
            </div>
            <div class="chart-box">
                <div class="chart-title"><span class="icon">💹</span> Capital Allocation ($B)</div>
                <div class="chart-wrapper tall"><canvas id="allocationComparisonChart"></canvas></div>
            </div>
        </div>

        <h2 class="section-title">6. Detailed Data Tables</h2>
        <div class="data-table">
            <div class="table-header"><h3>CapEx & OCF Historical ($B)</h3></div>
            <table id="mainTable">
                <thead><tr><th>Company</th><th>Metric</th><th>2021</th><th>2022</th><th>2023</th><th>2024</th><th>2025</th><th>Growth</th></tr></thead>
                <tbody id="mainTableBody"></tbody>
            </table>
        </div>

        <div class="data-table">
            <div class="table-header">
                <h3>OCF Breakdown Historical ($B)</h3>
                <select class="company-select" id="ocfTableCompanySelect" onchange="updateOcfTable()">
                    <option value="all">All Companies (Latest Year)</option>
                    <option value="Amazon">Amazon (Historical)</option>
                    <option value="Microsoft">Microsoft (Historical)</option>
                    <option value="Alphabet">Alphabet (Historical)</option>
                    <option value="Meta">Meta (Historical)</option>
                    <option value="Oracle">Oracle (Historical)</option>
                    <option value="Nvidia">Nvidia (Historical)</option>
                </select>
            </div>
            <table id="ocfTable"><thead id="ocfTableHead"></thead><tbody id="ocfTableBody"></tbody></table>
        </div>

        <div class="data-table">
            <div class="table-header">
                <h3>Funding & Capital Allocation Historical ($B)</h3>
                <select class="company-select" id="fundingTableCompanySelect" onchange="updateFundingTable()">
                    <option value="all">All Companies (Latest Year)</option>
                    <option value="Amazon">Amazon (Historical)</option>
                    <option value="Microsoft">Microsoft (Historical)</option>
                    <option value="Alphabet">Alphabet (Historical)</option>
                    <option value="Meta">Meta (Historical)</option>
                    <option value="Oracle">Oracle (Historical)</option>
                    <option value="Nvidia">Nvidia (Historical)</option>
                </select>
            </div>
            <table id="fundingTable"><thead id="fundingTableHead"></thead><tbody id="fundingTableBody"></tbody></table>
        </div>

        <p class="generated-info">Auto-generated from consolidated_data.json on {timestamp}</p>
    </div>

    <script>
        // Data auto-generated from consolidated_data.json
        const companyData = {{
{company_data_js}
        }};

        const years = [2021, 2022, 2023, 2024, 2025];
        let activeCompanies = new Set(Object.keys(companyData));

        // All chart instances
        let charts = {{}};

        const componentColors = {{
            netIncome: '#51cf66', depreciation: '#4dabf7', stockComp: '#be4bdb',
            workingCapital: '#fcc419', deferredTax: '#ff6b6b', other: '#868e96'
        }};

        function getLatestYear(company) {{
            const data = companyData[company];
            for (let i = years.length - 1; i >= 0; i--) {{
                if (data.ocfBreakdown[years[i]]) return years[i];
            }}
            return years[years.length - 1];
        }}

        function getAvailableYears(company) {{
            return years.filter(y => companyData[company].ocfBreakdown[y]);
        }}

        // Common chart options
        function getLineChartOptions(showLegend = false) {{
            return {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: showLegend, position: 'bottom', labels: {{ color: '#e4e4e4', usePointStyle: true, padding: 10 }} }},
                    tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)', callbacks: {{ label: ctx => ctx.raw !== null ? `${{ctx.dataset.label}}: $${{ctx.raw.toFixed(2)}}B` : null }} }}
                }},
                scales: {{
                    x: {{ grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#868e96' }} }},
                    y: {{ grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#868e96', callback: v => '$' + v + 'B' }} }}
                }}
            }};
        }}

        // Create line chart datasets for a specific metric
        function createLineDatasets(getValueFn) {{
            return Object.entries(companyData).map(([name, data]) => ({{
                label: name,
                data: years.map(y => getValueFn(data, y)),
                borderColor: data.color,
                backgroundColor: data.color + '40',
                borderWidth: 2,
                pointRadius: 3,
                tension: 0.3,
                hidden: !activeCompanies.has(name),
                spanGaps: true
            }}));
        }}

        // Initialize company legend
        function initCompanyLegend() {{
            const legend = document.getElementById('companyLegend');
            legend.innerHTML = Object.entries(companyData).map(([name, data]) =>
                `<div class="legend-item"><div class="legend-color" style="background:${{data.color}}"></div>${{name}}</div>`
            ).join('');
        }}

        function initCharts() {{
            initCompanyLegend();
            initDemandSupplyCharts();
            initOcfBreakdownCharts();
            initFundingSourceCharts();
            initComparisonCharts();
            initPercentageCharts();
            updateAllTables();
        }}

        function initDemandSupplyCharts() {{
            charts.demand = new Chart(document.getElementById('demandChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.capex[y]) }},
                options: getLineChartOptions(false)
            }});
            charts.supply = new Chart(document.getElementById('supplyChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.ocf[y]) }},
                options: getLineChartOptions(false)
            }});
        }}

        function initOcfBreakdownCharts() {{
            // Net Income
            charts.netIncome = new Chart(document.getElementById('netIncomeChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.ocfBreakdown[y]?.netIncome) }},
                options: getLineChartOptions(false)
            }});
            // Depreciation
            charts.depreciation = new Chart(document.getElementById('depreciationChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.ocfBreakdown[y]?.depreciation) }},
                options: getLineChartOptions(false)
            }});
            // Stock Compensation
            charts.stockComp = new Chart(document.getElementById('stockCompChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.ocfBreakdown[y]?.stockComp) }},
                options: getLineChartOptions(false)
            }});
            // Working Capital
            charts.workingCapital = new Chart(document.getElementById('workingCapitalChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.ocfBreakdown[y]?.workingCapital) }},
                options: getLineChartOptions(false)
            }});
            // Deferred Tax
            charts.deferredTax = new Chart(document.getElementById('deferredTaxChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.ocfBreakdown[y]?.deferredTax) }},
                options: getLineChartOptions(false)
            }});
            // Other
            charts.other = new Chart(document.getElementById('otherChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.ocfBreakdown[y]?.other) }},
                options: getLineChartOptions(false)
            }});
        }}

        function initFundingSourceCharts() {{
            // CapEx (in funding section for comparison)
            charts.capexFunding = new Chart(document.getElementById('capexFundingChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.funding[y]?.capex) }},
                options: getLineChartOptions(false)
            }});
            // Free Cash Flow
            charts.fcf = new Chart(document.getElementById('fcfChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.funding[y]?.fcf) }},
                options: getLineChartOptions(false)
            }});
            // Debt Issuance
            charts.debt = new Chart(document.getElementById('debtChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.funding[y]?.debtIssue) }},
                options: getLineChartOptions(false)
            }});
            // Buybacks
            charts.buyback = new Chart(document.getElementById('buybackChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.funding[y]?.buyback) }},
                options: getLineChartOptions(false)
            }});
            // Dividends
            charts.dividend = new Chart(document.getElementById('dividendChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.funding[y]?.dividend) }},
                options: getLineChartOptions(false)
            }});
            // Stock Issuance
            charts.stockIssue = new Chart(document.getElementById('stockIssueChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.funding[y]?.stockIssue) }},
                options: getLineChartOptions(false)
            }});
            // Debt Payment
            charts.debtPayment = new Chart(document.getElementById('debtPaymentChart'), {{
                type: 'line',
                data: {{ labels: years, datasets: createLineDatasets((data, y) => data.funding[y]?.debtPayment) }},
                options: getLineChartOptions(false)
            }});
        }}

        function initComparisonCharts() {{
            const companies = Object.keys(companyData).filter(c => activeCompanies.has(c));

            if (charts.ocfComparison) charts.ocfComparison.destroy();
            const ocfDatasets = [
                {{ label: 'Net Income', key: 'netIncome', color: componentColors.netIncome }},
                {{ label: 'D&A', key: 'depreciation', color: componentColors.depreciation }},
                {{ label: 'Stock Comp', key: 'stockComp', color: componentColors.stockComp }},
                {{ label: 'Working Capital', key: 'workingCapital', color: componentColors.workingCapital }},
                {{ label: 'Deferred Tax', key: 'deferredTax', color: componentColors.deferredTax }},
                {{ label: 'Other', key: 'other', color: componentColors.other }}
            ].map(item => ({{
                label: item.label,
                data: companies.map(c => {{ const year = getLatestYear(c); return companyData[c].ocfBreakdown[year]?.[item.key] || 0; }}),
                backgroundColor: item.color
            }}));
            charts.ocfComparison = new Chart(document.getElementById('ocfComparisonChart'), {{
                type: 'bar', data: {{ labels: companies, datasets: ocfDatasets }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#e4e4e4', padding: 8, font: {{ size: 10 }} }} }}, tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)', callbacks: {{ label: ctx => `${{ctx.dataset.label}}: $${{ctx.raw.toFixed(2)}}B` }} }} }},
                    scales: {{ x: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#e4e4e4' }} }}, y: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#868e96', callback: v => '$' + v + 'B' }} }} }}
                }}
            }});

            if (charts.allocationComparison) charts.allocationComparison.destroy();
            charts.allocationComparison = new Chart(document.getElementById('allocationComparisonChart'), {{
                type: 'bar',
                data: {{ labels: companies, datasets: [
                    {{ label: 'CapEx', data: companies.map(c => {{ const y = getLatestYear(c); return companyData[c].funding[y]?.capex || 0; }}), backgroundColor: '#4dabf7' }},
                    {{ label: 'Buybacks', data: companies.map(c => {{ const y = getLatestYear(c); return companyData[c].funding[y]?.buyback || 0; }}), backgroundColor: '#be4bdb' }},
                    {{ label: 'Dividends', data: companies.map(c => {{ const y = getLatestYear(c); return companyData[c].funding[y]?.dividend || 0; }}), backgroundColor: '#fcc419' }}
                ] }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#e4e4e4', padding: 15 }} }}, tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)', callbacks: {{ label: ctx => `${{ctx.dataset.label}}: $${{ctx.raw.toFixed(2)}}B` }} }} }},
                    scales: {{ x: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#e4e4e4' }} }}, y: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#868e96', callback: v => '$' + v + 'B' }}, beginAtZero: true }} }}
                }}
            }});
        }}

        // OCF Percentage Stacked Bar Chart (within-company)
        function updateOcfPctChart() {{
            const company = document.getElementById('ocfPctCompanySelect').value;
            const data = companyData[company];
            const availableYears = getAvailableYears(company);

            if (charts.ocfPctBar) charts.ocfPctBar.destroy();

            // Calculate percentages for each component
            const datasets = [
                {{ label: 'Net Income', key: 'netIncome', color: componentColors.netIncome }},
                {{ label: 'D&A', key: 'depreciation', color: componentColors.depreciation }},
                {{ label: 'Stock Comp', key: 'stockComp', color: componentColors.stockComp }},
                {{ label: 'Working Capital', key: 'workingCapital', color: componentColors.workingCapital }},
                {{ label: 'Deferred Tax', key: 'deferredTax', color: componentColors.deferredTax }},
                {{ label: 'Other', key: 'other', color: componentColors.other }}
            ].map(item => ({{
                label: item.label,
                data: availableYears.map(y => {{
                    const ocf = data.ocf[y];
                    const value = data.ocfBreakdown[y]?.[item.key] || 0;
                    return ocf && ocf !== 0 ? (value / ocf) * 100 : 0;
                }}),
                backgroundColor: item.color,
                borderColor: item.color,
                borderWidth: 1
            }}));

            charts.ocfPctBar = new Chart(document.getElementById('ocfPctBarChart'), {{
                type: 'bar',
                data: {{ labels: availableYears, datasets }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)', callbacks: {{ label: ctx => `${{ctx.dataset.label}}: ${{ctx.raw.toFixed(1)}}%` }} }}
                    }},
                    scales: {{
                        x: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#e4e4e4' }} }},
                        y: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#868e96', callback: v => v + '%' }} }}
                    }}
                }}
            }});
        }}

        // Funding Percentage Stacked Bar Chart (within-company)
        function updateFundingPctChart() {{
            const company = document.getElementById('fundingPctCompanySelect').value;
            const data = companyData[company];
            const availableYears = getAvailableYears(company);

            if (charts.fundingPctBar) charts.fundingPctBar.destroy();

            // Calculate percentages for CapEx, Buybacks, Dividends relative to OCF
            const datasets = [
                {{ label: 'CapEx', key: 'capex', color: '#4dabf7' }},
                {{ label: 'Buybacks', key: 'buyback', color: '#be4bdb' }},
                {{ label: 'Dividends', key: 'dividend', color: '#fcc419' }}
            ].map(item => ({{
                label: item.label,
                data: availableYears.map(y => {{
                    const ocf = data.ocf[y];
                    const value = data.funding[y]?.[item.key] || 0;
                    return ocf && ocf !== 0 ? (value / ocf) * 100 : 0;
                }}),
                backgroundColor: item.color,
                borderColor: item.color,
                borderWidth: 1
            }}));

            charts.fundingPctBar = new Chart(document.getElementById('fundingPctBarChart'), {{
                type: 'bar',
                data: {{ labels: availableYears, datasets }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)', callbacks: {{ label: ctx => `${{ctx.dataset.label}}: ${{ctx.raw.toFixed(1)}}%` }} }}
                    }},
                    scales: {{
                        x: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#e4e4e4' }} }},
                        y: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#868e96', callback: v => v + '%' }} }}
                    }}
                }}
            }});
        }}

        function initPercentageCharts() {{
            updateOcfPctChart();
            updateFundingPctChart();
        }}

        function toggleCompany(btn) {{
            const company = btn.dataset.company;
            if (activeCompanies.has(company)) {{ activeCompanies.delete(company); btn.classList.remove('active'); }}
            else {{ activeCompanies.add(company); btn.classList.add('active'); }}
            document.querySelector('.filter-btn.all').classList.toggle('active', activeCompanies.size === Object.keys(companyData).length);
            updateAllCharts();
        }}

        function toggleAll() {{
            const allBtn = document.querySelector('.filter-btn.all');
            const btns = document.querySelectorAll('.filter-btn[data-company]');
            if (activeCompanies.size === Object.keys(companyData).length) {{
                activeCompanies.clear(); allBtn.classList.remove('active'); btns.forEach(b => b.classList.remove('active'));
            }} else {{
                activeCompanies = new Set(Object.keys(companyData)); allBtn.classList.add('active'); btns.forEach(b => b.classList.add('active'));
            }}
            updateAllCharts();
        }}

        function updateAllCharts() {{
            // Update all line charts visibility
            const lineCharts = ['demand', 'supply', 'netIncome', 'depreciation', 'stockComp', 'workingCapital', 'deferredTax', 'other', 'capexFunding', 'fcf', 'debt', 'buyback', 'dividend', 'stockIssue', 'debtPayment'];
            lineCharts.forEach(chartName => {{
                if (charts[chartName]) {{
                    charts[chartName].data.datasets.forEach(ds => ds.hidden = !activeCompanies.has(ds.label));
                    charts[chartName].update();
                }}
            }});
            initComparisonCharts();
            updateAllTables();
        }}

        function updateAllTables() {{ updateMainTable(); updateOcfTable(); updateFundingTable(); }}

        function updateMainTable() {{
            const tbody = document.getElementById('mainTableBody'); tbody.innerHTML = '';
            Object.entries(companyData).forEach(([name, data]) => {{
                if (!activeCompanies.has(name)) return;
                const capexValues = years.map(y => data.capex[y]).filter(v => v !== null);
                const capexGrowth = capexValues.length >= 2 ? ((capexValues[capexValues.length-1] - capexValues[capexValues.length-2]) / capexValues[capexValues.length-2] * 100).toFixed(1) : null;
                const capexRow = document.createElement('tr');
                capexRow.innerHTML = `<td><span style="color:${{data.color}}">●</span> ${{name}}</td><td>CapEx</td>${{years.map(y => `<td>${{data.capex[y] !== null ? '$' + data.capex[y].toFixed(1) + 'B' : '-'}}</td>`).join('')}}<td class="${{capexGrowth > 0 ? 'growth-positive' : capexGrowth < 0 ? 'growth-negative' : ''}}">${{capexGrowth !== null ? (capexGrowth > 0 ? '+' : '') + capexGrowth + '%' : '-'}}</td>`;
                tbody.appendChild(capexRow);
                const ocfValues = years.map(y => data.ocf[y]).filter(v => v !== null);
                const ocfGrowth = ocfValues.length >= 2 ? ((ocfValues[ocfValues.length-1] - ocfValues[ocfValues.length-2]) / ocfValues[ocfValues.length-2] * 100).toFixed(1) : null;
                const ocfRow = document.createElement('tr');
                ocfRow.innerHTML = `<td></td><td>OCF</td>${{years.map(y => `<td>${{data.ocf[y] !== null ? '$' + data.ocf[y].toFixed(1) + 'B' : '-'}}</td>`).join('')}}<td class="${{ocfGrowth > 0 ? 'growth-positive' : ocfGrowth < 0 ? 'growth-negative' : ''}}">${{ocfGrowth !== null ? (ocfGrowth > 0 ? '+' : '') + ocfGrowth + '%' : '-'}}</td>`;
                tbody.appendChild(ocfRow);
            }});
        }}

        function updateOcfTable() {{
            const select = document.getElementById('ocfTableCompanySelect').value;
            const thead = document.getElementById('ocfTableHead'); const tbody = document.getElementById('ocfTableBody');
            if (select === 'all') {{
                thead.innerHTML = `<tr><th>Company</th><th>Net Income</th><th>D&A</th><th>Stock Comp</th><th>Working Capital</th><th>Deferred Tax</th><th>Other</th><th>Total OCF</th></tr>`;
                tbody.innerHTML = '';
                Object.entries(companyData).forEach(([name, data]) => {{
                    if (!activeCompanies.has(name)) return;
                    const year = getLatestYear(name); const b = data.ocfBreakdown[year];
                    const total = b.netIncome + b.depreciation + b.stockComp + b.workingCapital + b.deferredTax + b.other;
                    const row = document.createElement('tr');
                    row.innerHTML = `<td><span style="color:${{data.color}}">●</span> ${{name}} (${{year}})</td><td class="${{b.netIncome >= 0 ? 'growth-positive' : 'growth-negative'}}">$${{b.netIncome.toFixed(2)}}B</td><td>$${{b.depreciation.toFixed(2)}}B</td><td>$${{b.stockComp.toFixed(2)}}B</td><td class="${{b.workingCapital >= 0 ? 'growth-positive' : 'growth-negative'}}">$${{b.workingCapital.toFixed(2)}}B</td><td class="${{b.deferredTax >= 0 ? 'growth-positive' : 'growth-negative'}}">$${{b.deferredTax.toFixed(2)}}B</td><td>$${{b.other.toFixed(2)}}B</td><td style="font-weight:600">$${{total.toFixed(2)}}B</td>`;
                    tbody.appendChild(row);
                }});
            }} else {{
                const data = companyData[select]; const availableYears = getAvailableYears(select);
                thead.innerHTML = `<tr><th>Year</th><th>Net Income</th><th>D&A</th><th>Stock Comp</th><th>Working Capital</th><th>Deferred Tax</th><th>Other</th><th>Total OCF</th></tr>`;
                tbody.innerHTML = '';
                availableYears.forEach(year => {{
                    const b = data.ocfBreakdown[year]; const total = b.netIncome + b.depreciation + b.stockComp + b.workingCapital + b.deferredTax + b.other;
                    const row = document.createElement('tr');
                    row.innerHTML = `<td><span style="color:${{data.color}}">●</span> ${{year}}</td><td class="${{b.netIncome >= 0 ? 'growth-positive' : 'growth-negative'}}">$${{b.netIncome.toFixed(2)}}B</td><td>$${{b.depreciation.toFixed(2)}}B</td><td>$${{b.stockComp.toFixed(2)}}B</td><td class="${{b.workingCapital >= 0 ? 'growth-positive' : 'growth-negative'}}">$${{b.workingCapital.toFixed(2)}}B</td><td class="${{b.deferredTax >= 0 ? 'growth-positive' : 'growth-negative'}}">$${{b.deferredTax.toFixed(2)}}B</td><td>$${{b.other.toFixed(2)}}B</td><td style="font-weight:600">$${{total.toFixed(2)}}B</td>`;
                    tbody.appendChild(row);
                }});
            }}
        }}

        function updateFundingTable() {{
            const select = document.getElementById('fundingTableCompanySelect').value;
            const thead = document.getElementById('fundingTableHead'); const tbody = document.getElementById('fundingTableBody');
            if (select === 'all') {{
                thead.innerHTML = `<tr><th>Company</th><th>CapEx</th><th>OCF</th><th>FCF</th><th>Debt Issued</th><th>Buybacks</th><th>Dividends</th></tr>`;
                tbody.innerHTML = '';
                Object.entries(companyData).forEach(([name, data]) => {{
                    if (!activeCompanies.has(name)) return;
                    const year = getLatestYear(name); const f = data.funding[year];
                    const coverage = (f.ocf / f.capex * 100).toFixed(0);
                    const row = document.createElement('tr');
                    row.innerHTML = `<td><span style="color:${{data.color}}">●</span> ${{name}} (${{year}})</td><td>$${{f.capex.toFixed(2)}}B</td><td>$${{f.ocf.toFixed(2)}}B <span style="color:#868e96;font-size:0.8em">(${{coverage}}%)</span></td><td class="${{f.fcf >= 0 ? 'growth-positive' : 'growth-negative'}}">$${{f.fcf.toFixed(2)}}B</td><td>${{f.debtIssue > 0 ? '$' + f.debtIssue.toFixed(2) + 'B' : '-'}}</td><td>${{f.buyback > 0 ? '$' + f.buyback.toFixed(2) + 'B' : '-'}}</td><td>${{f.dividend > 0 ? '$' + f.dividend.toFixed(2) + 'B' : '-'}}</td>`;
                    tbody.appendChild(row);
                }});
            }} else {{
                const data = companyData[select]; const availableYears = getAvailableYears(select);
                thead.innerHTML = `<tr><th>Year</th><th>CapEx</th><th>OCF</th><th>FCF</th><th>Debt Issued</th><th>Buybacks</th><th>Dividends</th></tr>`;
                tbody.innerHTML = '';
                availableYears.forEach(year => {{
                    const f = data.funding[year]; if (!f) return;
                    const coverage = (f.ocf / f.capex * 100).toFixed(0);
                    const row = document.createElement('tr');
                    row.innerHTML = `<td><span style="color:${{data.color}}">●</span> ${{year}}</td><td>$${{f.capex.toFixed(2)}}B</td><td>$${{f.ocf.toFixed(2)}}B <span style="color:#868e96;font-size:0.8em">(${{coverage}}%)</span></td><td class="${{f.fcf >= 0 ? 'growth-positive' : 'growth-negative'}}">$${{f.fcf.toFixed(2)}}B</td><td>${{f.debtIssue > 0 ? '$' + f.debtIssue.toFixed(2) + 'B' : '-'}}</td><td>${{f.buyback > 0 ? '$' + f.buyback.toFixed(2) + 'B' : '-'}}</td><td>${{f.dividend > 0 ? '$' + f.dividend.toFixed(2) + 'B' : '-'}}</td>`;
                    tbody.appendChild(row);
                }});
            }}
        }}

        // Scroll to chart function with highlight effect
        function scrollToChart(elementId) {{
            const element = document.getElementById(elementId);
            if (element) {{
                const headerOffset = document.getElementById('stickyHeader').offsetHeight + 20;
                const elementPosition = element.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({{
                    top: offsetPosition,
                    behavior: 'smooth'
                }});

                // Add highlight effect
                element.style.transition = 'box-shadow 0.3s ease, transform 0.3s ease';
                element.style.boxShadow = '0 0 20px rgba(77, 171, 247, 0.6)';
                element.style.transform = 'scale(1.01)';

                setTimeout(() => {{
                    element.style.boxShadow = '';
                    element.style.transform = '';
                }}, 1500);
            }}
        }}

        initCharts();

        // Sticky header scroll behavior
        const stickyHeader = document.getElementById('stickyHeader');
        const section32 = document.querySelector('h3.subsection-title:last-of-type');

        window.addEventListener('scroll', function() {{
            // Add shadow when scrolled
            if (window.scrollY > 10) {{
                stickyHeader.classList.add('scrolled');
            }} else {{
                stickyHeader.classList.remove('scrolled');
            }}

            // Stop sticky when section 3.2 is reached
            const fundingPctSection = document.getElementById('fundingPctSection');
            if (fundingPctSection) {{
                const rect = fundingPctSection.getBoundingClientRect();
                const headerHeight = stickyHeader.offsetHeight;
                if (rect.top <= headerHeight + 50) {{
                    stickyHeader.style.position = 'relative';
                }} else {{
                    stickyHeader.style.position = 'sticky';
                }}
            }}
        }});
    </script>
</body>
</html>'''

        # Save HTML
        output_path = self.output_dir / "company_historical.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Saved: {output_path}")
        return html_content

    def generate_warning_dashboard(self):
        """Generate complete warning system visualizations"""
        print("=" * 60)
        print("Generating Warning System Dashboard")
        print("=" * 60)

        # Load warning system data
        warning_data = self.load_warning_dashboard()
        funding_health = self.load_funding_health()
        supply_demand = self.load_supply_demand()
        credit_data = self.load_credit_market()

        if warning_data is None:
            print("No warning dashboard data available. Run warning system first.")
            return

        # Generate plots
        if MATPLOTLIB_AVAILABLE:
            print("\nGenerating warning charts...")

            if warning_data:
                self.plot_warning_signals(warning_data)

            if supply_demand:
                self.plot_supply_demand_projection(supply_demand)

            if funding_health:
                self.plot_funding_health_gauge(funding_health)

            if credit_data:
                self.plot_credit_market_trends(credit_data)
        else:
            print("\nSkipping charts - matplotlib not installed")

        # Generate HTML report
        print("\nGenerating warning HTML dashboard...")
        self.generate_warning_html_report(warning_data, funding_health, supply_demand)

        print(f"\nAll warning outputs saved to: {self.output_dir}")

    def generate_all(self, include_warning: bool = True):
        """Generate all visualizations and reports

        Args:
            include_warning: Whether to include warning system dashboard
        """
        print("=" * 60)
        print("Generating Visualizations")
        print("=" * 60)

        # Load data
        assessment = self.load_assessment()
        scenarios = self.load_scenarios()

        if assessment is None:
            print("No assessment data available. Run risk_calculator.py first.")
        else:
            # Generate plots
            if MATPLOTLIB_AVAILABLE:
                print("\nGenerating risk assessment charts...")
                self.plot_company_risk_comparison(assessment)
                self.plot_risk_breakdown(assessment)
                self.plot_indicator_heatmap(assessment)

                if scenarios:
                    self.plot_scenario_projections(scenarios)
            else:
                print("\nSkipping charts - matplotlib not installed")

            # Generate HTML report
            print("\nGenerating HTML report...")
            self.generate_html_report(assessment, scenarios)

        # Generate warning system dashboard
        if include_warning:
            print("\n")
            self.generate_warning_dashboard()

        # Generate company historical dashboard
        consolidated_data = self.load_consolidated_data()
        if consolidated_data:
            print("\nGenerating company historical dashboard...")
            self.generate_company_historical_html(consolidated_data)

        print(f"\nAll outputs saved to: {self.output_dir}")


def main():
    """Main function to generate visualizations"""
    dashboard = RiskDashboard()
    dashboard.generate_all()


if __name__ == "__main__":
    main()
