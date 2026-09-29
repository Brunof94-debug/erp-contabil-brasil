# ERP Contábil Brasil — resumo para portfólio

## Visão geral

O ERP Contábil Brasil é um MVP de sistema web para organização financeira e contábil de pequenas empresas. O projeto foi construído em Django com foco em segurança, isolamento de dados por empresa, validações contábeis e preparação para deploy demo.

## Problema tratado

Pequenas empresas e operadores financeiros frequentemente controlam clientes, fornecedores, contas a pagar, contas a receber e lançamentos contábeis em planilhas dispersas. O projeto centraliza esses dados em uma aplicação web com regras mínimas de consistência.

## Principais funcionalidades

- Cadastro público de usuários.
- Onboarding de empresa.
- Isolamento multiempresa.
- Clientes e fornecedores.
- Plano de contas.
- Lançamentos contábeis com partidas dobradas.
- Contas a receber e a pagar.
- Relatórios financeiros.
- Importação e exportação CSV.
- Dashboard com indicadores.
- Recuperação de senha por e-mail.
- Dados demo profissionais.

## Stack

- Python 3.12.
- Django 5.
- PostgreSQL-ready via `DATABASE_URL`.
- WhiteNoise para arquivos estáticos.
- Gunicorn para deploy.
- Pytest.
- Ruff.

## Boas práticas aplicadas

- Nenhum secret versionado.
- `.env.example` para configuração local.
- Testes automatizados.
- Healthcheck.
- Runbook operacional.
- Changelog.
- Separação clara entre MVP demonstrável e recursos fiscais oficiais ainda fora de escopo.

## Status

Versão local atual: `v0.1.3-demo`.

O projeto está publicado como repositório de portfólio, com README visual, documentação de apoio, dados demo e estrutura preparada para deploy demo controlado. Ainda não deve ser apresentado como produto contábil/fiscal pronto para uso oficial sem validação especializada.
