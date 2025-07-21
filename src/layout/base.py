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
    # Prepare data for initial organization
    data = prepare_network_elements(default_org)

    # Unpack network and UI parameters
    elements = data['elements']
    basic_stylesheet = data['stylesheet']
    size_options = data['size_options']
    metrics_bounds = data['metrics_bounds']
    color_options = data['color_options']
    nodes = data['nodes']
    edges = data['edges']
    num_publication = data['num_publication']
    total_cites = data['num_cites']
    h_index = data['h_index']
    years = data['years']
    counts_publication_by_year = data['counts_publication_by_year']

    return html.Div([
        # Overlay components and hidden stores
        overlays(org_map, default_org),

        # Main content: sidebar controls + graph view
        html.Div([
            sidebar(
                size_options,
                color_options,
                nodes,
                edges,
                num_publication,
                total_cites,
                h_index,
                years,
                counts_publication_by_year
            ),
            graph_area(
                elements,
                basic_stylesheet,
                metrics_bounds
            )
        ], className='content')
    ], className='container')
