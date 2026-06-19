from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal
from typing import Optional, List

class TransactionResponse(BaseModel):
    txn_id: Optional[str] = None
    date: date
    merchant: str
    amount: Decimal
    currency: str
    status: str
    category: str
    account_id: str
    is_anomaly: bool
    anomaly_reasons: Optional[List[str]] = None
    llm_category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
