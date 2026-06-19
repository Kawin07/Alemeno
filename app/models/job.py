from sqlalchemy import Column, Integer, String, Text, DateTime, text, LargeBinary, Uuid
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_content = Column(LargeBinary, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    row_count_raw = Column(Integer, nullable=True)
    row_count_clean = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    completed_at = Column(DateTime, nullable=True)
    
    transactions = relationship("Transaction", back_populates="job", cascade="all, delete-orphan")
    summary = relationship("JobSummary", back_populates="job", uselist=False, cascade="all, delete-orphan")
