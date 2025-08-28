"""
Module: thesaurus_builder
Builds a thesaurus of author name variants for a given organization.
"""

import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transliterate import translit

def build_author_thesaurus(org_id: str, similarity_coefficient: float = 0.8, surname_diff: int = 3) -> None:
    """
    Generate and save a mapping of similar author names to a canonical form.

    Args:
        org_id: ID of the organization.
        similarity_coefficient: Minimum cosine similarity for two surnames to be considered similar.
        surname_diff: Max length difference between surnames to consider.

    Reads publications from:
        org_data/processed/{org_id}/publications.csv
    Writes the thesaurus to:
        org_data/processed/{org_id}/thesaurus_authors.txt
    """
    base_path = os.path.join('org_data', 'processed', org_id)
    input_file = os.path.join(base_path, 'publications.csv')
    output_file = os.path.join(base_path, 'thesaurus_authors.txt')

    # Load author names
    df = pd.read_csv(input_file)

    names_col = "Authors"
    ids_col = "Author(s) ID"

    # If ID column present -> use ID-based grouping (strict pairing by position)
    if ids_col in df.columns:
        # Assembling a thesaurus
        thesaurus = {}
        id_to_canonical = {}

        def split_semicolon(cell: str):
            if pd.isna(cell):
                return []
            return [p.strip() for p in str(cell).split(';') if p.strip()]

        for _, row in df.iterrows():
            raw_names = row.get(names_col, '')
            raw_ids = row.get(ids_col, '')

            names = split_semicolon(raw_names)
            ids = split_semicolon(raw_ids)

            for aid, aname in zip(ids, names):
                aid = str(aid).strip()
                aname = aname.strip()

                if aid not in id_to_canonical:
                    id_to_canonical[aid] = aname
                else:
                    canonical = id_to_canonical[aid]
                    if aname != canonical:
                        thesaurus[aname] = canonical

        # Write out thesaurus file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Label\tReplace by\n")
            for label, replace_by in thesaurus.items():
                f.write(f"{label}\t{replace_by}\n")
        return

    authors_series = (
        df['Authors']
        .dropna()
        .str.split('; ')
        .explode()
        .str.strip()
        .drop_duplicates()
    )

    # Filter out "et al" entries
    mask = ~authors_series.str.lower().str.endswith(('et al.', 'et al'))
    authors_series = authors_series[mask].reset_index(drop=True)

    # Prepare a DataFrame for processing
    authors_df = pd.DataFrame({'Authors': authors_series})

    # Normalize: remove all non-letters/dots, lowercase
    authors_df['Ready'] = (
        authors_series
        .str.lower()
        .str.replace(r'[^а-яa-zё .]', '', regex=True)
    )

    def transliterate_name(name: str) -> str:
        """
        Transliterate Cyrillic to Latin and normalize initials.
        """
        if len(name) > 0:
            name = name.rstrip('.')
            arr = name.split()
            name = arr[0] + ' ' + ''.join(arr[1:])
        return translit(name, 'ru', reversed=True)

    # Apply transliteration
    authors_df['Ready'] = authors_df['Ready'].apply(transliterate_name)

    # Split into surname and initials
    authors_df['Surnames'] = authors_df['Ready'].str.split().str[0].fillna('')
    authors_df['Initials'] = authors_df['Ready'].str.split().str[1].fillna('')

    # Algorithm for searching for similar surnames
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(authors_df['Surnames'])
    similarity = cosine_similarity(matrix)

    # Assembling a thesaurus
    thesaurus = {}
    total = len(similarity)

    for i in range(total):
        if authors_df['Authors'][i] in thesaurus:
            continue

        for j in range(i+1, total):
            if authors_df['Authors'][j] in thesaurus:
                continue

            if similarity[i][j] < similarity_coefficient:
                continue

            # Checking initials
            initials1 = authors_df['Initials'][i].split('.')
            initials2 = authors_df['Initials'][j].split('.')
            
            if len(initials1) != len(initials2):
                shorter, longer = sorted([initials1, initials2], key=len)
                if shorter != longer[:len(shorter)]:
                    continue
            elif initials1 != initials2:
                continue

            # Check surname length difference
            surname1, surname2 = authors_df['Surnames'][i], authors_df['Surnames'][j]
            if abs(len(surname1) - len(surname2)) > surname_diff:
                continue
                
            # Exclude male/female surname mismatch (ending in 'a')
            if (surname1[-1] == 'a') ^ (surname2[-1] == 'a'):
                continue

            # Map the variant to the canonical form
            thesaurus[authors_df['Authors'][j]] = authors_df['Authors'][i]

    # Write out thesaurus file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Label\tReplace by\n")
        for label, replace_by in thesaurus.items():
            f.write(f"{label}\t{replace_by}\n")
