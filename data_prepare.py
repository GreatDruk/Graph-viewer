from thesaurus_builder import build_author_thesaurus

import pandas as pd
import os.path
import pickle
from datetime import datetime
import itertools

def get_source_paths(org_id: str):
    base_path = f'org_data/processed/{org_id}'
    return {
        'thesaurus': os.path.join(base_path, 'thesaurus_authors.txt'),
        'publications': os.path.join(base_path, 'publications.csv'),
        'nodes': os.path.join(base_path, 'map.txt'),
        'edges': os.path.join(base_path, 'network.txt'),
    }


def is_cache(cache_path: str, source_paths: dict) -> bool:
    if not os.path.exists(cache_path):
        return False

    for p in source_paths.values():
        if not os.path.exists(p):
            return False

    return True


def load_cache(cache_path: str):
    with open(cache_path, 'rb') as f:
        return pickle.load(f)
    

def load_cache_authors(org_id: str) -> dict:
    path = f'org_data/processed/{org_id}/cache_authors.pkl'
    with open(path, 'rb') as f:
        return pickle.load(f)


def load_cache_coauthors(org_id: str) -> dict:
    path = f'org_data/processed/{org_id}/cache_coauthors.pkl'
    with open(path, 'rb') as f:
        return pickle.load(f)


def save_cache(cache_path: str, data):
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump(data, f)


def load_thesaurus(org_id: str) -> dict:
    thesaurus_path = f'org_data/processed/{org_id}/thesaurus_authors.txt'
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

    df['First_pub_year'] = df['Year'].apply(lambda yrs: min(yrs) if yrs else None)
    df['Last_pub_year'] = df['Year'].apply(lambda yrs: max(yrs) if yrs else None)

    return df


def build_coauthors_map(publication: pd.DataFrame, replace_dict: dict, edges_records: list) -> dict:
    df = (
        publication.assign(
            Authors = lambda df: df['Authors'].apply(
                standardize_author_names,
                replace_dict=replace_dict
            )
        )
    )

    coauthors_id_map = {}
    for ind, edge in enumerate(edges_records):
        source, target = sorted([edge['first_author'], edge['second_author']])
        coauthors_id_map[(source, target)] = ind

    co_map: dict[tuple[str, str], list[tuple]] = {}
    for _, row in df.iterrows():
        authors = row['Authors']
        for a, b in itertools.combinations(sorted(authors), 2):
            if (a, b) in coauthors_id_map:
                key = coauthors_id_map[(a, b)]
                if key not in co_map:
                    co_map[key] = []
                co_map[key].append((
                    row['Title'],
                    row['Year'],
                    row['Source title'],
                    row['Cited by'],
                    row['Link']
                ))

    return co_map


def scale_coordinates(series: pd.Series, new_min: int = 0, new_max: int = 2000) -> pd.Series:
    old_min = series.min()
    old_max = series.max()
    return new_min + (series - old_min) * (new_max - new_min) / (old_max - old_min)


def prepare_network_elements(org_id: str):
    # Cache
    source_paths = get_source_paths(org_id)
    cache_path = f'org_data/processed/{org_id}/cache.pkl'
    cache_path_authors = f'org_data/processed/{org_id}/cache_authors.pkl'
    cache_path_coauthors = f'org_data/processed/{org_id}/cache_coauthors.pkl'
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
    
    result = {
        'elements': elements,
        'stylesheet': basic_stylesheet,
        'size_options': size_options,
        'metrics_bounds': metrics_bounds,
        'color_options': color_options,
        'nodes': nodes,
        'edges': edges,
        'num_publication': len(publication)
    }
    
    try:
        save_cache(cache_path, result)
    except Exception:
        pass
    
    return result
