"""
Module: overlays
Defines all overlay dialogs and stores for application-level state.
"""
from dash import dcc, html

def overlays(
        elements,
        org_map,
        default_org
    ):
    """
    Build hidden stores and overlay components:
      - current-org store to track selected organization ID
      - canvas-store & active-canvas for custom canvases
      - confirmation dialog when reloading application
      - organization selector overlay
      - detailed info overlay for node/edge publications

    Args:
        elements (list[dict]): Cytoscape elements (nodes + edges) to render
        org_map (list[dict]): Dropdown options for organization selector
        default_org (str): Default selected organization ID

    Returns:
        html.Div: Container wrapping all overlay elements
    """
    pass
