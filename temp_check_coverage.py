import json

# Check raw SEC data for full coverage
with open('c:/Users/sudos/OneDrive/document/GitHub/ai-funding-risk/data/raw/sec_company_data.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

print("=" * 100)
print("原始 SEC 数据覆盖范围分析")
print("=" * 100)

for name in raw_data.keys():
    print(f"\n{'='*50}")
    print(f"{name}")
    print(f"{'='*50}")

    company = raw_data.get(name, {})
    metrics = company.get('metrics', {})

    # Check CapEx fields
    print("\n--- CapEx (PaymentsToAcquirePropertyPlantAndEquipment) ---")
    capex1 = metrics.get('PaymentsToAcquirePropertyPlantAndEquipment', [])
    annual1 = [x for x in capex1 if x.get('form') == '10-K']
    seen = {}
    for item in annual1:
        fy = item.get('fiscal_year')
        if fy and fy not in seen:
            seen[fy] = item
    sorted_years = sorted(seen.keys())
    print(f"  Fiscal Years: {sorted_years}")
    for fy in sorted_years[-6:]:  # Last 6 years
        item = seen[fy]
        value = item.get('value', 0) / 1e9
        end_date = item.get('end_date', 'N/A')
        print(f"    FY{fy}: ${value:.1f}B (end: {end_date})")

    print("\n--- CapEx Alt (PaymentsToAcquireProductiveAssets) ---")
    capex2 = metrics.get('PaymentsToAcquireProductiveAssets', [])
    annual2 = [x for x in capex2 if x.get('form') == '10-K']
    seen = {}
    for item in annual2:
        fy = item.get('fiscal_year')
        if fy and fy not in seen:
            seen[fy] = item
    sorted_years = sorted(seen.keys())
    if sorted_years:
        print(f"  Fiscal Years: {sorted_years}")
        for fy in sorted_years[-6:]:
            item = seen[fy]
            value = item.get('value', 0) / 1e9
            end_date = item.get('end_date', 'N/A')
            print(f"    FY{fy}: ${value:.1f}B (end: {end_date})")
    else:
        print("  No data")

    print("\n--- OCF (NetCashProvidedByUsedInOperatingActivities) ---")
    ocf = metrics.get('NetCashProvidedByUsedInOperatingActivities', [])
    annual_ocf = [x for x in ocf if x.get('form') == '10-K']
    seen = {}
    for item in annual_ocf:
        fy = item.get('fiscal_year')
        if fy and fy not in seen:
            seen[fy] = item
    sorted_years = sorted(seen.keys())
    print(f"  Fiscal Years: {sorted_years}")
    for fy in sorted_years[-6:]:
        item = seen[fy]
        value = item.get('value', 0) / 1e9
        end_date = item.get('end_date', 'N/A')
        print(f"    FY{fy}: ${value:.1f}B (end: {end_date})")
