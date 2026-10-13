from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, text

from app.db.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True)
    personal_info_id = Column(Integer, ForeignKey("personal_info.id", ondelete="CASCADE"), index=True)
    license_plate_number = Column(String(20), nullable=False, index=True)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    color = Column(String(50), nullable=False)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)
