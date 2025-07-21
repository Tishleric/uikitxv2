"""Debug logger for TYU5 P&L calculations.

Provides detailed logging of calculation steps when debug mode is enabled.
"""
import logging
from typing import Any, Optional, List, Dict
from datetime import datetime

class DebugLogger:
    """Centralized debug logger for TYU5 calculations."""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.logs: List[Dict[str, Any]] = []
        
        # Configure Python logger
        if self.enabled:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - TYU5 - %(levelname)s - %(message)s'
            )
        self.logger = logging.getLogger('TYU5')
        
    def log(self, category: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a debug message with optional data."""
        if not self.enabled:
            return
            
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'message': message,
            'data': data or {}
        }
        
        self.logs.append(log_entry)
        
        # Also log to Python logger
        log_msg = f"[{category}] {message}"
        if data:
            log_msg += f" | Data: {data}"
        self.logger.debug(log_msg)
        
    def log_price_lookup(self, symbol: str, price_type: str, price: Any, source: str = ""):
        """Log price lookup operations."""
        self.log(
            "PRICE_LOOKUP",
            f"Price lookup for {symbol}",
            {
                'symbol': symbol,
                'price_type': price_type,
                'price': price,
                'source': source,
                'found': price is not None
            }
        )
        
    def log_symbol_translation(self, original: str, translated: str, reason: str = ""):
        """Log symbol translation operations."""
        self.log(
            "SYMBOL_TRANSLATION",
            f"Symbol translation: {original} → {translated}",
            {
                'original': original,
                'translated': translated,
                'reason': reason
            }
        )
        
    def log_trade_matching(self, symbol: str, action: str, quantity: float, 
                          matched_qty: float = 0, remaining_qty: float = 0):
        """Log trade matching operations."""
        self.log(
            "TRADE_MATCHING",
            f"Trade matching for {symbol} {action} {quantity}",
            {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'matched_quantity': matched_qty,
                'remaining_quantity': remaining_qty
            }
        )
        
    def log_calculation(self, calc_type: str, symbol: str, inputs: Dict[str, Any], 
                       result: Any, error: Optional[str] = None):
        """Log calculation operations."""
        self.log(
            "CALCULATION",
            f"{calc_type} calculation for {symbol}",
            {
                'calculation_type': calc_type,
                'symbol': symbol,
                'inputs': inputs,
                'result': result,
                'error': error
            }
        )
        
    def log_expiration_lookup(self, symbol: str, expiry_date: Any, error: Optional[str] = None):
        """Log expiration calendar lookups."""
        self.log(
            "EXPIRATION_LOOKUP",
            f"Expiration lookup for {symbol}",
            {
                'symbol': symbol,
                'expiry_date': str(expiry_date) if expiry_date else None,
                'error': error
            }
        )
        
    def get_logs_dataframe(self):
        """Convert logs to DataFrame for Excel output."""
        import pandas as pd
        if not self.logs:
            return pd.DataFrame()
            
        # Flatten the log entries
        flattened = []
        for log in self.logs:
            entry = {
                'Timestamp': log['timestamp'],
                'Category': log['category'],
                'Message': log['message']
            }
            # Add data fields
            for key, value in log.get('data', {}).items():
                entry[f'Data_{key}'] = str(value)
            flattened.append(entry)
            
        return pd.DataFrame(flattened)
        
    def clear(self):
        """Clear all logs."""
        self.logs = []

# Global debug logger instance
_debug_logger: Optional[DebugLogger] = None

def get_debug_logger() -> DebugLogger:
    """Get the global debug logger instance."""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger(enabled=False)
    return _debug_logger

def set_debug_mode(enabled: bool):
    """Enable or disable debug mode."""
    global _debug_logger
    _debug_logger = DebugLogger(enabled=enabled) 