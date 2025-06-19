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