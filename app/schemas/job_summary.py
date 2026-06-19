from pydantic import BaseModel, ConfigDict, UUID4
from typing import Optional, List, Dict
from decimal import Decimal
from .transaction import TransactionResponse

class JobSummaryResponse(BaseModel):
    total_spend_inr: Optional[Decimal] = None
    total_spend_usd: Optional[Decimal] = None
    top_merchants: Optional[List[str]] = None
    anomaly_count: Optional[int] = None
    narrative: Optional[str] = None
    risk_level: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobResultsResponse(BaseModel):
    job_id: UUID4
    status: str
    transactions: List[TransactionResponse]
    anomalies: List[dict]
    category_breakdown: Dict[str, float]
    summary: Optional[JobSummaryResponse] = None
