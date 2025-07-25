"""
Module: tooltip_callbacks
Defines clientside callbacks for hover and click tooltips on graph.
"""
from dash import Input, Output, State

def tooltip_callbacks(app):
    """
    Registers all clientside callbacks related to displaying and hiding
    the hover and click tooltips on graph.

    Each tooltip shows different levels of detail:
      - hover-tooltip: shows minimal info (name, selected metric, cluster)
      - tapNodeData: shows detailed node info (links, publications, years, etc.)
      - tapEdgeData: shows edge info (source-target and weight)
    """
    # Hover tooltip
    app.clientside_callback(
        """
        function(mouseoverData, sizeValue, sizeOptions) {
            // Show small tooltip with node name, chosen metric value, and cluster on hover
            if (mouseoverData) {
                const name = mouseoverData.id || '';
                const val = mouseoverData[sizeValue] || '0';
                const label = sizeOptions.find(o => o.value === sizeValue)?.label || 'None';
                const cluster = mouseoverData.cluster;
                const description = [
                    window.React.createElement('span', {}, name),
                    window.React.createElement('span', {}, `${label}: ${val}`),
                    window.React.createElement('span', {}, `Кластер: ${cluster}`)
                ];
                return [
                    {
                        'display': 'flex',
                    },
                    description,
                    {
                        'display': 'none'
                    },
                ];
            }
            // Hide tooltip when not hovering any node
            return [{'display': 'none'}, '', {'display': 'none'}];
        }
        """,
        [
            Output('hover-tooltip', 'style', allow_duplicate=True),
            Output('hover-tooltip-content', 'children', allow_duplicate=True),
            Output('show-info-button', 'style', allow_duplicate=True),
        ],
        [
            Input('network-graph', 'mouseoverNodeData'),
            Input('size-dropdown', 'value'),
        ],
        State('size-dropdown', 'options'),
        prevent_initial_call=True
    )

    # Click tooltip for nodes
    app.clientside_callback(
        """
        function(nodeData, sizeOptions) {
            // Show detailed tooltip with all node metrics and publication years
            if (nodeData) {
                const name = nodeData.id || '';
                const links = nodeData.Links || '0';
                const indLinks = nodeData.Strength || '0';
                const documents = nodeData.Documents || '0';
                const citations = nodeData.Citations || '0';
                const first_pub_year = nodeData.First_pub_year || '0';
                const avg_pub_year = nodeData.Avg_pub_year || '0';
                const last_pub_year = nodeData.Last_pub_year || '0';
                const cluster = nodeData.cluster || '0';
                const description = [
                    window.React.createElement('span', {}, name),
                    window.React.createElement('span', {}, `Количество связей: ${links}`),
                    window.React.createElement('span', {}, `Индекс связанности: ${indLinks}`),
                    window.React.createElement('span', {}, `Число публикаций: ${documents}`),
                    window.React.createElement('span', {}, `Число цитирований: ${citations}`),
                    window.React.createElement('span', {}, `Год первой публикации: ${first_pub_year}`),
                    window.React.createElement('span', {}, `Ср. год публикаций: ${avg_pub_year}`),
                    window.React.createElement('span', {}, `Год последней публикации: ${last_pub_year}`),
                    window.React.createElement('span', {}, `Кластер: ${cluster}`),
                ];
                return [
                    {
                        'display': 'flex',
                    },
                    description,
                    {
                        'display': 'block',
                    },
                    nodeData.id,
                ];
            }
            // Hide when clicking outside nodes
            return [{'display': 'none'}, '', {'display': 'none'}, ''];
        }
        """,
        [
            Output('hover-tooltip', 'style', allow_duplicate=True),
            Output('hover-tooltip-content', 'children', allow_duplicate=True),
            Output('show-info-button', 'style'),
            Output('selected-item', 'data'),
        ],
        Input('network-graph', 'tapNodeData'),
        State('size-dropdown','options'),
        prevent_initial_call=True
    )

    # Click tooltip for edges
    app.clientside_callback(
        """
        function(edgeData) {
            // Show tooltip with source-target and weight on edge click
            if (edgeData) {
                const from = edgeData.source || '';
                const to = edgeData.target || '';
                const label = `${from} — ${to}`;
                const weight = `Совместных работ: ${edgeData.weight}`;
                const hoverText = edgeData.hover || '';
                const description = [
                    window.React.createElement('span', {}, label),
                    window.React.createElement('span', {}, weight),
                ];
                return [
                    {
                        'display': 'flex',
                    },
                    description,
                    {
                        'display': 'flex',
                    },
                    `${edgeData.id}#${label}`,
                ];
            }
            // Hide when clicking outside edges
            return [{'display': 'none'}, '', {'display': 'none'}, ''];
        }
        """,
        [
            Output('hover-tooltip', 'style', allow_duplicate=True),
            Output('hover-tooltip-content', 'children', allow_duplicate=True),
            Output('show-info-button', 'style', allow_duplicate=True),
            Output('selected-item', 'data', allow_duplicate=True),
        ],
        Input('network-graph', 'tapEdgeData'),
        prevent_initial_call=True
    )

    # Hide tooltip on clicking blank space
    app.clientside_callback(
        """
        function(selNodes, selEdges) {
            // If nothing is selected or clicked, hide tooltip
            if ((!selNodes || selNodes.length === 0) && (!selEdges || selEdges.length === 0)) {
                return {'display': 'none'};
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('hover-tooltip', 'style', allow_duplicate=True),
        [
            Input('network-graph', 'selectedNodeData'),
            Input('network-graph', 'selectedEdgeData'),
        ],
        prevent_initial_call=True
    )
