from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, Date, func, event, Numeric, select, text
from sqlalchemy.orm import Session

from app.db.database import Base

class AccountType(Base):
    __tablename__ = 'account_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)
