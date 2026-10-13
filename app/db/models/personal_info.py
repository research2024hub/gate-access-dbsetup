from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, UniqueConstraint, DateTime, ForeignKey, Date, func, event, Numeric, select, text
from sqlalchemy.orm import Session

from app.db.database import Base

class PersonalInfo(Base):
    __tablename__ = "personal_info"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    id_type = Column(String(50), nullable=True)
    id_num = Column(String(100), nullable=True)
    contact = Column(String(50), nullable=True)
    expiry = Column(UTCDateTime(), nullable=True)
    account_type_id = Column(Integer, ForeignKey("account_types.id"), server_default=text("1"), nullable=False, index=True)
    access_group_id = Column(Integer, ForeignKey("access_groups.id"), server_default=text("1"), nullable=False, index=True)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)

    __table_args__ = (UniqueConstraint("id_type", "id_num", "estate_id", name="uq_id_type_id_num"),)
