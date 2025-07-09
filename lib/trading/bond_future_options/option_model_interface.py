"""
Option Model Interface Protocol

Defines the standard interface that all option pricing models must implement.
This allows for easy switching between different model implementations while
keeping the calling code unchanged.
"""

from typing import Protocol, Dict, Any, Optional
from lib.monitoring.decorators import monitor


class OptionModelInterface(Protocol):
    """Protocol defining the interface for option pricing models."""
    
    @monitor()
    def calculate_price(
        self, 
        F: float, 
        K: float, 
        T: float, 
        volatility: float, 
        option_type: str = 'put'
    ) -> float:
        """
        Calculate option price using the model's pricing formula.
        
        Args:
            F: Future price
            K: Strike price
            T: Time to expiry in years
            volatility: Price volatility
            option_type: 'call' or 'put'
            
        Returns:
            Option price
        """
        ...
    
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
        """
        Calculate implied volatility from market price.
        
        Args:
            F: Future price
            K: Strike price
            T: Time to expiry in years
            market_price: Market price of the option
            option_type: 'call' or 'put'
            initial_guess: Initial volatility guess
            tolerance: Convergence tolerance
            max_iterations: Maximum iterations
            
        Returns:
            Implied volatility
            
        Raises:
            ValueError: If solver fails to converge or constraints violated
        """
        ...
    
    @monitor()
    def calculate_greeks(
        self, 
        F: float, 
        K: float, 
        T: float, 
        volatility: float, 
        option_type: str = 'put'
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for the option.
        
        Args:
            F: Future price
            K: Strike price
            T: Time to expiry in years
            volatility: Price volatility
            option_type: 'call' or 'put'
            
        Returns:
            Dictionary of Greek values (scaled as per standard conventions)
        """
        ...
    
    def get_version(self) -> str:
        """
        Get the model version identifier.
        
        Returns:
            Version string (e.g., 'bachelier_v1.0')
        """
        ...
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get the model's configuration parameters.
        
        Returns:
            Dictionary of model parameters (e.g., future_dv01, convexity, etc.)
        """
        ... 