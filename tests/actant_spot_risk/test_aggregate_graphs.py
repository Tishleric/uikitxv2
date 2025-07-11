"""
Test aggregate Greek graph functionality
"""
import pytest
import logging
from typing import Dict, List, Any
from apps.dashboards.spot_risk.callbacks import create_aggregate_greek_graph

logger = logging.getLogger(__name__)


def test_create_aggregate_greek_graph_single_expiry():
    """Test creating aggregate graph with single expiry"""
    # Mock profile data for one expiry
    profiles_by_expiry = {
        '11JUL25': {
            'strikes': [108.0, 109.0, 110.0, 111.0, 112.0],
            'greeks': {
                'delta': [0.1, 0.3, 0.5, 0.7, 0.9],
                'gamma': [0.05, 0.15, 0.20, 0.15, 0.05]
            },
            'positions': [
                {'strike': 109.0, 'position': 100, 'type': 'C', 'key': 'TEST1', 'current_greeks': {'delta': 0.3}},
                {'strike': 111.0, 'position': -50, 'type': 'P', 'key': 'TEST2', 'current_greeks': {'delta': 0.7}}
            ],
            'atm_strike': 110.0,
            'model_params': {'sigma': 0.75, 'tau': 0.25, 'F': 110.0}
        }
    }
    
    # Create aggregate graph for delta
    fig_dict = create_aggregate_greek_graph('delta', profiles_by_expiry, 'F')
    
    # Verify figure structure
    assert 'data' in fig_dict
    assert 'layout' in fig_dict
    
    # Should have 2 traces: line + markers
    assert len(fig_dict['data']) == 2
    
    # First trace should be the line
    line_trace = fig_dict['data'][0]
    assert line_trace['mode'] == 'lines'
    assert line_trace['name'] == '11JUL25'
    assert line_trace['x'] == [108.0, 109.0, 110.0, 111.0, 112.0]
    assert line_trace['y'] == [0.1, 0.3, 0.5, 0.7, 0.9]
    
    # Second trace should be position markers
    marker_trace = fig_dict['data'][1]
    assert marker_trace['mode'] == 'markers'
    assert len(marker_trace['x']) == 2  # 2 positions
    assert marker_trace['x'] == [109.0, 111.0]
    
    # Check layout
    layout = fig_dict['layout']
    assert 'title' in layout
    assert 'delta_F' in layout['title']['text']  # Should include space suffix
    assert 'shapes' in layout  # Should have ATM line
    
    # ATM line should be at 110.0
    atm_line = next((s for s in layout['shapes'] if s.get('type') == 'line'), None)
    assert atm_line is not None
    assert atm_line['x0'] == 110.0
    assert atm_line['x1'] == 110.0


def test_create_aggregate_greek_graph_multiple_expiries():
    """Test creating aggregate graph with multiple expiries"""
    # Mock profile data for multiple expiries
    profiles_by_expiry = {
        '11JUL25': {
            'strikes': [108.0, 109.0, 110.0, 111.0, 112.0],
            'greeks': {
                'gamma': [0.05, 0.15, 0.20, 0.15, 0.05]
            },
            'positions': [
                {'strike': 110.0, 'position': 200, 'type': 'C', 'key': 'TEST1', 'current_greeks': {'gamma': 0.20}}
            ],
            'atm_strike': 110.0,
            'model_params': {'sigma': 0.75, 'tau': 0.25, 'F': 110.0}
        },
        '14JUL25': {
            'strikes': [108.0, 109.0, 110.0, 111.0, 112.0],
            'greeks': {
                'gamma': [0.03, 0.10, 0.15, 0.10, 0.03]
            },
            'positions': [
                {'strike': 109.0, 'position': -100, 'type': 'P', 'key': 'TEST2', 'current_greeks': {'gamma': 0.10}}
            ],
            'atm_strike': 110.0,
            'model_params': {'sigma': 0.60, 'tau': 0.50, 'F': 110.0}
        }
    }
    
    # Create aggregate graph for gamma
    fig_dict = create_aggregate_greek_graph('gamma', profiles_by_expiry, 'F')
    
    # Should have 4 traces: 2 lines + 2 position markers
    assert len(fig_dict['data']) == 4
    
    # Check traces are in correct order (sorted by expiry)
    assert fig_dict['data'][0]['name'] == '11JUL25'  # First line
    assert fig_dict['data'][1]['name'] == '11JUL25 Positions'  # First positions
    assert fig_dict['data'][2]['name'] == '14JUL25'  # Second line
    assert fig_dict['data'][3]['name'] == '14JUL25 Positions'  # Second positions
    
    # Verify different colors used
    color1 = fig_dict['data'][0]['line']['color']
    color2 = fig_dict['data'][2]['line']['color']
    assert color1 != color2
    
    # Position markers should match line colors
    assert fig_dict['data'][1]['marker']['color'] == color1
    assert fig_dict['data'][3]['marker']['color'] == color2


def test_create_aggregate_greek_graph_y_space():
    """Test creating aggregate graph with Y-space Greeks"""
    profiles_by_expiry = {
        '11JUL25': {
            'strikes': [110.0, 111.0],
            'greeks': {
                'vega': [0.5, 0.3]
            },
            'positions': [],
            'atm_strike': 110.75,
            'model_params': {'sigma': 0.75, 'tau': 0.25, 'F': 110.75}
        }
    }
    
    # Create graph with Y-space
    fig_dict = create_aggregate_greek_graph('vega', profiles_by_expiry, 'y')
    
    # Check title includes correct suffix
    layout = fig_dict['layout']
    assert 'vega_y' in layout['title']['text']  # Should show Y-space suffix


def test_create_aggregate_greek_graph_missing_greek():
    """Test handling when Greek is missing from some expiries"""
    profiles_by_expiry = {
        '11JUL25': {
            'strikes': [110.0, 111.0],
            'greeks': {
                'delta': [0.5, 0.7]
            },
            'positions': [],
            'atm_strike': 110.75,
            'model_params': {'sigma': 0.75, 'tau': 0.25, 'F': 110.75}
        },
        '14JUL25': {
            'strikes': [110.0, 111.0],
            'greeks': {
                # No delta in this expiry
                'gamma': [0.1, 0.05]
            },
            'positions': [],
            'atm_strike': 110.75,
            'model_params': {'sigma': 0.60, 'tau': 0.50, 'F': 110.75}
        }
    }
    
    # Create graph for delta (missing from second expiry)
    fig_dict = create_aggregate_greek_graph('delta', profiles_by_expiry, 'F')
    
    # Should only have 1 trace (11JUL25) since 14JUL25 doesn't have delta
    assert len(fig_dict['data']) == 1
    assert fig_dict['data'][0]['name'] == '11JUL25'


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 