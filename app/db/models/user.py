from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, func, event, Numeric, select, text, CheckConstraint, Index
from sqlalchemy.orm import Session

from app.db.database import Base
from app.db.soft_delete import SoftDeleteMixin

class User(SoftDeleteMixin, Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    password = Column(String(255), nullable=False)
    reset_otp = Column(String(255), nullable=True)  # widened for hashed storage (e231770546e7)
    reset_expiry = Column(UTCDateTime(), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    is_admin = Column(Boolean, nullable=False, server_default=text("false"))
    # `deleted_at` comes from SoftDeleteMixin. NULL = live, timestamp = removed.
    # The app sets it (user.soft_delete()) instead of issuing DELETE; reads are
    # filtered automatically by the hook in app/db/soft_delete.py (9a900bb97a92).
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), default=func.current_timestamp(6), onupdate=func.current_timestamp(6), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR phone_number IS NOT NULL",
            name="ck_users_has_identifier",
        ),
        # Identity uniqueness applies only to live accounts, so a soft-deleted
        # user's email/phone can be re-registered (0715f96ac00a).
        Index("uq_users_email", text("(CASE WHEN deleted_at IS NULL THEN email ELSE NULL END)"), unique=True),
        Index("uq_users_phone_number", text("(CASE WHEN deleted_at IS NULL THEN phone_number ELSE NULL END)"), unique=True),
        Index("ix_users_deleted_at", "deleted_at"),
    )
