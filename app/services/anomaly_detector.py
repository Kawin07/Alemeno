import pandas as pd

DOMESTIC_ONLY_MERCHANTS = {
    "SWIGGY", "OLA", "IRCTC", "ZOMATO",
    "JIO RECHARGE", "HDFC ATM", "BOOKMYSHOW", "FLIPKART"
}

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    # Add anomaly columns if not exist
    df['is_anomaly'] = False
    df['anomaly_reasons'] = [[] for _ in range(len(df))]
    
    # 1. Statistical outlier detection: amount > 3 * median per account
    medians = df.groupby('account_id')['amount'].median()
    
    for idx, row in df.iterrows():
        reasons = []
        acc_id = row['account_id']
        amount = row['amount']
        merchant = str(row['merchant']).upper()
        currency = row['currency']
        
        # Outlier check
        if acc_id in medians and pd.notnull(medians[acc_id]):
            median_amt = medians[acc_id]
            if median_amt > 0 and amount > 3 * median_amt:
                reasons.append(f"Amount {amount} exceeds 3x median ({median_amt:.2f}) for account {acc_id}")
                
        # Currency mismatch check
        if currency == 'USD' and merchant in DOMESTIC_ONLY_MERCHANTS:
            reasons.append(f"USD currency used with domestic-only merchant {row['merchant']}")
            
        if reasons:
            df.at[idx, 'is_anomaly'] = True
            df.at[idx, 'anomaly_reasons'] = reasons
            
    return df
