"""""
Module: upload_org
Defines the server-side callback for loading and updating all main graph elements,
sidebar metrics and controls when the selected organization changes.
"""
from dash import Input, Output
import plotly.express as px
from src.data_prepare import prepare_network_elements

def upload_org(app, org_name_map):
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
    def upload_org_by_id(org_id):
        """
        Reload all graph elements, styles, metrics, and sidebar info
        when the selected organization changes.

        Args:
            org_id: selected organization identifier

        Returns:
            Values matching all Outputs defined above.
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
        pub_info = data['pub_info']

        # Name organization
        org_name = org_name_map.get(org_id, org_id)

        # Build sidebar text
        org_info_authors = f'Авторов: {len(nodes)}'
        org_info_pub = f'Публикаций: {num_publication}'
        org_info_cites = f'Цитирований: {total_cites}'
        org_info_hindex = f'Индекс Хирша: {h_index}'

        # Create graph publications over time
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

        # Initialize canvas store with full graph only
        empty_store = {'full': elements, 'canvases': [], 'nextCanvasIndex': 0, 'fullPubInfo': pub_info}
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
