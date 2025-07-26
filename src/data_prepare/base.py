"""
Module: base
Provides functions to load, preprocess and cache network elements
for the given organization. Builds node & edge data structures
for Dash Cytoscape, as well as author/co-author maps.

Cache files:
  - cache.pkl: full result dict from prepare_network_elements
  - cache_authors.pkl: mapping author -> list of their publications
  - cache_coauthors.pkl: mapping edge_id -> list of joint publications
"""
import os
import pandas as pd
from datetime import datetime
from .cache import is_cache, load_cache, save_cache
from .constants import BASE_PATH, CACHE_FILE, AUTHORS_CACHE_FILE, COAUTHORS_CACHE_FILE
from .loading import *
from .processing import *
from .utils import get_source_paths

def prepare_network_elements(org_id: str):
    """
    Main function: returns a dict with keys:
      - elements: list of cyto elements
      - stylesheet: base stylesheet
      - size_options, color_options, metrics_bounds
      - nodes, edges, num_publication
    Caches entire result in cache.pkl, and separately
    author/coauthor maps.
    """
    # Check cache
    source_paths = get_source_paths(org_id)
    cache_path = f'{BASE_PATH}/{org_id}/{CACHE_FILE}'
    cache_path_authors = f'{BASE_PATH}/{org_id}/{AUTHORS_CACHE_FILE}'
    cache_path_coauthors = f'{BASE_PATH}/{org_id}/{COAUTHORS_CACHE_FILE}'
    if is_cache(cache_path, source_paths) and os.path.exists(cache_path_authors) and os.path.exists(cache_path_coauthors):
        try:
            return load_cache(cache_path)
        except Exception:
            pass

    # Load data
    replace_dict = load_thesaurus(org_id)
    publication = load_publication(org_id)
    nodes = load_nodes(org_id)
    edges = load_edges(org_id)

    # Build authors info and years map
    authors_info = build_authors_with_inform(publication, replace_dict)
    years_map = authors_info.set_index('Authors')[['First_pub_year', 'Last_pub_year']].to_dict('index')

    authors_map = (
        authors_info
        .set_index('Authors')
        [['Title', 'Year', 'Cited by']]
        .to_dict('index')
    )
    save_cache(cache_path_authors, authors_map)

    # Convert IDs to names
    edges['first_author'] = edges['first_author'].apply(
        lambda ID: nodes.loc[nodes['id'] == ID, 'label'].iloc[0]
    )
    edges['second_author'] = edges['second_author'].apply(
        lambda ID: nodes.loc[nodes['id'] == ID, 'label'].iloc[0]
    )

    # Calculate max edge weight for each node
    max_edges = (
        pd.concat([
            edges[['first_author','weight']].rename(columns={'first_author':'label'}),
            edges[['second_author','weight']].rename(columns={'second_author':'label'})
        ], ignore_index=True)
        .groupby('label')['weight']
        .max()
        .to_dict()
    )
    nodes['max_edge_weight'] = nodes['label'].map(lambda lbl: max_edges.get(lbl, 0))

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

    # Append first and last pub years
    nodes['First_pub_year'] = nodes['label'].map(lambda lbl: years_map.get(lbl, {}).get('First_pub_year'))
    nodes['Last_pub_year']  = nodes['label'].map(lambda lbl: years_map.get(lbl, {}).get('Last_pub_year'))

    # Range years
    min_year = publication['Year'].min()
    max_year = publication['Year'].max()
    years = list(range(min_year, max_year + 1))

    # Count num of publications in each year
    counts_by_year = (
        publication.groupby('Year')
            .size()
            .reindex(years, fill_value=0)
            .tolist()
    )

    # Build elements
    nodes_records = nodes.to_dict('records')
    edges_records = edges.to_dict('records')

    node_color_map = nodes.set_index('label')['node_color'].to_dict()

    nodes_elements = [
        {
            'data': {
                'id': node['label'],
                'label': node['label'].title(),
                'val': node['Links'],
                'Links': node['Links'],
                'Strength': node['Strength'],
                'Documents': node['Documents'],
                'Citations': node['Citations'],
                'Norm_citations': node['Norm_citations'],
                'Avg_pub_year': node['Avg_pub_year'],
                'First_pub_year': node['First_pub_year'],
                'Last_pub_year': node['Last_pub_year'],
                'Avg_citations': node['Avg_citations'],
                'Avg_norm_citations': node['Avg_norm_citations'],
                'color': node['node_color'],
                'cluster': node['cluster'],
                'max_edge_weight': node['max_edge_weight'],
            },
            'position': {'x': node['x'], 'y': node['y']}
        }
        for node in nodes_records
    ]
    edges_elements = [
        {
            'data': {
                'id': f'edge-{ind}',
                'source': edge['first_author'],
                'target': edge['second_author'],
                'weight': edge['weight'],
                'color': node_color_map[edge['first_author']]
            },
        }
        for ind, edge in enumerate(edges_records)
    ]
    elements = nodes_elements + edges_elements

    # Build edge descriptions
    coauthors_info_map = build_coauthors_map(publication, replace_dict, edges_records)
    save_cache(cache_path_coauthors, coauthors_info_map)

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
                'text-background-color': '#EEECE3',
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
    options = ['Avg_pub_year', 'First_pub_year', 'Last_pub_year', 'Avg_citations', 'Avg_norm_citations']
    options_label = {'Avg_pub_year': 'Ср. год публикаций',
                    'First_pub_year': 'Год первой публикации',
                    'Last_pub_year': 'Год последней публикации',
                    'Avg_citations': 'Ср. число цитирований',
                    'Avg_norm_citations': 'Ср. норм. цитирования'}
    for col in options:
        color_options.append({'label': options_label[col], 'value': col})

    for col in options:
        metrics_bounds[col] = {
            'min': nodes[col].min(),
            'max': nodes[col].max()
        }

    # Counting citations for publications
    total_citations = publication['Cited by'].sum()
    h_index = compute_h_index(publication['Cited by'])
    
    result = {
        'elements': elements,
        'stylesheet': basic_stylesheet,
        'size_options': size_options,
        'metrics_bounds': metrics_bounds,
        'color_options': color_options,
        'nodes': nodes,
        'edges': edges,
        'num_publication': len(publication),
        'num_cites': total_citations,
        'h_index': h_index,
        'years': years,
        'counts_publication_by_year': counts_by_year,
    }
    
    try:
        save_cache(cache_path, result)
    except Exception:
        pass
    
    return result
