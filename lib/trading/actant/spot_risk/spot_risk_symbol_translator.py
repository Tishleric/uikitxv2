"""
Spot Risk Symbol Translator

Converts spot risk symbol format to Bloomberg format.
Spot risk format: XCME.ZN.SEP25 (futures), XCME.ZN2.11JUL25.110:25.C (options)
Bloomberg format: TYU5 Comdty (futures), VBYN25C2 110.750 Comdty (options)
"""

import re
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SpotRiskSymbolTranslator:
    """Translates spot risk symbols to Bloomberg format."""
    
    # Month codes
    MONTH_MAP = {
        'JAN': 'F', 'FEB': 'G', 'MAR': 'H', 'APR': 'J',
        'MAY': 'K', 'JUN': 'M', 'JUL': 'N', 'AUG': 'Q',
        'SEP': 'U', 'OCT': 'V', 'NOV': 'X', 'DEC': 'Z'
    }
    
    # Product mappings
    PRODUCT_MAP = {
        'ZN': 'TY',  # 10-Year Treasury Note
        'ZN2': 'TY', # Also 10-Year (with suffix)
        'TU': 'TU',  # 2-Year Treasury Note
        'FV': 'FV',  # 5-Year Treasury Note
        'US': 'US',  # Ultra Treasury Bond
        'ZB': 'US',  # Also Ultra Bond
    }
    
    # Weekly option series mapping (futures contract codes)
    WEEKLY_SERIES_MAP = {
        'ZN': 'TY',   # Standard
        'ZN2': 'VBY', # Monday weekly
        'ZN3': 'TJP', # Tuesday weekly
        'ZN4': 'TYW', # Wednesday weekly
        'ZN5': 'TJW', # Thursday weekly
        'ZN6': '3M',  # Friday weekly
    }
    
    def __init__(self):
        # Regex patterns
        self.future_pattern = re.compile(r'XCME\.([A-Z]+)\.([A-Z]{3})(\d{2})')
        # Updated pattern to handle colon notation in strikes (e.g., 110:75 for 110.75)
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
            # Try futures pattern first
            match = self.future_pattern.match(spot_risk_symbol)
            if match:
                return self._translate_future(match)
                
            # Try options pattern
            match = self.option_pattern.match(spot_risk_symbol)
            if match:
                return self._translate_option(match)
                
            logger.warning(f"Symbol doesn't match any pattern: {spot_risk_symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error translating {spot_risk_symbol}: {e}")
            return None
    
    def _translate_future(self, match) -> str:
        """Translate futures symbol."""
        product, month_str, year_str = match.groups()
        
        # Map product
        bloomberg_product = self.PRODUCT_MAP.get(product, product)
        
        # Map month
        month_code = self.MONTH_MAP.get(month_str.upper())
        if not month_code:
            raise ValueError(f"Unknown month: {month_str}")
            
        # Year - last digit only
        year_digit = year_str[-1]
        
        return f"{bloomberg_product}{month_code}{year_digit} Comdty"
    
    def _translate_option(self, match) -> str:
        """Translate options symbol."""
        product, day, month_str, year_str, strike_str, option_type = match.groups()
        
        # Determine contract code based on product suffix
        if product in self.WEEKLY_SERIES_MAP:
            contract_code = self.WEEKLY_SERIES_MAP[product]
        else:
            # Default to standard if no suffix
            contract_code = 'TY'
            
        # Map month
        month_code = self.MONTH_MAP.get(month_str.upper())
        if not month_code:
            raise ValueError(f"Unknown month: {month_str}")
            
        # Year - for non-Friday weeklies use 2 digits, Friday uses 1
        if contract_code == '3M':  # Friday
            year_code = year_str[-1]
        else:
            year_code = year_str
            
        # Calculate weekday occurrence (simplified - would need full calendar logic)
        # For now, approximate based on day of month
        day_int = int(day)
        occurrence = ((day_int - 1) // 7) + 1
        
        # Format strike price - handle whole numbers, decimals, and colon notation
        if ':' in strike_str:
            # Handle colon notation (e.g., 110:75 -> 110.75, 110:5 -> 110.50)
            parts = strike_str.split(':')
            whole = parts[0]
            fraction = parts[1]
            # Pad single digit fractions (e.g., :5 -> :50)
            if len(fraction) == 1:
                fraction = fraction + '0'
            strike_float = float(f"{whole}.{fraction}")
        else:
            # Handle regular formats (110 or 110.5)
            strike_float = float(strike_str)
        strike_formatted = f"{strike_float:.3f}"
        
        # Build Bloomberg symbol
        if contract_code == '3M':  # Friday format
            bloomberg_symbol = f"{contract_code}{month_code}{year_code}{option_type} {strike_formatted} Comdty"
        else:
            bloomberg_symbol = f"{contract_code}{month_code}{year_code}{option_type}{occurrence} {strike_formatted} Comdty"
            
        return bloomberg_symbol


# Example usage:
if __name__ == "__main__":
    translator = SpotRiskSymbolTranslator()
    
    # Test futures
    print(translator.translate("XCME.ZN.SEP25"))  # Should output: TYU5 Comdty
    
    # Test options
    print(translator.translate("XCME.ZN2.11JUL25.110:25.C"))  # Should output: VBYN25C2 110.250 Comdty 