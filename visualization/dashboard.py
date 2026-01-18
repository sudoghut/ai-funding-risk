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
        """Plot supply-demand balance projection"""
        if not MATPLOTLIB_AVAILABLE:
            return

        projections = supply_demand.get("projections", [])
        if not projections:
            return

        years = [p["year"] for p in projections]
        demand = [p["demand_B"] for p in projections]
        supply = [p["supply_B"] for p in projections]
        gap = [p["gap_B"] for p in projections]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Plot 1: Supply vs Demand
        ax1.plot(years, demand, 'r-o', label='Capital Demand', linewidth=2)
        ax1.plot(years, supply, 'g-o', label='Funding Supply', linewidth=2)
        ax1.fill_between(years, demand, supply, alpha=0.3,
                         color='green' if supply[-1] > demand[-1] else 'red')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Amount ($B)')
        ax1.set_title('AI Funding Supply vs Demand Projection')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Gap analysis
        colors = ['green' if g > 0 else 'red' for g in gap]
        ax2.bar(years, gap, color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Gap ($B)')
        ax2.set_title('Funding Gap (Positive = Surplus, Negative = Deficit)')
        ax2.grid(True, alpha=0.3, axis='y')

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

        # Supply-Demand Projections
        if supply_demand:
            projections = supply_demand.get("projections", [])
            if projections:
                html_parts.append("""
        <h2>5-Year Supply-Demand Projection</h2>
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
                for proj in projections:
                    gap_class = "positive" if proj.get("gap_B", 0) > 0 else "negative"
                    html_parts.append(f"""
                <tr>
                    <td>{proj.get('year', 'N/A')}</td>
                    <td>${proj.get('demand_B', 0):.0f}</td>
                    <td>${proj.get('supply_B', 0):.0f}</td>
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

        print(f"\nAll outputs saved to: {self.output_dir}")


def main():
    """Main function to generate visualizations"""
    dashboard = RiskDashboard()
    dashboard.generate_all()


if __name__ == "__main__":
    main()
