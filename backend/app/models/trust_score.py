import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.alert import Alert

class TrustScore(Base):
    __tablename__ = "trust_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_component: Mapped[float] = mapped_column(Float, nullable=False)
    risk_component: Mapped[float] = mapped_column(Float, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    model_score_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_scores.id", ondelete="SET NULL"), nullable=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, default=uuid.UUID("9f9bbf10-e3f3-470b-85be-587265bf02ab"))


    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trust_scores")
    # TODO: This relationship depends on the Alert model written next
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="trust_score")
