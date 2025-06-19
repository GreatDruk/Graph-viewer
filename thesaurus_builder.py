import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transliterate import translit

def build_author_thesaurus(org_id: str, similariti_coefficient: float = 0.8, surname_diff: int = 3):
    INPUT_FILE = f"org_data/processed/{org_id}/publications.csv"
    OUTPUT_FILE = f"org_data/processed/{org_id}/thesaurus_authors.txt"

    print("Uploading data...")
    df = pd.read_csv(INPUT_FILE)
