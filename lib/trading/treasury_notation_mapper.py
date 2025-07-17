"""
Treasury Notation Mapper

Comprehensive mapping between Bloomberg, Actant, and CME notation for US Treasury futures and options.
Supports all major treasury contracts and their options.
"""

from typing import Dict, Tuple, Optional, List
import re
from dataclasses import dataclass


@dataclass
class TreasuryProduct:
    """Treasury product information."""
    bloomberg_code: str
    cme_code: str
    actant_code: str
    description: str
    years_to_maturity: float
    tick_size: float
    contract_size: int


class TreasuryNotationMapper:
    """Maps between different treasury notation systems."""
    
    # Master product registry
    TREASURY_PRODUCTS = {
        # 2-Year Note
        'TU': TreasuryProduct(
            bloomberg_code='TU',
            cme_code='ZT',
            actant_code='TU',
            description='2-Year US Treasury Note',
            years_to_maturity=2.0,
            tick_size=0.0078125,  # 1/128
            contract_size=200000
        ),
        # 5-Year Note
        'FV': TreasuryProduct(
            bloomberg_code='FV',
            cme_code='ZF',
            actant_code='FV',
            description='5-Year US Treasury Note',
            years_to_maturity=5.0,
            tick_size=0.0078125,  # 1/128
            contract_size=100000
        ),
        # 10-Year Note
        'TY': TreasuryProduct(
            bloomberg_code='TY',
            cme_code='ZN',
            actant_code='ZN',
            description='10-Year US Treasury Note',
            years_to_maturity=10.0,
            tick_size=0.015625,  # 1/64
            contract_size=100000
        ),
        # 30-Year Bond
        'US': TreasuryProduct(
            bloomberg_code='US',
            cme_code='ZB',
            actant_code='US',
            description='30-Year US Treasury Bond',
            years_to_maturity=30.0,
            tick_size=0.03125,  # 1/32
            contract_size=100000
        ),
        # Ultra 10-Year Note
        'TN': TreasuryProduct(
            bloomberg_code='TN',
            cme_code='TN',
            actant_code='TN',
            description='Ultra 10-Year US Treasury Note',
            years_to_maturity=10.0,
            tick_size=0.015625,  # 1/64
            contract_size=100000
        ),
        # Ultra Bond
        'UB': TreasuryProduct(
            bloomberg_code='UB',
            cme_code='UB',
            actant_code='UB',
            description='Ultra US Treasury Bond',
            years_to_maturity=30.0,
            tick_size=0.03125,  # 1/32
            contract_size=100000
        ),
    }
    
    # Weekly option series for 10-Year Note
    TY_WEEKLY_OPTIONS = {
        'VBY': {'day': 'Monday', 'suffix': '2', 'actant': 'VY'},
        'TJP': {'day': 'Tuesday', 'suffix': '3', 'actant': 'TJ'},
        'TYW': {'day': 'Wednesday', 'suffix': '4', 'actant': 'WY'},
        'TJW': {'day': 'Thursday', 'suffix': '5', 'actant': 'TH'},
        '3M': {'day': 'Friday', 'suffix': '6', 'actant': 'ZN'},
    }
    
    # Reverse mappings for quick lookup
    def __init__(self):
        # Bloomberg to product mapping
        self.bloomberg_to_product = {p.bloomberg_code: p for p in self.TREASURY_PRODUCTS.values()}
        
        # CME to product mapping
        self.cme_to_product = {p.cme_code: p for p in self.TREASURY_PRODUCTS.values()}
        
        # Actant to product mapping
        self.actant_to_product = {p.actant_code: p for p in self.TREASURY_PRODUCTS.values()}
        
        # Special case: ZN maps to TY
        self.actant_to_product['ZN'] = self.TREASURY_PRODUCTS['TY']
        
        # Weekly options reverse mapping
        self.actant_weekly_to_bloomberg = {v['actant']: k for k, v in self.TY_WEEKLY_OPTIONS.items()}
        
    def normalize_symbol(self, symbol: str, source: str = 'auto') -> Dict[str, str]:
        """
        Normalize a treasury symbol to all notation systems.
        
        Args:
            symbol: Input symbol
            source: Source system ('bloomberg', 'cme', 'actant', or 'auto' to detect)
            
        Returns:
            Dictionary with 'bloomberg', 'cme', 'actant' keys
        """
        # Clean symbol
        symbol = symbol.strip().upper()
        
        # Auto-detect source if needed
        if source == 'auto':
            source = self._detect_source(symbol)
            
        # Parse based on source
        if source == 'bloomberg':
            return self._from_bloomberg(symbol)
        elif source == 'cme':
            return self._from_cme(symbol)
        elif source == 'actant':
            return self._from_actant(symbol)
        else:
            raise ValueError(f"Unknown source: {source}")
            
    def _detect_source(self, symbol: str) -> str:
        """Auto-detect symbol source."""
        # Bloomberg patterns
        if any(symbol.startswith(code) for code in self.bloomberg_to_product):
            return 'bloomberg'
        # Weekly options
        if any(symbol.startswith(code) for code in self.TY_WEEKLY_OPTIONS):
            return 'bloomberg'
        # CME patterns
        if any(symbol.startswith(code) for code in self.cme_to_product):
            return 'cme'
        # Actant patterns (check for XCME prefix)
        if symbol.startswith('XCME'):
            return 'actant'
        # Default to bloomberg
        return 'bloomberg'
        
    def _from_bloomberg(self, symbol: str) -> Dict[str, str]:
        """Parse Bloomberg symbol."""
        # Remove 'Comdty' suffix if present
        symbol = symbol.replace(' COMDTY', '').replace(' Comdty', '').strip()
        
        # Check weekly options first
        for weekly_code in self.TY_WEEKLY_OPTIONS:
            if symbol.startswith(weekly_code):
                # This is a TY weekly option
                product = self.TREASURY_PRODUCTS['TY']
                return {
                    'bloomberg': symbol,
                    'cme': symbol.replace(weekly_code, product.cme_code),
                    'actant': symbol.replace(weekly_code, product.actant_code + self.TY_WEEKLY_OPTIONS[weekly_code]['suffix'])
                }
                
        # Standard products
        for code, product in self.bloomberg_to_product.items():
            if symbol.startswith(code):
                return {
                    'bloomberg': symbol,
                    'cme': symbol.replace(code, product.cme_code),
                    'actant': symbol.replace(code, product.actant_code)
                }
                
        raise ValueError(f"Unknown Bloomberg symbol: {symbol}")
        
    def _from_cme(self, symbol: str) -> Dict[str, str]:
        """Parse CME symbol."""
        for code, product in self.cme_to_product.items():
            if symbol.startswith(code):
                return {
                    'bloomberg': symbol.replace(code, product.bloomberg_code),
                    'cme': symbol,
                    'actant': symbol.replace(code, product.actant_code)
                }
        raise ValueError(f"Unknown CME symbol: {symbol}")
        
    def _from_actant(self, symbol: str) -> Dict[str, str]:
        """Parse Actant symbol."""
        # Handle full Actant format (XCME...)
        if symbol.startswith('XCME'):
            # Extract product code from complex format
            # This would need the full Actant parsing logic
            raise NotImplementedError("Full Actant format parsing not yet implemented")
            
        # Simple product code
        for code, product in self.actant_to_product.items():
            if symbol.startswith(code):
                return {
                    'bloomberg': symbol.replace(code, product.bloomberg_code),
                    'cme': symbol.replace(code, product.cme_code),
                    'actant': symbol
                }
        raise ValueError(f"Unknown Actant symbol: {symbol}")
        
    def get_product_info(self, symbol: str) -> Optional[TreasuryProduct]:
        """Get product information for any symbol format."""
        try:
            normalized = self.normalize_symbol(symbol)
            # Extract product code from bloomberg format
            bloomberg = normalized['bloomberg']
            for code, product in self.bloomberg_to_product.items():
                if bloomberg.startswith(code):
                    return product
            # Check weekly options
            for weekly_code in self.TY_WEEKLY_OPTIONS:
                if bloomberg.startswith(weekly_code):
                    return self.TREASURY_PRODUCTS['TY']
        except:
            return None
            
    def is_option(self, symbol: str) -> bool:
        """Check if symbol represents an option."""
        symbol = symbol.upper()
        # Check for option indicators: C/P suffix or strike price
        return bool(re.search(r'[CP]\s*\d+', symbol) or re.search(r'\s+\d+\.\d+\s+', symbol))
        
    def is_weekly_option(self, symbol: str) -> bool:
        """Check if symbol represents a weekly option."""
        symbol = symbol.upper()
        return any(symbol.startswith(code) for code in self.TY_WEEKLY_OPTIONS)


# Example usage and validation
if __name__ == "__main__":
    mapper = TreasuryNotationMapper()
    
    # Test cases
    test_symbols = [
        ('TYU5 Comdty', 'bloomberg'),
        ('ZNH5', 'cme'),
        ('TUZ5', 'bloomberg'),
        ('VBYN25C2 110.750 Comdty', 'bloomberg'),
        ('3MN5P 108.000 Comdty', 'bloomberg'),
    ]
    
    print("Treasury Notation Mapping Test:")
    print("-" * 80)
    
    for symbol, source in test_symbols:
        try:
            result = mapper.normalize_symbol(symbol, source)
            product = mapper.get_product_info(symbol)
            print(f"\nInput: {symbol} ({source})")
            print(f"Bloomberg: {result['bloomberg']}")
            print(f"CME: {result['cme']}")
            print(f"Actant: {result['actant']}")
            if product:
                print(f"Product: {product.description}")
                print(f"Is Option: {mapper.is_option(symbol)}")
                print(f"Is Weekly: {mapper.is_weekly_option(symbol)}")
        except Exception as e:
            print(f"\nError processing {symbol}: {e}") 