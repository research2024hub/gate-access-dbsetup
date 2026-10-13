from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, String, DateTime, Time, ForeignKey, text, func, UniqueConstraint, Boolean
from app.db.database import Base

class Gate(Base):
    __tablename__ = "gates"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    last_controller_heartbeat = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), nullable=False)
    opening_time = Column(Time, server_default=text("'00:00:00'"), nullable=False)
    closing_time = Column(Time, server_default=text("'23:59:59'"), nullable=False)
    active = Column(Boolean, nullable=False, server_default=text("true"))
    date_created = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), nullable=False)
    date_updated = Column(UTCDateTime(), server_default=text("CURRENT_TIMESTAMP(6)"), onupdate=func.current_timestamp(6), nullable=False)
    last_alert_sent_at = Column(UTCDateTime(), nullable=True)
    snr = Column(String(50), nullable=True)
    rssi = Column(String(50), nullable=True)
    # Composite Unique Constraint
    __table_args__ = (UniqueConstraint("name", "estate_id", name="uq_gates_name_estate"),)
