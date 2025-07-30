#!/usr/bin/env python
"""Test script to verify position-weighted Greek calculations in positions table."""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_position_weighted_greeks():
    """Test the position-weighted Greek calculations."""
    
    # Connect to databases
    trades_db = Path(project_root) / "trades.db"
    spot_risk_db = Path("data/output/spot_risk/spot_risk.db")
    
    if not trades_db.exists():
        print(f"trades.db not found at {trades_db}")
        return
        
    if not spot_risk_db.exists():
        print(f"spot_risk.db not found at {spot_risk_db}")
        return
    
    print("=" * 80)
    print("Position-Weighted Greeks Verification")
    print("=" * 80)
    
    # Connect to trades.db
    conn = sqlite3.connect(trades_db)
    cursor = conn.cursor()
    
    # Get positions with Greeks
    cursor.execute("""
        SELECT 
            symbol,
            open_position,
            delta_y,
            gamma_y,
            vega,
            theta,
            instrument_type,
            has_greeks
        FROM positions
        WHERE has_greeks = 1 AND open_position != 0
        ORDER BY symbol
        LIMIT 10
    """)
    
    positions = cursor.fetchall()
    
    if not positions:
        print("No positions with Greeks found.")
        conn.close()
        return
    
    # Connect to spot_risk.db to get per-unit Greeks for comparison
    spot_conn = sqlite3.connect(spot_risk_db)
    spot_cursor = spot_conn.cursor()
    
    print(f"\n{'Symbol':<15} {'Position':>10} {'Type':<8} {'Delta_Y':>12} {'Gamma_Y':>12} {'Vega':>12} {'Theta':>12}")
    print("-" * 85)
    
    for symbol, open_pos, delta_y, gamma_y, vega, theta, inst_type, _ in positions:
        # Get per-unit Greeks from spot_risk.db
        spot_cursor.execute("""
            SELECT 
                c.delta_y as unit_delta,
                c.gamma_y as unit_gamma,
                c.vega_y as unit_vega,
                c.theta_F as unit_theta
            FROM spot_risk_calculated c
            JOIN spot_risk_raw r ON c.raw_id = r.id
            WHERE r.bloomberg_symbol = ?
                AND c.calculation_status = 'success'
            ORDER BY c.calculation_timestamp DESC
            LIMIT 1
        """, (symbol,))
        
        unit_greeks = spot_cursor.fetchone()
        
        # Display position-weighted Greeks
        print(f"{symbol:<15} {open_pos:>10.2f} {inst_type:<8} "
              f"{delta_y:>12.4f} {gamma_y:>12.4f} {vega:>12.4f} {theta:>12.4f}")
        
        # If we have unit Greeks, verify the calculation
        if unit_greeks:
            unit_delta, unit_gamma, unit_vega, unit_theta = unit_greeks
            
            # Calculate what position-weighted should be
            expected_delta = unit_delta * open_pos if unit_delta else None
            expected_gamma = unit_gamma * open_pos if unit_gamma else None
            expected_vega = unit_vega * open_pos if unit_vega else None
            expected_theta = unit_theta * open_pos if unit_theta else None
            
            # Check if calculations match (within small tolerance for floating point)
            tolerance = 0.0001
            
            checks = []
            if expected_delta is not None and delta_y is not None:
                delta_match = abs(delta_y - expected_delta) < tolerance
                checks.append(f"Delta: {'✓' if delta_match else '✗'}")
                
            if expected_gamma is not None and gamma_y is not None:
                gamma_match = abs(gamma_y - expected_gamma) < tolerance
                checks.append(f"Gamma: {'✓' if gamma_match else '✗'}")
                
            if expected_vega is not None and vega is not None:
                vega_match = abs(vega - expected_vega) < tolerance
                checks.append(f"Vega: {'✓' if vega_match else '✗'}")
                
            if expected_theta is not None and theta is not None:
                theta_match = abs(theta - expected_theta) < tolerance
                checks.append(f"Theta: {'✓' if theta_match else '✗'}")
            
            if checks:
                print(f"{'':>34} Verification: {', '.join(checks)}")
    
    # Show summary
    print("\n" + "=" * 80)
    print("Summary:")
    print(f"- Checked {len(positions)} positions with Greeks")
    print("- Greek values in positions table are position-weighted (Greek * open_position)")
    print("- ✓ indicates position-weighted calculation matches expected value")
    print("- ✗ indicates mismatch (may need investigation)")
    
    conn.close()
    spot_conn.close()

if __name__ == "__main__":
    test_position_weighted_greeks() 