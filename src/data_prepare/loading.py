import os
import pandas as pd
from .constants import BASE_PATH, THESAURUS_FILE, PUBLICATIONS_FILE, NODES_FILE, EDGES_FILE
from src.thesaurus_builder import build_author_thesaurus

def load_thesaurus(org_id: str) -> dict:
    """
    Check thesaurus exists (build if not),
    load and return dict[label -> replace_by].
    """
    thesaurus_path = f'{BASE_PATH}/{org_id}/{THESAURUS_FILE}'
    if not os.path.exists(thesaurus_path):
        build_author_thesaurus(org_id=org_id)

    replace_dict = (
        pd.read_csv(thesaurus_path, sep='\t')
        .set_index('Label')
        .to_dict()['Replace by']
    )

    return replace_dict


def load_publication(org_id: str) -> pd.DataFrame:
    """Load and return a publications"""
    return pd.read_csv(f'{BASE_PATH}/{org_id}/{PUBLICATIONS_FILE}')


def load_nodes(org_id: str) -> pd.DataFrame:
    """Load and return a nodes map"""
    nodes = pd.read_csv(f'{BASE_PATH}/{org_id}/{NODES_FILE}', sep='\t')

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
    """Load and return a edges map"""
    return pd.read_csv(f'{BASE_PATH}/{org_id}/{EDGES_FILE}', sep='\t',
                         names=['first_author','second_author','weight'], header=None)