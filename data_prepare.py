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

