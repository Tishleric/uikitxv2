"""Bachelier P&L Attribution Service

This service calculates P&L attribution using the Bachelier model for bond future options.
It enhances TYU5 positions data with detailed Greeks-based P&L explained.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

# Import Bachelier components from TYU5 core
import sys
sys.path.append(str(Path(__file__).parent.parent / "pnl" / "tyu5_pnl" / "core"))
from bachelier import (
    BachelierCombined,
    SafeBachelierVol,
    decompose_option_pnl,
    compute_cme_T
)

logger = logging.getLogger(__name__)


class BachelierAttributionService:
    """Service for calculating P&L attribution using Bachelier model."""
    
    def __init__(self, enable_attribution: bool = True):
        """Initialize the service.
        
        Args:
            enable_attribution: Feature flag to enable/disable attribution (for easy reversion)
        """
        self.enabled = enable_attribution
        self.expiration_calendar_path = self._find_expiration_calendar()
        
    def _find_expiration_calendar(self) -> str:
        """Locate the expiration calendar file.
        
        Returns:
            Path to ExpirationCalendar.csv
        """
        # Try multiple locations
        possible_paths = [
            Path(__file__).parent.parent / "pnl" / "tyu5_pnl" / "core" / "ExpirationCalendar.csv",
            Path("lib/trading/pnl/tyu5_pnl/core/ExpirationCalendar.csv"),
            Path("ExpirationCalendar.csv")
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found expiration calendar at: {path}")
                return str(path)
                
        logger.warning("Expiration calendar not found, attribution may fail")
        return "ExpirationCalendar.csv"
        
    def calculate_position_attribution(self,
                                     position_row: pd.Series,
                                     current_prices: Dict[str, float],
                                     prior_prices: Dict[str, float],
                                     futures_current: Dict[str, float],
                                     futures_prior: Dict[str, float],
                                     evaluation_time: Optional[datetime] = None) -> Dict[str, float]:
        """Calculate Bachelier attribution for a single option position.
        
        Args:
            position_row: Series containing position data (Symbol, Strike, Type, etc.)
            current_prices: Current option prices by symbol
            prior_prices: Prior option prices by symbol
            futures_current: Current futures prices
            futures_prior: Prior futures prices
            evaluation_time: Time for T calculation (defaults to now)
            
        Returns:
            Dictionary with attribution components
        """
        if not self.enabled:
            return self._empty_attribution()
            
        try:
            # Parse position details
            symbol_parts = str(position_row.get('Symbol', '')).split()
            if len(symbol_parts) < 3:
                logger.debug(f"Invalid symbol format: {position_row.get('Symbol')}")
                return self._empty_attribution()
                
            cme_symbol = symbol_parts[0]  # e.g., "HY3N5"
            type_char = symbol_parts[1].upper()  # "C" or "P"
            option_type = "call" if type_char == "C" else "put"
            strike = float(symbol_parts[2])
            
            # Get the underlying futures symbol (extract base from option symbol)
            # HY3N5 -> ZNU5 (from the expiration calendar's underlying mapping)
            futures_symbol = self._get_underlying_symbol(cme_symbol)
            
            # Get prices
            option_key = position_row.get('Symbol', '')
            current_opt_price = current_prices.get(option_key, 0.0)
            prior_opt_price = prior_prices.get(option_key, 0.0)
            
            # Get futures prices - try both mapped symbol and base "TYU5"
            current_fut_price = futures_current.get(futures_symbol, futures_current.get('TYU5', 110.0))
            prior_fut_price = futures_prior.get(futures_symbol, futures_prior.get('TYU5', 110.0))
            
            if current_opt_price <= 0 or prior_opt_price <= 0:
                logger.debug(f"Missing price data for {option_key}")
                return self._empty_attribution()
                
            # Calculate time to expiry
            eval_time = evaluation_time or datetime.now()
            T = compute_cme_T(eval_time, cme_symbol, self.expiration_calendar_path)
            
            if T <= 0:
                logger.debug(f"Option {cme_symbol} has expired")
                return self._empty_attribution()
                
            # Time decay (1 trading day)
            dT = 1 / 252.0
            T_prior = T + dT
            
            # Calculate implied vols and Greeks
            r = 0.01  # Risk-free rate
            
            # Current Greeks
            iv_now = SafeBachelierVol(F=current_fut_price, K=strike, T=T, r=r, 
                                     P=current_opt_price, option_type=option_type)()
            model_now = BachelierCombined(F=current_fut_price, K=strike, T=T, 
                                         sigma=iv_now, r=r, option_type=option_type)
            
            # Prior Greeks
            iv_prior = SafeBachelierVol(F=prior_fut_price, K=strike, T=T_prior, r=r,
                                       P=prior_opt_price, option_type=option_type)()
            model_prior = BachelierCombined(F=prior_fut_price, K=strike, T=T_prior,
                                          sigma=iv_prior, r=r, option_type=option_type)
            
            # Calculate attribution
            dPx = current_fut_price - prior_fut_price
            dVol = iv_now - iv_prior
            
            attribution = decompose_option_pnl(
                greeks=model_prior.greeks(),
                dPx=dPx,
                dVol=dVol,
                dT=dT,
                option_price_old=prior_opt_price,
                option_price_new=current_opt_price
            )
            
            # Scale by position size if available
            position_size = position_row.get('Current_Position', 1.0)
            
            return {
                'delta_pnl': attribution['delta'] * position_size,
                'gamma_pnl': attribution['gamma'] * position_size,
                'vega_pnl': attribution['vega'] * position_size,
                'theta_pnl': attribution['theta'] * position_size,
                'speed_pnl': attribution['speed'] * position_size,
                'residual': attribution['residual'] * position_size,
                'implied_vol_current': iv_now,
                'implied_vol_prior': iv_prior,
                'attribution_calculated': True
            }
            
        except Exception as e:
            logger.error(f"Error calculating attribution for {position_row.get('Symbol')}: {e}")
            return self._empty_attribution()
            
    def enhance_positions_dataframe(self,
                                   positions_df: pd.DataFrame,
                                   market_prices_df: pd.DataFrame) -> pd.DataFrame:
        """Add Bachelier attribution columns to positions DataFrame.
        
        Args:
            positions_df: TYU5 positions DataFrame
            market_prices_df: Market prices DataFrame with current/prior prices
            
        Returns:
            Enhanced DataFrame with attribution columns
        """
        if not self.enabled or positions_df.empty:
            return positions_df
            
        logger.info(f"Enhancing {len(positions_df)} positions with Bachelier attribution")
        
        # Extract price dictionaries
        current_prices, prior_prices, futures_current, futures_prior = self._extract_price_maps(market_prices_df)
        
        # Initialize attribution columns
        attribution_columns = [
            'delta_pnl', 'gamma_pnl', 'vega_pnl', 'theta_pnl', 
            'speed_pnl', 'residual', 'implied_vol_current', 
            'implied_vol_prior', 'attribution_calculated'
        ]
        
        for col in attribution_columns:
            positions_df[col] = 0.0
        positions_df['attribution_calculated'] = False
        
        # Calculate attribution for each option position
        for idx, row in positions_df.iterrows():
            # Skip futures positions
            if self._is_option_position(row):
                attribution = self.calculate_position_attribution(
                    row, current_prices, prior_prices, 
                    futures_current, futures_prior
                )
                
                for key, value in attribution.items():
                    positions_df.at[idx, key] = value
                    
        # Add summary column
        positions_df['total_attributed_pnl'] = (
            positions_df['delta_pnl'] + 
            positions_df['gamma_pnl'] + 
            positions_df['vega_pnl'] + 
            positions_df['theta_pnl'] + 
            positions_df['speed_pnl']
        )
        
        logger.info(f"Attribution calculated for {positions_df['attribution_calculated'].sum()} positions")
        return positions_df
        
    def _extract_price_maps(self, market_prices_df: pd.DataFrame) -> Tuple[Dict, Dict, Dict, Dict]:
        """Extract price dictionaries from market prices DataFrame.
        
        Returns:
            Tuple of (current_options, prior_options, current_futures, prior_futures)
        """
        current_opt = {}
        prior_opt = {}
        current_fut = {}
        prior_fut = {}
        
        for _, row in market_prices_df.iterrows():
            symbol = row.get('Symbol', '')
            current = row.get('Current_Price', 0.0)
            prior = row.get('Prior_Close', 0.0)
            
            # Determine if futures or options based on symbol format
            if ' ' in symbol:  # Options have spaces (e.g., "HY3N5 C 110.250")
                current_opt[symbol] = current
                prior_opt[symbol] = prior
            else:  # Futures (e.g., "TYU5")
                current_fut[symbol] = current
                prior_fut[symbol] = prior
                
        return current_opt, prior_opt, current_fut, prior_fut
        
    def _is_option_position(self, row: pd.Series) -> bool:
        """Check if a position is an option based on symbol format."""
        symbol = str(row.get('Symbol', ''))
        # Options have format "SYMBOL TYPE STRIKE" with spaces
        return ' ' in symbol and len(symbol.split()) >= 3
        
    def _get_underlying_symbol(self, option_symbol: str) -> str:
        """Map option symbol to underlying futures symbol.
        
        For now, assume all options are on TYU5 (10-year note).
        In production, this would use the expiration calendar mapping.
        """
        # TODO: Implement proper mapping from expiration calendar
        return 'TYU5'
        
    def _empty_attribution(self) -> Dict[str, float]:
        """Return empty attribution dictionary."""
        return {
            'delta_pnl': 0.0,
            'gamma_pnl': 0.0,
            'vega_pnl': 0.0,
            'theta_pnl': 0.0,
            'speed_pnl': 0.0,
            'residual': 0.0,
            'implied_vol_current': 0.0,
            'implied_vol_prior': 0.0,
            'attribution_calculated': False
        } 