from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    company: str = Field(min_length=2, max_length=120)
    company_website: HttpUrl | None = None
    job_title: str = Field(min_length=2, max_length=120)
    company_size: str
    challenge: str = Field(min_length=8, max_length=800)
    consent_email: bool


class ReplyCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1200)


class AttendanceUpdate(BaseModel):
    attended: bool
    demo_interest: bool = False


class MeetingCreate(BaseModel):
    lead_id: str
    slot_id: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class EventQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=600)


class AgentDecision(BaseModel):
    action: str
    channel: str = "simulator"
    message: str | None = None
    rationale: list[str]
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool = False


class IntentClassification(BaseModel):
    intent: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = []


class EvidenceEnrichment(BaseModel):
    industry: str
    estimated_size: str
    seniority: str
    domain: str
    security_signal: str
    source: str
    confidence: float = Field(ge=0, le=1)


class SlotOut(BaseModel):
    id: str
    starts_at: datetime
    duration_minutes: int
