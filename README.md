# Vigil AI

Aplicação de demonstração para o Vigil Summit: landing pública de inscrição e console B2B de triagem, decisão segura e auditoria.

**Documentação completa do case:** [`DOCUMENTACAO_TECNICA.md`](DOCUMENTACAO_TECNICA.md)  
**Deploy Render:** [`RENDER.md`](RENDER.md)

## Executar localmente

Em um terminal:

```powershell
cd backend
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.entrypoint:app --port 8000
```

Em outro:

```powershell
cd frontend
npm install
npm run dev
```

- Landing: http://localhost:3000
- Console: http://localhost:3000/ops
- API: http://localhost:8000/docs
- Operador local: `operator` / `vigil-demo` (configurável no `.env`)

## Modos do agente (Strategy LLM)

| `AGENT_MODE` | Provider | Credencial |
|--------------|----------|------------|
| `demo` | Keywords locais | nenhuma |
| `gemini` | Google Gemini | `GEMINI_API_KEY` |
| `anthropic` | Claude (preferência do case) | `ANTHROPIC_API_KEY` |

Para usar Gemini localmente, defina no `backend/.env`:

```env
AGENT_MODE=gemini
GEMINI_API_KEY=<sua-chave>
```

Chave gratuita: [Google AI Studio](https://aistudio.google.com/api-keys)

Para Claude, basta trocar `AGENT_MODE=anthropic` e `ANTHROPIC_API_KEY` — sem alteração de código.

## Princípios

- A IA interpreta texto; regras determinísticas autorizam estados e comunicação.
- Orquestração nativa em `workflow.py` — sem LangChain; SDK nativo para LLM.
- Consentimento ausente e opt-out bloqueiam qualquer ação automática.
- Sessão via cookie HttpOnly; senha não vai para o bundle.
- Viewer recebe PII mascarada; operador recebe o dossiê completo.
- Limite de 20 chamadas LLM por provider (`AGENT_CALL_LIMIT`).

## Validação

```powershell
cd backend
python -m pytest
cd ../frontend
npm run build
```
