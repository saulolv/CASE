import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete, text, update
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import AgentRun, AvailabilitySlot, EnrichmentSnapshot, Event, Interaction, Lead, Meeting, SourceDocument
from .schemas import AgentDecision, AttendanceUpdate, EventQuestion, LeadCreate, LoginRequest, MeetingCreate, ReplyCreate
from .services import ProviderResult, compose, enrich, persist_decision, provider_for, score

app = FastAPI(title="Vigil AI", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
COOKIE_NAME = "vigil_session"
RATE_BUCKET: dict[str, list[float]] = {}


def secret() -> bytes:
    return os.getenv("SESSION_SECRET", "change-me-in-production").encode()


def make_token(username: str, role: str) -> str:
    raw = base64.urlsafe_b64encode(json.dumps({"sub": username, "role": role, "exp": int(time.time()) + 28800}).encode()).decode().rstrip("=")
    return raw + "." + hmac.new(secret(), raw.encode(), hashlib.sha256).hexdigest()


def current_session(vigil_session: Annotated[str | None, Cookie()] = None) -> dict:
    if not vigil_session or "." not in vigil_session:
        raise HTTPException(401, "Sessao necessaria.")
    raw, signature = vigil_session.rsplit(".", 1)
    if not hmac.compare_digest(signature, hmac.new(secret(), raw.encode(), hashlib.sha256).hexdigest()):
        raise HTTPException(401, "Sessao invalida.")
    try:
        payload = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
    except Exception as error:
        raise HTTPException(401, "Sessao invalida.") from error
    if payload.get("exp", 0) < time.time():
        raise HTTPException(401, "Sessao expirada.")
    return payload


def require_operator(user: Annotated[dict, Depends(current_session)]) -> dict:
    if user.get("role") != "operator":
        raise HTTPException(403, "Acao permitida apenas a operadores.")
    return user


def seed(db: Session) -> Event:
    event = db.query(Event).filter_by(name="Vigil Summit - Seguranca para a Era da IA").first()
    if not event:
        event = Event(name="Vigil Summit - Seguranca para a Era da IA", event_date=datetime.utcnow() + timedelta(days=14), location="Recife, PE", capacity=120)
        db.add(event); db.commit(); db.refresh(event)
    if not db.query(AvailabilitySlot).count():
        base = (datetime.utcnow() + timedelta(days=16)).replace(hour=10, minute=0, second=0, microsecond=0)
        for offset in (0, 2, 24, 26, 48):
            db.add(AvailabilitySlot(starts_at=base + timedelta(hours=offset)))
        db.commit()
    if not db.query(SourceDocument).filter_by(event_id=event.id).count():
        docs = [
            ("Agenda do Vigil Summit", "https://vigil.example/agenda", "Agenda executiva sobre resposta a incidentes, governanca de IA e risco de terceiros."),
            ("Palestrantes do Vigil Summit", "https://vigil.example/palestrantes", "Lideres de seguranca e tecnologia compartilham decisoes praticas para organizacoes brasileiras."),
        ]
        for title, url, excerpt in docs:
            db.add(SourceDocument(event_id=event.id, title=title, url=url, excerpt=excerpt, content_hash=hashlib.sha256(url.encode()).hexdigest()))
        db.commit()
    return event


def migrate_sqlite_schema() -> None:
    """Incremental local migration for databases created by the MVP before Alembic."""
    if not str(engine.url).startswith("sqlite"):
        return
    additions = {
        "leads": {
            "company_website": "VARCHAR",
            "eligible_for_processing": "BOOLEAN NOT NULL DEFAULT 0",
            "deleted_at": "DATETIME",
        },
        "agent_runs": {
            "provider": "VARCHAR NOT NULL DEFAULT 'demo'",
            "model": "VARCHAR",
            "run_id": "VARCHAR",
            "input_tokens": "INTEGER NOT NULL DEFAULT 0",
            "output_tokens": "INTEGER NOT NULL DEFAULT 0",
            "estimated_cost_usd": "FLOAT NOT NULL DEFAULT 0",
            "error": "TEXT",
            "fallback": "BOOLEAN NOT NULL DEFAULT 0",
            "evidence": "JSON NOT NULL DEFAULT '[]'",
        },
    }
    with engine.begin() as connection:
        for table, columns in additions.items():
            current = {row[1] for row in connection.execute(text(f"PRAGMA table_info({table})"))}
            for name, definition in columns.items():
                if name not in current:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        connection.execute(text("UPDATE agent_runs SET run_id = lower(hex(randomblob(16))) WHERE run_id IS NULL"))
        connection.execute(text("UPDATE leads SET eligible_for_processing = consent_email WHERE status != 'opted_out'"))


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_schema()
    with next(get_db()) as db:
        seed(db)


def mask(value: str | None) -> str | None:
    if not value: return value
    if "@" in value:
        name, host = value.split("@", 1)
        return name[:2] + "***@" + host
    return value[:3] + "***"


def lead_payload(db: Session, lead: Lead, role: str = "operator") -> dict:
    hidden = role == "viewer"
    enrichment = db.query(EnrichmentSnapshot).filter_by(lead_id=lead.id).order_by(EnrichmentSnapshot.created_at.desc()).first()
    interactions = db.query(Interaction).filter_by(lead_id=lead.id).order_by(Interaction.created_at).all()
    runs = db.query(AgentRun).filter_by(lead_id=lead.id).order_by(AgentRun.created_at.desc()).all()
    meeting = db.query(Meeting).filter_by(lead_id=lead.id).first()
    return {
        "id": lead.id, "name": mask(lead.name) if hidden else lead.name, "email": mask(lead.email) if hidden else lead.email,
        "phone": mask(lead.phone) if hidden else lead.phone, "company": lead.company, "company_website": lead.company_website,
        "job_title": lead.job_title, "challenge": "Contexto protegido" if hidden else lead.challenge, "consent_email": lead.consent_email,
        "eligible_for_processing": lead.eligible_for_processing, "status": lead.status, "attendance": lead.attendance,
        "demo_interest": lead.demo_interest, "fit_score": lead.fit_score, "intent_score": lead.intent_score,
        "engagement_score": lead.engagement_score, "total_score": lead.total_score, "tier": lead.tier, "created_at": lead.created_at,
        "enrichment": enrichment.data if enrichment else None,
        "interactions": [{"id": item.id, "direction": item.direction, "kind": item.kind, "content": "Conteudo protegido" if hidden else item.content, "created_at": item.created_at} for item in interactions],
        "runs": [{"run_id": item.run_id, "trigger": item.trigger, "decision": item.decision, "provider": item.provider, "model": item.model, "latency_ms": item.latency_ms, "estimated_cost_usd": item.estimated_cost_usd, "fallback": item.fallback, "evidence": item.evidence, "created_at": item.created_at} for item in runs],
        "meeting_id": meeting.id if meeting else None,
    }


def guard_rate(request: Request) -> None:
    now, key = time.time(), (request.client.host if request.client else "unknown")
    recent = [item for item in RATE_BUCKET.get(key, []) if now - item < 60]
    if len(recent) >= 8:
        raise HTTPException(429, "Aguarde um minuto antes de tentar novamente.")
    RATE_BUCKET[key] = recent + [now]


@app.get("/health")
def health():
    return {"status": "ok", "mode": os.getenv("AGENT_MODE", "demo")}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.post("/auth/session")
def login(payload: LoginRequest, response: Response):
    accounts = {
        os.getenv("DEMO_VIEWER_USERNAME", "viewer"): (os.getenv("DEMO_VIEWER_PASSWORD", "viewer-demo"), "viewer"),
        os.getenv("DEMO_OPERATOR_USERNAME", "operator"): (os.getenv("DEMO_OPERATOR_PASSWORD", "vigil-demo"), "operator"),
    }
    account = accounts.get(payload.username)
    if not account or not hmac.compare_digest(payload.password, account[0]):
        raise HTTPException(401, "Credenciais invalidas.")
    response.set_cookie(COOKIE_NAME, make_token(payload.username, account[1]), httponly=True, secure=os.getenv("COOKIE_SECURE", "false").lower() == "true", samesite="lax", max_age=28800)
    return {"username": payload.username, "role": account[1]}


@app.get("/auth/session")
def session(user: Annotated[dict, Depends(current_session)]):
    return {"username": user["sub"], "role": user["role"]}


@app.delete("/auth/session", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)


@app.post("/leads", status_code=201)
def create_lead(payload: LeadCreate, request: Request, db: Session = Depends(get_db)):
    guard_rate(request)
    event = seed(db)
    email = payload.email.lower()
    if db.query(Lead).filter_by(event_id=event.id, email=email, deleted_at=None).first():
        raise HTTPException(409, "Este e-mail ja esta inscrito no evento.")
    data = payload.model_dump()
    data["email"] = email
    data["company_website"] = str(data["company_website"]) if data.get("company_website") else None
    lead = Lead(event_id=event.id, **data, eligible_for_processing=payload.consent_email, status="enriching" if payload.consent_email else "consent_required")
    db.add(lead); db.commit(); db.refresh(lead)
    if payload.consent_email:
        profile = enrich(lead)
        db.add(EnrichmentSnapshot(lead_id=lead.id, data=profile.__dict__, source=profile.source, confidence=profile.confidence))
        lead.fit_score, lead.intent_score, lead.engagement_score, lead.total_score, lead.tier = score(lead, profile)
        lead.status = "confirmation_pending"; db.commit()
        persist_decision(db, lead, "registration", compose(lead, profile, "registration"))
    else:
        db.add(AgentRun(lead_id=lead.id, trigger="registration", decision={"action": "stop_communication", "rationale": ["Consentimento ausente"]}, mode="system", provider="system"))
        db.commit()
    return lead_payload(db, lead)


@app.get("/leads")
def leads(user: Annotated[dict, Depends(current_session)], db: Session = Depends(get_db)):
    return [lead_payload(db, item, user["role"]) for item in db.query(Lead).filter(Lead.deleted_at.is_(None)).order_by(Lead.total_score.desc()).all()]


@app.get("/leads/{lead_id}")
def lead(lead_id: str, user: Annotated[dict, Depends(current_session)], db: Session = Depends(get_db)):
    item = db.get(Lead, lead_id)
    if not item or item.deleted_at: raise HTTPException(404, "Lead nao encontrado.")
    return lead_payload(db, item, user["role"])


@app.delete("/leads/{lead_id}", status_code=204)
def erase_lead(lead_id: str, _: Annotated[dict, Depends(require_operator)], db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead or lead.deleted_at: raise HTTPException(404, "Lead nao encontrado.")
    db.execute(delete(Interaction).where(Interaction.lead_id == lead.id))
    db.execute(delete(EnrichmentSnapshot).where(EnrichmentSnapshot.lead_id == lead.id))
    lead.name, lead.email, lead.phone, lead.company, lead.company_website, lead.challenge = "Lead removido", "deleted-" + lead.id + "@invalid", None, "-", None, "-"
    lead.status, lead.deleted_at = "deleted", datetime.utcnow()
    db.add(AgentRun(lead_id=lead.id, trigger="privacy_delete", decision={"action": "anonymized", "rationale": ["PII removida"]}, mode="system", provider="system"))
    db.commit()


@app.post("/leads/{lead_id}/reply")
def reply(lead_id: str, payload: ReplyCreate, _: Annotated[dict, Depends(require_operator)], db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead or lead.deleted_at: raise HTTPException(404, "Lead nao encontrado.")
    if lead.status == "opted_out" or not lead.eligible_for_processing: raise HTTPException(409, "Este lead nao pode receber processamento ou comunicacao.")
    db.add(Interaction(lead_id=lead.id, direction="inbound", kind="lead_reply", content=payload.content))
    result = provider_for(db).classify(payload.content)
    intent = result.value.intent if not result.error and result.value.confidence >= .65 else "unknown"
    if intent == "opt_out":
        lead.status = "opted_out"; decision = AgentDecision(action="stop_communication", rationale=["Opt-out explicito"], confidence=1)
    elif intent == "confirm":
        lead.status = "confirmed"; lead.engagement_score = min(20, lead.engagement_score + 10); lead.total_score = lead.fit_score + lead.intent_score + lead.engagement_score
        decision = compose(lead, enrich(lead), "confirmed")
    elif intent == "meeting_interest":
        lead.status = "meeting_offered"; lead.intent_score = min(30, lead.intent_score + 10); lead.total_score = lead.fit_score + lead.intent_score + lead.engagement_score
        decision = AgentDecision(action="show_slots", rationale=["Intencao de agendamento detectada"], confidence=result.value.confidence)
    else:
        decision = AgentDecision(action="human_review", rationale=["Baixa confianca, timeout, erro ou schema invalido"], confidence=result.value.confidence, requires_human_review=True)
    db.commit(); persist_decision(db, lead, "reply", decision, result=result)
    return lead_payload(db, lead)


@app.post("/leads/{lead_id}/attendance")
def attendance(lead_id: str, payload: AttendanceUpdate, _: Annotated[dict, Depends(require_operator)], db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead or lead.deleted_at: raise HTTPException(404, "Lead nao encontrado.")
    if lead.status == "opted_out" or not lead.eligible_for_processing: raise HTTPException(409, "Este lead nao pode avancar no funil.")
    lead.attendance, lead.demo_interest = ("attended" if payload.attended else "no_show"), payload.demo_interest
    lead.status = "follow_up_pending" if payload.attended else "no_show"
    lead.engagement_score = min(20, lead.engagement_score + (10 if payload.attended else 0)); lead.total_score = lead.fit_score + lead.intent_score + lead.engagement_score; db.commit()
    trigger, profile = ("attendance" if payload.attended else "no_show"), enrich(lead)
    persist_decision(db, lead, trigger, compose(lead, profile, trigger))
    if payload.attended and payload.demo_interest:
        lead.status = "meeting_offered"; db.commit()
    return lead_payload(db, lead)


@app.get("/slots")
def slots(_: Annotated[dict, Depends(current_session)], db: Session = Depends(get_db)):
    return [{"id": item.id, "starts_at": item.starts_at, "duration_minutes": item.duration_minutes} for item in db.query(AvailabilitySlot).filter_by(is_available=True).order_by(AvailabilitySlot.starts_at).all()]


@app.post("/meetings", status_code=201)
def meeting(payload: MeetingCreate, _: Annotated[dict, Depends(require_operator)], db: Session = Depends(get_db)):
    lead = db.get(Lead, payload.lead_id)
    if not lead or lead.deleted_at: raise HTTPException(404, "Lead nao encontrado.")
    if lead.status == "opted_out" or not lead.eligible_for_processing: raise HTTPException(409, "Este lead nao pode agendar.")
    claimed = db.execute(update(AvailabilitySlot).where(AvailabilitySlot.id == payload.slot_id, AvailabilitySlot.is_available.is_(True)).values(is_available=False))
    if claimed.rowcount != 1:
        db.rollback(); raise HTTPException(409, "Este horario acabou de ser reservado.")
    try:
        slot = db.get(AvailabilitySlot, payload.slot_id)
        lead.status = "meeting_booked"; item = Meeting(lead_id=lead.id, slot_id=slot.id)
        db.add(item); db.add(Interaction(lead_id=lead.id, direction="outbound", kind="meeting_booked", content="Reuniao confirmada."))
        db.commit()
    except Exception as error:
        db.rollback(); raise HTTPException(409, "Nao foi possivel reservar este horario.") from error
    return {"id": item.id, "lead_id": lead.id, "slot_id": slot.id, "status": "booked"}


@app.post("/event/answer")
def answer_event(payload: EventQuestion, _: Annotated[dict, Depends(current_session)], db: Session = Depends(get_db)):
    docs = db.query(SourceDocument).all()
    if not docs: return {"answer": "Sem evidencia suficiente; encaminhe para revisao humana.", "requires_human_review": True, "citations": []}
    return {"answer": docs[0].excerpt, "requires_human_review": False, "citations": [{"title": item.title, "url": item.url, "excerpt": item.excerpt} for item in docs[:2]]}


@app.get("/dashboard")
def dashboard(user: Annotated[dict, Depends(current_session)], db: Session = Depends(get_db)):
    items = db.query(Lead).filter(Lead.deleted_at.is_(None)).all(); runs = db.query(AgentRun).all()
    metrics = {"registered": len(items), "confirmed": sum(item.status == "confirmed" for item in items), "attended": sum(item.attendance == "attended" for item in items), "no_show": sum(item.attendance == "no_show" for item in items), "meetings": db.query(Meeting).count(), "human_review": sum(item.decision.get("action") == "human_review" for item in runs), "fallback": sum(item.fallback for item in runs), "avg_latency_ms": round(sum(item.latency_ms for item in runs) / len(runs)) if runs else 0, "estimated_cost_usd": round(sum(item.estimated_cost_usd for item in runs), 4)}
    return {"metrics": metrics, "leads": [lead_payload(db, item, user["role"]) for item in sorted(items, key=lambda item: -item.total_score)]}
