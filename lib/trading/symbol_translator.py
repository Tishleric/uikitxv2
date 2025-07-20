"""
Symbol Translator for Actant to Bloomberg Format

Handles conversion from Actant proprietary format to Bloomberg symbols for options.
The key insight is that the Bloomberg occurrence number represents the nth occurrence
of that weekday in the month (e.g., 2nd Monday = 2).
"""

import re
from datetime import datetime
from typing import Optional, Dict, Tuple
import calendar

class SymbolTranslator:
    """Translates Actant symbols to Bloomberg format"""
    
    # Actant series to Bloomberg contract codes and weekdays
    SERIES_TO_CONTRACT: Dict[str, Tuple[str, int]] = {
        'VY': ('VBY', calendar.MONDAY),      # Monday
        'TJ': ('TJP', calendar.TUESDAY),     # Tuesday  
        'GY': ('TJP', calendar.TUESDAY),     # Tuesday (CME Globex)
        'WY': ('TYY', calendar.WEDNESDAY),   # Wednesday (CTO shows TYY not TYW)
        'TH': ('TJW', calendar.THURSDAY),    # Thursday
        'HY': ('TJW', calendar.THURSDAY),    # Thursday (CME Globex)
        'ZN': ('3M', calendar.FRIDAY),       # Friday (special format)
    }
    
    # CME Globex to Actant series mapping (from CTO document)
    CME_TO_ACTANT: Dict[str, str] = {
        'VY': 'VY',  # Monday
        'GY': 'TJ',  # Tuesday (GY in CME -> TJ in Actant)
        'WY': 'WY',  # Wednesday
        'HY': 'TH',  # Thursday (HY in CME -> TH in Actant)
        'ZN': 'ZN',  # Friday
    }
    
    # Month codes for Bloomberg
    MONTH_CODES = {
        1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
        7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
    }
    
    # Futures product code mappings (Actant -> Bloomberg)
    FUTURES_PRODUCT_MAP = {
        'ZN': 'TY',  # 10-Year Treasury Note
        'TY': 'TY',  # Already correct
        'TU': 'TU',  # 2-Year Treasury Note
        'FV': 'FV',  # 5-Year Treasury Note
        'US': 'US',  # Ultra Treasury Bond
        'RX': 'RX',  # Euro-Bund
    }
    
    def __init__(self):
        # Regex pattern for Actant options format
        self.actant_option_pattern = re.compile(
            r'XCME(OCAD|OPAD)PS(\d{8})N0([A-Z]{2})(\d+)/(\d+(?:\.\d+)?)'
        )
        # Regex pattern for Actant futures format
        # Example: XCMEFFDPSX20250919U0ZN
        self.actant_futures_pattern = re.compile(
            r'XCMEFFDPSX(\d{8})([A-Z])(\d)([A-Z]{2})'
        )
    
    def get_occurrence_in_month(self, date: datetime, target_weekday: int) -> int:
        """
        Calculate which occurrence of the weekday this date is in the month.
        For example, July 14, 2025 (Monday) is the 2nd Monday of July.
        """
        occurrence = 0
        for day in range(1, date.day + 1):
            check_date = date.replace(day=day)
            if check_date.weekday() == target_weekday:
                occurrence += 1
        return occurrence
    
    def translate(self, actant_symbol: str) -> Optional[str]:
        """
        Translate Actant symbol to Bloomberg format.
        
        Examples:
            Options: XCMEOCADPS20250714N0VY2/108.75 -> VBYN25C2 108.750 Comdty
            Futures: XCMEFFDPSX20250919U0ZN -> TYU5 Comdty
        """
        # Try options pattern first
        match = self.actant_option_pattern.match(actant_symbol)
        if match:
            return self._translate_option(match)
            
        # Try futures pattern
        match = self.actant_futures_pattern.match(actant_symbol)
        if match:
            return self._translate_future(match)
            
        return None
    
    def _translate_option(self, match) -> Optional[str]:
        """Translate option symbol match to Bloomberg format."""
            
        option_type_code, date_str, series, series_num, strike = match.groups()
        
        # Parse option type
        option_type = 'C' if option_type_code == 'OCAD' else 'P'
        
        # Parse date
        try:
            date = datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            return None
            
        # Get Bloomberg contract and weekday
        if series not in self.SERIES_TO_CONTRACT:
            return None
        contract_code, target_weekday = self.SERIES_TO_CONTRACT[series]
        
        # Calculate occurrence of weekday in month
        occurrence = self.get_occurrence_in_month(date, target_weekday)
        
        # Get month and year codes
        month_code = self.MONTH_CODES.get(date.month)
        if not month_code:
            return None
        year_code = str(date.year % 100)
        
        # Format strike to always have 3 decimal places (match price file format)
        strike_float = float(strike)
        strike_formatted = f"{strike_float:.3f}"
        
        # Special handling for Friday format (uses week number + MA)
        if contract_code == '3M':
            # Friday uses format like 2MA (week number + MA) per CTO document
            # For backward compatibility, also support 3MN5 format
            if occurrence:
                # New format: 2MA C 110.750 Comdty
                bloomberg_symbol = f"{occurrence}MA {option_type} {strike_formatted} Comdty"
            else:
                # Legacy format: 3MN5C 110.750 Comdty
                bloomberg_symbol = f"{contract_code}{month_code}{year_code[-1]}{option_type} {strike_formatted} Comdty"
        else:
            # Standard weekday format: VBYN25C2 110.750 Comdty
            bloomberg_symbol = f"{contract_code}{month_code}{year_code}{option_type}{occurrence} {strike_formatted} Comdty"
            
        return bloomberg_symbol
    
    def _translate_future(self, match) -> Optional[str]:
        """
        Translate futures symbol match to Bloomberg format.
        
        Example: XCMEFFDPSX20250919U0ZN -> TYU5 Comdty
        """
        date_str, month_code, year_digit, product_code = match.groups()
        
        # Map product code to Bloomberg symbol
        bloomberg_product = self.FUTURES_PRODUCT_MAP.get(product_code)
        if not bloomberg_product:
            return None
            
        # Extract year from date string to get the last digit
        try:
            date = datetime.strptime(date_str, '%Y%m%d')
            year_last_digit = str(date.year % 10)
        except ValueError:
            return None
            
        # Construct Bloomberg symbol: {Product}{Month}{Year} Comdty
        bloomberg_symbol = f"{bloomberg_product}{month_code}{year_last_digit} Comdty"
        
        return bloomberg_symbol 