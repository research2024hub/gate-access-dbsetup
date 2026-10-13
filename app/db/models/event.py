from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, func, event, Numeric, select, text, CheckConstraint
from sqlalchemy.orm import Session

from app.db.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("account_holders.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    max_num_of_attendees = Column(Integer, nullable=False)
    start_time = Column(UTCDateTime(), nullable=False)
    end_time = Column(UTCDateTime(), nullable=False)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_events_end_after_start"),
    )
