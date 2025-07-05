import pandas as pd

def load_orgs():
    df = pd.read_csv('org_data/org.txt', sep='\t', dtype=str)
    df = df.sort_values('Name')
    org_map = df[['ID','Name']].rename(columns={'ID':'value','Name':'label'}).to_dict('records')
    org_name_map = {item['value']: item['label'] for item in org_map}

    return org_map, org_name_map