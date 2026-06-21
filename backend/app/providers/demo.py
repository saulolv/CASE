from ..schemas import IntentClassification
from .base import ProviderResult


class DemoProvider:
    name = "demo"

    def classify(self, content: str) -> ProviderResult:
        message = content.lower()
        if any(word in message for word in ("descadastro", "remova", "parar", "unsubscribe", "não quero", "nao quero")):
            value = IntentClassification(intent="opt_out", confidence=0.99, evidence=["explicit opt-out"])
        elif any(word in message for word in ("confirmo", "confirmada", "estarei", "vou", "presença", "presenca")):
            value = IntentClassification(intent="confirm", confidence=0.92, evidence=["attendance phrase"])
        elif any(word in message for word in ("demo", "reuni", "horário", "horario", "agenda")):
            value = IntentClassification(intent="meeting_interest", confidence=0.88, evidence=["meeting phrase"])
        elif any(word in message for word in ("dúvida", "duvida", "onde", "quando", "programa")):
            value = IntentClassification(intent="question", confidence=0.80, evidence=["event question"])
        else:
            value = IntentClassification(intent="unknown", confidence=0.30, evidence=[])
        return ProviderResult(value=value, provider=self.name)
