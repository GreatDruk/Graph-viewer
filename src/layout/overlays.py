"""
Module: overlays
Defines all overlay dialogs and stores for application-level state.
"""
from dash import dcc, html

def overlays(
        elements,
        org_map,
        default_org
    ):
    """
    Build hidden stores and overlay components:
      - current-org store to track selected organization ID
      - canvas-store & active-canvas for custom canvases
      - confirmation dialog when reloading application
      - organization selector overlay
      - detailed info overlay for node/edge publications

    Args:
        elements (list[dict]): Cytoscape elements (nodes + edges) to render
        org_map (list[dict]): Dropdown options for organization selector
        default_org (str): Default selected organization ID

    Returns:
        html.Div: Container wrapping all overlay elements
    """
    return html.Div([
        # Hidden dcc.Store components
        dcc.Store(id='current-org', data=default_org),
        dcc.Store(id='canvas-store', data={
            'full': elements,
            'canvases': [],
            'nextCanvasIndex': 0,
        }),
        dcc.Store(id='active-canvas', data='full'),
        dcc.Store(id='selected-item', data=None),
        
        # Full-screen confirmation dialog for reload
        html.Div([
            html.Div([
                html.Div(['Перезагрузить сайт?'], className='overlay__header'),
                html.Div(['Все изменения будут удалены.']),
                html.Div([
                    html.Button(
                        'Да',
                        id='dialog-yes-button',
                        className='button',
                        n_clicks=0
                    ),
                    html.Button(
                        'Отмена',
                        id='dialog-cancel-button',
                        className='button',
                        n_clicks=0
                    ),
                ], className='overlay__buttons')
            ], id='dialog-overlay-content', className='overlay__container')
        ], id='dialog-overlay', className='overlay'),

        # Detailed info overlay for publications
        html.Div([
            html.Div(
                id='info-overlay-content',
                className='overlay__container'
            )
        ], id='info-overlay', className='overlay'),

        # Organization selector overlay
        html.Div([
            html.Div([
                html.Div(
                    ['Выберите организацию'],
                    className='overlay__header'
                ),
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
        ], id='overlay', className='overlay'),

        # Preloader
        html.Div(
            [
                'Loading...',
            ],
            id='preloader',
            className='container__preloader',
        ),
    ])
