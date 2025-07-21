"""
Module: graph_area
Defines the main graph display area of application.
"""
from dash import dcc, html
import dash_cytoscape as cyto

def graph_area(
        elements,
        basic_stylesheet,
        metrics_bounds
    ):
    """
    Build the graph display section.

    Args:
        elements (list[dict]): Cytoscape elements (nodes + edges) to render
        basic_stylesheet (list[dict]): Base Cytoscape stylesheet definitions
        metrics_bounds (dict): Precomputed min/max bounds for all size metrics

    Returns:
        html.Div: Container with stored state, tabs, Cytoscape graph, legend, and tooltip
    """
    return html.Div([
        # Store to hold size-metric min/max for client-side resizing
        dcc.Store(
            id='size-limits',
            data=metrics_bounds
        ),

        # Tabs for switching between full graph and custom canvases
        dcc.Tabs(
            id='graph-tabs',
            value='full'
        ),

        # Cytoscape network component
        cyto.Cytoscape(
            id='network-graph',
            elements=elements,
            layout={'name': 'preset'},
            stylesheet=basic_stylesheet,
            userPanningEnabled=True,
            boxSelectionEnabled=True,
            autounselectify=False,
            wheelSensitivity=0.15,
            style = {
                'width': '100%',
                'backgroundColor': '#EEECE3'
            }
        ),

        # Color legend bar and labels (shown when metric coloring active)
        html.Div([
            html.Div(id='legend-bar'),
            html.Div(id='legend-labels')
        ], id='color-legend'),
        
        # Tooltip overlay: dynamic content and 'View publications' button
        html.Div([
            html.Div(id='hover-tooltip-content'),
            html.Button(
                'Смотреть публикации',
                id='show-info-button',
                n_clicks=0,
            )
        ], id='hover-tooltip'),
    ], className='content__graph')