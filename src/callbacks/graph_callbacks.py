"""
Module: graph_callbacks
Defines clientside callbacks for graph management.
"""
from dash import Input, Output, State

def graph_callbacks(app):
    """
    Registers callbacks related to the graph area interactions,
    including opening dialogs, handling sidebar toggles, and applying
    clientside styling and filtering to graph.
    """
    # Logo click: open confirmation dialog for reload
    app.clientside_callback(
        """
        function(n_clicks) {
            // Open confirmation dialog
            if (n_clicks > 0) {
                return {'display': 'flex'};
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('dialog-overlay', 'style'),
        Input('app-logo', 'n_clicks'),
        prevent_initial_call=True
    )

    # Sidebar toggle: show organization selection overlay
    app.clientside_callback(
        """
        function(n, current) {
            if (n > 0) {
                return [{'display': 'flex'}, current];
            }
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        """,
        [
            Output('overlay', 'style', allow_duplicate=True),
            Output('overlay-dropdown', 'value'),
        ],
        Input('open-overlay-button', 'n_clicks'),
        State('current-org', 'data'),
        prevent_initial_call=True
    )

    # Client-side graph styling: resize nodes by selected metric
    app.clientside_callback(
        """
        function(sizeValue, basic, sizeLimits) {
            let graphStyle = JSON.parse(JSON.stringify(basic));

            // Resize nodes by selected metric
            const bounds = sizeLimits[sizeValue];
            const VM = bounds.min;
            const VX = bounds.max;
            if(sizeValue && VM != null && VX != null) {
                graphStyle.push({
                    selector: `node[${sizeValue}]`,
                    style: {
                        'width': `mapData(${sizeValue}, ${VM}, ${VX}, 10, 40)`,
                        'height': `mapData(${sizeValue}, ${VM}, ${VX}, 10, 40)`,
                        'font-size': `mapData(${sizeValue}, ${VM}, ${VX}, 7, 17)`
                    }
                });
            };

            return graphStyle;
        }
        """,
        Output('network-graph', 'stylesheet', allow_duplicate=True),
        Input('size-dropdown', 'value'),
        [
            State('network-graph', 'stylesheet'),
            State('size-limits', 'data'),
        ],
        prevent_initial_call=True
    )

    # Client-side graph styling: hide edges below threshold
    app.clientside_callback(
        """
        function(edgeTh, basic, showIsolates) {
            let graphStyle = JSON.parse(JSON.stringify(basic));

            // Hide edges below threshold
            graphStyle.push({
                selector: `edge[weight < ${edgeTh}]`,
                style: { 'display': 'none' }
            });
            graphStyle.push({
                selector: `node[max_edge_weight < ${edgeTh}]`,
                style: { 'display': showIsolates.length ? 'element' : 'none' }
            });
            
            graphStyle.push({
                selector: `edge[weight >= ${edgeTh}]`,
                style: { 'display': 'element' }
            });
            graphStyle.push({
                selector: `node[max_edge_weight >= ${edgeTh}]`,
                style: { 'display': 'element'}
            });

            return graphStyle;
        }
        """,
        Output('network-graph', 'stylesheet', allow_duplicate=True),
        Input('edge-threshold', 'value'),
        [
            State('network-graph', 'stylesheet'),
            State('show-isolates', 'value'),
        ],
        prevent_initial_call=True
    )

    # Client-side graph styling: show edge labels
    app.clientside_callback(
        """
        function(showWeight, basic) {
            let graphStyle = JSON.parse(JSON.stringify(basic));

            // Show edge labels
            graphStyle.push({
                selector: 'edge',
                style: { 'text-opacity': showWeight.length ? 1 : 0 }
            });

            return graphStyle;
        }
        """,
        Output('network-graph', 'stylesheet', allow_duplicate=True),
        Input('show-weights', 'value'),
        State('network-graph', 'stylesheet'),
        prevent_initial_call=True
    )

    # Client-side graph styling: show isolate nodes
    app.clientside_callback(
        """
        function(showIsolates, edgeTh, basic) {
            let graphStyle = JSON.parse(JSON.stringify(basic));

            // Show isolate nodes
            graphStyle.push({
                selector: `node[max_edge_weight < ${edgeTh}]`,
                style: { 'display': showIsolates.length ? 'element' : 'none' }
            });
            graphStyle.push({
                selector: `node[max_edge_weight >= ${edgeTh}]`,
                style: { 'display': 'element'}
            });

            return graphStyle;
        }
        """,
        Output('network-graph', 'stylesheet', allow_duplicate=True),
        Input('show-isolates', 'value'),
        [
            State('edge-threshold', 'value'),
            State('network-graph', 'stylesheet'),
        ],
        prevent_initial_call=True
    )

    # Client-side graph styling: highlight nodes matching search
    app.clientside_callback(
        """
        function(person, basic) {
            let graphStyle = JSON.parse(JSON.stringify(basic));

            // Highlight nodes matching search
            if(person) {
                const low = person.toLowerCase();
                graphStyle.push({
                    selector: `node[id *= "${low}"]`,
                    style: { 'background-color': 'red' }
                });
                graphStyle.push({
                    selector: `node[id !*= "${low}"]`,
                    style: { 'background-color': '#b0daff' }
                });
            }

            return graphStyle;
        }
        """,
        Output('network-graph', 'stylesheet', allow_duplicate=True),
        Input('person-search', 'value'),
        State('network-graph', 'stylesheet'),
        prevent_initial_call=True
    )

    # Client-side graph styling: highlight nodes by cluster and select others
    app.clientside_callback(
        """
        function(clusterValue, elements, basic) {
            // Highlight all nodes in the chosen cluster and lock others
            if (clusterValue === null || clusterValue === '') {
                return [window.dash_clientside.no_update, window.dash_clientside.no_update];
            }
            const clusterNum = Number(clusterValue);
            let graphStyle = JSON.parse(JSON.stringify(basic));
            const updated = JSON.parse(JSON.stringify(elements));
            for (let el of updated) {
                if (el.data && el.data.cluster !== undefined) {
                    el.selected = (el.data.cluster === clusterNum);
                }
            }
            graphStyle.push({
                selector: `node[cluster = ${clusterValue}]`,
                style: { 'background-color': 'red' }
            });
            graphStyle.push({
                selector: `node[cluster != ${clusterValue}]`,
                style: { 'background-color': '#b0daff' }
            });
            return [graphStyle, updated];
        }
        """,
        [
            Output('network-graph', 'stylesheet', allow_duplicate=True),
            Output('network-graph', 'elements', allow_duplicate=True),
        ],
        Input('cluster-filter', 'value'),
        [
            State('network-graph', 'elements'),
            State('network-graph', 'stylesheet'),
        ],
        prevent_initial_call=True
    )

    # Reset filters: restore original styles and clear search/cluster inputs
    app.clientside_callback(
        """
        function(clickReset, basic) {
            // On reset, restore original node colors and clear filters
            let graphStyle = JSON.parse(JSON.stringify(basic));

            if(clickReset) {
                graphStyle.push({
                    selector: `node[label]`,
                    style: { 'background-color': 'data(color)' }
                });
                return [graphStyle, '', ''];
            }
            return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        """,
        [
            Output('network-graph', 'stylesheet', allow_duplicate=True),
            Output('person-search', 'value', allow_duplicate=True),
            Output('cluster-filter', 'value', allow_duplicate=True),
        ],
        Input('reset-button', 'n_clicks'),
        State('network-graph', 'stylesheet'),
        prevent_initial_call=True
    )

    # Client-side graph styling: color nodes by chosen metric
    app.clientside_callback(
        """
        function(colorMetric, vmin, vmax, basic, sizeLimits) {
            let graphStyle = JSON.parse(JSON.stringify(basic));

            // Color nodes by chosen metric
            if(colorMetric) {
                let minVal = sizeLimits[colorMetric].min;
                let maxVal = sizeLimits[colorMetric].max;

                minVal = Math.max(minVal, vmin);
                maxVal = Math.min(maxVal, vmax);

                if (minVal <= maxVal) {
                    const midVal = (minVal + maxVal) / 2;
                    graphStyle.push({
                        selector: `node[${colorMetric} <= ${midVal}][${colorMetric} >= ${minVal}]`,
                        style: {
                            'background-color': `mapData(${colorMetric}, ${minVal}, ${midVal}, #440154, #26828E)`,
                            'display': 'element'
                        }
                    });
                    graphStyle.push({
                        selector: `node[${colorMetric} > ${midVal}][${colorMetric} <= ${maxVal}]`,
                        style: {
                            'background-color': `mapData(${colorMetric}, ${midVal}, ${maxVal}, #26828E, #FDE725)`,
                            'display': 'element'
                        }
                    });

                    graphStyle.push({
                        selector: `node[${colorMetric} < ${vmin}]`,
                        style: { 'display': 'none' }
                    });
                    graphStyle.push({
                        selector: `node[${colorMetric} > ${vmax}]`,
                        style: { 'display': 'none' }
                    });
                }
            };

            return graphStyle;
        }
        """,
        Output('network-graph', 'stylesheet', allow_duplicate=True),
        [
            Input('color-by-dropdown', 'value'),
            Input('node-color-min', 'value'),
            Input('node-color-max', 'value'),
        ],
        [
            State('network-graph', 'stylesheet'),
            State('size-limits', 'data')
        ],
        prevent_initial_call=True
    )

    # Toggle metric coloring controls
    app.clientside_callback(
        """
        function(clickColor, basic) {
            // Toggle display of the metric-coloring controls
            if (!clickColor) {
                return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
            }
            let graphStyle = JSON.parse(JSON.stringify(basic));
            if (clickColor % 2 == 1) {
                return [graphStyle, {'display': 'block'}, {'display': 'flex'}, ''];
            }
            graphStyle.push({
                selector: `node[label]`,
                style: {
                    'background-color': 'data(color)',
                    'display': 'element'
                }
            });
            return [graphStyle, {'display': 'none'}, {'display': 'none'}, ''];
        }
        """,
        [
            Output('network-graph', 'stylesheet', allow_duplicate=True),
            Output('color-by-container', 'style', allow_duplicate=True),
            Output('color-thresholds-container', 'style', allow_duplicate=True),
            Output('color-by-dropdown', 'value', allow_duplicate=True),
        ],
        Input('color-button', 'n_clicks'),
        State('network-graph', 'stylesheet'),
        prevent_initial_call=True
    )

    # Update metric limits when a new metric is chosen
    app.clientside_callback(
        """
        function(metric, nodeSize) {
            if (!metric || !nodeSize || !nodeSize[metric]) {
                return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
            }

            const sizes = nodeSize[metric];
            const vmin = Math.floor(sizes.min);
            const vmax = Math.ceil(sizes.max);

            return [vmin, vmax, {'vmin': vmin, 'vmax': vmax}];
        }
        """,
        [
            Output('node-color-min', 'value', allow_duplicate=True),
            Output('node-color-max', 'value', allow_duplicate=True),
            Output('node-color-limits', 'data', allow_duplicate=True),
        ],
        Input('color-by-dropdown','value'),
        State('size-limits', 'data'),
        prevent_initial_call=True
    )

    # Build and show color legend when metric coloring is active
    app.clientside_callback(
        """
        function(colorMetric, vmin, vmax) {
            // Build and show legend labels when metric selected
            if (!colorMetric || vmin == null || vmax == null) {
                return [{'display': 'none'}, window.dash_clientside.no_update];
            }
            const mid = (vmin + vmax) / 2;
            const legendStyle = {
                'display': 'block',
            };
            const labels = [
                window.React.createElement('span', {children: `${vmin}`}),
                window.React.createElement('span', {children: `${mid}`}),
                window.React.createElement('span', {children: `${vmax}`})
            ];
            return [legendStyle, labels];
        }
        """,
        [
            Output('color-legend', 'style', allow_duplicate=True),
            Output('legend-labels', 'children'),
        ],
        [
            Input('color-by-dropdown', 'value'),
            Input('node-color-min', 'value'),
            Input('node-color-max', 'value'),
        ],
        prevent_initial_call=True
    )
