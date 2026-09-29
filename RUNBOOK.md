# Runbook Operacional

## Checks locais

```powershell
python -m compileall .
python manage.py check
python manage.py makemigrations --check
pytest
ruff check .
```

## Deploy futuro

Antes de production:

- validar variáveis de ambiente;
- rodar migrations em staging;
- testar login, cadastro e dashboard;
- testar criação de lançamento balanceado;
- testar rejeição de lançamento desbalanceado;
- confirmar backup e restore;
- confirmar que nenhum secret aparece em logs.

