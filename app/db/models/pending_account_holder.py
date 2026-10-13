from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, Boolean, String, DateTime, ForeignKey, func, text

from app.db.database import Base

class PendingAccountHolder(Base):
    __tablename__ = "pending_account_holders"

    id = Column(Integer, primary_key=True)
    # user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    personal_info_id = Column(Integer, ForeignKey("personal_info.id", ondelete="CASCADE"), index=True)
    house_address = Column(String(255), nullable=False)
    otp = Column(String(255), nullable=True)  # widened for hashed storage (e231770546e7)
    otp_generated_at = Column(UTCDateTime(), nullable=True)
    owner_account_holder_id = Column(Integer, ForeignKey("account_holders.id", ondelete="CASCADE"), nullable=True, index=True)
    is_pending = Column(Boolean, nullable=False, server_default=text("true"))
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)
    email = Column(String(255), nullable=True, unique=True)
