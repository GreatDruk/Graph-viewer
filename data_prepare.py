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
