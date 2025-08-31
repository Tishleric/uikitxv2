"""
Strike format converter for handling XCME colon notation.

XCME uses special notation for fractional strikes:
- 111 → 111.000
- 111:25 → 111.250
- 111:5 → 111.500 (note: :5 means .50)
- 111:75 → 111.750
"""

from typing import Union


class StrikeConverter:
    """Handles conversion between XCME colon notation and decimal format."""
    
    @staticmethod
    def xcme_to_decimal(xcme_strike: str) -> float:
        """
        Convert XCME strike format to decimal.
        
        Examples:
            "111" → 111.0
            "111:25" → 111.25
            "111:5" → 111.5
            "111:75" → 111.75
        """
        if not xcme_strike:
            raise ValueError("Strike cannot be empty")
            
        xcme_strike = str(xcme_strike).strip()
        
        if ':' in xcme_strike:
            parts = xcme_strike.split(':')
            if len(parts) != 2:
                raise ValueError(f"Invalid XCME strike format: {xcme_strike}")
                
            whole_str, fraction_str = parts
            
            try:
                whole = int(whole_str)
            except ValueError:
                raise ValueError(f"Invalid whole number in strike: {whole_str}")
                
            # Special case: :5 means .50
            if fraction_str == '5':
                fraction = 50
            else:
                try:
                    fraction = int(fraction_str)
                except ValueError:
                    raise ValueError(f"Invalid fraction in strike: {fraction_str}")
                    
            return float(whole) + (fraction / 100.0)
        else:
            try:
                return float(xcme_strike)
            except ValueError:
                raise ValueError(f"Invalid strike format: {xcme_strike}")
    
    @staticmethod
    def decimal_to_xcme(decimal_strike: Union[float, str]) -> str:
        """
        Convert decimal strike to XCME format.
        
        Examples:
            111.0 → "111"
            111.25 → "111:25"
            111.5 → "111:5"
            111.75 → "111:75"
        """
        decimal = float(decimal_strike)
        
        # Check if it's a whole number
        if decimal % 1 == 0:
            return str(int(decimal))
            
        whole = int(decimal)
        fraction = round((decimal - whole) * 100)
        
        # Special case for .50
        if fraction == 50:
            return f"{whole}:5"
        else:
            return f"{whole}:{fraction}"
    
    @staticmethod
    def format_strike(strike: Union[str, float], target_format: str) -> str:
        """
        Format strike for target system.
        
        Args:
            strike: Input strike (can be XCME format or decimal)
            target_format: 'bloomberg', 'cme', 'actantrisk', 'actanttrades', or 'actanttime'
            
        Returns:
            Formatted strike string
        """
        # First normalize to decimal
        if isinstance(strike, str) and ':' in strike:
            decimal = StrikeConverter.xcme_to_decimal(strike)
        else:
            decimal = float(strike)
            
        if target_format == 'bloomberg':
            # Bloomberg uses up to 3 decimal places, without trailing zeros
            # Format with 3 decimals then strip trailing zeros and decimal point if not needed
            formatted = f"{decimal:.3f}"
            # Remove trailing zeros after decimal point
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')
            return formatted
        elif target_format == 'cme':
            # CME uses integer format with special handling
            # E.g., 111.75 → "11175"
            if decimal % 1 == 0:
                return f"{int(decimal)}00"
            else:
                # Convert to basis points (hundredths)
                return f"{int(decimal * 100)}"
        elif target_format == 'actantrisk':
            return StrikeConverter.decimal_to_xcme(decimal)
        elif target_format == 'actanttrades':
            # ActantTrades uses decimal format in strikes
            if decimal % 1 == 0:
                return str(int(decimal))
            else:
                return str(decimal)
        elif target_format == 'actanttime':
            # ActantTime doesn't use strikes in the base format
            return ""
        elif target_format == 'broker':
            # Broker uses decimal format like Bloomberg
            if decimal % 1 == 0:
                return str(int(decimal))
            else:
                return str(decimal)
        else:
            raise ValueError(f"Unknown target format: {target_format}")

