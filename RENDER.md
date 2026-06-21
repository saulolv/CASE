# Deploy no Render

Guia para publicar o Vigil AI no [Render](https://render.com) (plano gratuito). O frontend faz proxy de `/backend/*` para o FastAPI, mantendo cookies HttpOnly no mesmo domínio.

## Arquitetura

```
Usuário → Frontend (Next.js, onrender.com)
              ↓ rewrite /backend/*
          Backend (FastAPI, onrender.com)
              ↓
          PostgreSQL (Render)
              ↓
          Gemini API (AGENT_MODE=gemini)
```

## Opção A — Blueprint (recomendado)

1. Faça push do repositório para GitHub/GitLab.
2. Acesse [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**.
3. Conecte o repositório — o Render detecta `[render.yaml](render.yaml)` na raiz.
4. Após o preview, defina os secrets que o Blueprint marca como `sync: false`:
  - `GEMINI_API_KEY` — chave do [Google AI Studio](https://aistudio.google.com/api-keys)
  - `DEMO_OPERATOR_PASSWORD` — senha para avaliadores (ex: `vigil-demo`)
  - `DEMO_VIEWER_PASSWORD` — senha viewer (ex: `viewer-demo`)
5. Clique em **Apply** e aguarde o deploy dos 3 recursos (PostgreSQL + backend + frontend).
6. Após o deploy, no serviço **vigil-backend**, defina `FRONTEND_ORIGIN` com a URL pública do frontend (ex: `https://vigil-frontend.onrender.com`).

O Blueprint configura automaticamente:

- `DATABASE_URL` no backend
- `BACKEND_INTERNAL_URL` no frontend → URL do backend
- `SESSION_SECRET` gerado automaticamente

Defina manualmente após o primeiro deploy:

- `FRONTEND_ORIGIN` no backend → URL do frontend (necessário para CORS)

## Opção B — Manual

### 1. PostgreSQL

1. **New** → **PostgreSQL** → plano **Free**.
2. Anote a **Internal Database URL** ou **External Database URL**.

### 2. Backend

1. **New** → **Web Service** → conecte o repositório.
2. Configuração:


| Campo             | Valor                                                    |
| ----------------- | -------------------------------------------------------- |
| Root Directory    | `backend`                                                |
| Runtime           | Python 3                                                 |
| Build Command     | `pip install -r requirements.txt`                        |
| Start Command     | `uvicorn app.entrypoint:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health`                                                |


1. Variáveis de ambiente:


| Variável                 | Valor                                           |
| ------------------------ | ----------------------------------------------- |
| `DATABASE_URL`           | URL do PostgreSQL Render                        |
| `AGENT_MODE`             | `gemini`                                        |
| `GEMINI_API_KEY`         | Chave do AI Studio                              |
| `GEMINI_MODEL`           | `gemini-2.0-flash`                              |
| `AGENT_CALL_LIMIT`       | `20`                                            |
| `SESSION_SECRET`         | String aleatória longa (32+ caracteres)         |
| `DEMO_OPERATOR_USERNAME` | `operator`                                      |
| `DEMO_OPERATOR_PASSWORD` | Senha para avaliadores                          |
| `DEMO_VIEWER_USERNAME`   | `viewer`                                        |
| `DEMO_VIEWER_PASSWORD`   | Senha viewer                                    |
| `FRONTEND_ORIGIN`        | URL do frontend (definir após criar o frontend) |
| `COOKIE_SECURE`          | `true`                                          |
| `COOKIE_SAMESITE`        | `lax`                                           |


### 3. Frontend

1. **New** → **Web Service** → mesmo repositório.
2. Configuração:


| Campo          | Valor                          |
| -------------- | ------------------------------ |
| Root Directory | `frontend`                     |
| Runtime        | Node                           |
| Build Command  | `npm install && npm run build` |
| Start Command  | `npm start`                    |


1. Variáveis de ambiente:


| Variável                    | Valor                                                             |
| --------------------------- | ----------------------------------------------------------------- |
| `NEXT_PUBLIC_USE_API_PROXY` | `true`                                                            |
| `BACKEND_INTERNAL_URL`      | URL pública do backend (ex: `https://vigil-backend.onrender.com`) |


1. Volte ao backend e atualize `FRONTEND_ORIGIN` com a URL do frontend (ex: `https://vigil-frontend.onrender.com`).

## Verificar deploy

- `GET https://<backend>/health` → `{"status":"ok","mode":"gemini"}`
- `GET https://<backend>/ready` → `{"status":"ready"}`
- Abra a URL do **frontend** → landing carrega
- Console `/ops` → login funciona

## Plano gratuito — o que esperar


| Recurso         | Comportamento                                                         |
| --------------- | --------------------------------------------------------------------- |
| Web services    | Spin-down após ~15 min sem tráfego; primeiro acesso pode levar 30–60s |
| PostgreSQL free | Disponível por 90 dias; depois migrar para paid ou outro host         |
| Builds          | Limites de minutos/mês no free tier                                   |


Para demo do case, o free tier é suficiente — avise avaliadores sobre o cold start.

## Trocar para Anthropic (Claude)

No serviço **vigil-backend**, altere:

```env
AGENT_MODE=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

Nenhuma alteração de código — o padrão Strategy resolve automaticamente.

## Teste end-to-end

1. Abra a URL pública do **frontend**.
2. Cadastre um lead na landing com consentimento.
3. Acesse `/ops` e faça login (`operator` / sua senha).
4. Simule reply: `Confirmo minha presença`.
5. Verifique no dossiê `AgentRun` com `provider: gemini`.
6. Marque presença + demo e reserve um horário.

## Acesso para avaliação

- Documentação: `[DOCUMENTACAO_TECNICA.md](DOCUMENTACAO_TECNICA.md)`
- Contato temporário: `ramon@pareto.io`

## Troubleshooting


| Problema                             | Solução                                                                     |
| ------------------------------------ | --------------------------------------------------------------------------- |
| Cold start lento                     | Normal no free tier; aguarde ~1 min no primeiro acesso                      |
| Cookie de sessão não persiste        | `NEXT_PUBLIC_USE_API_PROXY=true`; frontend usa `/backend`                   |
| CORS error                           | `FRONTEND_ORIGIN` no backend = URL exata do frontend                        |
| DB connection failed                 | `DATABASE_URL` com `postgresql://` (normalizado em `db.py`)                 |
| LLM cai em demo                      | Verifique `GEMINI_API_KEY` e `AGENT_CALL_LIMIT`                             |
| Blueprint falha em `FRONTEND_ORIGIN` | Deploy backend primeiro manualmente, ou aplique Blueprint e ajuste env vars |


