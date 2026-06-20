import pandas as pd
from datetime import datetime

def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    if df['amount'].dtype == object:
        df['amount'] = df['amount'].str.replace(r'[\$\,\s]', '', regex=True)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    

    df['status'] = df['status'].astype(str).str.strip().str.upper()
    df['currency'] = df['currency'].astype(str).str.strip().str.upper()
    

    df['category'] = df['category'].fillna('Uncategorised')

    df.loc[df['category'].str.strip() == '', 'category'] = 'Uncategorised'
    

    df['date'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True, format='mixed').dt.date
    

    df['notes'] = df['notes'].fillna('')
    df['txn_id'] = df['txn_id'].fillna('')
    

    df = df.dropna(subset=['amount', 'date', 'merchant', 'account_id'])
    

    df = df.drop_duplicates()
    
    return df
