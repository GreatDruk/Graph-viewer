"""
Module: overlay_callbacks
Defines the callbacks for overlay dialogs (organization selection,
confirmation dialogs, and detailed info overlays).
"""
from dash import html, Input, Output, State, exceptions
import pandas as pd
from src.data_prepare import load_cache_authors, load_cache_coauthors

def overlay_callbacks(app):
    """
    Register all callbacks related to overlays:
      - Organization change overlay
      - Confirmation dialog (reload site)
      - Detailed info overlay for nodes/edges
    """
    # Confirm organization selection, hide overlay, show preloader and clear graph
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

    # Cancel organization selection overlay
    app.clientside_callback(
        """
        function(n) {
            // On "Cancel" - hide the overlay
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

    # Confirm reload site dialog (Yes)
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

    # Cancel reload site dialog
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

    # Server-side callback - show detailed publications overlay
    @app.callback(
        Output('info-overlay','style'),
        Output('info-overlay-content','children'),
        Input('show-info-button','n_clicks'),
        State('selected-item','data'),
        State('current-org', 'data'),
        prevent_initial_call=True
    )
    def show_info_overlay(n_clicks, item_label, org_id):
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
    
    # Close detailed info overlay
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
