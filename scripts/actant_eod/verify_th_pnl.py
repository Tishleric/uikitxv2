#!/usr/bin/env python3
"""
Simple verification script to confirm Th PnL data integrity.
"""

from trading.actant.eod import ActantDataService
from pathlib import Path

def main():
    """Verify Th PnL data is working correctly."""
    print("🔍 Th PnL Data Verification")
    print("=" * 40)
    
    # Initialize service
    service = ActantDataService()
    json_file = Path('GE_XCME.ZN_20250528_124425.json')
    
    # Load data
    if json_file.exists():
        success = service.load_data_from_json(json_file)
        print(f"✅ Data loaded: {success}")
    else:
        print("❌ JSON file not found")
        return False
    
    # Test 1: Check categorization
    categories = service.categorize_metrics()
    th_pnl_metrics = categories.get("Th PnL", [])
    print(f"\n📊 Th PnL metrics in category: {th_pnl_metrics}")
    
    # Test 2: Test individual metric queries
    for metric in th_pnl_metrics:
        try:
            data = service.get_filtered_data(metrics=[metric])
            print(f"✅ {metric}: {len(data)} rows")
        except Exception as e:
            print(f"❌ {metric}: Error - {e}")
    
    # Test 3: Test all Th PnL metrics together
    try:
        all_th_pnl_data = service.get_filtered_data(metrics=th_pnl_metrics)
        print(f"\n✅ All Th PnL metrics together: {len(all_th_pnl_data)} rows")
        
        # Show sample data
        if not all_th_pnl_data.empty:
            print("\n📋 Sample Th PnL data:")
            print(all_th_pnl_data[['scenario_header', 'shock_type'] + th_pnl_metrics].head(3))
    except Exception as e:
        print(f"❌ All Th PnL query failed: {e}")
    
    # Test 4: Test prefix filtering on Th PnL
    for prefix in ["base", "ab", "bs", "pa"]:
        filtered_metrics = service.filter_metrics_by_prefix(th_pnl_metrics, prefix)
        print(f"🏷️  {prefix} prefix Th PnL metrics: {filtered_metrics}")
    
    # Test 5: Test dashboard-style query
    scenarios = service.get_scenario_headers()[:2]  # First 2 scenarios
    shock_types = service.get_shock_types()
    
    print(f"\n🎯 Dashboard-style queries:")
    for scenario in scenarios:
        for shock_type in shock_types:
            try:
                min_shock, max_shock = service.get_shock_range_by_scenario(scenario, shock_type)
                shock_ranges = {scenario: [min_shock, max_shock]}
                
                dashboard_data = service.get_filtered_data_with_range(
                    scenario_headers=[scenario],
                    shock_types=[shock_type],
                    shock_ranges=shock_ranges,
                    metrics=["Th PnL"]
                )
                
                print(f"✅ {scenario} ({shock_type}): {len(dashboard_data)} rows")
            except Exception as e:
                print(f"❌ {scenario} ({shock_type}): {e}")
    
    print("\n✅ Th PnL verification complete!")
    return True

if __name__ == "__main__":
    main() 