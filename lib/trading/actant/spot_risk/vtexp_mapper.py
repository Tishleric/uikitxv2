"""
Mapper for matching spot risk options to vtexp values by expiry date.

Simplified approach: Match by expiry date (e.g., "21JUL25") since all options 
expiring on the same date have the same time to expiry.
"""

import re
import logging
from typing import Optional, Dict

from lib.trading.market_prices.rosetta_stone import RosettaStone
from .vtexp_prefix_resolver import extract_spot_prefix, resolve_time_symbol_from_prefix

logger = logging.getLogger(__name__)


class VtexpSymbolMapper:
    """Maps spot risk options to vtexp values using expiry date matching."""
    
    def __init__(self):
        # Pattern to extract expiry date from spot risk symbol
        # Handles both formats:
        # - Weekly: XCME.ZN2.11JUL25.110.C -> captures "11JUL25"
        # - Quarterly: XCME.OZN.AUG25.110:75.P -> captures "AUG25"
        self.spot_risk_pattern = re.compile(r'XCME\.[A-Z]+\d?\.(\d{0,2}[A-Z]{3}\d{2})\.')
        
        # Pattern to extract expiry date from vtexp symbol
        # Handles both formats:
        # - Weekly: XCME.ZN.N.G.17JUL25 -> captures "17JUL25"
        # - Quarterly: XCME.ZN.N.G.AUG25 -> captures "AUG25"
        self.vtexp_pattern = re.compile(r'XCME\.[A-Z]+\.N\.G\.(\d{0,2}[A-Z]{3}\d{2})')
    
    def extract_expiry_from_spot_risk(self, symbol: str) -> Optional[str]:
        """Extract expiry date from spot risk symbol."""
        match = self.spot_risk_pattern.search(symbol)
        if match:
            return match.group(1)
        return None
    
    def extract_expiry_from_vtexp(self, symbol: str) -> Optional[str]:
        """Extract expiry date from vtexp symbol."""
        match = self.vtexp_pattern.search(symbol)
        if match:
            return match.group(1)
        return None
    
    def create_mapping_dict(self, spot_risk_symbols: list, vtexp_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Create mapping from spot risk symbols to vtexp values based on expiry date.
        
        Args:
            spot_risk_symbols: List of spot risk option symbols
            vtexp_dict: Dictionary of vtexp symbols to time values
            
        Returns:
            Dictionary mapping spot risk symbols to vtexp values
        """
        # First, create expiry date to vtexp value mapping
        expiry_to_vtexp = {}
        for vtexp_symbol, vtexp_value in vtexp_dict.items():
            expiry = self.extract_expiry_from_vtexp(vtexp_symbol)
            if expiry:
                # Store the vtexp value for this expiry date
                # If multiple products have same expiry, they should have same vtexp
                if expiry not in expiry_to_vtexp:
                    expiry_to_vtexp[expiry] = vtexp_value
                elif expiry_to_vtexp[expiry] != vtexp_value:
                    logger.warning(f"Different vtexp values for same expiry {expiry}: {expiry_to_vtexp[expiry]} vs {vtexp_value}")
        
        logger.info(f"Created expiry mapping for {len(expiry_to_vtexp)} unique expiry dates")
        
        # Now map spot risk symbols to vtexp values
        mapping = {}
        unmapped_expiries = set()

        # Optional: attempt exact symbol mapping via Rosetta from prefix -> time-format
        rosetta: Optional[RosettaStone] = None
        try:
            rosetta = RosettaStone()
        except Exception:
            rosetta = None
        
        for spot_symbol in spot_risk_symbols:
            # 1) Exact time-format symbol via Rosetta (prefix-based)
            if rosetta is not None:
                try:
                    prefix = extract_spot_prefix(spot_symbol)
                    if prefix:
                        time_symbol = resolve_time_symbol_from_prefix(prefix, rosetta)
                        if time_symbol and time_symbol in vtexp_dict:
                            mapping[spot_symbol] = vtexp_dict[time_symbol]
                            continue
                except Exception:
                    # Fail-safe to expiry mapping
                    pass

            # 2) Fallback to expiry-based mapping (existing behavior)
            expiry = self.extract_expiry_from_spot_risk(spot_symbol)
            if expiry and expiry in expiry_to_vtexp:
                mapping[spot_symbol] = expiry_to_vtexp[expiry]
            elif expiry:
                unmapped_expiries.add(expiry)
        
        if unmapped_expiries:
            logger.warning(f"No vtexp data for expiries: {sorted(unmapped_expiries)}")
        
        logger.info(f"Mapped {len(mapping)} of {len(spot_risk_symbols)} spot risk symbols to vtexp values")
        
        return mapping 