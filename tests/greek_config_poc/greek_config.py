"""
Greek Configuration Module - Proof of Concept
Allows selective calculation of Greeks for performance optimization.
"""

from typing import Dict, List, Set
import os

# Default Greek configuration
DEFAULT_ENABLED_GREEKS = {
    # First-order Greeks (enabled by default)
    'delta_F': True,
    'delta_y': True,
    'theta_F': True,
    
    # Second-order Greeks (enabled by default)
    'gamma_F': True,
    'gamma_y': True,
    'speed_F': True,
    'speed_y': True,  # Calculated from speed_F
    
    # Optional Greeks (disabled by default for performance)
    'vega_price': False,
    'vega_y': False,
    'volga_price': False,
    'vanna_F_price': False,
    'charm_F': False,
    'color_F': False,
    'ultima': False,
    'zomma': False
}

# Greeks required for positions aggregator
REQUIRED_FOR_POSITIONS = {'delta_y', 'gamma_y', 'speed_y', 'theta_F', 'vega_y'}

# All possible Greeks
ALL_GREEKS = set(DEFAULT_ENABLED_GREEKS.keys()) | {'speed_y'}


class GreekConfiguration:
    """Manages Greek calculation configuration."""
    
    def __init__(self, enabled_greeks: Dict[str, bool] = None):
        """
        Initialize Greek configuration.
        
        Args:
            enabled_greeks: Dictionary of Greek names to enabled status.
                          If None, uses DEFAULT_ENABLED_GREEKS.
        """
        self.enabled_greeks = enabled_greeks or DEFAULT_ENABLED_GREEKS.copy()
        self._load_from_env()
        self._validate_configuration()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_greeks = os.environ.get('SPOT_RISK_GREEKS_ENABLED')
        if env_greeks:
            # Parse comma-separated list of Greek names
            enabled_list = [g.strip() for g in env_greeks.split(',')]
            # Disable all Greeks first
            for greek in self.enabled_greeks:
                self.enabled_greeks[greek] = False
            # Enable specified Greeks
            for greek in enabled_list:
                if greek in self.enabled_greeks:
                    self.enabled_greeks[greek] = True
    
    def _validate_configuration(self):
        """Validate that required Greeks are enabled."""
        # Check if we need position Greeks
        needs_positions = os.environ.get('SPOT_RISK_POSITIONS_ENABLED', '1') == '1'
        
        if needs_positions:
            missing_required = []
            for greek in REQUIRED_FOR_POSITIONS:
                # Handle derived Greeks
                if greek == 'speed_y' and self.enabled_greeks.get('speed_F'):
                    continue  # speed_y is calculated from speed_F
                elif greek in self.enabled_greeks and not self.enabled_greeks.get(greek):
                    missing_required.append(greek)
            
            if missing_required:
                print(f"Warning: Enabling required Greeks for positions: {missing_required}")
                for greek in missing_required:
                    if greek in self.enabled_greeks:
                        self.enabled_greeks[greek] = True
    
    def get_enabled_greeks(self) -> Set[str]:
        """Get set of enabled Greek names."""
        enabled = {k for k, v in self.enabled_greeks.items() if v}
        # Add derived Greeks
        if 'speed_F' in enabled:
            enabled.add('speed_y')
        return enabled
    
    def get_disabled_greeks(self) -> Set[str]:
        """Get set of disabled Greek names."""
        return ALL_GREEKS - self.get_enabled_greeks()
    
    def is_enabled(self, greek_name: str) -> bool:
        """Check if a specific Greek is enabled."""
        if greek_name == 'speed_y':
            return self.enabled_greeks.get('speed_F', False)
        return self.enabled_greeks.get(greek_name, False)
    
    def get_api_requested_greeks(self) -> List[str]:
        """Get list of Greeks to request from the bond_future_options API."""
        # The API expects these specific Greek names
        api_greeks = []
        enabled = self.get_enabled_greeks()
        
        # Map our Greek names to API Greek names
        greek_mapping = {
            'delta_F': 'delta_F',
            'delta_y': 'delta_y',
            'gamma_F': 'gamma_F',
            'gamma_y': 'gamma_y',
            'vega_price': 'vega_price',
            'vega_y': 'vega_y',
            'theta_F': 'theta_F',
            'volga_price': 'volga_price',
            'vanna_F_price': 'vanna_F_price',
            'charm_F': 'charm_F',
            'speed_F': 'speed_F',
            'color_F': 'color_F',
            'ultima': 'ultima',
            'zomma': 'zomma'
        }
        
        for our_name, api_name in greek_mapping.items():
            if our_name in enabled:
                api_greeks.append(api_name)
        
        return api_greeks
    
    def summary(self) -> str:
        """Get human-readable summary of configuration."""
        enabled = self.get_enabled_greeks()
        disabled = self.get_disabled_greeks()
        
        lines = [
            "Greek Configuration Summary:",
            f"Enabled ({len(enabled)}): {', '.join(sorted(enabled))}",
            f"Disabled ({len(disabled)}): {', '.join(sorted(disabled))}"
        ]
        
        return '\n'.join(lines)