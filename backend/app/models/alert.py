import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.trust_score import TrustScore
    from app.models.policy_rule import PolicyRule

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trust_score_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trust_scores.id", ondelete="SET NULL"), nullable=True)
    policy_rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("policy_rules.id", ondelete="SET NULL"), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open")
    reviewed_by: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, default=uuid.UUID("9f9bbf10-e3f3-470b-85be-587265bf02ab"))


    # Relationships
    trust_score: Mapped["TrustScore"] = relationship("TrustScore", back_populates="alerts")
    policy_rule: Mapped["PolicyRule"] = relationship("PolicyRule", back_populates="alerts")
