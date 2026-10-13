from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, func, event, Numeric, select, text
from sqlalchemy.orm import Session

from app.db.database import Base

class AccountTypePrivilegeLink(Base):
    __tablename__ = "account_type_privilege_links"

    account_type_id = Column(Integer, ForeignKey("account_types.id", ondelete="CASCADE"), primary_key=True)
    privilege_id = Column(Integer, ForeignKey("privileges.id", ondelete="CASCADE"), primary_key=True, index=True)
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)
    
