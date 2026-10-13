from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, UniqueConstraint, DateTime, ForeignKey, Date, func, event, Numeric, select, text
from sqlalchemy.orm import Session

from app.db.database import Base

class AccessGroup(Base):
    __tablename__ = "access_groups"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)

    __table_args__ = (UniqueConstraint("name", "estate_id", name="uq_access_groups_name_estate"),)

    
