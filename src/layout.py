"""
Module: layout
Defines the Dash app layout for graph viewer.
"""

from dash import dcc, html
import dash_cytoscape as cyto

from src.data_prepare import prepare_network_elements

def base_layout(org_map, default_org: str) -> html.Div:
    """
    Build the base application layout.

    Args:
        org_map: List of organization options for the dropdown ({'label', 'value'}).
        default_org: ID of the default organization to load on startup.

    Returns:
        A Dash HTML Div representing the full application UI.
    """
    # Load data for the default organization
    data = prepare_network_elements(default_org)

    elements = data['elements']
    basic_stylesheet = data['stylesheet']
    size_options = data['size_options']
    metrics_bounds = data['metrics_bounds']
    color_options = data['color_options']
    nodes = data['nodes']
    edges = data['edges']
    num_publication = data['num_publication']

    return html.Div([
        # Hidden stores for state management
        dcc.Store(id='current-org', data=default_org),
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
                        dcc.Checklist(
                            id='show-isolates',
                            options=[{
                                'label': 'Показывать вершины без рёбер', 
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
                        value=default_org,
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