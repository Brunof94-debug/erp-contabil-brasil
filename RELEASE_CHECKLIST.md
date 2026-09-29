# Checklist de Produto — ERP Contábil Brasil

## v0.1.1-demo

Checklist usado para considerar a demo local pronta antes de publicar no GitHub.

## Produto

- Dashboard principal abre e apresenta métricas operacionais.
- Cadastro, login, logout e recuperação de senha estão disponíveis.
- Primeiro acesso cria ou vincula uma empresa.
- Dados são isolados por empresa.
- Cadastros de empresas, clientes, fornecedores e plano de contas funcionam.
- Lançamentos contábeis validam débito e crédito balanceados.
- Contas a receber e contas a pagar estão disponíveis.
- Relatórios financeiros exibem fluxo previsto, vencidos e resumo mensal.
- Importações CSV funcionam para clientes, fornecedores e plano de contas.
- Exportações CSV funcionam para contas a receber, contas a pagar e fluxo previsto.
- Páginas institucionais de sobre, termos e privacidade estão publicadas localmente.
- Interface está polida para desktop e celular.

## Qualidade

- Ruff: PASS.
- Testes automatizados: PASS — 34 testes.
- Django check: PASS.
- `makemigrations --check`: PASS.
- `collectstatic`: PASS.
- Varredura básica de secrets: sem secrets reais encontrados.

## Limites declarados

- Não declara conformidade fiscal oficial.
- Não substitui contador, advogado ou validação especializada.
- Não possui SPED, NF-e, eSocial ou obrigações fiscais oficiais.
- Não possui integração bancária real.
- Não deve ser usado como produto contábil de produção sem nova fase de validação.
