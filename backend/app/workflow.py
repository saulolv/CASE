from sqlalchemy.orm import Session

from .models import AgentRun, EnrichmentSnapshot, Interaction, Lead
from .providers import provider_for
from .schemas import AgentDecision
from .services import compose, enrich, persist_decision, score


def on_registration(db: Session, lead: Lead) -> None:
    if not lead.consent_email:
        db.add(
            AgentRun(
                lead_id=lead.id,
                trigger="registration",
                decision={"action": "stop_communication", "rationale": ["Consentimento ausente"]},
                mode="system",
                provider="system",
            )
        )
        db.commit()
        return
    profile = enrich(lead)
    db.add(EnrichmentSnapshot(lead_id=lead.id, data=profile.__dict__, source=profile.source, confidence=profile.confidence))
    lead.fit_score, lead.intent_score, lead.engagement_score, lead.total_score, lead.tier = score(lead, profile)
    lead.status = "confirmation_pending"
    db.commit()
    persist_decision(db, lead, "registration", compose(lead, profile, "registration"))


def on_reply(db: Session, lead: Lead, content: str) -> None:
    db.add(Interaction(lead_id=lead.id, direction="inbound", kind="lead_reply", content=content))
    result = provider_for(db).classify(content)
    intent = result.value.intent if not result.error and result.value.confidence >= 0.65 else "unknown"
    if intent == "opt_out":
        lead.status = "opted_out"
        decision = AgentDecision(action="stop_communication", rationale=["Opt-out explicito"], confidence=1)
    elif intent == "confirm":
        lead.status = "confirmed"
        lead.engagement_score = min(20, lead.engagement_score + 10)
        lead.total_score = lead.fit_score + lead.intent_score + lead.engagement_score
        decision = compose(lead, enrich(lead), "confirmed")
    elif intent == "meeting_interest":
        lead.status = "meeting_offered"
        lead.intent_score = min(30, lead.intent_score + 10)
        lead.total_score = lead.fit_score + lead.intent_score + lead.engagement_score
        decision = AgentDecision(
            action="show_slots",
            rationale=["Intencao de agendamento detectada"],
            confidence=result.value.confidence,
        )
    else:
        decision = AgentDecision(
            action="human_review",
            rationale=["Baixa confianca, timeout, erro ou schema invalido"],
            confidence=result.value.confidence,
            requires_human_review=True,
        )
    db.commit()
    persist_decision(db, lead, "reply", decision, result=result)


def on_attendance(db: Session, lead: Lead, attended: bool, demo_interest: bool) -> None:
    lead.attendance = "attended" if attended else "no_show"
    lead.demo_interest = demo_interest
    lead.status = "follow_up_pending" if attended else "no_show"
    lead.engagement_score = min(20, lead.engagement_score + (10 if attended else 0))
    lead.total_score = lead.fit_score + lead.intent_score + lead.engagement_score
    db.commit()
    trigger = "attendance" if attended else "no_show"
    profile = enrich(lead)
    persist_decision(db, lead, trigger, compose(lead, profile, trigger))
    if attended and demo_interest:
        lead.status = "meeting_offered"
        db.commit()
