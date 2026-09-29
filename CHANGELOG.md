# Changelog

## v0.1.0-demo — MVP demonstrável

Primeira versão local demonstrável do ERP Contábil Brasil.

### Incluído

- Autenticação com cadastro, login, logout e recuperação de senha.
- Onboarding de empresa para novos usuários.
- Isolamento de dados por empresa.
- Cadastros de empresas, clientes, fornecedores e plano de contas.
- Lançamentos contábeis com validação de partidas dobradas.
- Contas a receber e contas a pagar.
- Relatório financeiro com fluxo previsto, vencidos e resumo mensal.
- Importação CSV de clientes, fornecedores e plano de contas.
- Exportação CSV de contas a receber, contas a pagar e fluxo previsto.
- Dashboard visual com métricas operacionais.
- Seed demo profissional com dados fictícios.
- Healthcheck em `/healthz/`.
- Configuração preparada para deploy demo com Gunicorn, WhiteNoise e PostgreSQL via `DATABASE_URL`.
- Testes automatizados cobrindo regras contábeis, isolamento por empresa, autenticação, financeiro, CSV e seed demo.

### Validações locais

- Ruff: PASS.
- Testes automatizados: PASS.
- Django check: PASS.
- `makemigrations --check`: PASS.
- `collectstatic`: PASS.

### Limitações conhecidas

- Não declara conformidade fiscal, SPED, NF-e, eSocial ou obrigações legais.
- Não possui integração bancária real.
- Não possui módulo fiscal oficial.
- Não possui controle avançado de papéis e permissões por equipe.
