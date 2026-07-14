import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.device import Device
    from app.models.model_score import ModelScore

class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[str] = mapped_column(String(255), nullable=True)
    bytes_transferred: Mapped[int] = mapped_column(BigInteger, default=0)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    location: Mapped[str] = mapped_column(String(100), nullable=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, default=uuid.UUID("9f9bbf10-e3f3-470b-85be-587265bf02ab"))


    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="access_logs")
    device: Mapped["Device"] = relationship("Device", back_populates="access_logs")
    # TODO: This relationship depends on the ModelScore model written next
    model_scores: Mapped[List["ModelScore"]] = relationship("ModelScore", back_populates="access_log")
