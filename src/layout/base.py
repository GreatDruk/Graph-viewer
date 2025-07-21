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
    pass
