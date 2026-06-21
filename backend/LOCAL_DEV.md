# CORS no ambiente local

Use o entrypoint local abaixo quando a landing estiver em desenvolvimento:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.dev_entrypoint:app --port 8000
```

Ele aceita `localhost:3000`, `127.0.0.1:3000` e o IP local apresentado pelo Next.js.
