"""
UserSkill ORM model — aggregated skill strength per user/technology.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserSkill(Base):
    __tablename__ = "user_skills"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Graph hierarchy: Domain → Technology → Concept
    domain: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    technology: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    concept: Mapped[str] = mapped_column(String(200), nullable=True)

    # Strength: 0 – 100
    score: Mapped[float] = mapped_column(Float, default=0.0)
    level: Mapped[str] = mapped_column(String(50), default="Novice")  # Novice / Beginner / Intermediate / Advanced / Expert

    # Activity tracking
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="skills")  # noqa: F821

    def __repr__(self) -> str:
        return f"<UserSkill user={self.user_id} tech={self.technology!r} score={self.score:.1f}>"
