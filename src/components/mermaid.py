from __future__ import annotations
from typing import Any, Dict, Optional

import dash_extensions
from dash import html, dcc
import dash_bootstrap_components as dbc

from ..core.mermaid_protocol import MermaidProtocol
from ..utils.colour_palette import get_mermaid_default_styles, Theme, default_theme

class Mermaid(MermaidProtocol):
    """
    Mermaid diagram component for rendering mermaid.js diagrams.
    
    This component wraps the dash-extensions Mermaid component to provide
    a consistent theming and API interface within the UIKitX framework.
    """
    
    def __init__(self, theme: Optional[Theme] = None):
        """
        Initialize a new Mermaid component.
        
        Args:
            theme (Optional[Theme]): The theme to use for styling. 
                If not provided, the default theme will be used.
        """
        self.theme = theme or default_theme
        self.default_styles = get_mermaid_default_styles(self.theme)
        
    def apply_theme(self, theme_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply theme configuration to the component.
        
        Args:
            theme_config (Dict[str, Any]): Theme configuration dictionary.
            
        Returns:
            Dict[str, Any]: Updated theme configuration.
        """
        # Merge provided config with defaults, with provided config taking precedence
        merged_config = self.default_styles.copy()
        
        if theme_config.get("style"):
            merged_config["style"] = {**merged_config["style"], **theme_config["style"]}
            
        if theme_config.get("mermaid_config"):
            merged_config["mermaid_config"] = {
                **merged_config["mermaid_config"], 
                **theme_config["mermaid_config"]
            }
            
            # Merge theme variables if provided
            if theme_config.get("mermaid_config", {}).get("themeVariables"):
                merged_config["mermaid_config"]["themeVariables"] = {
                    **merged_config["mermaid_config"]["themeVariables"],
                    **theme_config["mermaid_config"]["themeVariables"]
                }
                
        return merged_config
    
    def render(self, id: str, graph_definition: str, **kwargs) -> Any:
        """
        Render a Mermaid diagram.
        
        Args:
            id (str): The ID for the component.
            graph_definition (str): The Mermaid diagram syntax.
            **kwargs: Additional keyword arguments to pass to the component.
                Supported kwargs:
                - style (Dict): Additional CSS styling for the container
                - chart_config (Dict): Additional configuration for Mermaid
                - className (str): Additional CSS classes
                - title (str): Optional title for the diagram
                - description (str): Optional description text
            
        Returns:
            dash.html.Div: A container with the rendered Mermaid component.
        """
        # Get styles
        style = kwargs.pop("style", {})
        container_style = {**self.default_styles["style"], **style}
        
        # Get Mermaid configuration
        chart_config = kwargs.pop("chart_config", {})
        mermaid_config = self.default_styles["mermaid_config"].copy()
        
        if chart_config:
            # Deep merge of nested theme variables if provided
            if chart_config.get("themeVariables"):
                mermaid_config["themeVariables"] = {
                    **mermaid_config.get("themeVariables", {}), 
                    **chart_config.get("themeVariables", {})
                }
                # Remove theme variables from chart_config to avoid duplication
                chart_config_clean = chart_config.copy()
                chart_config_clean.pop("themeVariables", None)
                # Merge other chart configs
                mermaid_config.update(chart_config_clean)
            else:
                # Simple merge if no theme variables
                mermaid_config.update(chart_config)
        
        # Optional title and description
        title = kwargs.pop("title", None)
        description = kwargs.pop("description", None)
        className = kwargs.pop("className", "")
        
        # Create component hierarchy
        header_elements = []
        if title:
            header_elements.append(html.H4(title, style={"color": self.theme.text_light}))
        if description:
            header_elements.append(html.P(description, style={"color": self.theme.text_subtle}))
        
        return html.Div([
            # Optional header
            *header_elements,
            # Mermaid diagram
            dash_extensions.Mermaid(
                id=id,
                chart=graph_definition,
                config=mermaid_config,
                **kwargs
            )
        ], style=container_style, className=f"uikitx-mermaid {className}".strip()) 