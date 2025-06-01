#!/usr/bin/env python3
"""
Data Integrity Verification Script for ActantEOD Dashboard

This script performs comprehensive checks to ensure no data is lost or misprocessed
throughout the data pipeline from JSON → SQLite → UI → Visualizations.
"""

import json
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Any
from trading.actant.eod import ActantDataService

class DataIntegrityChecker:
    """Comprehensive data integrity verification for ActantEOD dashboard."""
    
    def __init__(self, json_file_path: Path):
        self.json_file = json_file_path
        self.service = ActantDataService()
        self.raw_json_data = None
        self.issues = []
        
    def load_raw_json(self) -> Dict[str, Any]:
        """Load and parse raw JSON data."""
        print(f"📁 Loading raw JSON: {self.json_file}")
        with open(self.json_file, 'r') as f:
            self.raw_json_data = json.load(f)
        
        print(f"✅ Raw JSON loaded: {len(self.raw_json_data)} top-level entries")
        return self.raw_json_data
    
    def check_json_to_sqlite_integrity(self) -> Dict[str, Any]:
        """Verify data integrity from JSON to SQLite."""
        print("\n🔍 CHECKING: JSON → SQLite Data Integrity")
        
        # Load data into SQLite
        success = self.service.load_data_from_json(self.json_file)
        if not success:
            self.issues.append("❌ Failed to load JSON into SQLite")
            return {}
        
        # Get raw metrics from JSON
        raw_metrics = self._extract_metrics_from_json()
        print(f"📊 Raw JSON metrics found: {len(raw_metrics)}")
        
        # Get metrics from SQLite
        db_metrics = set(self.service.get_metric_names())
        print(f"🗄️  SQLite metrics found: {len(db_metrics)}")
        
        # Compare
        missing_in_db = raw_metrics - db_metrics
        extra_in_db = db_metrics - raw_metrics
        
        if missing_in_db:
            self.issues.append(f"❌ Metrics missing in SQLite: {sorted(missing_in_db)}")
        
        if extra_in_db:
            self.issues.append(f"⚠️  Extra metrics in SQLite: {sorted(extra_in_db)}")
        
        if not missing_in_db and not extra_in_db:
            print("✅ JSON → SQLite: All metrics preserved")
        
        return {
            "raw_metrics_count": len(raw_metrics),
            "db_metrics_count": len(db_metrics),
            "missing_in_db": sorted(missing_in_db),
            "extra_in_db": sorted(extra_in_db)
        }
    
    def check_metric_categorization_integrity(self) -> Dict[str, Any]:
        """Verify metric categorization is comprehensive."""
        print("\n🔍 CHECKING: Metric Categorization Integrity")
        
        all_metrics = set(self.service.get_metric_names())
        categories = self.service.categorize_metrics()
        
        categorized_metrics = set()
        for category, metrics in categories.items():
            categorized_metrics.update(metrics)
        
        uncategorized = all_metrics - categorized_metrics
        
        if uncategorized:
            self.issues.append(f"❌ Uncategorized metrics: {sorted(uncategorized)}")
        else:
            print("✅ All metrics properly categorized")
        
        # Check specific Th PnL metrics
        th_pnl_metrics = categories.get("Th PnL", [])
        print(f"💰 Th PnL category metrics: {th_pnl_metrics}")
        
        # Find all metrics containing "PnL" in raw data
        all_pnl_metrics = {m for m in all_metrics if "PnL" in m or "pnl" in m.lower()}
        missing_pnl = all_pnl_metrics - set(th_pnl_metrics)
        
        if missing_pnl:
            self.issues.append(f"❌ PnL metrics not in Th PnL category: {sorted(missing_pnl)}")
        
        return {
            "total_metrics": len(all_metrics),
            "categorized_metrics": len(categorized_metrics),
            "uncategorized_metrics": sorted(uncategorized),
            "th_pnl_metrics": th_pnl_metrics,
            "all_pnl_metrics": sorted(all_pnl_metrics),
            "missing_pnl": sorted(missing_pnl)
        }
    
    def check_filtering_integrity(self) -> Dict[str, Any]:
        """Verify filtering doesn't drop data unexpectedly."""
        print("\n🔍 CHECKING: Data Filtering Integrity")
        
        scenarios = self.service.get_scenario_headers()
        shock_types = self.service.get_shock_types()
        metrics = self.service.get_metric_names()
        
        print(f"📋 Scenarios: {len(scenarios)}")
        print(f"⚡ Shock types: {shock_types}")
        print(f"📊 Total metrics: {len(metrics)}")
        
        # Test filtering with different combinations
        results = {}
        
        # Test each shock type
        for shock_type in shock_types:
            filtered_data = self.service.get_filtered_data(shock_types=[shock_type])
            results[f"shock_type_{shock_type}"] = len(filtered_data)
            print(f"📊 {shock_type} data rows: {len(filtered_data)}")
        
        # Test each prefix filter
        prefix_filters = ["all", "base", "ab", "bs", "pa"]
        for prefix in prefix_filters:
            filtered_metrics = self.service.filter_metrics_by_prefix(metrics, prefix)
            results[f"prefix_{prefix}"] = len(filtered_metrics)
            print(f"🏷️  {prefix} prefix metrics: {len(filtered_metrics)}")
        
        # Test Th PnL specifically
        try:
            th_pnl_data = self.service.get_filtered_data(metrics=["Th PnL"])
            results["th_pnl_rows"] = len(th_pnl_data)
            print(f"💰 Th PnL data rows: {len(th_pnl_data)}")
        except Exception as e:
            print(f"❌ Error querying Th PnL: {e}")
            self.issues.append(f"❌ SQL error with 'Th PnL' metric: {str(e)}")
            results["th_pnl_rows"] = 0
        
        if results.get("th_pnl_rows", 0) == 0:
            self.issues.append("❌ No Th PnL data found in database")
        
        return results
    
    def check_visualization_data_integrity(self) -> Dict[str, Any]:
        """Verify visualization data matches filtered data."""
        print("\n🔍 CHECKING: Visualization Data Integrity")
        
        scenarios = self.service.get_scenario_headers()[:2]  # Test first 2 scenarios
        shock_types = self.service.get_shock_types()
        
        results = {}
        
        for scenario in scenarios:
            for shock_type in shock_types:
                # Get range for this scenario/shock type
                min_shock, max_shock = self.service.get_shock_range_by_scenario(scenario, shock_type)
                
                # Get filtered data using dashboard method
                shock_ranges = {scenario: [min_shock, max_shock]}
                dashboard_data = self.service.get_filtered_data_with_range(
                    scenario_headers=[scenario],
                    shock_types=[shock_type],
                    shock_ranges=shock_ranges
                )
                
                # Get data using original method
                original_data = self.service.get_filtered_data(
                    scenario_headers=[scenario],
                    shock_types=[shock_type]
                )
                
                key = f"{scenario}_{shock_type}"
                results[key] = {
                    "dashboard_rows": len(dashboard_data),
                    "original_rows": len(original_data),
                    "range": [min_shock, max_shock]
                }
                
                if len(dashboard_data) != len(original_data):
                    self.issues.append(f"❌ Data mismatch for {key}: {len(dashboard_data)} vs {len(original_data)}")
        
        return results
    
    def _extract_metrics_from_json(self) -> Set[str]:
        """Extract all metric names from raw JSON data."""
        metrics = set()
        
        if not self.raw_json_data:
            return metrics
        
        # Navigate the JSON structure to find all metric keys
        for scenario_key, scenario_data in self.raw_json_data.items():
            if isinstance(scenario_data, dict):
                for shock_key, shock_data in scenario_data.items():
                    if isinstance(shock_data, dict):
                        # Extract metric names (excluding system fields)
                        system_fields = {"uprice", "point_header_original"}
                        for key in shock_data.keys():
                            if key not in system_fields:
                                metrics.add(key)
        
        return metrics
    
    def generate_report(self) -> str:
        """Generate comprehensive integrity report."""
        print("\n📋 GENERATING INTEGRITY REPORT")
        print("=" * 60)
        
        report = []
        report.append("# ActantEOD Data Integrity Report")
        report.append(f"📁 JSON File: {self.json_file}")
        report.append(f"📅 Generated: {pd.Timestamp.now()}")
        report.append("")
        
        if self.issues:
            report.append("## ❌ ISSUES FOUND:")
            for issue in self.issues:
                report.append(f"- {issue}")
        else:
            report.append("## ✅ NO ISSUES FOUND - Data integrity verified!")
        
        report.append("")
        report.append("## 📊 Summary Statistics:")
        
        # Get final stats
        scenarios = self.service.get_scenario_headers()
        metrics = self.service.get_metric_names()
        categories = self.service.categorize_metrics()
        
        report.append(f"- Total scenarios: {len(scenarios)}")
        report.append(f"- Total metrics: {len(metrics)}")
        report.append(f"- Categories: {len(categories)}")
        report.append(f"- Th PnL metrics: {len(categories.get('Th PnL', []))}")
        
        # Print and return report
        report_text = "\n".join(report)
        print(report_text)
        
        return report_text
    
    def run_full_check(self) -> Dict[str, Any]:
        """Run all integrity checks."""
        print("🚀 STARTING COMPREHENSIVE DATA INTEGRITY CHECK")
        print("=" * 60)
        
        self.load_raw_json()
        
        results = {}
        results["json_to_sqlite"] = self.check_json_to_sqlite_integrity()
        results["categorization"] = self.check_metric_categorization_integrity()
        results["filtering"] = self.check_filtering_integrity()
        results["visualization"] = self.check_visualization_data_integrity()
        
        report = self.generate_report()
        results["report"] = report
        results["issues"] = self.issues
        
        return results

def main():
    """Run data integrity check on the most recent JSON file."""
    json_file = Path("GE_XCME.ZN_20250528_124425.json")
    
    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        return
    
    checker = DataIntegrityChecker(json_file)
    results = checker.run_full_check()
    
    # Save report
    report_file = Path("data_integrity_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(results["report"])
    
    print(f"\n📄 Report saved to: {report_file}")
    
    return results

if __name__ == "__main__":
    results = main() 