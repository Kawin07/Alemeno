from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Boolean, ForeignKey, Uuid, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Uuid(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    txn_id = Column(String(50), nullable=True)
    date = Column(Date, nullable=False)
    merchant = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(10), nullable=False)
    category = Column(String(50), nullable=False)
    account_id = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    is_anomaly = Column(Boolean, nullable=False, default=False)
    anomaly_reasons = Column(JSON, nullable=True)
    llm_category = Column(String(50), nullable=True)
    llm_raw_response = Column(Text, nullable=True)
    llm_failed = Column(Boolean, nullable=False, default=False)

    job = relationship("Job", back_populates="transactions")
