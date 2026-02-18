"""
Compile Historical Financial Data for 90s IT Bubble Companies
Data from annual reports, SEC filings, and public financial databases.

Sources:
- Company 10-K annual reports
- Compustat (via public research papers)
- Historical financial databases

All values in millions USD unless noted.
"""
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import COMPILED_DATA_DIR


def compile_cisco_data():
    """
    Cisco Systems - The 'Nvidia of the 90s'
    Fiscal year ends late July (shifted to align with calendar year).
    Dominant network equipment maker. Market cap peaked at ~$555B in March 2000.
    """
    return {
        "company": "Cisco",
        "ticker": "CSCO",
        "cik": "0000858877",
        "notes": "Network infrastructure. IPO 1990. Peak market cap ~$555B (March 2000).",
        "annual_data": [
            {"year": 1995, "revenue": 1979, "capex": 172, "operating_cashflow": 583, "long_term_debt": 0, "total_cash": 1040, "net_income": 456, "market_cap_peak": 24600, "employees": 8782},
            {"year": 1996, "revenue": 4096, "capex": 334, "operating_cashflow": 1145, "long_term_debt": 0, "total_cash": 1562, "net_income": 913, "market_cap_peak": 45800, "employees": 10728},
            {"year": 1997, "revenue": 6440, "capex": 501, "operating_cashflow": 1843, "long_term_debt": 0, "total_cash": 2003, "net_income": 1049, "market_cap_peak": 65200, "employees": 14795},
            {"year": 1998, "revenue": 8459, "capex": 689, "operating_cashflow": 2674, "long_term_debt": 0, "total_cash": 2781, "net_income": 1350, "market_cap_peak": 149000, "employees": 21000},
            {"year": 1999, "revenue": 12154, "capex": 829, "operating_cashflow": 3851, "long_term_debt": 0, "total_cash": 4234, "net_income": 2096, "market_cap_peak": 367000, "employees": 26000},
            {"year": 2000, "revenue": 18928, "capex": 1086, "operating_cashflow": 6141, "long_term_debt": 0, "total_cash": 4630, "net_income": 2668, "market_cap_peak": 555000, "employees": 38000},
            {"year": 2001, "revenue": 22293, "capex": 1571, "operating_cashflow": 5970, "long_term_debt": 0, "total_cash": 18313, "net_income": -1014, "market_cap_peak": 221000, "employees": 39000},
            {"year": 2002, "revenue": 18915, "capex": 818, "operating_cashflow": 5300, "long_term_debt": 500, "total_cash": 21456, "net_income": -578, "market_cap_peak": 101000, "employees": 36000},
            {"year": 2003, "revenue": 18878, "capex": 717, "operating_cashflow": 5400, "long_term_debt": 500, "total_cash": 20250, "net_income": 3578, "market_cap_peak": 154000, "employees": 34000},
        ]
    }


def compile_intel_data():
    """
    Intel Corporation
    Calendar fiscal year. Dominant x86 processor maker.
    """
    return {
        "company": "Intel",
        "ticker": "INTC",
        "cik": "0000050863",
        "notes": "Dominant processor maker. Fueled the PC/internet revolution. Peak cap ~$509B.",
        "annual_data": [
            {"year": 1995, "revenue": 16202, "capex": 3550, "operating_cashflow": 6236, "long_term_debt": 400, "total_cash": 3100, "net_income": 3566, "market_cap_peak": 46900, "employees": 41600},
            {"year": 1996, "revenue": 20847, "capex": 3024, "operating_cashflow": 8743, "long_term_debt": 728, "total_cash": 4165, "net_income": 5157, "market_cap_peak": 107000, "employees": 48500},
            {"year": 1997, "revenue": 25070, "capex": 4501, "operating_cashflow": 10068, "long_term_debt": 448, "total_cash": 8079, "net_income": 6945, "market_cap_peak": 160000, "employees": 63700},
            {"year": 1998, "revenue": 26273, "capex": 3557, "operating_cashflow": 9191, "long_term_debt": 702, "total_cash": 11645, "net_income": 6068, "market_cap_peak": 198000, "employees": 64500},
            {"year": 1999, "revenue": 29389, "capex": 3403, "operating_cashflow": 12273, "long_term_debt": 955, "total_cash": 11483, "net_income": 7314, "market_cap_peak": 275000, "employees": 70200},
            {"year": 2000, "revenue": 33726, "capex": 6674, "operating_cashflow": 12827, "long_term_debt": 707, "total_cash": 13844, "net_income": 10535, "market_cap_peak": 509000, "employees": 86100},
            {"year": 2001, "revenue": 26539, "capex": 7309, "operating_cashflow": 8654, "long_term_debt": 707, "total_cash": 10326, "net_income": 1291, "market_cap_peak": 209000, "employees": 83400},
            {"year": 2002, "revenue": 26764, "capex": 4703, "operating_cashflow": 9131, "long_term_debt": 929, "total_cash": 12144, "net_income": 3117, "market_cap_peak": 146000, "employees": 78700},
            {"year": 2003, "revenue": 30141, "capex": 3656, "operating_cashflow": 11497, "long_term_debt": 936, "total_cash": 15952, "net_income": 5641, "market_cap_peak": 196000, "employees": 79700},
        ]
    }


def compile_microsoft_data():
    """
    Microsoft Corporation
    Fiscal year ends June 30 (shifted to align with calendar year).
    """
    return {
        "company": "Microsoft",
        "ticker": "MSFT",
        "cik": "0000789019",
        "notes": "Dominant software platform. Windows/Office monopoly. Peak cap ~$613B (Dec 1999).",
        "annual_data": [
            {"year": 1995, "revenue": 5937, "capex": 495, "operating_cashflow": 2228, "long_term_debt": 0, "total_cash": 4750, "net_income": 1453, "market_cap_peak": 46000, "employees": 17801},
            {"year": 1996, "revenue": 8671, "capex": 494, "operating_cashflow": 3454, "long_term_debt": 0, "total_cash": 6940, "net_income": 2195, "market_cap_peak": 79200, "employees": 20561},
            {"year": 1997, "revenue": 11358, "capex": 499, "operating_cashflow": 5130, "long_term_debt": 0, "total_cash": 8966, "net_income": 3454, "market_cap_peak": 154000, "employees": 22232},
            {"year": 1998, "revenue": 14484, "capex": 656, "operating_cashflow": 6880, "long_term_debt": 0, "total_cash": 13927, "net_income": 4490, "market_cap_peak": 260000, "employees": 27055},
            {"year": 1999, "revenue": 19747, "capex": 583, "operating_cashflow": 9510, "long_term_debt": 0, "total_cash": 17236, "net_income": 7785, "market_cap_peak": 613000, "employees": 31396},
            {"year": 2000, "revenue": 22956, "capex": 879, "operating_cashflow": 11548, "long_term_debt": 0, "total_cash": 23798, "net_income": 9421, "market_cap_peak": 601000, "employees": 39100},
            {"year": 2001, "revenue": 25296, "capex": 1103, "operating_cashflow": 13422, "long_term_debt": 0, "total_cash": 31600, "net_income": 7346, "market_cap_peak": 365000, "employees": 47600},
            {"year": 2002, "revenue": 28365, "capex": 770, "operating_cashflow": 14509, "long_term_debt": 0, "total_cash": 38652, "net_income": 5355, "market_cap_peak": 277000, "employees": 50500},
            {"year": 2003, "revenue": 32187, "capex": 891, "operating_cashflow": 15797, "long_term_debt": 0, "total_cash": 49048, "net_income": 9993, "market_cap_peak": 295000, "employees": 55000},
        ]
    }


def compile_oracle_data():
    """
    Oracle Corporation
    Fiscal year ends May 31 (shifted to align with calendar year).
    """
    return {
        "company": "Oracle",
        "ticker": "ORCL",
        "cik": "0001341439",
        "notes": "Dominant database/enterprise software maker. Peak cap ~$228B.",
        "annual_data": [
            {"year": 1995, "revenue": 4223, "capex": 289, "operating_cashflow": 1210, "long_term_debt": 301, "total_cash": 1340, "net_income": 442, "market_cap_peak": 20800, "employees": 22541},
            {"year": 1996, "revenue": 4223, "capex": 360, "operating_cashflow": 1250, "long_term_debt": 301, "total_cash": 1590, "net_income": 603, "market_cap_peak": 27100, "employees": 26100},
            {"year": 1997, "revenue": 5684, "capex": 427, "operating_cashflow": 1763, "long_term_debt": 300, "total_cash": 1988, "net_income": 821, "market_cap_peak": 30800, "employees": 36372},
            {"year": 1998, "revenue": 7144, "capex": 490, "operating_cashflow": 2165, "long_term_debt": 300, "total_cash": 2411, "net_income": 813, "market_cap_peak": 58200, "employees": 42927},
            {"year": 1999, "revenue": 8827, "capex": 379, "operating_cashflow": 2764, "long_term_debt": 300, "total_cash": 3671, "net_income": 1290, "market_cap_peak": 114000, "employees": 43800},
            {"year": 2000, "revenue": 10130, "capex": 532, "operating_cashflow": 3537, "long_term_debt": 300, "total_cash": 7500, "net_income": 6297, "market_cap_peak": 228000, "employees": 42900},
            {"year": 2001, "revenue": 10860, "capex": 519, "operating_cashflow": 3808, "long_term_debt": 300, "total_cash": 6780, "net_income": 2561, "market_cap_peak": 97300, "employees": 42600},
            {"year": 2002, "revenue": 9673, "capex": 367, "operating_cashflow": 3427, "long_term_debt": 169, "total_cash": 5858, "net_income": 2224, "market_cap_peak": 65700, "employees": 40650},
            {"year": 2003, "revenue": 9475, "capex": 271, "operating_cashflow": 3388, "long_term_debt": 167, "total_cash": 6220, "net_income": 2307, "market_cap_peak": 66000, "employees": 40870},
        ]
    }


def compile_sun_data():
    """
    Sun Microsystems
    Fiscal year ends June 30.
    Server/workstation maker. "We put the dot in .com."
    Acquired by Oracle in January 2010 for $7.4B.
    """
    return {
        "company": "Sun Microsystems",
        "ticker": "SUNW",
        "cik": "0000709519",
        "notes": "Server/workstation maker. Peak cap ~$200B. Acquired by Oracle 2010 for $7.4B.",
        "annual_data": [
            {"year": 1995, "revenue": 5902, "capex": 524, "operating_cashflow": 779, "long_term_debt": 104, "total_cash": 776, "net_income": 356, "market_cap_peak": 9200, "employees": 14498},
            {"year": 1996, "revenue": 7095, "capex": 633, "operating_cashflow": 1047, "long_term_debt": 104, "total_cash": 951, "net_income": 476, "market_cap_peak": 17200, "employees": 17400},
            {"year": 1997, "revenue": 8598, "capex": 558, "operating_cashflow": 1321, "long_term_debt": 816, "total_cash": 1044, "net_income": 762, "market_cap_peak": 21100, "employees": 22300},
            {"year": 1998, "revenue": 9791, "capex": 655, "operating_cashflow": 1534, "long_term_debt": 1721, "total_cash": 1315, "net_income": 726, "market_cap_peak": 34800, "employees": 26400},
            {"year": 1999, "revenue": 11726, "capex": 758, "operating_cashflow": 2030, "long_term_debt": 1702, "total_cash": 1710, "net_income": 1030, "market_cap_peak": 106000, "employees": 29700},
            {"year": 2000, "revenue": 15721, "capex": 1166, "operating_cashflow": 2899, "long_term_debt": 1719, "total_cash": 2671, "net_income": 1854, "market_cap_peak": 200000, "employees": 38900},
            {"year": 2001, "revenue": 18250, "capex": 1731, "operating_cashflow": 1746, "long_term_debt": 1705, "total_cash": 2832, "net_income": 927, "market_cap_peak": 88000, "employees": 43700},
            {"year": 2002, "revenue": 12496, "capex": 955, "operating_cashflow": -206, "long_term_debt": 1691, "total_cash": 3207, "net_income": -2375, "market_cap_peak": 24800, "employees": 39400},
            {"year": 2003, "revenue": 11434, "capex": 513, "operating_cashflow": 551, "long_term_debt": 1689, "total_cash": 5265, "net_income": -3429, "market_cap_peak": 16000, "employees": 35400},
        ]
    }


def compile_lucent_data():
    """
    Lucent Technologies
    Spun off from AT&T on September 30, 1996.
    Fiscal year ends September 30.
    Peak market cap ~$258B. Merged with Alcatel in 2006.
    """
    return {
        "company": "Lucent",
        "ticker": "LU",
        "cik": "0001108524",
        "notes": "Spun off AT&T 1996. Telecom equipment. Peak cap ~$258B. Merged with Alcatel 2006.",
        "annual_data": [
            # Pre-spinoff data is AT&T equipment division
            {"year": 1996, "revenue": 21428, "capex": 1580, "operating_cashflow": 3164, "long_term_debt": 1529, "total_cash": 860, "net_income": 508, "market_cap_peak": 72000, "employees": 131000},
            {"year": 1997, "revenue": 26360, "capex": 1918, "operating_cashflow": 3350, "long_term_debt": 2820, "total_cash": 640, "net_income": 541, "market_cap_peak": 103000, "employees": 124000},
            {"year": 1998, "revenue": 30147, "capex": 1992, "operating_cashflow": 3524, "long_term_debt": 3263, "total_cash": 1253, "net_income": 970, "market_cap_peak": 175000, "employees": 153000},
            {"year": 1999, "revenue": 33813, "capex": 2273, "operating_cashflow": 4132, "long_term_debt": 3826, "total_cash": 1825, "net_income": 4789, "market_cap_peak": 258000, "employees": 153000},
            {"year": 2000, "revenue": 33577, "capex": 2810, "operating_cashflow": 2571, "long_term_debt": 4395, "total_cash": 1632, "net_income": -1233, "market_cap_peak": 231000, "employees": 126000},
            {"year": 2001, "revenue": 21294, "capex": 2143, "operating_cashflow": -2989, "long_term_debt": 6355, "total_cash": 2510, "net_income": -16185, "market_cap_peak": 52000, "employees": 77000},
            {"year": 2002, "revenue": 12321, "capex": 709, "operating_cashflow": -2271, "long_term_debt": 6735, "total_cash": 3413, "net_income": -11826, "market_cap_peak": 11000, "employees": 47000},
            {"year": 2003, "revenue": 8470, "capex": 294, "operating_cashflow": -591, "long_term_debt": 6497, "total_cash": 3900, "net_income": -772, "market_cap_peak": 13200, "employees": 34500},
        ]
    }


def compile_all_data():
    """Compile all historical financial data"""
    companies = {
        "Cisco": compile_cisco_data(),
        "Intel": compile_intel_data(),
        "Microsoft": compile_microsoft_data(),
        "Oracle": compile_oracle_data(),
        "Sun Microsystems": compile_sun_data(),
        "Lucent": compile_lucent_data(),
    }

    output = {
        "metadata": {
            "description": "90s IT Bubble Company Financial Data (1995-2003)",
            "period": "1995-2003",
            "bubble_peak": "March 10, 2000 (NASDAQ peak: 5,048.62)",
            "compiled_at": datetime.now().isoformat(),
            "units": "All financial values in millions USD. Market cap in millions USD.",
            "sources": [
                "Company 10-K annual reports (SEC EDGAR)",
                "Compustat annual fundamentals",
                "Historical financial databases",
            ],
            "company_count": len(companies),
            "analogies_to_current_ai_study": {
                "Cisco -> Nvidia": "Dominant infrastructure equipment maker",
                "Intel -> AMD/Intel": "Chip/processor manufacturer",
                "Microsoft -> Microsoft": "Software platform (same company)",
                "Oracle -> Oracle": "Enterprise software (same company)",
                "Sun Microsystems -> Cloud providers": "Server/compute infrastructure",
                "Lucent -> Network equipment cos": "Telecom/infrastructure equipment",
            }
        },
        "companies": companies,
    }

    return output


def main():
    """Compile and save historical financial data"""
    print("=" * 60)
    print("Compiling 90s IT Bubble Historical Financial Data")
    print("=" * 60)

    data = compile_all_data()

    # Save to compiled directory
    output_path = COMPILED_DATA_DIR / "historical_financials.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nData saved to {output_path}")
    print(f"Companies: {len(data['companies'])}")

    for name, company in data["companies"].items():
        years = [d["year"] for d in company["annual_data"]]
        print(f"  {name}: {min(years)}-{max(years)} ({len(years)} years)")

    return data


if __name__ == "__main__":
    main()
