"""
Module: processing
Provides core data transformation functions for preparing author
and coauthor information, scaling node coordinates, and computing
bibliometric metrics.
"""
import itertools
import pandas as pd

def standardize_author_names(names: str, replace_dict: dict) -> list:
    """
    Given raw 'Authors' column of semicolon-delimited strings,
    explode to individual lowercase names with thesaurus replacement.
    """
    arr_authors = [name.replace('et al.', '').strip() for name in names.split(';')]
    res = []
    for name in arr_authors:
        res.append(replace_dict.get(name, name).lower())
    return res


def build_authors_with_inform(publication: pd.DataFrame, replace_dict: dict) -> pd.DataFrame:
    """
    Build DataFrame indexed by author, with aggregated lists:
    - Title, Year, Source title, Cited by, Link
    plus computed columns First_pub_year, Last_pub_year.
    """
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
    """
    Build a mapping edge_id -> list of joint publications.
    - standardizes authors in each paper
    - for each unordered pair that exists in edges_records,
      collects (Title, Year, Source title, Cited by, Link)
    """
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


def scale_coordinates(series: pd.Series, new_min: int = 0, new_max: int = None) -> pd.Series:
    """
    Linearly scale 'series' values into [new_min, new_max].
    """
    count = len(series)
    if new_max is None:
        if count < 100:
            new_max = 1000
        elif count < 500:
            new_max = 2000
        elif count < 1000:
            new_max = 3000
        elif count < 3000:
            new_max = 4000
        elif count < 4000:
            new_max = 5000
        else:
            new_max = 6000
    
    old_min = series.min()
    old_max = series.max()
    return new_min + (series - old_min) * (new_max - new_min) / (old_max - old_min)


def compute_h_index(citation_counts):
    """
    Compute the h-index.
    """
    counts = list(citation_counts)
    counts.sort(reverse=True)
    h = 0

    for i, c in enumerate(counts, start=1):
        if c < i:
            break
        h = i
    return h
