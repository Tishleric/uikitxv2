"""
FULLPNL Symbol Mapper

Converts TYU5 format symbols to Bloomberg format for joining with spot risk data.
Uses CentralizedSymbolTranslator for accurate mappings.
"""

import logging
from typing import Optional
from pathlib import Path

from lib.trading.market_prices.centralized_symbol_translator import CentralizedSymbolTranslator

logger = logging.getLogger(__name__)


class FULLPNLSymbolMapper:
    """Maps TYU5 symbols to Bloomberg format for FULLPNL table integration."""
    
    def __init__(self):
        """Initialize with centralized symbol translator."""
        try:
            self.translator = CentralizedSymbolTranslator()
            logger.info("Initialized FULLPNLSymbolMapper with CentralizedSymbolTranslator")
        except Exception as e:
            logger.error(f"Failed to initialize CentralizedSymbolTranslator: {e}")
            self.translator = None
    
    def tyu5_to_bloomberg(self, tyu5_symbol: str) -> Optional[str]:
        """Convert TYU5 format to Bloomberg format.
        
        Args:
            tyu5_symbol: TYU5 format symbol
            
        Returns:
            Bloomberg format symbol or None if translation fails
            
        Examples:
            "TYU5" -> "TYU5 Comdty"
            "VY3N5 P 110.25" -> "VBYN25P3 110.250 Comdty"
        """
        if not tyu5_symbol or not isinstance(tyu5_symbol, str):
            return None
            
        if not self.translator:
            logger.warning("CentralizedSymbolTranslator not available")
            return None
            
        try:
            parts = tyu5_symbol.strip().split()
            
            if len(parts) == 1:
                # Future - simple case, just add Comdty suffix
                # Handle common future symbols like TYU5, TYZ5, etc.
                future_symbol = parts[0]
                return f"{future_symbol} Comdty"
                
            elif len(parts) == 3:
                # Option format: "VY3N5 P 110.25"
                base = parts[0]      # VY3N5
                opt_type = parts[1]  # P or C
                strike = parts[2]    # 110.25
                
                # Convert strike to CME integer format (110.25 -> 11025)
                try:
                    strike_float = float(strike)
                    strike_int = str(int(strike_float * 100))   # 110.25 -> 11025
                except ValueError:
                    logger.warning(f"Invalid strike format: {strike}")
                    return None
                
                # Construct full CME format for translator
                cme_symbol = f"{base} {opt_type}{strike_int}"  # "VY3N5 P110250"
                
                # Translate full CME symbol to Bloomberg
                bloomberg_result = self.translator.translate(cme_symbol, 'cme', 'bloomberg')
                if not bloomberg_result:
                    logger.warning(f"No translation found for CME symbol: {cme_symbol}")
                    return None
                
                # Bloomberg result should already be complete: "VBYN25P3 110.250 Comdty"
                logger.debug(f"Translated: {tyu5_symbol} -> {bloomberg_result}")
                return bloomberg_result
                
            else:
                logger.warning(f"Unrecognized TYU5 symbol format: {tyu5_symbol} (parts: {len(parts)})")
                return None
                
        except Exception as e:
            logger.error(f"Error translating symbol {tyu5_symbol}: {e}")
            return None
    
    def bloomberg_to_tyu5(self, bloomberg_symbol: str) -> Optional[str]:
        """Convert Bloomberg format back to TYU5 format.
        
        Args:
            bloomberg_symbol: Bloomberg format symbol
            
        Returns:
            TYU5 format symbol or None if translation fails
        """
        if not bloomberg_symbol or not isinstance(bloomberg_symbol, str):
            return None
            
        if not self.translator:
            logger.warning("CentralizedSymbolTranslator not available")
            return None
            
        try:
            # Remove ' Comdty' suffix
            clean_symbol = bloomberg_symbol.replace(' Comdty', '').strip()
            
            # Check if it's a future (no space = single part)
            if ' ' not in clean_symbol:
                # Future symbol like "TYU5"
                return clean_symbol
                
            # Option symbol: "VBYN25P3 110.250"
            parts = clean_symbol.split()
            if len(parts) >= 2:
                bb_base = parts[0]    # VBYN25P3
                strike = parts[1]     # 110.250
                
                # Translate Bloomberg base to CME
                cme_result = self.translator.translate(bb_base, 'bloomberg', 'cme')
                if not cme_result:
                    logger.warning(f"No translation found for Bloomberg symbol: {bb_base}")
                    return None
                    
                # Parse CME result: should be like "VY3N5 P110250" or similar
                cme_parts = cme_result.split()
                if len(cme_parts) >= 2:
                    cme_base = cme_parts[0]  # VY3N5
                    cme_opt_part = cme_parts[1]  # P110250
                    
                    # Extract option type from CME format
                    if cme_opt_part.startswith('P'):
                        opt_type = 'P'
                    elif cme_opt_part.startswith('C'):
                        opt_type = 'C'
                    else:
                        logger.warning(f"Could not determine option type from CME result: {cme_result}")
                        return None
                    
                    # Format strike to 2 decimal places for TYU5
                    try:
                        strike_float = float(strike)
                        strike_formatted = f"{strike_float:.2f}".rstrip('0').rstrip('.')
                        if '.' not in strike_formatted:
                            strike_formatted += '.0'
                    except ValueError:
                        logger.warning(f"Invalid strike format: {strike}")
                        return None
                    
                    tyu5_symbol = f"{cme_base} {opt_type} {strike_formatted}"
                    logger.debug(f"Reverse translated: {bloomberg_symbol} -> {tyu5_symbol}")
                    return tyu5_symbol
                    
            logger.warning(f"Could not parse Bloomberg symbol: {bloomberg_symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error reverse translating symbol {bloomberg_symbol}: {e}")
            return None
    
    def create_symbol_mapping(self, tyu5_symbols: list) -> dict:
        """Create mapping dictionary from TYU5 to Bloomberg symbols.
        
        Args:
            tyu5_symbols: List of TYU5 format symbols
            
        Returns:
            Dictionary mapping TYU5 -> Bloomberg symbols
        """
        mapping = {}
        
        for tyu5_symbol in tyu5_symbols:
            bloomberg_symbol = self.tyu5_to_bloomberg(tyu5_symbol)
            if bloomberg_symbol:
                mapping[tyu5_symbol] = bloomberg_symbol
            else:
                logger.warning(f"Failed to map symbol: {tyu5_symbol}")
                
        logger.info(f"Created symbol mapping for {len(mapping)}/{len(tyu5_symbols)} symbols")
        return mapping 