# Segurança

## Princípios

- Nenhum secret no Git.
- Produção sempre com `DJANGO_DEBUG=False`.
- Acesso administrativo restrito.
- Logs sem dados sensíveis.
- Auditoria para ações relevantes.

## Dados sensíveis

O sistema pode armazenar dados empresariais, contábeis e financeiros. Antes de produção real, validar:

- base legal LGPD;
- política de privacidade;
- retenção e exclusão;
- backup criptografado;
- controle de acesso por empresa.

