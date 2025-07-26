"""
Module: utils
Helper functions for building file system paths to org data.
"""
import os
from .constants import BASE_PATH, THESAURUS_FILE, PUBLICATIONS_FILE, NODES_FILE, EDGES_FILE

def get_source_paths(org_id: str):
    """
    Build absolute paths to all source data files for a given organization.

    Args:
        org_id: The unique identifier of the organization (folder name under BASE_PATH).

    Returns:
        A dictionary mapping logical file keys to Path objects:
          - 'thesaurus': path to the author thesaurus file
          - 'publications': path to the publications CSV
          - 'nodes': path to the nodes definition file
          - 'edges': path to the edges definition file
    """
    path = f'{BASE_PATH}/{org_id}'
    return {
        'thesaurus': os.path.join(path, THESAURUS_FILE),
        'publications': os.path.join(path, PUBLICATIONS_FILE),
        'nodes': os.path.join(path, NODES_FILE),
        'edges': os.path.join(path, EDGES_FILE),
    }
