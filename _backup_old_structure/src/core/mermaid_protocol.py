from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

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