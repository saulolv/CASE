from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uid() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.utcnow()


class Event(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String, unique=True)
    event_date: Mapped[datetime] = mapped_column(DateTime)
    location: Mapped[str] = mapped_column(String)
    capacity: Mapped[int] = mapped_column(Integer, default=120)


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (UniqueConstraint("event_id", "email", name="uq_lead_event_email"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, index=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    company: Mapped[str] = mapped_column(String)
    company_website: Mapped[str | None] = mapped_column(String, nullable=True)
    job_title: Mapped[str] = mapped_column(String)
    company_size: Mapped[str] = mapped_column(String)
    challenge: Mapped[str] = mapped_column(Text)
    consent_email: Mapped[bool] = mapped_column(Boolean, default=False)
    eligible_for_processing: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String, default="registered", index=True)
    attendance: Mapped[str] = mapped_column(String, default="unknown")
    demo_interest: Mapped[bool] = mapped_column(Boolean, default=False)
    fit_score: Mapped[float] = mapped_column(Float, default=0)
    intent_score: Mapped[float] = mapped_column(Float, default=0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0)
    total_score: Mapped[float] = mapped_column(Float, default=0)
    tier: Mapped[str] = mapped_column(String, default="nurture")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class EnrichmentSnapshot(Base):
    __tablename__ = "enrichment_snapshots"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    data: Mapped[dict] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class SourceDocument(Base):
    __tablename__ = "source_documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), index=True)
    url: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    excerpt: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    content_hash: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Interaction(Base):
    __tablename__ = "interactions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    direction: Mapped[str] = mapped_column(String)
    channel: Mapped[str] = mapped_column(String, default="simulator")
    kind: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    lead_id: Mapped[str | None] = mapped_column(ForeignKey("leads.id"), nullable=True, index=True)
    trigger: Mapped[str] = mapped_column(String)
    decision: Mapped[dict] = mapped_column(JSON)
    mode: Mapped[str] = mapped_column(String)
    provider: Mapped[str] = mapped_column(String, default="demo")
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    run_id: Mapped[str] = mapped_column(String, default=uid, unique=True, index=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)


class Meeting(Base):
    __tablename__ = "meetings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    slot_id: Mapped[str] = mapped_column(ForeignKey("availability_slots.id"), unique=True)
    status: Mapped[str] = mapped_column(String, default="booked")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
