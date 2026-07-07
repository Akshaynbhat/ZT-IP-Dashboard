import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Float, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.access_log import AccessLog

class ModelScore(Base):
    __tablename__ = "model_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    access_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("access_logs.id", ondelete="SET NULL"), nullable=True)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_class: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_probability: Mapped[float] = mapped_column(Float, nullable=False)
    shap_values: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    access_log: Mapped["AccessLog"] = relationship("AccessLog", back_populates="model_scores")
