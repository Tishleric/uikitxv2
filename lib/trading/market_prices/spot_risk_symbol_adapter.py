"""
Spot Risk Symbol Adapter

Converts spot risk symbol format to Actant format that SymbolTranslator expects.
This allows us to use the more accurate weekday occurrence calculation.
"""

import re
from typing import Optional
from datetime import datetime
import logging

from lib.trading.symbol_translator import SymbolTranslator

logger = logging.getLogger(__name__)


class SpotRiskSymbolAdapter:
    """Adapts spot risk symbols to use the main SymbolTranslator."""
    
    # Month name to month number
    MONTH_TO_NUM = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4,
        'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8,
        'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    # Month name to month code
    MONTH_TO_CODE = {
        'JAN': 'F', 'FEB': 'G', 'MAR': 'H', 'APR': 'J',
        'MAY': 'K', 'JUN': 'M', 'JUL': 'N', 'AUG': 'Q',
        'SEP': 'U', 'OCT': 'V', 'NOV': 'X', 'DEC': 'Z'
    }
    
    # Series mapping for options
    SERIES_MAP = {
        'ZN': 'ZN',   # Standard/Friday
        'ZN2': 'VY',  # Monday weekly
        'ZN3': 'TJ',  # Tuesday weekly (maps to TJP in Bloomberg)
        'ZN4': 'WY',  # Wednesday weekly
        'ZN5': 'TH',  # Thursday weekly (maps to TJW)
        'ZN6': 'ZN',  # Friday weekly (same as standard)
        'VY': 'VY',   # Direct mappings
        'TJ': 'TJ',
        'GY': 'TJ',   # Tuesday (CME format)
        'WY': 'WY',   
        'TH': 'TH',
        'HY': 'TH',   # Thursday (CME format)
    }
    
    def __init__(self):
        self.translator = SymbolTranslator()
        # Spot risk patterns
        self.future_pattern = re.compile(r'XCME\.([A-Z]+)\.([A-Z]{3})(\d{2})')
        self.option_pattern = re.compile(r'XCME\.([A-Z]+\d?)\.(\d{1,2})([A-Z]{3})(\d{2})\.(\d+(?::\d+)?)\.([CP])')
        
    def translate(self, spot_risk_symbol: str) -> Optional[str]:
        """
        Translate spot risk symbol to Bloomberg format.
        
        Args:
            spot_risk_symbol: Symbol in spot risk format
            
        Returns:
            Bloomberg symbol or None if translation fails
        """
        try:
            # Try to convert to Actant format first
            actant_symbol = self._convert_to_actant(spot_risk_symbol)
            if actant_symbol:
                # Use the main translator
                bloomberg = self.translator.translate(actant_symbol)
                if bloomberg:
                    return bloomberg
                    
            # If conversion failed, fall back to direct translation
            return self._direct_translate(spot_risk_symbol)
            
        except Exception as e:
            logger.error(f"Error translating {spot_risk_symbol}: {e}")
            return None
            
    def _convert_to_actant(self, spot_risk_symbol: str) -> Optional[str]:
        """Convert spot risk format to Actant format."""
        
        # Try futures pattern first
        match = self.future_pattern.match(spot_risk_symbol)
        if match:
            product, month_str, year_str = match.groups()
            
            # Get month code
            month_code = self.MONTH_TO_CODE.get(month_str.upper())
            if not month_code:
                return None
                
            # Get month number
            month_num = self.MONTH_TO_NUM.get(month_str.upper())
            if not month_num:
                return None
                
            # Build date string (assuming 3rd Friday for futures)
            # This is approximate but good enough for symbol translation
            year = 2000 + int(year_str)
            date_str = f"{year}{month_num:02d}15"  # Mid-month approximation
            
            # Build Actant futures format: XCMEFFDPSX20250919U0ZN
            return f"XCMEFFDPSX{date_str}{month_code}0{product}"
            
        # Try options pattern
        match = self.option_pattern.match(spot_risk_symbol)
        if match:
            product, day, month_str, year_str, strike_str, option_type = match.groups()
            
            # Get series code
            series = self.SERIES_MAP.get(product, product)
            
            # Special handling for ZN with numbers (Friday weeklies)
            # ZN, ZN2, ZN3, etc. should all map to ZN for Friday
            if product.startswith('ZN'):
                series = 'ZN'
            elif len(series) > 2:
                series = series[:2]  # Take first 2 chars
                
            # Get month number
            month_num = self.MONTH_TO_NUM.get(month_str.upper())
            if not month_num:
                return None
                
            # Build full date
            year = 2000 + int(year_str)
            day_int = int(day)
            date_str = f"{year}{month_num:02d}{day_int:02d}"
            
            # Handle strike format
            if ':' in strike_str:
                # Convert 110:75 to 110.75
                parts = strike_str.split(':')
                whole = parts[0]
                fraction = parts[1]
                if len(fraction) == 1:
                    fraction = fraction + '0'
                strike = f"{whole}.{fraction}"
            else:
                strike = strike_str
                
            # Determine option type code
            option_code = 'OCAD' if option_type == 'C' else 'OPAD'
            
            # Build Actant option format: XCMEOCADPS20250714N0VY2/108.75
            return f"XCME{option_code}PS{date_str}N0{series}2/{strike}"
            
        return None
        
    def _direct_translate(self, spot_risk_symbol: str) -> Optional[str]:
        """Direct translation without going through Actant format."""
        
        # Use the SpotRiskSymbolTranslator as fallback
        from lib.trading.actant.spot_risk.spot_risk_symbol_translator import SpotRiskSymbolTranslator
        fallback = SpotRiskSymbolTranslator()
        return fallback.translate(spot_risk_symbol) 