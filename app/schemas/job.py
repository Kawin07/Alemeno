from pydantic import BaseModel, UUID4, ConfigDict, Field
from datetime import datetime
from typing import Optional

class JobCreate(BaseModel):
    pass

class JobResponse(BaseModel):
    job_id: UUID4 = Field(validation_alias="id")
    status: str
    filename: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobStatusResponse(BaseModel):
    job_id: UUID4
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    summary: Optional[dict] = None  # We will fill this if completed

    model_config = ConfigDict(from_attributes=True)

class JobListResponse(BaseModel):
    job_id: UUID4 = Field(validation_alias="id")
    filename: str
    status: str
    row_count_raw: Optional[int] = None
    row_count_clean: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
