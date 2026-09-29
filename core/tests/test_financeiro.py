from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from core.models import Cliente, Empresa, Fornecedor, PerfilUsuario, TituloFinanceiro


@pytest.mark.django_db
def test_titulo_financeiro_exige_valor_positivo():
    empresa = Empresa.objects.create(nome="Empresa")
    titulo = TituloFinanceiro(
        empresa=empresa,
        tipo=TituloFinanceiro.Tipo.RECEBER,
        descricao="Inválido",
        valor=Decimal("0.00"),
        vencimento=timezone.localdate(),
    )

    with pytest.raises(ValidationError):
        titulo.clean()


@pytest.mark.django_db
def test_conta_receber_nao_aceita_fornecedor():
    empresa = Empresa.objects.create(nome="Empresa")
    fornecedor = Fornecedor.objects.create(empresa=empresa, nome="Fornecedor")
    titulo = TituloFinanceiro(
        empresa=empresa,
        tipo=TituloFinanceiro.Tipo.RECEBER,
        descricao="Inválido",
        valor=Decimal("10.00"),
        vencimento=timezone.localdate(),
        fornecedor=fornecedor,
    )

    with pytest.raises(ValidationError):
        titulo.clean()


@pytest.mark.django_db
def test_usuario_ve_apenas_contas_a_receber_da_sua_empresa(client, django_user_model):
    empresa_a = Empresa.objects.create(nome="Empresa A")
    empresa_b = Empresa.objects.create(nome="Empresa B")
    cliente_a = Cliente.objects.create(empresa=empresa_a, nome="Cliente A")
    cliente_b = Cliente.objects.create(empresa=empresa_b, nome="Cliente B")
    TituloFinanceiro.objects.create(
        empresa=empresa_a,
        tipo=TituloFinanceiro.Tipo.RECEBER,
        descricao="Receber A",
        cliente=cliente_a,
        valor=Decimal("149.00"),
        vencimento=timezone.localdate(),
    )
    TituloFinanceiro.objects.create(
        empresa=empresa_b,
        tipo=TituloFinanceiro.Tipo.RECEBER,
        descricao="Receber B",
        cliente=cliente_b,
        valor=Decimal("200.00"),
        vencimento=timezone.localdate(),
    )
    user = django_user_model.objects.create_user(username="financeiro", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa_a)
    client.force_login(user)

    response = client.get(reverse("receber_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Receber A" in content
    assert "Receber B" not in content


@pytest.mark.django_db
def test_relatorio_financeiro_mostra_totais_da_empresa(client, django_user_model):
    empresa_a = Empresa.objects.create(nome="Empresa A")
    empresa_b = Empresa.objects.create(nome="Empresa B")
    cliente = Cliente.objects.create(empresa=empresa_a, nome="Cliente A")
    fornecedor = Fornecedor.objects.create(empresa=empresa_a, nome="Fornecedor A")
    cliente_b = Cliente.objects.create(empresa=empresa_b, nome="Cliente B")
    TituloFinanceiro.objects.create(
        empresa=empresa_a,
        tipo=TituloFinanceiro.Tipo.RECEBER,
        descricao="Receber relatório",
        cliente=cliente,
        valor=Decimal("149.00"),
        vencimento=timezone.localdate(),
    )
    TituloFinanceiro.objects.create(
        empresa=empresa_a,
        tipo=TituloFinanceiro.Tipo.PAGAR,
        descricao="Pagar relatório",
        fornecedor=fornecedor,
        valor=Decimal("49.00"),
        vencimento=timezone.localdate(),
    )
    TituloFinanceiro.objects.create(
        empresa=empresa_b,
        tipo=TituloFinanceiro.Tipo.RECEBER,
        descricao="Receber outra empresa",
        cliente=cliente_b,
        valor=Decimal("999.00"),
        vencimento=timezone.localdate(),
    )
    user = django_user_model.objects.create_user(username="relatorio", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa_a)
    client.force_login(user)

    response = client.get(reverse("financeiro_report"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "149" in content
    assert "49" in content
    assert "100" in content
    assert "Receber outra empresa" not in content


@pytest.mark.django_db
def test_exportacao_csv_receber_respeita_empresa(client, django_user_model):
    empresa_a = Empresa.objects.create(nome="Empresa A")
    empresa_b = Empresa.objects.create(nome="Empresa B")
    cliente_a = Cliente.objects.create(empresa=empresa_a, nome="Cliente A")
    cliente_b = Cliente.objects.create(empresa=empresa_b, nome="Cliente B")
    TituloFinanceiro.objects.create(
        empresa=empresa_a,
        tipo=TituloFinanceiro.Tipo.RECEBER,
        descricao="Exportar A",
        cliente=cliente_a,
        valor=Decimal("149.00"),
        vencimento=timezone.localdate(),
    )
    TituloFinanceiro.objects.create(
        empresa=empresa_b,
        tipo=TituloFinanceiro.Tipo.RECEBER,
        descricao="Exportar B",
        cliente=cliente_b,
        valor=Decimal("999.00"),
        vencimento=timezone.localdate(),
    )
    user = django_user_model.objects.create_user(username="csv", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa_a)
    client.force_login(user)

    response = client.get(reverse("receber_csv"))

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    content = response.content.decode("utf-8-sig")
    assert "Exportar A" in content
    assert "Exportar B" not in content


@pytest.mark.django_db
def test_exportacao_csv_fluxo_previsto(client, django_user_model):
    empresa = Empresa.objects.create(nome="Empresa")
    cliente = Cliente.objects.create(empresa=empresa, nome="Cliente")
    fornecedor = Fornecedor.objects.create(empresa=empresa, nome="Fornecedor")
    TituloFinanceiro.objects.create(
        empresa=empresa,
        tipo=TituloFinanceiro.Tipo.RECEBER,
        descricao="Receber fluxo",
        cliente=cliente,
        valor=Decimal("149.00"),
        vencimento=timezone.localdate(),
    )
    TituloFinanceiro.objects.create(
        empresa=empresa,
        tipo=TituloFinanceiro.Tipo.PAGAR,
        descricao="Pagar fluxo",
        fornecedor=fornecedor,
        valor=Decimal("49.00"),
        vencimento=timezone.localdate(),
    )
    user = django_user_model.objects.create_user(username="fluxo", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa)
    client.force_login(user)

    response = client.get(reverse("financeiro_report_csv"))

    assert response.status_code == 200
    content = response.content.decode("utf-8-sig")
    assert "mes;receber;pagar;saldo" in content
    assert "149" in content
    assert "49" in content
    assert "100" in content
