"""
Module: constants
Holds all file- and directory-related constants for data preparation.
"""
# Base directory for orgs
BASE_PATH: str = 'org_data/processed'

# Constants for file names under org_data/processed/{org_id}/
CACHE_FILE: str = 'cache.pkl'
AUTHORS_CACHE_FILE: str = 'cache_authors.pkl'
COAUTHORS_CACHE_FILE: str = 'cache_coauthors.pkl'
THESAURUS_FILE: str = 'thesaurus_authors.txt'
PUBLICATIONS_FILE: str = 'publications.csv'
NODES_FILE: str = 'map.txt'
EDGES_FILE: str = 'network.txt'
