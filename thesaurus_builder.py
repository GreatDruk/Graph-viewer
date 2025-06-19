import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transliterate import translit

def build_author_thesaurus(org_id: str, similariti_coefficient: float = 0.8, surname_diff: int = 3):
    INPUT_FILE = f"org_data/processed/{org_id}/publications.csv"
    OUTPUT_FILE = f"org_data/processed/{org_id}/thesaurus_authors.txt"

    print("Uploading data...")
    df = pd.read_csv(INPUT_FILE)

    print("Author processing...")
    authors = df['Authors'].dropna()
    authors = authors.str.split('; ').explode()  # separation authors
    authors = authors[
        ~authors.str.strip()
        .str.lower()
        .str.endswith(('et al.', 'et al'))
    ]  # delete et al
    authors = authors.drop_duplicates().reset_index(drop=True)

    X = pd.DataFrame({'Authors': authors})
    X['Ready'] = authors.str.lower().str.replace(r'[^а-яa-zё .]', '', regex=True)

    def transliterate_name(name):
        if len(name) > 0:
            if name[-1] == '.':
                name = name[:-1]
            arr = name.split()
            name = arr[0] + ' ' + ''.join(arr[1:])
        return translit(name, 'ru', reversed=True)

    X['Ready'] = X['Ready'].apply(transliterate_name)

    # Separation of last name and initials
    X['Surnames'] = X['Ready'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else '')
    X['Initials'] = X['Ready'].apply(lambda x: x.split()[1] if len(x.split()) > 1 else '')

    # Algorithm for searching for similar surnames
    print("Searching for similar surnames...")
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 2))  # ngram_range an be changed
    matrix = vectorizer.fit_transform(X['Surnames'])
    similarity = cosine_similarity(matrix)

    # Assembling a thesaurus
    print("Assembling a thesaurus...")
    thesaurus = {}
    total = len(similarity)