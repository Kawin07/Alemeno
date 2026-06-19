from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, Uuid, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class JobSummary(Base):
    __tablename__ = "job_summaries"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Uuid(as_uuid=True), ForeignKey("jobs.id"), unique=True, nullable=False)
    total_spend_inr = Column(Numeric(14, 2), nullable=True)
    total_spend_usd = Column(Numeric(14, 2), nullable=True)
    top_merchants = Column(JSON, nullable=True)
    anomaly_count = Column(Integer, nullable=True)
    narrative = Column(Text, nullable=True)
    risk_level = Column(String(10), nullable=True)
    llm_raw_response = Column(Text, nullable=True)

    job = relationship("Job", back_populates="summary")
