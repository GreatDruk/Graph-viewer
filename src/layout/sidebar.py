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
    # Organization Info Tab: title, stats, and pub graph
    info_tab = dcc.Tab(
        label='',
        value='Organization info',
        className='content__tab content__tab_1',
        children=[
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
                [f'Кластеров: {nodes['cluster'].max()}'],
                id='info-organization-cluster',
                className='content__info-org content__info-org_cluster'
            ),
            html.Div(
                [f'Цитирований: {total_cites}'],
                id='info-organization-cites',
                className='content__info-org content__info-org_cites'
            ),
            html.Div(
                [f'Индекс Хирша: {h_index}'],
                id='info-organization-hindex',
                className='content__info-org content__info-hindex'
            ),

            # Graph publications over time
            html.Div(
                [f'Публикационная активность:'],
                className='content__info-org-graph_header'
            ),
            dcc.Graph(
                id='info-organization-graph',
                figure=(
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
                ),
                config={
                    'displayModeBar': False,
                    'staticPlot': True
                },
                className='content__graph-org'
            ),

            # Select organization
            html.Button(
                'Сменить организацию',
                id='open-overlay-button',
                className='content__change-org button',
                n_clicks=0
            ),
        ],
    )

    # Assemble sidebar with all tabs
    return html.Div([
        # Logo
        html.Div([
            html.Img(src='assets/logo.svg', alt='logo', id='app-logo', n_clicks=0),
            html.Div('AcademicNet')
        ], className='content__logo'),

        # Tabs container
        dcc.Tabs(
            id='sidebar-tabs',
            className='content__tabs',
            value='Organization info',
            children=[
            # Organization info
            info_tab,

            # Visualization
            vis_tab,

            # Search
            search_tab,

            # Canvas management
            canvas_tab,
        ]),
    ], className='content__sidebar')
