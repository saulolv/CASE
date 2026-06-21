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
- Senha do console: `vigil-demo`
- API: `http://localhost:8000/docs`

## Roteiro curto

1. Inscreva um CISO, CTO ou Diretor de TI com e-mail corporativo.
2. Entre no console e abra o dossiê criado.
3. Use `Confirmar presença`, depois `Presente + demo`.
4. Veja os horários e reserve uma reunião.
5. Cadastre outro lead e use `Opt-out` para demonstrar o guardrail.

O modo padrão é demonstrativo: enriquecimento e mensagens são determinísticos e persistidos. Apollo e Claude entram como providers substituíveis quando as credenciais estiverem disponíveis.
