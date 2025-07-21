"""
Module: sidebar
Defines the sidebar layout of application.
"""
from dash import dcc, html
import plotly.express as px

def sidebar(
        size_options,
        color_options,
        nodes,
        edges,
        num_publication,
        total_cites,
        h_index,
        years,
        counts_publication_by_year
    ):
    """
    Build the sidebar component consisting of:
      - Application logo and title
      - Tabs: Organization info, Visualization, Search, Canvas management

    Args:
        size_options (list[dict]): Dropdown options for node size metrics
        color_options (list[dict]): Dropdown options for node color metrics
        nodes (DataFrame): Node metadata (clusters, positions, etc.)
        edges (DataFrame): Edge metadata (weights, sources, targets)
        num_publication (int): Total number of publications
        total_cites (int): Total citation count
        h_index (int): H-index for the org
        years (list[int]): Range of publication years
        counts_publication_by_year (list[int]): Publication counts per year

    Returns:
        html.Div: Sidebar container
    """
    pass
