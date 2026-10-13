from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, func, event, Numeric, select, text, UniqueConstraint
from sqlalchemy.orm import Session

from app.db.database import Base

class EventRegister(Base):
    __tablename__ = "event_registers"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id", ondelete="CASCADE"), nullable=False, index=True)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)

    __table_args__ = (
        UniqueConstraint("event_id", "guest_id", name="uq_event_registers_event_guest"),
    )
