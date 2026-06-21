import os
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from .models import AgentRun, Interaction, Lead
from .providers import ProviderResult, provider_for
from .schemas import AgentDecision, IntentClassification

TARGET_ROLES = ("ciso", "cto", "diretor", "director", "head", "gerente", "manager", "risk", "risco")
SECURITY_TERMS = ("seguran", "vulnerab", "lgpd", "compliance", "iso", "soc", "risco", "amea")


@dataclass
class Profile:
    industry: str
    estimated_size: str
    seniority: str
    domain: str
    security_signal: str
    source: str = "demo_catalog"
    confidence: float = 0.78


def enrich(lead: Lead) -> Profile:
    """Deterministic, allowlisted demo enrichment; no open-web discovery or commercial scraping."""
    company = lead.company.lower()
    if "fin" in company or "bank" in company:
        industry, signal = "Serviços financeiros", "LGPD e risco de terceiros"
    elif "saude" in company or "health" in company:
        industry, signal = "Saúde", "Governança de dados sensíveis"
    elif "ind" in company or "factory" in company:
        industry, signal = "Indústria", "Exposição de tecnologia operacional"
    else:
        industry, signal = "Tecnologia B2B", "Postura contínua de segurança"
    domain = re.sub(r"[^a-z0-9]", "", company.split()[0]) + ".com.br"
    seniority = "executivo" if any(role in lead.job_title.lower() for role in TARGET_ROLES) else "gestão"
    return Profile(industry, lead.company_size, seniority, domain, signal)


def score(lead: Lead, profile: Profile) -> tuple[float, float, float, float, str]:
    role_points = 20 if any(role in lead.job_title.lower() for role in TARGET_ROLES) else 8
    size_points = 20 if lead.company_size in {"201-500", "501-1000", "1000+"} else 5
    pain_points = 10 if any(term in lead.challenge.lower() for term in SECURITY_TERMS) else 4
    fit, intent, engagement = role_points + size_points + pain_points, (10 if len(lead.challenge.strip()) > 20 else 5), 0
    total = fit + intent + engagement
    tier = "hot" if total >= 75 else "priority" if total >= 60 else "qualified" if total >= 40 else "nurture"
    return float(fit), float(intent), float(engagement), float(total), tier


def compose(lead: Lead, profile: Profile, trigger: str) -> AgentDecision:
    if not lead.eligible_for_processing or lead.status == "opted_out":
        return AgentDecision(action="stop_communication", message=None, rationale=["Consentimento ausente ou opt-out"], confidence=1)
    if trigger == "registration":
        return AgentDecision(
            action="send_confirmation",
            message=(
                f"Olá, {lead.name.split()[0]}. No Vigil Summit vamos discutir "
                f"{profile.security_signal.lower()} com foco em decisões executivas. Posso confirmar sua presença?"
            ),
            rationale=["Consentimento ativo", "Perfil enriquecido", "Confirmação pré-evento"],
            confidence=0.91,
        )
    if trigger == "confirmed":
        return AgentDecision(
            action="send_agenda",
            message=f"Excelente, {lead.name.split()[0]}. Vou enviar uma trilha alinhada a {lead.challenge.lower()}.",
            rationale=["Presença confirmada", "Agenda personalizada"],
            confidence=0.90,
        )
    if trigger == "attendance" and lead.demo_interest:
        return AgentDecision(
            action="offer_meeting",
            message=f"Obrigado por participar, {lead.name.split()[0]}. Posso sugerir horários para uma conversa de 30 minutos?",
            rationale=["Presença", "Interesse em demo"],
            confidence=0.94,
        )
    if trigger == "attendance":
        return AgentDecision(
            action="send_recap",
            message=f"Obrigado pela presença, {lead.name.split()[0]}. Posso compartilhar um resumo ligado ao seu desafio?",
            rationale=["Presença", "Follow-up contextual"],
            confidence=0.86,
        )
    if trigger == "no_show":
        return AgentDecision(
            action="send_no_show_recap",
            message=f"Sentimos sua falta, {lead.name.split()[0]}. Posso compartilhar os aprendizados do Vigil Summit?",
            rationale=["No-show", "Follow-up leve"],
            confidence=0.85,
        )
    return AgentDecision(action="human_review", message=None, rationale=["Sem playbook determinístico"], confidence=0.45, requires_human_review=True)


def persist_decision(db: Session, lead: Lead, trigger: str, decision: AgentDecision, *, result: ProviderResult | None = None) -> AgentDecision:
    result = result or ProviderResult(IntentClassification(intent="system", confidence=1), "demo")
    allowed = lead.eligible_for_processing and lead.status != "opted_out" and not decision.requires_human_review
    if decision.message and allowed:
        db.add(Interaction(lead_id=lead.id, direction="outbound", kind=decision.action, content=decision.message))
    db.add(
        AgentRun(
            lead_id=lead.id,
            trigger=trigger,
            decision=decision.model_dump(),
            mode=os.getenv("AGENT_MODE", "demo"),
            provider=result.provider,
            model=result.model,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            estimated_cost_usd=result.estimated_cost_usd,
            error=result.error,
            fallback=result.fallback,
            evidence=result.value.evidence,
        )
    )
    db.commit()
    return decision
