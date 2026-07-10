import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.alert import Alert

class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    threshold_min: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_max: Mapped[float] = mapped_column(Float, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    # TODO: This relationship depends on the Alert model written next
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="policy_rule")
