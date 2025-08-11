"""
Greek Calculator API Facade

High-level API for option Greeks calculation with model selection and batch processing.
This provides a simple, clean interface for calculating Greeks across different models.
"""

from typing import Dict, List, Any, Optional, Union
from .model_factory import ModelFactory
from lib.monitoring.decorators import monitor


class GreekCalculatorAPI:
    """Facade for option Greeks calculation with model selection."""
    
    def __init__(self, default_model: str = 'bachelier_v1'):
        """
        Initialize the Greek Calculator API.
        
        Args:
            default_model: Default model to use if not specified in calls
        """
        self.default_model = default_model
    
    @monitor()
    def analyze(
        self,
        options_data: Union[Dict, List[Dict]],
        model: Optional[str] = None,
        model_params: Optional[Dict[str, Any]] = None,
        requested_greeks: Optional[List[str]] = None
    ) -> Union[Dict, List[Dict]]:
        """
        Analyze options to calculate implied volatility and Greeks.
        
        Args:
            options_data: Single option dict or list of option dicts containing:
                - F: Future price
                - K: Strike price
                - T: Time to expiry in years
                - market_price: Market price of the option
                - option_type: 'call' or 'put' (default: 'put')
            model: Model name to use (default: self.default_model)
            model_params: Model-specific parameters (e.g., future_dv01)
            requested_greeks: Optional list of specific Greeks to calculate (default: all)
            
        Returns:
            Single result dict or list of result dicts with:
                - All input fields
                - volatility: Implied volatility
                - greeks: Dictionary of Greek values
                - model_version: Version of model used
                - success: True if calculation succeeded
                - error_message: Error details if failed
                
        Example:
            >>> api = GreekCalculatorAPI()
            >>> result = api.analyze({
            ...     'F': 110.75, 'K': 110.5, 'T': 0.05, 
            ...     'market_price': 0.359375
            ... })
        """
        # Handle single option as list of one
        single_option = isinstance(options_data, dict)
        if single_option:
            options_data = [options_data]
        
        # Use specified model or default
        model_name = model or self.default_model
        model_params = model_params or {}
        
        # Create model instance
        model_instance = ModelFactory.create_model(model_name, **model_params)
        model_version = model_instance.get_version()
        
        # Process each option
        results = []
        for option in options_data:
            result = self._analyze_single(option, model_instance, model_version, requested_greeks)
            results.append(result)
        
        # Return single result if input was single
        return results[0] if single_option else results
    
    def _analyze_single(
        self,
        option: Dict,
        model: Any,
        model_version: str,
        requested_greeks: Optional[List[str]] = None
    ) -> Dict:
        """Analyze a single option."""
        # Extract required fields
        F = option['F']
        K = option['K']
        T = option['T']
        market_price = option['market_price']
        option_type = option.get('option_type', 'put')
        
        # Create result with input data
        result = option.copy()
        result['model_version'] = model_version
        
        try:
            # Calculate implied volatility
            volatility = model.calculate_implied_vol(
                F, K, T, market_price, option_type
            )
            
            # Calculate Greeks
            all_greeks = model.calculate_greeks(
                F, K, T, volatility, option_type
            )
            
            # Filter Greeks if requested
            if requested_greeks is not None:
                # Only include requested Greeks
                greeks = {k: v for k, v in all_greeks.items() if k in requested_greeks}
                # Also handle derived Greeks
                if 'speed_F' in requested_greeks and 'speed_y' in all_greeks:
                    greeks['speed_y'] = all_greeks['speed_y']
            else:
                # Return all Greeks if no filter specified (backward compatibility)
                greeks = all_greeks
            
            # Add results
            result['volatility'] = volatility
            result['greeks'] = greeks
            result['success'] = True
            result['error_message'] = None
            
        except Exception as e:
            # Handle calculation failures
            result['volatility'] = None
            result['greeks'] = None
            result['success'] = False
            result['error_message'] = str(e)
        
        return result
    
    @monitor()
    def compare_models(
        self,
        models: List[str],
        options_data: Union[Dict, List[Dict]],
        model_params: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Compare results across multiple models (stub for future implementation).
        
        Args:
            models: List of model names to compare
            options_data: Option(s) to analyze
            model_params: Model-specific parameters by model name
            
        Returns:
            Comparison results (structure TBD)
        """
        # Stub for future implementation
        raise NotImplementedError(
            "Model comparison will be implemented in a future version"
        ) 