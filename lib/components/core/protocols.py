"""Protocol definitions for UIKitXv2 components and services"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Tuple
from pathlib import Path
import pandas as pd


class MermaidProtocol(ABC):
    """
    Protocol for Mermaid diagram components.
    
    This abstract base class defines the interface for Mermaid diagram
    components that render diagrams using Mermaid syntax.
    """
    
    @abstractmethod
    def render(self, id: str, graph_definition: str, **kwargs) -> Any:
        """
        Render a Mermaid diagram.
        
        Args:
            id (str): The ID for the component.
            graph_definition (str): The Mermaid diagram syntax.
            **kwargs: Additional keyword arguments to pass to the component.
            
        Returns:
            Any: The rendered component.
        """
        pass
    
    @abstractmethod
    def apply_theme(self, theme_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply theme configuration to the component.
        
        Args:
            theme_config (Dict[str, Any]): Theme configuration dictionary.
            
        Returns:
            Dict[str, Any]: Updated theme configuration.
        """
        pass


class DataServiceProtocol(ABC):
    """
    Abstract protocol for ActantEOD data service operations.
    
    This protocol defines the interface for data loading, processing, and querying
    operations for Actant scenario metrics data.
    """
    
    @abstractmethod
    def load_data_from_json(self, json_file_path: Path) -> bool:
        """
        Load and process data from a JSON file into the service.
        
        Args:
            json_file_path: Path to the Actant JSON file to load
            
        Returns:
            True if data was loaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_scenario_headers(self) -> List[str]:
        """
        Get list of unique scenario headers from the loaded data.
        
        Returns:
            List of scenario header strings
        """
        pass
    
    @abstractmethod
    def get_shock_types(self) -> List[str]:
        """
        Get list of unique shock types from the loaded data.
        
        Returns:
            List of shock type strings (e.g., "percentage", "absolute_usd")
        """
        pass
    
    @abstractmethod
    def get_metric_names(self) -> List[str]:
        """
        Get list of available metric names from the loaded data.
        
        Returns:
            List of metric name strings
        """
        pass
    
    @abstractmethod
    def get_filtered_data(
        self, 
        scenario_headers: Optional[List[str]] = None,
        shock_types: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get filtered data based on selection criteria.
        
        Args:
            scenario_headers: List of scenario headers to include (None = all)
            shock_types: List of shock types to include (None = all)
            metrics: List of metrics to include (None = all)
            
        Returns:
            Filtered pandas DataFrame
        """
        pass
    
    @abstractmethod
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about the loaded data.
        
        Returns:
            Dictionary containing data summary information
        """
        pass
    
    @abstractmethod
    def is_data_loaded(self) -> bool:
        """
        Check if data has been successfully loaded.
        
        Returns:
            True if data is loaded and ready for queries, False otherwise
        """
        pass 