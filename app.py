from data_prepare import prepare_network_elements
from dash import Dash, dcc, html, Input, Output, State
import dash_cytoscape as cyto

# DATA LOADING
org_id = "14346"
data = prepare_network_elements(org_id)

elements = data['elements']
basic_stylesheet = data['stylesheet']
size_options = data['size_options']
metrics_bounds = data['metrics_bounds']
color_options = data['color_options']
nodes = data['nodes']
edges = data['edges']


# DASH
app = Dash(__name__, suppress_callback_exceptions=True)
# Layout
app.layout = html.Div([
    html.Div([
        html.Div([
            html.Label('Размер вершин:'),
            dcc.Dropdown(
                id = 'size-dropdown',
                options = size_options,
                value = size_options[0]['value']
            )
        ], id='content__size'),
        html.Div([
            html.Label('Минимальный вес ребра:'),
            dcc.Input(
                id = 'edge-threshold',
                type = 'number',
                min = int(edges['weight'].min()),
                max = int(edges['weight'].max()),
                step = 1,
                value = int(edges['weight'].min()),
            )
        ], id='content__filter_edge'),
        html.Div([
            html.Label('Поиск автора:'),
            html.Div([
                dcc.Input(
                    id = 'person-search',
                    type = 'text',
                    placeholder = 'иванов и.и.',
                    debounce = True
                )
            ], id='content__input-search'),
            html.Div([
                html.Button('', id = 'search-button', n_clicks = 0)
            ], id='content__search-button')
        ], id='content__search'),
        html.Div([
            html.Button("Сбросить поиск", id = "reset-button", n_clicks = 0)
        ], id='content__reset'),
        html.Div([
            dcc.Checklist(
                id = 'show-weights',
                options = [{'label': 'Показывать веса рёбер', 'value': 'show'}],
                value = ['show'],
                labelStyle = {'display': 'flex'}
            ),
        ], id='content__checkbox'),
        html.Div([
            html.Button("Анализ по метрике", id="color-button", n_clicks=0),
            html.Div([
                dcc.Dropdown(
                    id = 'color-by-dropdown',
                    options = color_options,
                    placeholder = "Выберите показатель",
                ),
            ], id='color-by-container', style={'display': 'none'}),
            html.Div([
                dcc.Store(id='node-color-limits', data={'vmin': None, 'vmax': None}),
                html.Label('Порог минимума:'),
                dcc.Input(id='node-color-min', type='number'),
                html.Label('Порог максимума:'),
                dcc.Input(id='node-color-max', type='number'),
            ], id='color-thresholds-container', style={'display': 'none'}),
        ], id='content__scale')
    ], id='content__sidebar'),
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
            style = {'width': '100%', 'height': '100%'}
        )
    ], id='content__graph')
], id='content')


app.clientside_callback(
    """
    function(sizeVal, edgeTh, person, showWeight, colorMetric, vmin, vmax, basic, sizeLimits) {
        let graphStyle = JSON.parse(JSON.stringify(basic));

        // 1) ресайз вершин:
        const bounds = sizeLimits[sizeVal];
        const VM = bounds.min;
        const VX = bounds.max;
        if(sizeVal && VM != null && VX != null) {
            graphStyle.push({
                selector: `node[${sizeVal}]`,
                style: {
                    'width': `mapData(${sizeVal}, ${VM}, ${VX}, 10, 40)`,
                    'height': `mapData(${sizeVal}, ${VM}, ${VX}, 10, 40)`,
                    'font-size': `mapData(${sizeVal}, ${VM}, ${VX}, 7, 17)`
                }
            });
        };

        // 2) фильтр рёбер:
        graphStyle.push({
            selector: `edge[weight < ${edgeTh}]`,
            style: { display: 'none' }
        });
        graphStyle.push({
            selector: `edge[weight >= ${edgeTh}]`,
            style: { display: 'element' }
        });

        // 3) подсветка поиска:
        if(person) {
            const low = person.toLowerCase();
            graphStyle.push({
                selector: `node[label *= "${low}"]`,
                style: { 'background-color': 'red' }
            });
            graphStyle.push({
                selector: `node[label !*= "${low}"]`,
                style: { 'background-color': 'data(color)' }
            });
        }

        // 4) веса рёбер:
        graphStyle.push({
            selector: 'edge',
            style: { 'text-opacity': showWeight.length ? 1 : 0 }
        });

        // 5) окраска по метрике:
        if(colorMetric) {
            graphStyle.push({
                selector: 'node',
                style: {
                    'background-color': `mapData(${colorMetric}, ${vmin}, ${vmax}, blue, red)`
                }
            });
        }

        // 6) пороги цвета:
        if(vmin != null && vmax != null) {
            graphStyle.push({
                selector: 'node',
                style: { 'cmin': vmin, 'cmax': vmax }
            });
        }

        return graphStyle;
    }
    """,
    Output('network-graph', 'stylesheet'),
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
        State('size-limits', 'data')
    ]
)


# START
if __name__ == '__main__':
    app.run(debug=True)
