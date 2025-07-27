"""
RosettaStone - Universal symbol translator using ExpirationCalendar_CLEANED.csv as source of truth.

This module serves as the single source of truth for all symbol translations,
replacing complex regex-based translation with simple CSV lookups and handling 
all special cases for weekly, Friday, and quarterly options.
"""

import re
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple, NamedTuple
from enum import Enum
import calendar
from datetime import datetime

from .strike_converter import StrikeConverter


class SymbolFormat(Enum):
    """Supported symbol formats."""
    BLOOMBERG = "bloomberg"
    CME = "cme"
    ACTANT_RISK = "actantrisk"  # formerly XCME
    ACTANT_TRADES = "actanttrades"  # regex-based trade format
    ACTANT_TIME = "actanttime"  # vtexp format


class SymbolClass(Enum):
    """Classification of option symbols."""
    WEEKLY_MON_THU = "weekly_monThu"
    WEEKLY_FRIDAY = "weekly_friday"
    QUARTERLY = "quarterly"


class ParsedSymbol(NamedTuple):
    """Parsed symbol components."""
    base: str
    strike: str
    option_type: str  # 'C' or 'P'
    symbol_class: SymbolClass
    

# Month codes for futures contracts
MONTH_CODES = {
    1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
    7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
}

# Reverse month codes
MONTH_CODES_REVERSE = {v: k for k, v in MONTH_CODES.items()}

# Actant series to Bloomberg contract codes and weekdays
SERIES_TO_CONTRACT = {
    'VY': ('VBY', calendar.MONDAY),
    'GY': ('TJP', calendar.TUESDAY),     # CME Globex Tuesday
    'WY': ('TYY', calendar.WEDNESDAY),   # Note: CTO shows TYY not TYW
    'HY': ('TJW', calendar.THURSDAY),    # CME Globex Thursday
    'ZN': ('3M', calendar.FRIDAY),       # Friday special format
}
    
    
class RosettaStone:
    """CSV-based universal symbol translator for market prices."""
    
    def __init__(self, csv_path: Optional[Path] = None):
        """Initialize translator with CSV mappings."""
        if csv_path is None:
            csv_path = Path("data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv")
            
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self._build_lookups()
        
        # Regex patterns for ActantTrades format
        self.actant_option_pattern = re.compile(
            r'XCMEOCADPS(\d{8})([A-Z])0([A-Z]{2,3})(\d*)/(\d+(?:\.\d+)?)'
        )
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
        
    def _build_lookups(self):
        """Build bidirectional lookup dictionaries from CSV."""
        self.lookups = {}
        
        # Build all combinations of lookups
        for _, row in self.df.iterrows():
            # Skip rows with missing data
            if pd.isna(row['CME']) or pd.isna(row['ActantRisk']):
                continue
                
            # Base symbols
            cme_base = str(row['CME'])
            actantrisk_base = str(row['ActantRisk'])
            
            # Handle Bloomberg Call/Put separately
            if not pd.isna(row['Bloomberg_Call']):
                bb_call = str(row['Bloomberg_Call'])
                self.lookups[f"cme_{cme_base}_to_bloomberg_C"] = bb_call
                self.lookups[f"actantrisk_{actantrisk_base}_to_bloomberg_C"] = bb_call
                self.lookups[f"bloomberg_{bb_call}_to_cme"] = cme_base
                self.lookups[f"bloomberg_{bb_call}_to_actantrisk"] = actantrisk_base
                
            if not pd.isna(row['Bloomberg_Put']):
                bb_put = str(row['Bloomberg_Put'])
                self.lookups[f"cme_{cme_base}_to_bloomberg_P"] = bb_put
                self.lookups[f"actantrisk_{actantrisk_base}_to_bloomberg_P"] = bb_put
                self.lookups[f"bloomberg_{bb_put}_to_cme"] = cme_base
                self.lookups[f"bloomberg_{bb_put}_to_actantrisk"] = actantrisk_base
                
            # Direct CME <-> ActantRisk mappings
            self.lookups[f"cme_{cme_base}_to_actantrisk"] = actantrisk_base
            self.lookups[f"actantrisk_{actantrisk_base}_to_cme"] = cme_base
            
            # Add ActantTrades mappings if available
            if 'ActantTrades' in row and not pd.isna(row['ActantTrades']):
                actanttrades_base = str(row['ActantTrades'])
                self.lookups[f"actanttrades_{actanttrades_base}_to_bloomberg_C"] = bb_call if not pd.isna(row.get('Bloomberg_Call')) else None
                self.lookups[f"actanttrades_{actanttrades_base}_to_bloomberg_P"] = bb_put if not pd.isna(row.get('Bloomberg_Put')) else None
                self.lookups[f"actanttrades_{actanttrades_base}_to_cme"] = cme_base
                self.lookups[f"actanttrades_{actanttrades_base}_to_actantrisk"] = actantrisk_base
                self.lookups[f"cme_{cme_base}_to_actanttrades"] = actanttrades_base
                self.lookups[f"actantrisk_{actantrisk_base}_to_actanttrades"] = actanttrades_base
            
            # Add ActantTime mappings if available
            if 'ActantTime' in row and not pd.isna(row['ActantTime']):
                actanttime_base = str(row['ActantTime'])
                self.lookups[f"actanttime_{actanttime_base}_to_bloomberg_C"] = bb_call if not pd.isna(row.get('Bloomberg_Call')) else None
                self.lookups[f"actanttime_{actanttime_base}_to_bloomberg_P"] = bb_put if not pd.isna(row.get('Bloomberg_Put')) else None
                self.lookups[f"actanttime_{actanttime_base}_to_cme"] = cme_base
                self.lookups[f"actanttime_{actanttime_base}_to_actantrisk"] = actantrisk_base
                self.lookups[f"cme_{cme_base}_to_actanttime"] = actanttime_base
                self.lookups[f"actantrisk_{actantrisk_base}_to_actanttime"] = actanttime_base
            
    def classify_symbol(self, symbol: str, format_type: SymbolFormat) -> SymbolClass:
        """Determine symbol classification."""
        if format_type == SymbolFormat.CME:
            if symbol.startswith('OZN'):
                return SymbolClass.QUARTERLY
            elif symbol.startswith('ZN'):
                return SymbolClass.WEEKLY_FRIDAY
            else:
                return SymbolClass.WEEKLY_MON_THU
                
        elif format_type == SymbolFormat.ACTANT_RISK:
            # Check the base after XCME.
            if '.OZN.' in symbol:
                return SymbolClass.QUARTERLY
            elif '.ZN' in symbol and symbol.split('.')[1].startswith('ZN'):
                return SymbolClass.WEEKLY_FRIDAY
            else:
                return SymbolClass.WEEKLY_MON_THU
                
        elif format_type == SymbolFormat.ACTANT_TRADES:
            # Parse the symbol to extract series
            match = self.actant_option_pattern.match(symbol)
            if match:
                series = match.group(3)  # VY, GY, WY, HY, ZN, OZN
                if series == 'OZN':
                    return SymbolClass.QUARTERLY
                elif series == 'ZN':
                    return SymbolClass.WEEKLY_FRIDAY
                else:
                    return SymbolClass.WEEKLY_MON_THU
            return SymbolClass.WEEKLY_MON_THU  # Default
            
        elif format_type == SymbolFormat.ACTANT_TIME:
            # All ActantTime symbols are treated as weekly for now
            # Could parse date to determine if it's Friday/Mon-Thu
            return SymbolClass.WEEKLY_MON_THU
                
        elif format_type == SymbolFormat.BLOOMBERG:
            # Check first character
            if symbol[0].isdigit():
                return SymbolClass.WEEKLY_FRIDAY
            elif symbol.startswith('TY') and len(symbol) >= 3 and symbol[2] != 'W':
                # TYQ5C, TYU5C are quarterly (not TYW which is Wednesday)
                return SymbolClass.QUARTERLY
            else:
                return SymbolClass.WEEKLY_MON_THU
                
    def parse_symbol(self, symbol: str, format_type: SymbolFormat) -> ParsedSymbol:
        """Parse symbol into components based on format."""
        symbol = symbol.strip()
        
        if format_type == SymbolFormat.ACTANT_RISK:
            # Format: XCME.VY3.21JUL25.111:75.C
            parts = symbol.split('.')
            if len(parts) < 5:
                raise ValueError(f"Invalid ActantRisk format: {symbol}")
                
            base = '.'.join(parts[:3])  # XCME.VY3.21JUL25
            strike = parts[3]
            option_type = parts[4].upper()
            
        elif format_type == SymbolFormat.CME:
            # Format: VY3N5 C11100
            match = re.match(r'^([A-Z0-9]+)\s+([CP])(\d+)$', symbol)
            if not match:
                raise ValueError(f"Invalid CME format: {symbol}")
                
            base = match.group(1)
            option_type = match.group(2)
            strike_int = match.group(3)
            
            # Convert CME strike format to decimal
            if len(strike_int) == 5:  # e.g., 11100
                strike = str(int(strike_int) / 100)
            else:
                strike = strike_int
                
        elif format_type == SymbolFormat.BLOOMBERG:
            # Format: VBYN25C3 111.750 Comdty
            parts = symbol.split()
            if len(parts) < 2:
                raise ValueError(f"Invalid Bloomberg format: {symbol}")
                
            # Extract base and option type
            base_with_type = parts[0]
            strike = parts[1]
            
            # Find where option type is embedded
            # For weekly: VBYN25C3 or VBYN25P3
            # For Friday: 1MQ5C or 1MQ5P
            # For quarterly: TYQ5C or TYQ5P
            
            if base_with_type[-1].isdigit():
                # Weekly Mon-Thu: option type is before the last digit
                option_type = base_with_type[-2]
                base = base_with_type
            else:
                # Friday or Quarterly: option type is last character
                option_type = base_with_type[-1]
                base = base_with_type
                
        elif format_type == SymbolFormat.ACTANT_TRADES:
            # Format: XCMEOCADPS20250728N0VY4/111
            match = self.actant_option_pattern.match(symbol)
            if match:
                date_str, month_code, series, week_num, strike = match.groups()
                # Reconstruct base without strike
                base = f"XCMEOCADPS{date_str}{month_code}0{series}{week_num}"
                # Determine option type from OCAD (Call) or OPAD (Put)
                option_type = 'C' if 'OCAD' in symbol else 'P'
            else:
                # Try futures pattern
                match = self.actant_futures_pattern.match(symbol)
                if match:
                    # Handle futures separately if needed
                    raise ValueError(f"Futures not yet supported: {symbol}")
                else:
                    raise ValueError(f"Invalid ActantTrades format: {symbol}")
                    
        elif format_type == SymbolFormat.ACTANT_TIME:
            # Format: XCME.ZN.N.G.21JUL25
            parts = symbol.split('.')
            if len(parts) < 5:
                raise ValueError(f"Invalid ActantTime format: {symbol}")
            base = symbol  # Use full symbol as base for ActantTime
            strike = "0"  # ActantTime doesn't include strike in base
            option_type = 'C'  # Default, will be determined by context
                
        else:
            raise ValueError(f"Unknown format: {format_type}")
            
        symbol_class = self.classify_symbol(symbol, format_type)
        return ParsedSymbol(base, strike, option_type, symbol_class)
        
    def translate(self, symbol: str, from_format: str, to_format: str) -> Optional[str]:
        """
        Translate symbol between formats.
        
        Args:
            symbol: Input symbol
            from_format: Source format ('bloomberg', 'cme', 'actantrisk', 'actanttrades', 'actanttime')
            to_format: Target format ('bloomberg', 'cme', 'actantrisk', 'actanttrades', 'actanttime')
            
        Returns:
            Translated symbol or None if mapping not found
        """
        from_fmt = SymbolFormat(from_format)
        to_fmt = SymbolFormat(to_format)
        
        # Parse input symbol
        try:
            parsed = self.parse_symbol(symbol, from_fmt)
        except ValueError as e:
            print(f"Failed to parse {symbol}: {e}")
            return None
            
        # Look up base mapping
        if from_fmt == SymbolFormat.BLOOMBERG:
            # Bloomberg base already includes option type
            lookup_key = f"bloomberg_{parsed.base}_to_{to_format}"
        else:
            # For non-Bloomberg formats, we need to specify option type when going to Bloomberg
            if to_fmt == SymbolFormat.BLOOMBERG:
                lookup_key = f"{from_format}_{parsed.base}_to_bloomberg_{parsed.option_type}"
            else:
                lookup_key = f"{from_format}_{parsed.base}_to_{to_format}"
                
        target_base = self.lookups.get(lookup_key)
        if not target_base:
            print(f"No mapping found for {lookup_key}")
            return None
            
        # Format strike for target system
        try:
            strike_formatted = StrikeConverter.format_strike(parsed.strike, to_format)
        except ValueError as e:
            print(f"Failed to format strike {parsed.strike}: {e}")
            return None
            
        # Reconstruct symbol
        return self._reconstruct_symbol(
            target_base, 
            strike_formatted, 
            parsed.option_type,
            to_fmt,
            parsed.symbol_class
        )
        
    def _reconstruct_symbol(self, base: str, strike: str, option_type: str,
                          format_type: SymbolFormat, symbol_class: SymbolClass) -> str:
        """Reconstruct full symbol from components."""
        if format_type == SymbolFormat.BLOOMBERG:
            # Bloomberg always uses same format
            return f"{base} {strike} Comdty"
            
        elif format_type == SymbolFormat.CME:
            # CME format varies slightly by type but generally: BASE C/P+STRIKE
            return f"{base} {option_type}{strike}"
            
        elif format_type == SymbolFormat.ACTANT_RISK:
            # ActantRisk: base.strike.option_type
            return f"{base}.{strike}.{option_type}"
            
        elif format_type == SymbolFormat.ACTANT_TRADES:
            # ActantTrades: base/strike
            return f"{base}/{strike}"
            
        elif format_type == SymbolFormat.ACTANT_TIME:
            # ActantTime doesn't include strike or option type in the format
            # The base already contains the full symbol
            return base
            
        else:
            raise ValueError(f"Unknown format: {format_type}") 