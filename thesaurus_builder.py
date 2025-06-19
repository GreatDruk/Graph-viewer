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

    for i in range(total):
        if X['Authors'][i] in thesaurus:
            continue
            
        if (i + 1) % 500 == 0:
            print(f"Processed: {i+1}/{total}")
            
        for j in range(i+1, total):
            if X['Authors'][j] in thesaurus:
                continue
                
            if similarity[i][j] < similariti_coefficient:
                continue
                
            # Checking initials
            initials1 = X['Initials'][i].split('.')
            initials2 = X['Initials'][j].split('.')
            
            if len(initials1) != len(initials2):
                shorter, longer = sorted([initials1, initials2], key=len)
                if shorter != longer[:len(shorter)]:
                    continue
            elif initials1 != initials2:
                continue
                
            # Checking surnames
            surname1, surname2 = X['Surnames'][i], X['Surnames'][j]
            if abs(len(surname1) - len(surname2)) > surname_diff:
                continue
                
            if (surname1[-1] == 'a') ^ (surname2[-1] == 'a'):  # XOR for checking male/female last name
                continue
                
            thesaurus[X['Authors'][j]] = X['Authors'][i]
    