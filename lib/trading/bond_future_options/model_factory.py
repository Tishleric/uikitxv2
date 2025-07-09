"""
Model Factory for Option Pricing Models

Provides a central registry and factory for creating option pricing model instances.
This allows for easy model selection and future extensibility.
"""

from typing import Dict, Type, Any
from .option_model_interface import OptionModelInterface
from .models import BachelierV1
from lib.monitoring.decorators import monitor


class ModelFactory:
    """Factory for creating option pricing model instances."""
    
    # Registry of available models
    _models: Dict[str, Type[OptionModelInterface]] = {
        'bachelier_v1': BachelierV1,
        'bachelier_v1.0': BachelierV1,  # Alias for convenience
    }
    
    @staticmethod
    @monitor()
    def create_model(
        model_name: str = 'bachelier_v1',
        **kwargs: Any
    ) -> OptionModelInterface:
        """
        Create an instance of the specified model.
        
        Args:
            model_name: Name of the model to create
            **kwargs: Model-specific parameters (e.g., future_dv01, convexity)
            
        Returns:
            Instance of the requested model
            
        Raises:
            ValueError: If model_name is not recognized
            
        Example:
            >>> model = ModelFactory.create_model('bachelier_v1', future_dv01=0.063)
            >>> vol = model.calculate_implied_vol(110.75, 110.5, 0.05, 0.359375)
        """
        if model_name not in ModelFactory._models:
            available = list(ModelFactory._models.keys())
            raise ValueError(
                f"Unknown model '{model_name}'. Available models: {available}"
            )
        
        model_class = ModelFactory._models[model_name]
        return model_class(**kwargs)
    
    @staticmethod
    def list_models() -> Dict[str, str]:
        """
        List all available models with their versions.
        
        Returns:
            Dictionary of model names to version strings
        """
        result = {}
        for name, model_class in ModelFactory._models.items():
            # Create temporary instance to get version
            instance = model_class()
            result[name] = instance.get_version()
        return result
    
    @staticmethod
    def register_model(name: str, model_class: Type[OptionModelInterface]) -> None:
        """
        Register a new model in the factory.
        
        This allows for dynamic model registration, useful for plugins
        or custom implementations.
        
        Args:
            name: Name to register the model under
            model_class: Model class implementing OptionModelInterface
            
        Raises:
            ValueError: If name is already registered
        """
        if name in ModelFactory._models:
            raise ValueError(f"Model '{name}' is already registered")
        
        ModelFactory._models[name] = model_class 