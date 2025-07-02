from data_prepare import prepare_network_elements, load_cache_authors, load_cache_coauthors
from dash import Dash, dcc, html, Input, Output, State, exceptions
import dash_cytoscape as cyto
import pandas as pd
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

DEFAULT_ORG = '14346'

# DASH
app = Dash(
    __name__,
    title='AcademicNet',
    update_title=None,
    suppress_callback_exceptions=True
)


def base_layout(org_map):
    # DATA LOADING
    # Load default organization
    data = prepare_network_elements(DEFAULT_ORG)

    elements = data['elements']
    basic_stylesheet = data['stylesheet']
    size_options = data['size_options']
    metrics_bounds = data['metrics_bounds']
    color_options = data['color_options']
    nodes = data['nodes']
    edges = data['edges']
    num_publication = data['num_publication']

    return html.Div([
        # Stores
        dcc.Store(id='current-org', data=DEFAULT_ORG),
        dcc.Store(id='overlay-visible', data=True),

        # Main container
        html.Div([
            # Content
            html.Div([
                # Sidebar
                html.Div([
                    # Logo
                    html.Div([
                        html.Img(src='assets/logo.svg', alt='logo'),
                        html.Div('AcademicNet')
                    ], className='content__logo'),

                    # Organization info
                    html.Div(
                        ['Университет Иннополис'],
                        id='name-organization',
                        className='content__name-org header'
                    ),
                    html.Div(
                        [f'Авторов: {len(nodes)}'],
                        id='info-organization-authors',
                        className='content__info-org'
                    ),
                    html.Div(
                        [f'Публикаций: {num_publication}'],
                        id='info-organization-publications',
                        className='content__info-org content__info-org_pub'
                    ),
                    html.Div(
                        f'Кластеров: {nodes['cluster'].max()}',
                        id='info-organization-cluster',
                        className='content__info-org content__info-org_cluster'
                    ),

                    # Select organization
                    html.Button(
                        'Сменить организацию',
                        id='open-overlay-button',
                        className='content__change-org button',
                        n_clicks=0
                    ),

                    # Resize nodes
                    html.Div([
                        html.Label('Размер вершин:'),
                        dcc.Dropdown(
                            id='size-dropdown',
                            options=size_options,
                            value=size_options[0]['value']
                        )
                    ], className='content__size dropdown'),

                    # Weight threshold
                    html.Div([
                        html.Label('Минимальный вес ребра:'),
                        dcc.Input(
                            id='edge-threshold',
                            type='number',
                            min=int(edges['weight'].min()),
                            max=int(edges['weight'].max()),
                            step=1,
                            value=int(edges['weight'].min()),
                        )
                    ], className='content__edge-threshold dropdown'),

                    # Cluster search
                    html.Div([
                        html.Label('Поиск кластера:'),
                        html.Div([
                            dcc.Input(
                                id='cluster-filter',
                                type='number',
                                min=int(nodes['cluster'].min()),
                                max=int(nodes['cluster'].max()),
                                placeholder='Введите номер',
                                debounce=True
                            )
                        ], className='search__input'),

                        html.Div([
                            html.Button(
                                '',
                                id='cluster-button',
                                n_clicks=0
                            )
                        ], className='search__button')
                    ], className='content__cluster search'),

                    # Author search
                    html.Div([
                        html.Label('Поиск автора:'),
                        html.Div([
                            dcc.Input(
                                id='person-search',
                                type='text',
                                placeholder='Иванов И.И.',
                                debounce=True
                            )
                        ], className='search__input'),

                        html.Div([
                            html.Button(
                                '',
                                id='search-button',
                                n_clicks=0
                            )
                        ], className='search__button')
                    ], className='search'),

                    # Reset search
                    html.Div([
                        html.Button(
                            'Сбросить поиск',
                            id='reset-button',
                            className='button',
                            n_clicks=0
                        )
                    ], className='content__reset'),

                    # Show weights
                    html.Div([
                        dcc.Checklist(
                            id='show-weights',
                            options=[{
                                'label': 'Показывать веса рёбер',
                                'value': 'show'
                            }],
                            value=['show'],
                            labelStyle={'display': 'flex'}
                        ),
                    ], className='content__checkbox'),

                    # Metrics
                    html.Div([
                        html.Button(
                            'Анализ по метрике',
                            id='color-button',
                            className='button',
                            n_clicks=0
                        ),
                        html.Div([
                            dcc.Dropdown(
                                id='color-by-dropdown',
                                options=color_options,
                                placeholder='Выберите показатель',
                            ),
                        ], id='color-by-container', className='dropdown', style={'display': 'none'}),

                        html.Div([
                            dcc.Store(
                                id='node-color-limits',
                                data={'vmin': None, 'vmax': None}
                            ),
                            html.Label('Порог минимума:'),
                            dcc.Input(id='node-color-min', type='number'),
                            html.Label('Порог максимума:'),
                            dcc.Input(id='node-color-max', type='number'),
                        ], id='color-thresholds-container', style={'display': 'none'}),
                    ], className='content__metric')
                ], className='content__sidebar'),

                # Graph
                html.Div([
                    dcc.Store(
                        id='size-limits',
                        data=metrics_bounds
                    ),
                    cyto.Cytoscape(
                        id='network-graph',
                        elements=elements,
                        layout={'name': 'preset'},
                        stylesheet=basic_stylesheet,
                        userPanningEnabled=True,
                        boxSelectionEnabled=True,
                        autounselectify=False,
                        wheelSensitivity=0.15,
                        style = {'width': '100%', 'height': '100%', 'backgroundColor': '#EEECE3'}
                    ),

                    # Legend
                    html.Div([
                        html.Div(id='legend-bar'),
                        html.Div(id='legend-labels')
                    ], id='color-legend'),
                    
                    # Tooltip
                    html.Div([
                        html.Div(id='hover-tooltip-content'),
                        html.Button(
                            'Смотреть публикации',
                            id='show-info-button',
                            n_clicks=0,
                        )
                    ], id='hover-tooltip'),
                ], className='content__graph')
            ], className='content'),

            # Overlay info
            dcc.Store(id='selected-item', data=None),
            html.Div([
                html.Div(id='info-overlay-content')
            ], id='info-overlay'),

            # Overlay
            html.Div([
                html.Div([
                    html.Div(['Выберите организацию'], className='overlay__header'),

                    dcc.Dropdown(
                        id='overlay-dropdown',
                        options=org_map,
                        value=DEFAULT_ORG,
                        clearable=False
                    ),

                    html.Div([
                        html.Button(
                            'Выбрать',
                            id='overlay-button',
                            className='button',
                            n_clicks=0
                        ),
                        html.Button(
                            'Отмена',
                            id='overlay-cancel-button',
                            className='button',
                            n_clicks=0
                        ),
                    ], className='overlay__buttons')
                ], className='overlay__container'),
            ], id='overlay'),
        ], className='container')
    ])


# Organization map
df = pd.read_csv('org_data/org.txt', sep='\t', dtype=str)
df = df.sort_values('Name')
org_map = df[['ID','Name']].rename(columns={'ID':'value','Name':'label'}).to_dict('records')
org_name_map = {item['value']: item['label'] for item in org_map}


# Layout
app.layout = base_layout(org_map)


# Update graph
@app.callback(
    Output('network-graph', 'elements'),
    Output('network-graph', 'stylesheet'),

    Output('name-organization', 'children'),

    Output('info-organization-authors', 'children'),
    Output('info-organization-publications', 'children'),

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

    Output('color-by-dropdown', 'value'),
    Output('node-color-min', 'value'),
    Output('node-color-max', 'value'),
    Output('color-by-container', 'style'),
    Output('color-thresholds-container', 'style'),
    Output('node-color-limits', 'data'),
    
    Output('size-limits', 'data'),

    Output('color-legend', 'style'),
    Output('hover-tooltip', 'style'),
    Output('hover-tooltip-content', 'children'),

    Input('current-org', 'data')
)
def update_graph_for_org(org_id):
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

    # Name organization
    org_name = org_name_map.get(org_id, org_id)

    # Info organization
    org_info_authors = f'Авторов: {len(nodes)}'
    org_info_pub = f'Публикаций: {num_publication}'

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

        org_name, # name-organization children

        org_info_authors,  # info-organization-authors children
        org_info_pub,  # info-organization-publications children

        default_size,  # size-dropdown value

        min_w,  # edge-threshold min
        max_w,  # edge-threshold max
        init_w,  # edge-threshold value

        cluster_info_text,  # info-organization-cluster children
        min_cluster,  # cluster-filter min
        max_cluster,  # cluster-filter max
        '',  # cluster-filter value

        '', # person-search value

        default_show_weights,  # show-weights value

        default_color_value,  # color-by-dropdown value
        None,  # node-color-min value
        None,  # node-color-max value
        hidden_style,  # color-by-container style
        hidden_style,  # color-thresholds-container style
        default_node_color_limits,  # node-color-limits data

        metrics_bounds,  # size-limits data

        hidden_style,  # color-legend style
        hidden_style,  # hover-tooltip style
        '',  # hover-tooltip-content children
    )

# Overlay
app.clientside_callback(
    """
    function(vis) {
        if (vis) {
            return {'display': 'flex'};
        }
        return {'display': 'none'};
    }
    """,
    Output('overlay', 'style'),
    Input('overlay-visible', 'data'),
    prevent_initial_call=True
)

# Button select organization
app.clientside_callback(
    """
    function(n, sel) {
        if (n > 0) {
            return [sel, false];
        }
        return [window.dash_clientside.no_update, window.dash_clientside.no_update];
    }
    """,
    [
        Output('current-org', 'data'),
        Output('overlay-visible', 'data'),
    ],
    Input('overlay-button', 'n_clicks'),
    State('overlay-dropdown', 'value'),
    prevent_initial_call=True
)

# Button cancel
app.clientside_callback(
    """
    function(n) {
        if (n > 0) {
            return false;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('overlay-visible', 'data', allow_duplicate=True),
    Input('overlay-cancel-button', 'n_clicks'),
    prevent_initial_call=True
)

# Tools
app.clientside_callback(
    """
    function(sizeValue, edgeTh, person, showWeight, colorMetric, vmin, vmax, basic, sizeLimits, limitsStore) {
        let graphStyle = JSON.parse(JSON.stringify(basic));

        // 1) Update nodes:
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

        // 2) Filter edges:
        graphStyle.push({
            selector: `edge[weight < ${edgeTh}]`,
            style: { display: 'none' }
        });
        graphStyle.push({
            selector: `edge[weight >= ${edgeTh}]`,
            style: { display: 'element' }
        });

        // 3) Show weights:
        graphStyle.push({
            selector: 'edge',
            style: { 'text-opacity': showWeight.length ? 1 : 0 }
        });

        // 4) Metrics:
        if(colorMetric) {
            let minVal = sizeLimits[colorMetric].min;
            let maxVal = sizeLimits[colorMetric].max;

            minVal = Math.max(minVal, vmin);
            maxVal = Math.min(maxVal, vmax);

            if (minVal <= maxVal) {
                const midVal = (minVal + maxVal) / 2;
                graphStyle.push({
                    selector: `node[${colorMetric} <= ${midVal}]`,
                    style: {
                        'background-color': `mapData(${colorMetric}, ${minVal}, ${midVal}, #440154, #26828E)`
                    }
                });
                graphStyle.push({
                    selector: `node[${colorMetric} > ${midVal}]`,
                    style: {
                        'background-color': `mapData(${colorMetric}, ${midVal}, ${maxVal}, #26828E, #FDE725)`
                    }
                });
                graphStyle.push({
                    selector: `node[${colorMetric} < ${vmin}]`,
                    style: { 'background-color': '#d7ecff' }
                });
                graphStyle.push({
                    selector: `node[${colorMetric} > ${vmax}]`,
                    style: { 'background-color': '#d7ecff' }
                });
            }
        };

        // 5) Search:
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

# Select organization
app.clientside_callback(
    """
    function(n, current) {
        if (n > 0) {
            return [true, current];
        }
        return [window.dash_clientside.no_update, window.dash_clientside.no_update];
    }
    """,
    [
        Output('overlay-visible', 'data', allow_duplicate=True),
        Output('overlay-dropdown', 'value'),
    ],
    Input('open-overlay-button', 'n_clicks'),
    State('current-org', 'data'),
    prevent_initial_call=True
)

# Cluster search
app.clientside_callback(
    """
    function(clusterValue, elements, basic) {
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

# Reset search
app.clientside_callback(
    """
    function(clickReset, basic) {
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

# Analize by metrics
app.clientside_callback(
    """
    function(clickColor, basic) {
        if (!clickColor) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        let graphStyle = JSON.parse(JSON.stringify(basic));
        if (clickColor % 2 == 1) {
            return [graphStyle, {'display': 'block'}, {'display': 'flex'}, ''];
        }
        graphStyle.push({
            selector: `node[label]`,
            style: { 'background-color': 'data(color)' }
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

# Hover tooltip
app.clientside_callback(
    """
    function(mouseoverData, sizeValue, sizeOptions) {
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

# Nodes tooltip
app.clientside_callback(
    """
    function(nodeData, sizeOptions) {
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

# Edges tooltip
app.clientside_callback(
    """
    function(edgeData) {
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

# Info tooltip button
@app.callback(
    Output('info-overlay','style'),
    Output('info-overlay-content','children'),
    Input('show-info-button','n_clicks'),
    State('selected-item','data'),
    State('current-org', 'data'),
    prevent_initial_call=True
)
def show_pubs(n_clicks, item_label, org_id):
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

# Button close
app.clientside_callback(
    """
    function(n) {
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


# START
if __name__ == '__main__':
    app.run(debug=False)
