from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, func, event, Numeric, select, text
from sqlalchemy.orm import Session

from app.db.database import Base

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id", ondelete="SET NULL"), index=True)
    target_account_holder_id = Column(Integer, ForeignKey("account_holders.id", ondelete="SET NULL"), index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    # Set for vehicle entry/exit events; NULL for every other log type (2047cc35125e).
    license_plate_number = Column(String(20), nullable=True, index=True)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
