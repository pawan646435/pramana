"""
SQLAlchemy 2.0 declarative models, async-compatible.

Historical persistence only - the compute/generation/verification layers
never import from here. Rows are written by the API route layer after a
pydantic result already exists, never the other way around.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class EvalRun(Base):
    """One row per full eval harness run (POST /api/eval/run)."""

    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column()
    avg_ungrounded_hallucination_rate: Mapped[float] = mapped_column()
    avg_grounded_hallucination_rate: Mapped[float] = mapped_column()
    relative_reduction: Mapped[float] = mapped_column()
    num_cases: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cases: Mapped[list["EvalCase"]] = relationship(back_populates="eval_run", cascade="all, delete-orphan")


class EvalCase(Base):
    """One row per individual golden-set chart within an eval run."""

    __tablename__ = "eval_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eval_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_runs.id", ondelete="CASCADE"))

    birth_date: Mapped[str] = mapped_column()
    birth_time: Mapped[str] = mapped_column()
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    timezone_offset_hours: Mapped[float] = mapped_column()

    ungrounded_hallucination_rate: Mapped[float] = mapped_column()
    grounded_hallucination_rate: Mapped[float] = mapped_column()
    ungrounded_narrative: Mapped[str] = mapped_column(Text)
    grounded_narrative: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    eval_run: Mapped["EvalRun"] = relationship(back_populates="cases")


class GenerationLog(Base):
    """One row per single generate-and-verify call (POST /api/generate/narrative)."""

    __tablename__ = "generation_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    birth_date: Mapped[str] = mapped_column()
    birth_time: Mapped[str] = mapped_column()
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    timezone_offset_hours: Mapped[float] = mapped_column()

    provider: Mapped[str] = mapped_column()
    model_used: Mapped[str] = mapped_column()
    narrative: Mapped[str] = mapped_column(Text)

    hallucination_rate: Mapped[float] = mapped_column()
    num_claims: Mapped[int] = mapped_column()
    num_grounded_claims: Mapped[int] = mapped_column()
    num_ungrounded_claims: Mapped[int] = mapped_column()
    num_unverifiable_claims: Mapped[int] = mapped_column()

    claims_detail: Mapped[list[dict]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
