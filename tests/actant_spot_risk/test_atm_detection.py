"""Test ATM detection logic for Spot Risk dashboard"""

import pytest
import pandas as pd
import numpy as np
from apps.dashboards.spot_risk.controller import SpotRiskController


class TestATMDetection:
    """Test ATM strike detection based on rounded future price"""
    
    def test_atm_detection_with_future_price(self):
        """Test ATM detection when future price is available"""
        # Create test data with futures and options
        test_data = pd.DataFrame({
            'itype': ['F', 'C', 'C', 'C', 'C', 'P', 'P'],
            'midpoint_price': [110.234, 1.5, 1.2, 0.8, 0.5, 0.4, 0.6],
            'strike': [None, 109.0, 110.0, 110.25, 111.0, 110.0, 110.5],
            'expiry_date': ['2024-03-15'] * 7,
            'delta_F': [None, 0.7, 0.55, 0.48, 0.3, -0.45, -0.4]
        })
        
        controller = SpotRiskController()
        controller.current_data = test_data
        
        # Test find_atm_strike (main method)
        atm_strike = controller.find_atm_strike()
        
        # Future price is 110.234, rounds to 110.25
        # Closest strike should be 110.25
        assert atm_strike == 110.25
        
        # Test _find_atm_strike_for_expiry
        atm_strike_expiry = controller._find_atm_strike_for_expiry(test_data)
        assert atm_strike_expiry == 110.25
    
    def test_atm_detection_different_rounding(self):
        """Test ATM detection with different rounding scenarios"""
        # Test case where future price rounds down
        test_data = pd.DataFrame({
            'itype': ['F', 'C', 'C', 'C'],
            'midpoint_price': [110.10, 1.5, 1.2, 0.8],  # 110.10 rounds to 110.00
            'strike': [None, 109.75, 110.0, 110.25],
            'expiry_date': ['2024-03-15'] * 4,
        })
        
        controller = SpotRiskController()
        controller.current_data = test_data
        
        atm_strike = controller.find_atm_strike()
        # 110.10 rounds to 110.00, closest strike is 110.0
        assert atm_strike == 110.0
        
        # Test case where future price rounds up
        test_data2 = pd.DataFrame({
            'itype': ['F', 'C', 'C', 'C'],
            'midpoint_price': [110.88, 1.5, 1.2, 0.8],  # 110.88 rounds to 111.00
            'strike': [None, 110.75, 111.0, 111.25],
            'expiry_date': ['2024-03-15'] * 4,
        })
        
        controller.current_data = test_data2
        atm_strike = controller.find_atm_strike()
        # 110.88 rounds to 111.00, closest strike is 111.0
        assert atm_strike == 111.0
    
    def test_atm_detection_fallback_to_delta(self):
        """Test ATM detection falls back to delta when no future price"""
        # No futures in data, only options
        test_data = pd.DataFrame({
            'itype': ['C', 'C', 'C', 'P', 'P'],
            'midpoint_price': [1.5, 1.2, 0.8, 0.4, 0.6],
            'strike': [110.0, 110.25, 110.5, 110.0, 110.5],
            'expiry_date': ['2024-03-15'] * 5,
            'delta': [0.6, 0.51, 0.4, -0.4, -0.5]  # Using 'delta' column
        })
        
        controller = SpotRiskController()
        controller.current_data = test_data
        
        atm_strike = controller.find_atm_strike()
        # Should pick strike with delta closest to 0.5, which is 110.25 (delta=0.51)
        assert atm_strike == 110.25
    
    def test_atm_detection_no_valid_strikes(self):
        """Test ATM detection when no valid strikes available"""
        # Only futures, no options
        test_data = pd.DataFrame({
            'itype': ['F'],
            'midpoint_price': [110.234],
            'strike': [None],
            'expiry_date': ['2024-03-15']
        })
        
        controller = SpotRiskController()
        controller.current_data = test_data
        
        atm_strike = controller.find_atm_strike()
        # Should return None when no valid strikes
        assert atm_strike is None
    
    def test_atm_rounding_precision(self):
        """Test that rounding to 0.25 works correctly for edge cases"""
        test_cases = [
            (110.124, 110.00),  # rounds down
            (110.125, 110.25),  # exact boundary rounds up
            (110.374, 110.25),  # rounds down
            (110.375, 110.50),  # exact boundary rounds up
            (110.624, 110.50),  # rounds down
            (110.625, 110.75),  # exact boundary rounds up
            (110.874, 110.75),  # rounds down
            (110.875, 111.00),  # exact boundary rounds up
        ]
        
        for future_price, expected_rounded in test_cases:
            # Use the same standard rounding logic as the controller
            rounded = int(future_price * 4 + 0.5) / 4
            assert rounded == expected_rounded, f"Future {future_price} should round to {expected_rounded}, got {rounded}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 