import pandas as pd
import io

def parse_csv(content: bytes) -> pd.DataFrame:
    """Read CSV from bytes into a pandas DataFrame."""
    try:
        df = pd.read_csv(io.BytesIO(content))
        
        # Ensure column names are stripped of whitespace and lowercase
        df.columns = df.columns.str.strip().str.lower()
        
        expected_columns = {
            'txn_id', 'date', 'merchant', 'amount', 'currency', 
            'status', 'category', 'account_id', 'notes'
        }
        
        # Some flexibility if columns are missing
        if not expected_columns.issubset(set(df.columns)):
            missing = expected_columns - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")
            
        return df
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {str(e)}")
