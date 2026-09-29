# Runbook Operacional

## Checks locais

```powershell
python -m compileall .
python manage.py check
python manage.py makemigrations --check
pytest
ruff check .
```

## Deploy demo

Arquivos de deploy preparados:

- `Procfile` — coleta estáticos, aplica migrations e inicia Gunicorn.
- `runtime.txt` — fixa Python 3.12.
- `railway.json` — healthcheck em `/healthz/`.

Variáveis mínimas para um ambiente demo:

```text
DJANGO_SECRET_KEY=<gerar valor seguro>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<dominio-demo>
CSRF_TRUSTED_ORIGINS=https://<dominio-demo>
DATABASE_URL=<postgres-provider-url>
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
```

Após o primeiro deploy demo:

```powershell
python manage.py createsuperuser
python manage.py seed_demo
```

Antes de production real:

- validar variáveis de ambiente;
- rodar migrations em staging;
- testar login, cadastro e dashboard;
- testar criação de lançamento balanceado;
- testar rejeição de lançamento desbalanceado;
- confirmar backup e restore;
- confirmar que nenhum secret aparece em logs.

