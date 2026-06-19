import pandas as pd
from datetime import datetime

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Strip currency symbols from amounts and convert to numeric
    # Remove '$', commas, spaces, then cast to float/numeric
    if df['amount'].dtype == object:
        df['amount'] = df['amount'].str.replace(r'[\$\,\s]', '', regex=True)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    # 2. Uppercase status and currency
    df['status'] = df['status'].astype(str).str.strip().str.upper()
    df['currency'] = df['currency'].astype(str).str.strip().str.upper()
    
    # 3. Fill missing categories
    df['category'] = df['category'].fillna('Uncategorised')
    # Treat empty strings or just whitespace as Uncategorised too
    df.loc[df['category'].str.strip() == '', 'category'] = 'Uncategorised'
    
    # 4. Normalise dates
    # Pandas to_datetime is smart but can be tricked by mixed DD-MM and MM-DD.
    # Since we know it's mixed, we'll try dayfirst=True
    df['date'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True, format='mixed').dt.date
    
    # Fill any null values for string columns with empty string (like notes, txn_id)
    df['notes'] = df['notes'].fillna('')
    df['txn_id'] = df['txn_id'].fillna('')
    
    # Drop rows where critical fields couldn't be parsed (like amount=NaN or date=NaT)
    df = df.dropna(subset=['amount', 'date', 'merchant', 'account_id'])
    
    # 5. Remove exact duplicates
    df = df.drop_duplicates()
    
    return df
