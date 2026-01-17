"""
Visualization Dashboard Module
Generates charts and reports for AI funding risk assessment
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import PROCESSED_DATA_DIR, RISK_LEVELS

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

    def generate_all(self):
        """Generate all visualizations and reports"""
        print("=" * 60)
        print("Generating Visualizations")
        print("=" * 60)

        # Load data
        assessment = self.load_assessment()
        scenarios = self.load_scenarios()

        if assessment is None:
            print("No assessment data available. Run risk_calculator.py first.")
            return

        # Generate plots
        if MATPLOTLIB_AVAILABLE:
            print("\nGenerating charts...")
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

        print(f"\nAll outputs saved to: {self.output_dir}")


def main():
    """Main function to generate visualizations"""
    dashboard = RiskDashboard()
    dashboard.generate_all()


if __name__ == "__main__":
    main()
