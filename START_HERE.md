# Comece aqui

## Demo local

Abra dois terminais na raiz do projeto.

```powershell
# Terminal 1
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime.txt
.\.venv\Scripts\python.exe -m uvicorn app.entrypoint:app --port 8000
```

```powershell
# Terminal 2
cd frontend
npm install
npm run dev
```

- Landing: `http://localhost:3000`
- Console: `http://localhost:3000/ops`
- Senha do console: `vigil-demo` (usuário `operator`)
- API: `http://localhost:8000/docs`

## Agente com Gemini

Copie `backend/.env.example` para `backend/.env` e configure:

```env
AGENT_MODE=gemini
GEMINI_API_KEY=<sua-chave-do-ai-studio>
```

Sem chave, o sistema usa fallback `demo` (keywords locais).

Para Claude (preferência do case): `AGENT_MODE=anthropic` + `ANTHROPIC_API_KEY`.

## Roteiro curto

1. Inscreva um CISO, CTO ou Diretor de TI com e-mail corporativo.
2. Entre no console e abra o dossiê criado.
3. Simule reply: `Confirmo minha presença`.
4. Use `Presente + demo`, veja horários e reserve uma reunião.
5. Cadastre outro lead e simule `Por favor, remova meu contato` (opt-out).

## Documentação

- Case completo: [`DOCUMENTACAO_TECNICA.md`](DOCUMENTACAO_TECNICA.md)
- Deploy: [`RAILWAY.md`](RAILWAY.md)

O funil usa orquestração nativa (`workflow.py`) + playbooks determinísticos. A LLM (Gemini ou Claude) classifica apenas a intenção das respostas — troca de provider via `AGENT_MODE`, sem mudar código.
