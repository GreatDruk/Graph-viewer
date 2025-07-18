"""
Module: callbacks
Defines all Dash callbacks for:
  - updating the graph on organization change
  - controlling the overlay (select org, cancel)
  - client-side tools: sizing, filtering, search, metrics coloring
  - rendering node/edge tooltips
  - showing detailed info overlay for nodes and edges
"""

from dash import html, Input, Output, State, exceptions
import pandas as pd
import plotly.express as px

from src.data_prepare import prepare_network_elements, load_cache_authors, load_cache_coauthors

def get_callbacks(app, org_name_map):
    # Update graph by 'Change organization'
    @app.callback(
        Output('network-graph', 'elements'),
        Output('network-graph', 'stylesheet'),
        Output('network-graph', 'mouseoverNodeData'),

        Output('name-organization', 'children'),

        Output('info-organization-authors', 'children'),
        Output('info-organization-publications', 'children'),
        Output('info-organization-cites', 'children'),
        Output('info-organization-hindex', 'children'),

        Output('info-organization-graph', 'figure'),

        Output('canvas-store', 'data'),
        Output('active-canvas', 'data'),
        Output('canvas-error', 'style'),
        Output('canvas-error', 'children'),

        Output('size-dropdown', 'value'),

        Output('edge-threshold', 'min'),
        Output('edge-threshold', 'max'),
        Output('edge-threshold', 'value'),

        Output('info-organization-cluster', 'children'),
        Output('cluster-filter', 'min'),
        Output('cluster-filter', 'max'),
        Output('cluster-filter', 'value'),

        Output('person-search', 'value'),

        Output('show-weights', 'value'),
        Output('show-isolates', 'value'),

        Output('color-by-dropdown', 'value'),
        Output('node-color-min', 'value'),
        Output('node-color-max', 'value'),
        Output('color-by-container', 'style'),
        Output('color-thresholds-container', 'style'),
        Output('node-color-limits', 'data'),
        
        Output('size-limits', 'data'),

        Output('color-legend', 'style'),
        Output('hover-tooltip', 'style'),

        Output('preloader', 'style'),

        Input('current-org', 'data')
    )
    def update_graph_for_org(org_id):
        """
        Server-side callback. Reloads all graph data (elements, styles,
        sidebar info, thresholds, etc.) when the selected organization changes.
        """
        # Load new data
        data = prepare_network_elements(org_id)
        elements = data['elements']
        stylesheet = data['stylesheet']
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

        # Name organization
        org_name = org_name_map.get(org_id, org_id)

        # Info organization
        org_info_authors = f'Авторов: {len(nodes)}'
        org_info_pub = f'Публикаций: {num_publication}'
        org_info_cites = f'Цитирований: {total_cites}'
        org_info_hindex = f'Индекс Хирша: {h_index}'

        # Graph publications over time
        fig = (
            px.line(
                x=years,
                y=counts_publication_by_year,
            )
            .update_traces(line=dict(color='#EEECE3'))
            .update_layout(
                height=200,
                title=None,
                font_family='Arial',
                paper_bgcolor='#373539',
                plot_bgcolor='#373539',
                margin=dict(l=0, r=13, t=0, b=0),
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=True,
                    title=None,
                    showline=True,
                    linecolor='#EEECE3',
                    linewidth=1,
                    ticks='outside',
                    ticklen=3,
                    tickcolor='#EEECE3',
                    tickfont=dict(
                        color='#EEECE3',
                        family='Arial',
                        size=10,
                    ),
                    tickson='labels',
                    ticklabelposition='outside'
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=True,
                    title=None,
                    showline=True,
                    linecolor='#EEECE3',
                    linewidth=1,
                    ticklen=3,
                    tickcolor='#EEECE3',
                    ticks='outside',
                    tickfont=dict(
                        color='#EEECE3',
                        family='Arial',
                        size=10,
                    ),
                    tickson='labels',
                    ticklabelposition='outside'
                ),
                dragmode=False,
            )
        )

        # Default canvases
        empty_store = {'full': elements, 'canvases': [], 'nextCanvasIndex': 0,}
        default_active = 'full'

        # Default size option
        default_size = size_options[0]['value']

        # Edges thresholds
        min_w = int(edges['weight'].min())
        max_w = int(edges['weight'].max())
        n_nodes = len(nodes)
        if n_nodes >= 1000:
            init_w = 7
        elif n_nodes >= 800:
            init_w = 6
        elif n_nodes >= 600:
            init_w = 5
        elif n_nodes >= 500:
            init_w = 4
        elif n_nodes >= 400:
            init_w = 3
        elif n_nodes >= 300:
            init_w = 2
        else:
            init_w = 1
        init_w = max(min_w, min(init_w, max_w))

        stylesheet.append({
            'selector': f'edge[weight < {init_w}]',
            'style': {'display': 'none'}
        })
        stylesheet.append({
            'selector': f'edge[weight >= {init_w}]',
            'style': {'display': 'element'}
        })
        
        # Cluster
        min_cluster = int(nodes['cluster'].min())
        max_cluster = int(nodes['cluster'].max())
        cluster_info_text = f'Кластеров: {max_cluster}'

        # Show weights
        default_show_weights = ['show']

        # Metrics
        hidden_style = {'display': 'none'}
        default_color_value = None
        default_node_color_limits = {'vmin': None, 'vmax': None}

        return (
            elements,  # network-graph elements
            stylesheet,  # network-graph stylesheet
            None,  # network-graph mouseoverNodeData

            org_name,  # name-organization children

            org_info_authors,  # info-organization-authors children
            org_info_pub,  # info-organization-publications children
            org_info_cites,  # info-organization-cites children
            org_info_hindex,  # info-organization-hindex children

            fig,  # info-organization-graph figure

            empty_store,  # canvas-store data
            default_active,  # active-canvas data
            hidden_style,  # canvas-error style
            '',  # canvas-error children

            default_size,  # size-dropdown value

            min_w,  # edge-threshold min
            max_w,  # edge-threshold max
            init_w,  # edge-threshold value

            cluster_info_text,  # info-organization-cluster children
            min_cluster,  # cluster-filter min
            max_cluster,  # cluster-filter max
            '',  # cluster-filter value

            '',  # person-search value

            default_show_weights,  # show-weights value
            default_show_weights,  # show-isolates value

            default_color_value,  # color-by-dropdown value
            None,  # node-color-min value
            None,  # node-color-max value
            hidden_style,  # color-by-container style
            hidden_style,  # color-thresholds-container style
            default_node_color_limits,  # node-color-limits data

            metrics_bounds,  # size-limits data

            hidden_style,  # color-legend style
            hidden_style,  # hover-tooltip style

            hidden_style,  # preloader style
        )

    # Button 'Select organization'
    app.clientside_callback(
        """
        function(n, sel) {
            // On "Select" button click, update current-org, hide overlay and clear graph
            if (n > 0) {
                return [sel, {'display': 'none'}, {'display': 'flex'}, []];
            }
            return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        """,
        [
            Output('current-org', 'data'),
            Output('overlay', 'style'),
            Output('preloader', 'style', allow_duplicate=True),
            Output('network-graph', 'elements', allow_duplicate=True),
        ],
        Input('overlay-button', 'n_clicks'),
        State('overlay-dropdown', 'value'),
        prevent_initial_call=True
    )

    # Button 'Cancel'
    app.clientside_callback(
        """
        function(n) {
            // On "Cancel", simply hide the overlay
            if (n > 0) {
                return {'display': 'none'};
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('overlay', 'style', allow_duplicate=True),
        Input('overlay-cancel-button', 'n_clicks'),
        prevent_initial_call=True
    )

    # Button 'Change organization'
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

    # Click on logo
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

    # Button 'Yes' (dialog)
    app.clientside_callback(
        """
        function(n_clicks) {
            // On "Yes" button click, reload site
            if (n_clicks > 0) {
                window.location.reload();
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('dialog-overlay', 'children'),
        Input('dialog-yes-button', 'n_clicks'),
        prevent_initial_call=True
    )

    # Button 'Cancel' (dialog)
    app.clientside_callback(
        """
        function(n_clicks) {
            // On "Cancel", simply hide the dialog
            if (n_clicks > 0) {
                return {'display': 'none'};
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('dialog-overlay', 'style', allow_duplicate=True),
        Input('dialog-cancel-button', 'n_clicks'),
        prevent_initial_call=True
    )
    
    # Client-side Tools: sizing, filtering, coloring, search
    app.clientside_callback(
        """
        function(sizeValue, edgeTh, person, showWeight, showIsolates, colorMetric, vmin, vmax, basic, sizeLimits, limitsStore) {
            let graphStyle = JSON.parse(JSON.stringify(basic));

            // 1) Resize nodes by selected metric
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

            // 2) Hide edges below threshold
            graphStyle.push({
                selector: `edge[weight < ${edgeTh}]`,
                style: { 'display': 'none' }
            });
            graphStyle.push({
                selector: `edge[weight >= ${edgeTh}]`,
                style: { 'display': 'element' }
            });

            // 3) Show edge labels
            graphStyle.push({
                selector: 'edge',
                style: { 'text-opacity': showWeight.length ? 1 : 0 }
            });

            // 4) Show isolate nodes
            graphStyle.push({
                selector: `node[max_edge_weight < ${edgeTh}]`,
                style: { 'display': showIsolates.length ? 'element' : 'none' }
            });
            graphStyle.push({
                selector: `node[max_edge_weight >= ${edgeTh}]`,
                style: { 'display': 'element'}
            });

            // 5) Color nodes by chosen metric
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

            // 6) Highlight nodes matching search
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
        [
            Input('size-dropdown', 'value'),
            Input('edge-threshold', 'value'),
            Input('person-search', 'value'),
            Input('show-weights', 'value'),
            Input('show-isolates', 'value'),
            Input('color-by-dropdown', 'value'),
            Input('node-color-min', 'value'),
            Input('node-color-max', 'value'),
        ],
        [
            State('network-graph', 'stylesheet'),
            State('size-limits', 'data'),
            State('node-color-limits','data'),
        ],
        prevent_initial_call=True
    )

    # Cluster search
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

    # Button 'Reset search'
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

    # Button 'Analize by metrics'
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

    # Min/max limits
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

    # Build legend
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

    # Hover tooltip (Node)
    app.clientside_callback(
        """
        function(mouseoverData, sizeValue, sizeOptions) {
            // Show small tooltip with name, metric value and cluster on hover
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
            return [{'display': 'none'}, '', {'display': 'none'}];
        }
        """,
        [
            Output('hover-tooltip', 'style', allow_duplicate=True),
            Output('hover-tooltip-content', 'children', allow_duplicate=True),
            Output('show-info-button', 'style', allow_duplicate=True),
        ],
        Input('network-graph', 'mouseoverNodeData'),
        Input('size-dropdown', 'value'),
        State('size-dropdown', 'options'),
        prevent_initial_call=True
    )

    # Tooltip (Nodes)
    app.clientside_callback(
        """
        function(nodeData, sizeOptions) {
            // Show tooltip with name, all metric values, years and cluster on click
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

    # Tooltip (Edge)
    app.clientside_callback(
        """
        function(edgeData) {
            // Show small tooltip with source-target and weight on click
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

    # Hide tooltip (click on empty space)
    app.clientside_callback(
        """
        function(selNodes, selEdges) {
            if ((!selNodes || selNodes.length === 0) && (!selEdges || selEdges.length === 0)) {
                return {'display': 'none'};
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('hover-tooltip', 'style', allow_duplicate=True),
        Input('network-graph', 'selectedNodeData'),
        Input('network-graph', 'selectedEdgeData'),
        prevent_initial_call=True
    )

    # Show Detailed Info Overlay
    @app.callback(
        Output('info-overlay','style'),
        Output('info-overlay-content','children'),
        Input('show-info-button','n_clicks'),
        State('selected-item','data'),
        State('current-org', 'data'),
        prevent_initial_call=True
    )
    def show_publications(n_clicks, item_label, org_id):
        """
        Server-side callback. Renders a full overlay listing
        either an author's publications or co-authored works,
        with summary statistics and sortable table.
        """
        if not n_clicks:
            raise exceptions.PreventUpdate
        
        item_label = item_label.split('#')

        if item_label[0][:5] == 'edge-':
            # Search common pub
            data = load_cache_coauthors(org_id)
            coauthors_list = data.get(int(item_label[0][5:]), None)

            header = html.Div(item_label[1], className='info-overlay__header')

            if not coauthors_list:
                table = [html.Div('Совместные публикации не найдены')]
                description = html.Div([])
            else:
                df = pd.DataFrame(
                    coauthors_list,
                    columns=['Title', 'Year', 'Source title', 'Cited by', 'Link']
                ).sort_values('Cited by', ascending=False)

                description = html.Div([
                    html.Div([f'Число публикаций: {len(df)}']),
                    html.Div([f'Год первой публикации: {df['Year'].min()}']),
                    html.Div([f'Ср. год публикаций: {round(df['Year'].mean(), 4)}']),
                    html.Div([f'Год последней публикации: {df['Year'].max()}']),
                ], className='info-overlay__description')

                table = html.Div([
                    html.Table([
                        html.Thead(html.Tr([html.Th(c) for c in ['Название','Год','Цит.']])),
                        html.Tbody([
                            html.Tr([
                                html.Td(row['Title']),
                                html.Td(row['Year']),
                                html.Td(row['Cited by'])
                            ])
                            for _, row in df.iterrows()
                        ])
                    ], className='info-overlay__table'),
                ], className='info-overlay__text')
        else:
            # Search author
            data = load_cache_authors(org_id)
            author_dict = data.get(item_label[0].lower(), None)

            header = html.Div(item_label[0], className='info-overlay__header')

            if not author_dict:
                table = [html.Div('Публикации не найдены')]
                description = html.Div([])
            else:
                df = pd.DataFrame({
                    'Title': author_dict['Title'],
                    'Year': author_dict['Year'],
                    'Cited by': author_dict['Cited by']
                }).sort_values('Cited by', ascending=False)

                description = html.Div([
                    html.Div([f'Число публикаций: {len(df)}']),
                    html.Div([f'Год первой публикации: {df['Year'].min()}']),
                    html.Div([f'Ср. год публикаций: {round(df['Year'].mean(), 4)}']),
                    html.Div([f'Год последней публикации: {df['Year'].max()}']),
                ], className='info-overlay__description')

                table = html.Div([
                    html.Table([
                        html.Thead(html.Tr([html.Th(c) for c in ['Название','Год','Цит.']])),
                        html.Tbody([
                            html.Tr([
                                html.Td(row['Title']),
                                html.Td(row['Year']),
                                html.Td(row['Cited by'])
                            ])
                            for _, row in df.iterrows()
                        ])
                    ], className='info-overlay__table'),
                ], className='info-overlay__text')

        content = [
            header,
            description,
            table,
            html.Button('Закрыть', id='info-overlay-close', className='info-overlay__close button', n_clicks=0),
        ]
        return {'display':'flex'}, content

    # Button 'Close'
    app.clientside_callback(
        """
        function(n) {
            // Hide the detailed info overlay on close button
            if (n > 0) {
                return {'display':'none'};
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('info-overlay', 'style', allow_duplicate=True),
        Input('info-overlay-close', 'n_clicks'),
        prevent_initial_call=True
    )

    # Create new canvas
    app.clientside_callback(
        """
        function(n_clicks, selectedNodes, store) {
            if (n_clicks < 1) {
                return [window.dash_clientside.no_update, {'display': 'none'}, ''];
            }

            // Unpack store
            const full = (store && store.full) || [];
            const canvases = (store && store.canvases) || [];

            // Error: already 50 canvas 
            if (canvases.length >= 50) {
                return [
                    window.dash_clientside.no_update,
                    {'display': 'flex'},
                    'Вы достигли максимального количества холстов (50).'
                ];
            }

            // Error: no one selected nodes
            if (!selectedNodes || selectedNodes.length === 0) {
                return [
                    window.dash_clientside.no_update,
                    {'display': 'flex'},
                    'Чтобы создать холст, выберите в графе хотя бы одну вершину.'
                ];
            }

            // Error: >300 nodes
            if (selectedNodes.length > 300) {
                return [
                    window.dash_clientside.no_update,
                    {'display': 'flex'},
                    `Вы выбрали ${selectedNodes.length} вершин.\n` +
                    'Максимально допустимо — 300. Пожалуйста, сократите выбор.'
                ];
            }

            // Get ID selected nodes
            const selected = selectedNodes.slice(0, 300);
            const nodesIDs = selected.map(n => n.id);

            // Filter nodes & edges
            const nodes = full.filter(e => e.data && nodesIDs.includes(e.data.id)).map(e => ({ ...e }));
            const edges = full.filter(e => e.data && e.data.source
                            && nodesIDs.includes(e.data.source)
                            && nodesIDs.includes(e.data.target))
                            .map(e => ({ ...e }));

            // Save positions only for selected nodes
            const positions = {};
            nodes.forEach(n => {
                positions[n.id] = n.position;
            });

            // Create new object canvas
            const indx = store.nextCanvasIndex + 1;
            const newCanvas = {
                id: `canvas-${indx}`,
                name: `${indx}`,
                elements: nodes.concat(edges),
                positions: positions
            };

            return [
                {
                    full: full,
                    canvases: canvases.concat(newCanvas).slice(-50),
                    nextCanvasIndex: indx,
                }, 
                {
                    'display': 'none'
                },
                ''
            ];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('canvas-error', 'style', allow_duplicate=True),
            Output('canvas-error', 'children', allow_duplicate=True)
        ],
        Input('create-new-canvas', 'n_clicks'),
        [
            State('network-graph', 'selectedNodeData'),
            State('canvas-store', 'data'),
        ],
        prevent_initial_call=True
    )

    # Add new tab and canvas-list
    app.clientside_callback(
        """
        function(store) {
            // create Tab object
            function makeTab(label, value) {
                return {
                    type: 'Tab',
                    namespace: 'dash_core_components',
                    props: { label: label, value: value }
                };
            }

            const slides = (store && store.canvases) || [];

            const tabs = [ makeTab('Полный граф', 'full') ];
            slides.forEach(c => {
                tabs.push(makeTab(c.name, c.id));
            });

            const options = [];
            const optionsOverlay = [];
            const allCanvases = [{ id: 'full', name: 'Полный граф' }].concat(slides);

            allCanvases.forEach(c => {
                // label
                options.push({
                    label: window.React.createElement(
                        'span', 
                        { className: 'canvas-list__label' }, 
                        c.name
                    ),
                    value: c.id + '-label',
                });

                // rename
                optionsOverlay.push({
                    label: window.React.createElement('img', {
                        src: '/assets/icons/rename.svg',
                        alt: 'rename',
                    }),
                    value: c.id + '-rename',
                });

                // delete
                optionsOverlay.push({
                    label: window.React.createElement('img', {
                        src: '/assets/icons/delete.svg',
                        alt: 'delete',
                    }),
                    value: c.id + '-delete',
                });

                // duplicate
                optionsOverlay.push({
                    label: window.React.createElement('img', {
                        src: '/assets/icons/duplicate.svg',
                        alt: 'duplicate',
                    }),
                    value: c.id + '-duplicate',
                });

            });

            return [tabs, options, optionsOverlay];
        }
        """,
        [
            Output('graph-tabs', 'children'),
            Output('canvas-list', 'options'),
            Output('canvas-list-action', 'options'),
        ],
        Input('canvas-store', 'data')
    )

    # Save selected tab in active-canvas
    app.clientside_callback(
        """
        function(newTab, store, currentElements, prevTab) {
            if (!store) {
                return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
            }

            if (prevTab) {
                if (prevTab === 'full') {
                    const newFullPos = {};
                    currentElements.forEach(el => {
                        if (el.data && el.data.id && el.position) {
                            newFullPos[el.data.id] = el.position;
                        }
                    });
                    store.fullPositions = newFullPos;
                } else {
                    const indx = store.canvases.findIndex(c => c.id === prevTab);
                    if (indx > -1) {
                        const pos = store.canvases[indx].positions || {};
                        currentElements.forEach(el => {
                            if (el.data && el.data.id && el.position) {
                                pos[el.data.id] = el.position;
                            }
                        });
                        store.canvases[indx].positions = pos;
                    }
                }
            }

            const listValue = `${newTab}-label`;

            return [store, newTab, listValue];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('active-canvas', 'data', allow_duplicate=True),
            Output('canvas-list', 'value'),
        ],
        Input('graph-tabs', 'value'),
        [
            State('canvas-store', 'data'),
            State('network-graph', 'elements'),
            State('active-canvas', 'data'),
        ],
        prevent_initial_call=True
    )

    # Insert into Cytoscape elements & positions
    app.clientside_callback(
        """
        function(activeID, store) {
            if (!store) {
                return window.dash_clientside.no_update;
            }

            // Return full graph
            if (activeID === 'full') {
                const fullCanvas = store.full || [];
                const fullPos = store.fullPositions || {};
                return fullCanvas.map(e => {
                    if (e.data && e.data.id && fullPos[e.data.id]) {
                        return {...e, position: fullPos[e.data.id]};
                    }
                    return e;
                });
            }

            // Search canvas
            const canvas = (store.canvases || []).find(s => s.id === activeID);
            if (!canvas) {
                return window.dash_clientside.no_update;
            }

            // For Cytoscape: return elements with positions
            return canvas.elements.map(e => {
                if (e.data && e.data.id && canvas.positions[e.data.id]) {
                    return { ...e, position: canvas.positions[e.data.id] };
                }
                return e;
            });
        }
        """,
        Output('network-graph', 'elements', allow_duplicate=True),
        Input('active-canvas', 'data'),
        State('canvas-store', 'data'),
        prevent_initial_call=True
    )

    # Switch to selected canvas by click on canvas-list item
    app.clientside_callback(
        """
        function(selectedValue) {
            if (!selectedValue) {
                return window.dash_clientside.no_update;
            }

            const indx = selectedValue.lastIndexOf('-');
            if (indx < 0) {
                return window.dash_clientside.no_update;
            }

            const canvasId = selectedValue.substring(0, indx);
            const action = selectedValue.substring(indx + 1);
            if (action !== 'label') {
                return window.dash_clientside.no_update;
            }
            return canvasId;
        }
        """,
        Output('graph-tabs', 'value', allow_duplicate=True),
        Input('canvas-list', 'value'),
        prevent_initial_call=True
    )

    # Perform selected action by click on canvas-list item
    app.clientside_callback(
        """
        function(selectedAction, store, activeId) {
            if (!selectedAction || !store || !store.canvases) {
                return [ window.dash_clientside.no_update, null, {'display': 'none'}, window.dash_clientside.no_update, window.dash_clientside.no_update ];
            }

            const indx = selectedAction.lastIndexOf('-');
            const canvasId = selectedAction.substring(0, indx);
            const action   = selectedAction.substring(indx + 1);

            const newStore = {
                full: store.full,
                fullPositions: store.fullPositions || {},
                canvases: store.canvases.map(c => ({ ...c })),
                nextCanvasIndex: store.nextCanvasIndex + 1,
            };

            let inputStyle = { display: 'none' };
            let inputValue = null;
            let newActive = window.dash_clientside.no_update;

            if (action === 'rename') {
                newStore.editingName = canvasId;

                const idx = store.canvases.findIndex(c=>c.id===canvasId) + 1;
                const topPx = (idx * 36) + 'px';

                inputValue = store.canvases.find(c=>c.id===canvasId)?.name || '';
                inputStyle = {
                    display: 'flex',
                    top: topPx,
                };

                window.setTimeout(() => {
                    const el = document.getElementById('rename-overlay-input');
                    if (el) { el.focus(); el.select(); }
                }, 0);
            } else if (action === 'delete') {
                newStore.canvases = newStore.canvases.filter(c => c.id !== canvasId);
                if (activeId === canvasId) {
                    newActive = 'full';
                }
            } else if (action === 'duplicate') {
                const orig = store.canvases.find(c => c.id === canvasId);
                if (orig && store.canvases.length < 50) {
                    const newIndx = newStore.nextCanvasIndex;
                    newStore.canvases.push({
                        id: `canvas-${newIndx}`,
                        name: `${orig.name} (копия)`,
                        elements: orig.elements,
                        positions: { ...orig.positions }
                    });
                    newStore.nextCanvasIndex = newIndx + 1;
                } else {
                    return [ window.dash_clientside.no_update, null, inputStyle, window.dash_clientside.no_update, newActive ];
                }
            } else {
                return [ window.dash_clientside.no_update, null, inputStyle, window.dash_clientside.no_update, newActive ];
            }

            return [ newStore, null, inputStyle, inputValue, newActive ];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('canvas-list-action','value'),
            Output('rename-overlay', 'style'),
            Output('rename-overlay-input', 'value'),
            Output('graph-tabs', 'value', allow_duplicate=True),
        ],
        Input('canvas-list-action', 'value'),
        [
            State('canvas-store', 'data'),
            State('active-canvas', 'data'),
        ],
        prevent_initial_call=True
    )

    # Save new name canvas
    app.clientside_callback(
        """
        function(nSubmit, nBlur, newName, store) {
            if (!store || !store.editingName) {
                return [ window.dash_clientside.no_update, window.dash_clientside.no_update ];
            }
            if (!(nSubmit > 0 || nBlur > 0)) {
                return [ window.dash_clientside.no_update, window.dash_clientside.no_update ];
            }

            if (!newName) {
                return [ window.dash_clientside.no_update, {'display': 'none'} ];
            }

            const id = store.editingName;
            const newStore = { ...store };
            newStore.canvases = newStore.canvases.map(c => {
                if (c.id === id) {
                    return { ...c, name: newName };
                }
                return c;
            });

            delete newStore.editingName;

            return [ newStore, {'display': 'none'} ];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('rename-overlay', 'style', allow_duplicate=True),
        ],
        [
            Input('rename-overlay-input', 'n_submit'),
            Input('rename-overlay-input', 'n_blur'),
        ],
        [
            State('rename-overlay-input', 'value'),
            State('canvas-store', 'data'),
        ],
        prevent_initial_call=True
    )