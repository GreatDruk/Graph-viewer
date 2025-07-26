"""
Module: cache
Defines functions for checking, loading, and saving caches.
"""
import os
import pickle
from .constants import BASE_PATH, AUTHORS_CACHE_FILE, COAUTHORS_CACHE_FILE

def is_cache(cache_path: str, source_paths: dict) -> bool:
    """
    Check if 'cache_path' and all cache files exist.
    Returns False if cache is missing.
    """
    if not os.path.exists(cache_path):
        return False

    for p in source_paths.values():
        if not os.path.exists(p):
            return False

    return True


def load_cache(cache_path: str):
    """Load and return a cache"""
    with open(cache_path, 'rb') as f:
        return pickle.load(f)
    

def load_cache_authors(org_id: str) -> dict:
    """Load and return a authors cache"""
    path = f'{BASE_PATH}/{org_id}/{AUTHORS_CACHE_FILE}'
    with open(path, 'rb') as f:
        return pickle.load(f)


def load_cache_coauthors(org_id: str) -> dict:
    """Load and return a coauthors cache"""
    path = f'{BASE_PATH}/{org_id}/{COAUTHORS_CACHE_FILE}'
    with open(path, 'rb') as f:
        return pickle.load(f)


def save_cache(cache_path: str, data):
    """Save 'data' to 'path' as pickle, creating folders as needed."""
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump(data, f)
