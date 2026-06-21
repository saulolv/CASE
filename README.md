# Vigil AI

Aplicacao de demonstracao para o Vigil Summit: uma landing publica de inscricao e um console B2B de triagem, decisao segura e auditoria.

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
- Operador local: configure `DEMO_OPERATOR_USERNAME` e `DEMO_OPERATOR_PASSWORD` no backend.

## Principios

- A IA interpreta texto; regras deterministicas autorizam estados e comunicacao.
- Consentimento ausente e opt-out bloqueiam qualquer acao automatica.
- A sessao e um cookie HttpOnly emitido pelo backend; a senha nao vai para o bundle.
- Viewer recebe PII mascarada; operador recebe o dossie completo.
- O modo demo nao usa chamadas externas. Anthropic permanece opcional e limitado a 20 chamadas persistidas por ambiente.

## Validacao

```powershell
python -m pytest
cd frontend; npm run build
```
