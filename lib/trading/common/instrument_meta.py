"""
Instrument metadata for futures contracts.

Provides contract specifications including multipliers for P&L calculations.
"""

# Contract multipliers (DV01 in dollars)
# Source: CME contract specifications
MULTIPLIERS = {
    # Treasury futures
    'TY': 1000,      # 10-Year Note
    'TU': 2000,      # 2-Year Note  
    'FV': 1000,      # 5-Year Note
    'US': 1000,      # 30-Year Bond
    'UB': 1000,      # Ultra Bond
    
    # Eurodollar/SOFR
    'ED': 2500,      # Eurodollar
    'SR': 4167,      # SOFR 3-month
    
    # For specific contract months (will match prefix)
    'TYU5': 1000,    # Sep 2025 10-Year
    'TUU5': 2000,    # Sep 2025 2-Year
    
    # Default fallback
    'DEFAULT': 1000
}


def get_multiplier(symbol: str) -> float:
    """
    Get the contract multiplier for a given symbol.
    
    Args:
        symbol: Contract symbol (e.g., 'TY', 'TYU5')
        
    Returns:
        Contract multiplier value
    """
    # Direct match
    if symbol in MULTIPLIERS:
        return MULTIPLIERS[symbol]
    
    # Try prefix match (e.g., 'TYU5' matches 'TY')
    for prefix in ['TY', 'TU', 'FV', 'US', 'UB', 'ED', 'SR']:
        if symbol.startswith(prefix):
            return MULTIPLIERS[prefix]
    
    # Default
    return MULTIPLIERS['DEFAULT'] 