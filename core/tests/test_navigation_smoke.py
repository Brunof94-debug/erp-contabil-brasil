import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from core.models import Cliente, ContaContabil, Fornecedor, LancamentoContabil, TituloFinanceiro


@pytest.fixture
def demo_client(client):
    call_command("seed_demo")
    user = get_user_model().objects.get(username="demo")
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_demo_usuario_abre_telas_principais_sem_erro(demo_client):
    rotas = [
        "dashboard",
        "empresa_list",
        "cliente_list",
        "cliente_import",
        "cliente_create",
        "fornecedor_list",
        "fornecedor_import",
        "fornecedor_create",
        "conta_list",
        "conta_import",
        "conta_create",
        "lancamento_list",
        "lancamento_create",
        "receber_list",
        "receber_create",
        "pagar_list",
        "pagar_create",
        "financeiro_report",
    ]

    for rota in rotas:
        response = demo_client.get(reverse(rota))
        assert response.status_code == 200, rota


@pytest.mark.django_db
def test_demo_dashboard_mostra_indicadores_financeiros_visuais(demo_client):
    response = demo_client.get(reverse("dashboard"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Saldo previsto" in content
    assert "Títulos vencidos" in content
    assert "Receber versus pagar" in content


@pytest.mark.django_db
def test_demo_usuario_abre_edicao_detalhe_e_exclusao_sem_erro(demo_client):
    cliente = Cliente.objects.get(nome="Padaria Central Ltda.")
    fornecedor = Fornecedor.objects.get(nome="Nuvem Tecnologia")
    conta = ContaContabil.objects.get(codigo="1.1.1")
    lancamento = LancamentoContabil.objects.get(historico="Recebimento de honorários contábeis")
    titulo_receber = TituloFinanceiro.objects.get(descricao="Honorários mensais — Padaria Central")
    titulo_pagar = TituloFinanceiro.objects.get(descricao="Servidor em nuvem")

    rotas_com_pk = [
        ("cliente_update", cliente.pk),
        ("cliente_delete", cliente.pk),
        ("fornecedor_update", fornecedor.pk),
        ("fornecedor_delete", fornecedor.pk),
        ("conta_update", conta.pk),
        ("conta_delete", conta.pk),
        ("lancamento_detail", lancamento.pk),
        ("lancamento_update", lancamento.pk),
        ("lancamento_delete", lancamento.pk),
        ("receber_update", titulo_receber.pk),
        ("receber_delete", titulo_receber.pk),
        ("pagar_update", titulo_pagar.pk),
        ("pagar_delete", titulo_pagar.pk),
    ]

    for rota, pk in rotas_com_pk:
        response = demo_client.get(reverse(rota, args=[pk]))
        assert response.status_code == 200, rota


@pytest.mark.django_db
def test_demo_usuario_exporta_csvs_sem_erro(demo_client):
    rotas = ["receber_csv", "pagar_csv", "financeiro_report_csv"]

    for rota in rotas:
        response = demo_client.get(reverse(rota))
        assert response.status_code == 200, rota
        assert response["Content-Type"].startswith("text/csv")
