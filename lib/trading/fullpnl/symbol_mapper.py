"""
Symbol mapping utilities for FULLPNL automation.

Handles conversions between:
- Bloomberg format: "VBYN25P3 110.250 Comdty"
- Actant format: "XCME.ZN3.18JUL25.110:25.P"
- vtexp format: "XCME.ZN2.18JUL25" or "XCME.ZN.JUL25"
"""

import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedSymbol:
    """Parsed symbol components."""
    symbol_type: str  # 'FUT', 'CALL', 'PUT'
    base_symbol: str  # e.g., 'TYU5', 'VBYN25P3'
    strike: Optional[float] = None
    expiry: Optional[str] = None
    contract_code: Optional[str] = None
    
    
class SymbolMapper:
    """Centralized symbol format conversion logic."""
    
    # Contract code to expiry mappings discovered from scripts
    CONTRACT_TO_EXPIRY = {
        "3M": "18JUL25",
        "3MN": "18JUL25", 
        "VBY": "21JUL25",
        "VBYN": "21JUL25",
        "TWN": "23JUL25",
        "TYWN": "23JUL25",
    }
    
    # Month mappings for futures
    MONTH_MAP = {
        'H': 'MAR', 'M': 'JUN', 'U': 'SEP', 'Z': 'DEC',
        'G': 'FEB', 'J': 'APR', 'K': 'MAY', 'N': 'JUL',
        'Q': 'AUG', 'V': 'OCT', 'X': 'NOV', 'F': 'JAN'
    }
    
    def __init__(self):
        # Compile regex patterns once
        self._bloomberg_option_pattern = re.compile(
            r'^([A-Z0-9]+)(C|P)(\d+)\s+([\d.]+)\s+Comdty$'
        )
        self._actant_option_pattern = re.compile(
            r'^XCME\.([A-Z]+\d*)\.(\d+[A-Z]+\d+)\.([\d:]+)\.(C|P)$'
        )
        
    def parse_bloomberg_symbol(self, symbol: str) -> Optional[ParsedSymbol]:
        """Parse Bloomberg format symbol.
        
        Examples:
        - "TYU5 Comdty" -> Future
        - "VBYN25P3 110.250 Comdty" -> Put option
        """
        if not symbol or not symbol.endswith(' Comdty'):
            return None
            
        # Remove ' Comdty' suffix
        base = symbol[:-7].strip()
        
        # Check if it's an option (has space and strike)
        if ' ' in base:
            parts = base.split()
            if len(parts) == 2:
                symbol_part = parts[0]
                strike = float(parts[1])
                
                # Parse option symbol (e.g., VBYN25P3, 3MN5P)
                # Try with trailing digit (VBYN25P3, TYWN25P4)
                match = re.match(r'^([A-Z]+\d+)([CP])(\d+)$', symbol_part)
                if match:
                    contract_code = match.group(1)  # Keep full code (e.g., VBYN25)
                    # Extract base without year digits for mapping
                    base_match = re.match(r'^([A-Z]+)', contract_code)
                    base_code = base_match.group(1) if base_match else contract_code
                    opt_type = 'CALL' if match.group(2) == 'C' else 'PUT'
                    
                    return ParsedSymbol(
                        symbol_type=opt_type,
                        base_symbol=symbol_part,
                        strike=strike,
                        contract_code=base_code  # Use base code for mapping
                    )
                
                # Try without trailing digit (3MN5P)
                match = re.match(r'^([A-Z0-9]+)([CP])$', symbol_part)
                if match:
                    contract_code = match.group(1)  # e.g., 3MN5
                    # Extract base without any digits for mapping
                    base_match = re.match(r'^(\d*[A-Z]+)', contract_code)
                    base_code = base_match.group(1) if base_match else contract_code
                    opt_type = 'CALL' if match.group(2) == 'C' else 'PUT'
                    
                    return ParsedSymbol(
                        symbol_type=opt_type,
                        base_symbol=symbol_part,
                        strike=strike,
                        contract_code=base_code  # Use base code for mapping
                    )
        else:
            # Future format (e.g., TYU5)
            return ParsedSymbol(
                symbol_type='FUT',
                base_symbol=base,
                contract_code=base
            )
            
        return None
        
    def parse_actant_symbol(self, key: str) -> Optional[ParsedSymbol]:
        """Parse Actant format symbol.
        
        Examples:
        - "XCME.ZN.SEP25" -> Future
        - "XCME.ZN3.18JUL25.110:25.P" -> Put option with fractional strike
        """
        parts = key.split('.')
        
        if len(parts) == 3:
            # Future: XCME.ZN.SEP25
            return ParsedSymbol(
                symbol_type='FUT',
                base_symbol=parts[1],
                expiry=parts[2]
            )
        elif len(parts) >= 5:
            # Option: XCME.ZN3.18JUL25.110:25.P
            expiry = parts[2]
            strike_str = parts[3]
            opt_type = 'CALL' if parts[-1] == 'C' else 'PUT'
            
            # Handle fractional strikes (110:25 = 110.25)
            if ':' in strike_str:
                main, frac = strike_str.split(':')
                strike = float(main) + float(frac) / 100
            else:
                strike = float(strike_str)
                
            return ParsedSymbol(
                symbol_type=opt_type,
                base_symbol=parts[1],
                strike=strike,
                expiry=expiry
            )
            
        return None
        
    def map_contract_to_expiry(self, contract_code: Optional[str]) -> Optional[str]:
        """Map contract code to expiry date.
        
        Examples:
        - "3MN" -> "18JUL25"
        - "VBYN" -> "21JUL25"
        - "3MN5" -> "18JUL25"
        """
        if not contract_code:
            return None
            
        # Try exact match first
        if contract_code in self.CONTRACT_TO_EXPIRY:
            return self.CONTRACT_TO_EXPIRY[contract_code]
            
        # Try without trailing digits (VBYN25 -> VBYN)
        base = re.match(r'^([A-Z]+)', contract_code)
        if base:
            base_code = base.group(1)
            if base_code in self.CONTRACT_TO_EXPIRY:
                return self.CONTRACT_TO_EXPIRY[base_code]
                
        # Try with numeric prefix (3MN5 -> 3MN)
        base = re.match(r'^(\d*[A-Z]+)', contract_code)
        if base:
            base_code = base.group(1)
            if base_code in self.CONTRACT_TO_EXPIRY:
                return self.CONTRACT_TO_EXPIRY[base_code]
                
        return None
        
    def convert_strike_format(self, strike: float, to_colon: bool = True) -> str:
        """Convert between decimal and colon strike notation.
        
        Args:
            strike: Strike price as float (e.g., 110.25)
            to_colon: If True, convert to colon format (110:25), else decimal (110.250)
            
        Returns:
            Formatted strike string
        """
        if to_colon:
            # Convert 110.25 to 110:25
            whole = int(strike)
            frac = int(round((strike - whole) * 100))
            if frac == 0:
                return str(whole)
            else:
                return f"{whole}:{frac:02d}"
        else:
            # Convert to decimal with 3 places
            return f"{strike:.3f}"
            
    def bloomberg_to_actant_expiry(self, bloomberg_symbol: str) -> Optional[str]:
        """Extract expiry from Bloomberg symbol using contract mappings.
        
        Examples:
        - "VBYN25P3 110.250 Comdty" -> "21JUL25"
        - "3MN5P 110.000 Comdty" -> "18JUL25"
        """
        parsed = self.parse_bloomberg_symbol(bloomberg_symbol)
        if not parsed:
            return None
            
        if parsed.contract_code:
            return self.map_contract_to_expiry(parsed.contract_code)
            
        return None
        
    def match_symbols(self, bloomberg_symbol: str, actant_symbol: str) -> bool:
        """Check if Bloomberg and Actant symbols refer to the same instrument.
        
        Matches based on:
        - Instrument type (future/call/put)
        - Strike price (if option)
        - Expiry mapping (if available)
        """
        bloom_parsed = self.parse_bloomberg_symbol(bloomberg_symbol)
        actant_parsed = self.parse_actant_symbol(actant_symbol)
        
        if not bloom_parsed or not actant_parsed:
            return False
            
        # Type must match
        if bloom_parsed.symbol_type != actant_parsed.symbol_type:
            return False
            
        # For futures, check if symbols correspond
        if bloom_parsed.symbol_type == 'FUT':
            # TYU5 should match SEP25
            if bloom_parsed.base_symbol == 'TYU5' and actant_parsed.expiry == 'SEP25':
                return True
            return False
            
        # For options, check strike and expiry
        if bloom_parsed.strike and actant_parsed.strike:
            # Strikes must match (within tolerance for float comparison)
            if abs(bloom_parsed.strike - actant_parsed.strike) > 0.001:
                return False
                
            # Check expiry if we can map it
            bloom_expiry = self.map_contract_to_expiry(bloom_parsed.contract_code)
            if bloom_expiry and actant_parsed.expiry:
                return bloom_expiry == actant_parsed.expiry
                
        return True  # If we can't determine expiry, assume match based on type and strike 