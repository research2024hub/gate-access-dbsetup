from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, func, event, Numeric, select, text
from sqlalchemy.orm import Session

from app.db.database import Base

class Accesslog(Base):
    __tablename__ = "accesslog"

    id = Column(Integer, primary_key=True)
    # estate_id = Column(Integer, ForeignKey("estates.id", ondelete="CASCADE"))
    license_plate_number = Column(String(20), nullable=False)
    # actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    event = Column(String(50), nullable=False)
    gate_id = Column(Integer, ForeignKey("gates.id", ondelete="CASCADE"), nullable=False, index=True)
    # message = Column(String, nullable=False)
    timestamp = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
