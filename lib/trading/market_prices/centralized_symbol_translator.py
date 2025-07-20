"""
Centralized symbol translator using ExpirationCalendar_CLEANED.csv as source of truth.

This module replaces the complex regex-based translation with simple CSV lookups,
handling all special cases for weekly, Friday, and quarterly options.
"""

import re
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple, NamedTuple
from enum import Enum

from .strike_converter import StrikeConverter


class SymbolFormat(Enum):
    """Supported symbol formats."""
    BLOOMBERG = "bloomberg"
    CME = "cme"
    XCME = "xcme"


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
    
    
class CentralizedSymbolTranslator:
    """CSV-based symbol translator for market prices."""
    
    def __init__(self, csv_path: Optional[Path] = None):
        """Initialize translator with CSV mappings."""
        if csv_path is None:
            csv_path = Path("data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv")
            
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self._build_lookups()
        
    def _build_lookups(self):
        """Build bidirectional lookup dictionaries from CSV."""
        self.lookups = {}
        
        # Build all combinations of lookups
        for _, row in self.df.iterrows():
            # Skip rows with missing data
            if pd.isna(row['CME']) or pd.isna(row['XCME']):
                continue
                
            # CME lookups
            cme_base = str(row['CME'])
            xcme_base = str(row['XCME'])
            
            # Handle Bloomberg Call/Put separately
            if not pd.isna(row['Bloomberg_Call']):
                bb_call = str(row['Bloomberg_Call'])
                self.lookups[f"cme_{cme_base}_to_bloomberg_C"] = bb_call
                self.lookups[f"xcme_{xcme_base}_to_bloomberg_C"] = bb_call
                self.lookups[f"bloomberg_{bb_call}_to_cme"] = cme_base
                self.lookups[f"bloomberg_{bb_call}_to_xcme"] = xcme_base
                
            if not pd.isna(row['Bloomberg_Put']):
                bb_put = str(row['Bloomberg_Put'])
                self.lookups[f"cme_{cme_base}_to_bloomberg_P"] = bb_put
                self.lookups[f"xcme_{xcme_base}_to_bloomberg_P"] = bb_put
                self.lookups[f"bloomberg_{bb_put}_to_cme"] = cme_base
                self.lookups[f"bloomberg_{bb_put}_to_xcme"] = xcme_base
                
            # Direct CME <-> XCME mappings
            self.lookups[f"cme_{cme_base}_to_xcme"] = xcme_base
            self.lookups[f"xcme_{xcme_base}_to_cme"] = cme_base
            
    def classify_symbol(self, symbol: str, format_type: SymbolFormat) -> SymbolClass:
        """Determine symbol classification."""
        if format_type == SymbolFormat.CME:
            if symbol.startswith('OZN'):
                return SymbolClass.QUARTERLY
            elif symbol.startswith('ZN'):
                return SymbolClass.WEEKLY_FRIDAY
            else:
                return SymbolClass.WEEKLY_MON_THU
                
        elif format_type == SymbolFormat.XCME:
            # Check the base after XCME.
            if '.OZN.' in symbol:
                return SymbolClass.QUARTERLY
            elif '.ZN' in symbol and symbol.split('.')[1].startswith('ZN'):
                return SymbolClass.WEEKLY_FRIDAY
            else:
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
        
        if format_type == SymbolFormat.XCME:
            # Format: XCME.VY3.21JUL25.111:75.C
            parts = symbol.split('.')
            if len(parts) < 5:
                raise ValueError(f"Invalid XCME format: {symbol}")
                
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
                
        else:
            raise ValueError(f"Unknown format: {format_type}")
            
        symbol_class = self.classify_symbol(symbol, format_type)
        return ParsedSymbol(base, strike, option_type, symbol_class)
        
    def translate(self, symbol: str, from_format: str, to_format: str) -> Optional[str]:
        """
        Translate symbol between formats.
        
        Args:
            symbol: Input symbol
            from_format: Source format ('bloomberg', 'cme', 'xcme')
            to_format: Target format ('bloomberg', 'cme', 'xcme')
            
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
            # For CME/XCME, we need to specify option type when going to Bloomberg
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
            
        elif format_type == SymbolFormat.XCME:
            # XCME: base.strike.option_type
            return f"{base}.{strike}.{option_type}"
            
        else:
            raise ValueError(f"Unknown format: {format_type}") 