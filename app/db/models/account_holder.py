from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, Boolean, String, DateTime, ForeignKey, func, text, Index

from app.db.database import Base
from app.db.soft_delete import SoftDeleteMixin

class AccountHolder(SoftDeleteMixin, Base):
    __tablename__ = "account_holders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    personal_info_id = Column(Integer, ForeignKey("personal_info.id", ondelete="CASCADE"), index=True)
    house_address = Column(String(255), nullable=False)
    otp = Column(String(255), nullable=True)  # widened for hashed storage (e231770546e7)
    otp_generated_at = Column(UTCDateTime(), nullable=True)
    # SET NULL, not CASCADE: deleting a parent detaches sub-accounts (bc3a5a003434)
    owner_account_holder_id = Column(Integer, ForeignKey("account_holders.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, server_default=text("false"))
    # `deleted_at` comes from SoftDeleteMixin. NULL = live membership,
    # timestamp = left/removed from the estate. The one-per-user-per-estate
    # trigger ignores deleted rows; reads are filtered by the
    # hook in app/db/soft_delete.py.
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)

    __table_args__ = (
        Index("ix_account_holders_deleted_at", "deleted_at"),
    )
