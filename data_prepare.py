from thesaurus_builder import build_author_thesaurus

import pandas as pd
import numpy as np
import os.path
from datetime import datetime

def load_thesaurus(org_id: str) -> dict:
    thesaurus_path = f"org_data/processed/{org_id}/thesaurus_authors.txt"
    if not os.path.exists(thesaurus_path):
        build_author_thesaurus(org_id=org_id)

    replace_dict = (
        pd.read_csv(thesaurus_path, sep='\t')
        .set_index('Label')
        .to_dict()['Replace by']
    )

    return replace_dict


def load_publication(org_id: str) -> pd.DataFrame:
    return pd.read_csv(f'org_data/processed/{org_id}/publications.csv')


def load_nodes(org_id: str) -> pd.DataFrame:
    nodes = pd.read_csv(f'org_data/processed/{org_id}/map.txt', sep='\t')

    rename_dict = {
        'weight<Links>': 'Links',
        'weight<Total link strength>': 'Strength',
        'weight<Documents>': 'Documents',
        'weight<Citations>': 'Citations',
        'weight<Norm. citations>': 'Norm_citations',
        'score<Avg. pub. year>': 'Avg_pub_year',
        'score<Avg. citations>': 'Avg_citations',
        'score<Avg. norm. citations>': 'Avg_norm_citations'
    }
    nodes = nodes.rename(columns=rename_dict)
    return nodes


def load_edges(org_id: str) -> pd.DataFrame:
    return pd.read_csv(f'org_data/processed/{org_id}/network.txt', sep='\t',
                         names=['first_author','second_author','weight'], header=None)


def standardize_author_names(names: str, replace_dict: dict) -> list:
    arr_authors = [name.replace('et al.', '').strip() for name in names.split(';')]
    res = []
    for name in arr_authors:
        res.append(replace_dict.get(name, name).lower())
    return res


def build_authors_with_inform(publication: pd.DataFrame, replace_dict: dict) -> pd.DataFrame:
    df = (
        publication.assign(
            Authors = lambda df: df['Authors'].apply(
                standardize_author_names,
                replace_dict=replace_dict
            )
        )
        .explode('Authors')
        .groupby('Authors', as_index=False)
        .agg({
            'Title': list,
            'Year': list,
            'Source title': list,
            'Cited by': list,
            'Link': list
        })
    )
    return df


def build_description(row, nodes: pd.DataFrame, authors_with_inform: pd.DataFrame, max_display: int = 3) -> str:
    first = nodes.loc[nodes['id'] == row['first_author'], 'label'].iloc[0]
    second = nodes.loc[nodes['id'] == row['second_author'], 'label'].iloc[0]

    first_inform = authors_with_inform[authors_with_inform['Authors'] == first].iloc[0]
    second_inform = authors_with_inform[authors_with_inform['Authors'] == second].iloc[0]

    first_works = set(zip(first_inform['Title'], first_inform['Year'],
                          first_inform['Source title'], first_inform['Cited by']))
    second_works = set(zip(second_inform['Title'], second_inform['Year'],
                           second_inform['Source title'], second_inform['Cited by']))
    
    common = sorted(first_works & second_works, key=lambda x: x[-1], reverse=True)

    res = []
    for number, inform in enumerate(common[:max_display], 1):
        res.append(f"{number}. {inform[0]}, {inform[1]}")
    total = len(common)
    if total > max_display:
        res.append(f"\nи ещё {total - max_display} совместных работ.")
    return '<br>'.join(res)


def wrap_text(txt: str, width: int = 50) -> str:
    sentences = txt.split('<br>')
    res = []
    for sentence in sentences:
        words = sentence.split(' ')
        lines, cur = [], ''
        for w in words:
            if len(cur) + len(w) + 1 > width:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        lines.append(cur)
        res.append('<br>'.join(lines))
    return '<br>'.join(res)


def scale_coordinates(series: pd.Series, new_min: int = 0, new_max: int = 1000) -> pd.Series:
    old_min = series.min()
    old_max = series.max()
    return new_min + (series - old_min) * (new_max - new_min) / (old_max - old_min)


def prepare_network_elements(org_id: str):
    # Load data
    replace_dict = load_thesaurus(org_id)
    publication = load_publication(org_id)
    nodes = load_nodes(org_id)
    edges = load_edges(org_id)

    # Build authors info
    authors_info = build_authors_with_inform(publication, replace_dict)

    # Build edge descriptions
    edges['hover_text'] = edges.apply(
        lambda row: build_description(row, nodes, authors_info), axis=1
    )

    # Convert IDs to names
    edges['first_author'] = edges['first_author'].apply(
        lambda ID: nodes.loc[nodes['id'] == ID, 'label'].iloc[0]
    )
    edges['second_author'] = edges['second_author'].apply(
        lambda ID: nodes.loc[nodes['id'] == ID, 'label'].iloc[0]
    )

    # Impossible years
    YEAR_NOW = datetime.now().year
    nodes['Avg_pub_year'] = nodes['Avg_pub_year'].apply(
        lambda x: x if x <= YEAR_NOW else YEAR_NOW
    )

    # Scaling coordinates
    nodes['x'] = scale_coordinates(nodes['x'])
    nodes['y'] = scale_coordinates(nodes['y'])

    # Clusters to colors
    COLORS = [
        '#E87757', '#8DD4F6', '#F7A978', '#5E9DBE', '#AD9281', '#F9CD94',
        '#CAD892', '#F0ACB7', '#A0BA46', '#EB5A6D', '#758D46', '#F2C6C7',
        '#BDBDBD', '#83A061', '#EEADA7', '#80E3CD', '#E7A396', '#3C8782',
        '#EBCFB2', '#BAB9E1', '#EACE84', '#CCCBF2', '#F9F4BC', '#F3C9E4',
        '#FAF5AF', '#D9A1C0', '#969A60', '#F8E5EB', '#DDE48E', '#ED6C84',
    ]
    clusters = nodes['cluster'].unique()
    cluster_colors_map = {}
    for cl in clusters:
        cluster_colors_map[cl] = COLORS[(cl-1) % len(COLORS)]
    nodes['node_color'] = nodes['cluster'].map(cluster_colors_map)

    # Build elements
    nodes_records = nodes.to_dict('records')
    edges_records = edges.to_dict('records')

    node_color_map = nodes.set_index('label')['node_color'].to_dict()

    nodes_elements = [
        {
            'data': {
                'id': node['label'],
                'label': node['label'],
                'val': node['Links'],
                'Links': node['Links'],
                'Strength': node['Strength'],
                'Documents': node['Documents'],
                'Citations': node['Citations'],
                'Norm_citations': node['Norm_citations'],
                'Avg_pub_year': node['Avg_pub_year'],
                'Avg_citations': node['Avg_citations'],
                'Avg_norm_citations': node['Avg_norm_citations'],
                'color': node['node_color'],
                'cluster': node['cluster'],
            },
            'position': {'x': node['x'], 'y': node['y']}
        }
        for node in nodes_records
    ]
    edges_elements = [
        {
            'data': {
                'id': f"{edge['first_author']}-{edge['second_author']}",
                'source': edge['first_author'],
                'target': edge['second_author'],
                'weight': edge['weight'],
                'hover': edge['hover_text'],
                'color': node_color_map[edge['first_author']]
            },
        }
        for edge in edges_records
    ]
    elements = nodes_elements + edges_elements

    # Initializing x range
    X_MIN, X_MAX = nodes['x'].min(), nodes['x'].max()
    initial_x_range = np.abs(X_MAX - X_MIN)
    last_x_range = initial_x_range

    val_min = nodes['Links'].min()
    val_max = nodes['Links'].max()

    basic_stylesheet = [
        {
            'selector': 'node',
            'style': {
                'width':  f'mapData(val, {val_min}, {val_max}, 10, 40)',
                'height': f'mapData(val, {val_min}, {val_max}, 10, 40)',
                'background-color': 'data(color)',
                'label': 'data(label)',
                'font-size': f'mapData(val, {val_min}, {val_max}, 7, 17)',
                'opacity': 0.85,
                'text-halign': 'center',
                'text-valign': 'center',
            }
        },
        {
            'selector': 'edge',
            'style': {
                'width': '1',
                'line-color': 'data(color)',
                'line-opacity': 0.3,
                'opacity': 0.7,
                'label': 'data(weight)',
                'font-size': '6px',
                'text-rotation': 'autorotate',
                'text-background-color': '#fff',
                'text-background-opacity': 0.6,
                'text-background-shape': 'roundrectangle'
            }
        },
    ]

    # Option dictionaries
    size_options = []
    options = ['Links', 'Strength', 'Documents', 'Citations', 'Norm_citations']
    options_label = {'Links': 'Количество связей',
                    'Strength': 'Индекс связанности',
                    'Documents': 'Число публикаций',
                    'Citations': 'Число цитирований',
                    'Norm_citations': 'Норм. цитирования'}
    for col in nodes.columns:
        if col in options:
            size_options.append({'label': options_label[col], 'value': col})

    metrics_bounds = {}
    for col in options:
        metrics_bounds[col] = {
            'min': nodes[col].min(),
            'max': nodes[col].max()
        }

    color_options = []
    options = ['Avg_pub_year', 'Avg_citations', 'Avg_norm_citations']
    options_label = {'Avg_pub_year': 'Ср. год публикаций',
                    'Avg_citations': 'Ср. число цитирований',
                    'Avg_norm_citations': 'Ср. норм. цитирования'}
    for col in nodes.columns:
        if col in options:
            color_options.append({'label': options_label[col], 'value': col})

    for col in options:
        metrics_bounds[col] = {
            'min': nodes[col].min(),
            'max': nodes[col].max()
        }
    
    return {
        'elements': elements,
        'stylesheet': basic_stylesheet,
        'size_options': size_options,
        'metrics_bounds': metrics_bounds,
        'color_options': color_options,
        'nodes': nodes,
        'edges': edges
    }