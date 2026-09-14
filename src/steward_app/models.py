from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class SuspectRecord(Base):
    __tablename__ = "suspect_records"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, index=True)       # e.g., sales_payment_tenders
    violation_rule = Column(String)               # e.g., FX_RATE_INVALID
    error_message = Column(String)
    raw_payload_json = Column(String)             # Dữ liệu gốc định dạng JSON
    status = Column(String, default="PENDING")    # PENDING | APPROVED | REJECTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
