"""
Symbol utilities for consistent symbol handling across TYU5 and other modules.

Provides canonical symbol transformation to ensure consistent matching
between trade data, market prices, and database records.
"""

def canonical(symbol: str) -> str:
    """
    Convert symbol to canonical form for consistent matching.
    
    Transformations:
    - Strip whitespace
    - Convert to uppercase
    - Remove " COMDTY" suffix (Bloomberg notation)
    - Remove "XCME." prefix (exchange prefix)
    
    Args:
        symbol: Raw symbol string
        
    Returns:
        Canonical symbol string
        
    Examples:
        >>> canonical("TYU5 COMDTY")
        'TYU5'
        >>> canonical("XCME.TY.SEP25")
        'TY.SEP25'
        >>> canonical(" tyu5 ")
        'TYU5'
    """
    if not symbol:
        return ""
    
    # Strip whitespace and uppercase
    result = symbol.strip().upper()
    
    # Remove common suffixes
    if result.endswith(" COMDTY"):
        result = result[:-7]
    
    # Remove exchange prefixes
    if result.startswith("XCME."):
        result = result[5:]
    
    return result


def is_same_symbol(sym1: str, sym2: str) -> bool:
    """Check if two symbols are the same after canonicalization."""
    return canonical(sym1) == canonical(sym2) 