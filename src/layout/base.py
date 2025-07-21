"""
Module: base
Defines the main Dash application layout by composing sidebar, graph area, and overlay components.
"""
from dash import html
from .sidebar import sidebar
from .graph_area import graph_area
from .overlays import overlays
from src.data_prepare import prepare_network_elements

def base_layout(org_map, default_org):
    """
    Create and return the top-level layout:
      - Initialize hidden overlays and state stores (org selector, dialogs, canvases).
      - Build the sidebar.
      - Build the main graph area.

    Args:
        org_map (list[dict]): Dropdown options for organization selection.
        default_org (str): Default organization ID to load on app start.

    Returns:
        html.Div: Root container holding all UI components.
    """
    pass
