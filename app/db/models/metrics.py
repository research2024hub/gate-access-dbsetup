from app.db.types import UTCDateTime
from sqlalchemy import JSON
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric, text, func

from app.db.database import Base


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True)
    gate_id = Column(Integer, ForeignKey("gates.id", ondelete="CASCADE"), nullable=False, index=True)
    device_timestamp = Column(UTCDateTime(), nullable=False)
    temperature_celsius = Column(Numeric(6, 3), nullable=False)
    total_cameras = Column(Integer, nullable=False)
    online_cameras = Column(Integer, nullable=False)
    running_services = Column(JSON, nullable=False, server_default=text("(JSON_OBJECT())"))
    storage_used_gb = Column(Numeric(12, 3), nullable=False)
    storage_total_gb = Column(Numeric(12, 3), nullable=False)
    # List of camera IDs that were offline when the metric was recorded
    offline_camera_ids = Column(JSON, nullable=False, server_default=text("(JSON_ARRAY())"))
    camera_alert_ts = Column(UTCDateTime(), nullable=True)
    # Timestamp when the metric record was received by the backend
    received_at = Column(
        UTCDateTime(),
        server_default=text("CURRENT_TIMESTAMP(6)"),
        default=func.current_timestamp(6),
        nullable=False,
    )
