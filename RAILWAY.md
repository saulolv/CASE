# Deploy no Railway

Guia para publicar o Vigil AI com **domínio único**: o frontend faz proxy de `/backend/*` para o serviço FastAPI, mantendo cookies HttpOnly no mesmo domínio.

## Arquitetura

```
Usuário → Frontend (Next.js, público)
              ↓ rewrite /backend/*
          Backend (FastAPI, interno ou público)
              ↓
          PostgreSQL (plugin Railway)
              ↓
          Gemini API (AGENT_MODE=gemini)
```

## 1. Criar projeto

1. Acesse [railway.app](https://railway.app) e crie um projeto.
2. Adicione **PostgreSQL** (Database → Add PostgreSQL).
3. Adicione **dois serviços** a partir do mesmo repositório:
   - **backend** — root directory: `backend`
   - **frontend** — root directory: `frontend`

## 2. Backend

O arquivo [`backend/railway.toml`](backend/railway.toml) define o start command e healthcheck em `/health`.

### Variáveis de ambiente

| Variável | Valor |
|----------|-------|
| `DATABASE_URL` | Referência ao PostgreSQL (`${{Postgres.DATABASE_URL}}`) |
| `AGENT_MODE` | `gemini` |
| `GEMINI_API_KEY` | Chave do [Google AI Studio](https://aistudio.google.com/api-keys) |
| `GEMINI_MODEL` | `gemini-2.0-flash` |
| `AGENT_CALL_LIMIT` | `20` |
| `SESSION_SECRET` | String aleatória longa (32+ caracteres) |
| `DEMO_OPERATOR_USERNAME` | `operator` (ou outro) |
| `DEMO_OPERATOR_PASSWORD` | Senha para avaliadores |
| `DEMO_VIEWER_USERNAME` | `viewer` |
| `DEMO_VIEWER_PASSWORD` | Senha viewer |
| `FRONTEND_ORIGIN` | URL pública do frontend (ex: `https://vigil-ai-production.up.railway.app`) |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `lax` |

### Verificar

- `GET https://<backend-url>/health` → `{"status":"ok","mode":"gemini"}`
- `GET https://<backend-url>/ready` → `{"status":"ready"}`

## 3. Frontend

O arquivo [`frontend/railway.toml`](frontend/railway.toml) executa `npm run build && npm run start`.

### Variáveis de ambiente

| Variável | Valor |
|----------|-------|
| `NEXT_PUBLIC_USE_API_PROXY` | `true` |
| `BACKEND_INTERNAL_URL` | URL do serviço backend (preferir rede interna Railway: `http://backend.railway.internal:PORT` ou URL pública do backend) |
| `PORT` | Injetado pelo Railway |

Com proxy ativo, o frontend chama `/backend/leads`, `/backend/auth/session`, etc., no mesmo domínio.

## 4. Trocar para Anthropic (Claude)

No backend, altere:

```env
AGENT_MODE=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

Nenhuma alteração de código é necessária — o padrão Strategy resolve o provider automaticamente.

## 5. Teste end-to-end

1. Abra a URL pública do **frontend**.
2. Cadastre um lead na landing com consentimento.
3. Acesse `/ops` e faça login com as credenciais de operador.
4. Simule reply: `Confirmo minha presença`.
5. Verifique no dossiê que `AgentRun` registrou `provider: gemini` (ou `anthropic`).
6. Marque presença + demo e reserve um horário.

## 6. Acesso para avaliação

- Documentação completa: [`DOCUMENTACAO_TECNICA.md`](DOCUMENTACAO_TECNICA.md)
- Para acesso temporário: `ramon@pareto.io`

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Cookie de sessão não persiste | Confirme `NEXT_PUBLIC_USE_API_PROXY=true` e que o frontend usa `/backend` |
| CORS error | Defina `FRONTEND_ORIGIN` no backend com a URL exata do frontend |
| DB connection failed | Verifique se `DATABASE_URL` usa `postgresql://` (normalizado automaticamente em `db.py`) |
| LLM cai em demo | Verifique `GEMINI_API_KEY` e limite `AGENT_CALL_LIMIT` |
