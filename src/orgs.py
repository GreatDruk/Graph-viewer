"""
Module: orgs
Load organization ID and names from a TSV file.
"""

import os
import pandas as pd

def load_orgs():
    """
    Load organization ID from a TSV file.

    Returns:
        org_map: List of dicts with 'value' (org ID) and 'label' (org Name) for dropdown options.
        org_name_map: Mapping from org ID to org Name for quick lookup.

    Raises:
        FileNotFoundError: If the org_file does not exist.
    """
    org_file = 'org_data/org.txt'

    if not os.path.exists(org_file):
        raise FileNotFoundError(f'Organization file not found: {org_file}')
    
    df = pd.read_csv(org_file, sep='\t', dtype=str)
    df = df.sort_values('Name')

    org_map = df[['ID', 'Name']].rename(columns={'ID':'value','Name':'label'}).to_dict('records')
    org_name_map = {item['value']: item['label'] for item in org_map}

    return org_map, org_name_map
