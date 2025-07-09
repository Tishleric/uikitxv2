"""
Bachelier Model V1 Implementation

Wraps the existing BondFutureOption implementation to conform to the
OptionModelInterface protocol. This maintains all current functionality
while providing a standardized interface.
"""

from typing import Dict, Any, Optional
from ..api import (
    calculate_implied_volatility as api_implied_vol,
    calculate_greeks as api_greeks
)
from ..pricing_engine import BondFutureOption
from lib.monitoring.decorators import monitor


class BachelierV1:
    """Bachelier model v1.0 implementation using existing bond future options engine."""
    
    def __init__(
        self,
        future_dv01: float = 0.063,
        future_convexity: float = 0.002404,
        yield_level: float = 0.05
    ):
        """
        Initialize the Bachelier V1 model.
        
        Args:
            future_dv01: DV01 of the bond future
            future_convexity: Convexity of the bond future
            yield_level: Current yield level
        """
        self.future_dv01 = future_dv01
        self.future_convexity = future_convexity
        self.yield_level = yield_level
        self._engine = BondFutureOption(future_dv01, future_convexity, yield_level)
    
    @monitor()
    def calculate_price(
        self, 
        F: float, 
        K: float, 
        T: float, 
        volatility: float, 
        option_type: str = 'put'
    ) -> float:
        """Calculate option price using Bachelier formula."""
        return self._engine.bachelier_future_option_price(F, K, T, volatility, option_type)
    
    @monitor()
    def calculate_implied_vol(
        self, 
        F: float, 
        K: float, 
        T: float, 
        market_price: float, 
        option_type: str = 'put',
        initial_guess: Optional[float] = None,
        tolerance: float = 1e-6,
        max_iterations: int = 100
    ) -> float:
        """Calculate implied volatility using existing API with all safeguards."""
        return api_implied_vol(
            F=F,
            K=K,
            T=T,
            market_price=market_price,
            option_type=option_type,
            future_dv01=self.future_dv01,
            future_convexity=self.future_convexity,
            yield_level=self.yield_level,
            initial_guess=initial_guess,
            tolerance=tolerance,
            max_iterations=max_iterations,
            suppress_output=True
        )
    
    @monitor()
    def calculate_greeks(
        self, 
        F: float, 
        K: float, 
        T: float, 
        volatility: float, 
        option_type: str = 'put'
    ) -> Dict[str, float]:
        """Calculate all Greeks using existing API."""
        return api_greeks(
            F=F,
            K=K,
            T=T,
            volatility=volatility,
            option_type=option_type,
            future_dv01=self.future_dv01,
            future_convexity=self.future_convexity,
            yield_level=self.yield_level,
            return_scaled=True
        )
    
    def get_version(self) -> str:
        """Get model version identifier."""
        return "bachelier_v1.0"
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get model configuration parameters."""
        return {
            "model_type": "bachelier",
            "version": "1.0",
            "future_dv01": self.future_dv01,
            "future_convexity": self.future_convexity,
            "yield_level": self.yield_level,
            "tolerance": 1e-6,
            "max_iterations": 100,
            "min_price_safeguard": 1/64,
            "max_implied_vol": 1000.0
        } 