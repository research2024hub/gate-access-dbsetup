from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, text, func
from app.db.database import Base

class PendingUser(Base):
    __tablename__ = 'pending_users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=True, unique=True)
    password = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True, unique=True)
    otp = Column(String(255), nullable=False)  # widened for hashed storage (e231770546e7)
    otp_expiry = Column(UTCDateTime(), nullable=False)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)
