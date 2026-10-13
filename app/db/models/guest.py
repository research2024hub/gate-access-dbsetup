from app.db.types import UTCDateTime
from sqlalchemy import JSON
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, func, event, Numeric, select, text
from sqlalchemy.orm import Session

from app.db.database import Base

class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True)
    personal_info_id = Column(Integer, ForeignKey("personal_info.id", ondelete="CASCADE"), index=True)
    creator_id = Column(Integer, ForeignKey("account_holders.id", ondelete="CASCADE"), index=True)
    status = Column(String(20), nullable=False, server_default=text("'EXPECTED'"))
    other_info = Column(JSON, nullable=False, server_default=text("(JSON_OBJECT())"))
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)
