from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, Time, ForeignKey, Date, func, event, Numeric, select, text
from sqlalchemy.orm import Session

from app.db.database import Base

class GateAccessGroupLink(Base):
    __tablename__ = "gate_access_group_links"

    gate_id = Column(Integer, ForeignKey("gates.id", ondelete="CASCADE"), primary_key=True)
    access_group_id = Column(Integer, ForeignKey("access_groups.id", ondelete="CASCADE"), primary_key=True, index=True)
    opening_time = Column(Time, server_default=text("'00:00:00'"), nullable=False)
    closing_time = Column(Time, server_default=text("'23:59:59'"), nullable=False)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)
    
