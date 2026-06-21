# Execução do backend

Para executar a versão funcional da demo, use o entrypoint normalizado:

```powershell
python -m pip install -r requirements-runtime.txt
uvicorn app.entrypoint:app --reload --port 8000
```

O banco padrão é SQLite local. No Render, defina `DATABASE_URL` com a URL PostgreSQL antes do deploy.
