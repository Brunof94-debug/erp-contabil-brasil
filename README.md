# ERP Contábil Brasil

Base inicial profissional para um sistema ERP contábil brasileiro, criada do zero para evoluir com segurança.

## Escopo inicial do MVP

- Cadastro de empresas.
- Clientes e fornecedores.
- Plano de contas.
- Lançamentos contábeis com validação de débito/crédito.
- Dashboard operacional.
- Trilha de auditoria.
- Estrutura preparada para PostgreSQL, deploy e testes.

Importante: este projeto ainda não declara conformidade fiscal, SPED, NF-e, eSocial ou obrigações legais. Essas etapas precisam de validação contábil/jurídica antes de uso oficial.

## Como rodar localmente

```powershell
cd C:\Users\Pichau\Documents\Codex\erp-contabil-brasil
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Depois acesse:

```text
http://127.0.0.1:8000/
```

## Telas disponíveis

- `/` — dashboard.
- `/login/` — login.
- `/cadastro/` — cadastro público de usuário.
- `/senha/recuperar/` — recuperação de senha por e-mail.
- `/onboarding/empresa/` — primeiro acesso para criar/vincular empresa.
- `/admin/` — administração Django.
- `/empresas/` — empresas.
- `/clientes/` — clientes.
- `/clientes/importar/` — importação CSV de clientes.
- `/fornecedores/` — fornecedores.
- `/fornecedores/importar/` — importação CSV de fornecedores.
- `/plano-de-contas/` — plano de contas.
- `/plano-de-contas/importar/` — importação CSV do plano de contas.
- `/lancamentos/` — lançamentos contábeis.
- `/financeiro/receber/` — contas a receber.
- `/financeiro/pagar/` — contas a pagar.
- `/financeiro/relatorios/` — fluxo previsto, vencidos e resumo mensal.
- `/financeiro/receber/exportar.csv` — exportação CSV de contas a receber.
- `/financeiro/pagar/exportar.csv` — exportação CSV de contas a pagar.
- `/financeiro/relatorios/exportar.csv` — exportação CSV do fluxo previsto.
- `/healthz/` — healthcheck.

As telas de cadastro exigem login. Crie um superusuário com `python manage.py createsuperuser`.

O comando `python manage.py seed_demo` também cria um usuário local de demonstração:

```text
usuário: demo
senha: demo12345
```

Esse usuário fica vinculado à `Empresa Demonstração`, permitindo testar o isolamento por empresa.

## Primeiro acesso de novos usuários

Usuários comuns sem empresa vinculada são enviados para:

```text
/onboarding/empresa/
```

Nessa tela o usuário cria a própria empresa e passa a enxergar apenas os dados dela.
Superusuários continuam com visão administrativa geral.

## Importação CSV

As importações aceitam arquivos UTF-8 com separador vírgula ou ponto e vírgula.
Os registros são sempre vinculados à empresa do usuário logado.

- Clientes: `nome`, `documento`, `email`, `telefone`.
- Fornecedores: `nome`, `documento`, `email`, `telefone`.
- Plano de contas: `codigo`, `nome`, `tipo`.

Tipos aceitos no plano de contas:

```text
ATIVO, PASSIVO, PATRIMONIO, RECEITA, DESPESA
```

## Cadastro público

Novos usuários podem criar conta em:

```text
/cadastro/
```

Após criar a conta, o usuário entra automaticamente e é levado para o onboarding da empresa.

## E-mail e recuperação de senha

Por padrão, o projeto usa backend de console:

```text
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Isso permite testar recuperação de senha localmente sem provedor externo. Em produção,
configure SMTP ou provedor transacional por variáveis de ambiente, sem colocar secrets no Git.

## Próximas fases

1. Fechar requisitos do MVP comercial.
2. Definir módulos fiscais/contábeis obrigatórios.
3. Implementar autenticação multiusuário por empresa.
4. Criar telas CRUD completas.
5. Adicionar relatórios financeiros e contábeis.
6. Preparar deploy staging/production.
