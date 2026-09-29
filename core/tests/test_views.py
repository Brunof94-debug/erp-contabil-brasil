from decimal import Decimal

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from core.models import (
    Cliente,
    ContaContabil,
    Empresa,
    LancamentoContabil,
    LancamentoItem,
    PerfilUsuario,
)


@pytest.mark.django_db
def test_dashboard_publico_responde(client):
    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert "ERP Contábil Brasil" in response.content.decode()


@pytest.mark.django_db
def test_login_responde(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert "Entrar" in response.content.decode()


@pytest.mark.django_db
def test_recuperacao_senha_responde(client):
    response = client.get(reverse("password_reset"))

    assert response.status_code == 200
    assert "Recuperar senha" in response.content.decode()


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_recuperacao_senha_envia_email_para_usuario_existente(client, django_user_model):
    django_user_model.objects.create_user(
        username="recuperar",
        email="recuperar@example.com",
        password="senha-antiga-123",
    )

    response = client.post(reverse("password_reset"), {"email": "recuperar@example.com"})

    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "ERP Contábil Brasil" in mail.outbox[0].body


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_recuperacao_senha_nao_revela_email_inexistente(client):
    response = client.post(reverse("password_reset"), {"email": "naoexiste@example.com"})

    assert response.status_code == 302
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_cadastro_responde(client):
    response = client.get(reverse("signup"))

    assert response.status_code == 200
    assert "Crie sua conta" in response.content.decode()


@pytest.mark.django_db
def test_cadastro_cria_usuario_e_redireciona_para_onboarding(client, django_user_model):
    response = client.post(
        reverse("signup"),
        {
            "username": "novo-usuario",
            "email": "novo@example.com",
            "password1": "senha-forte-123",
            "password2": "senha-forte-123",
        },
    )

    assert response.status_code == 302
    assert reverse("onboarding_empresa") in response["Location"]
    user = django_user_model.objects.get(username="novo-usuario")
    assert user.email == "novo@example.com"


@pytest.mark.django_db
def test_cadastro_rejeita_email_duplicado(client, django_user_model):
    django_user_model.objects.create_user(
        username="existente",
        email="duplicado@example.com",
        password="senha-teste",
    )

    response = client.post(
        reverse("signup"),
        {
            "username": "outro",
            "email": "duplicado@example.com",
            "password1": "senha-forte-123",
            "password2": "senha-forte-123",
        },
    )

    assert response.status_code == 200
    assert "Já existe uma conta com este e-mail" in response.content.decode()


@pytest.mark.django_db
def test_cadastros_exigem_login(client):
    response = client.get(reverse("empresa_list"))

    assert response.status_code == 302
    assert reverse("login") in response["Location"]


@pytest.mark.django_db
def test_usuario_logado_sem_empresa_e_redirecionado_para_onboarding(client, django_user_model):
    user = django_user_model.objects.create_user(username="sem-empresa", password="senha-teste")
    client.force_login(user)

    response = client.get(reverse("cliente_list"))

    assert response.status_code == 302
    assert reverse("onboarding_empresa") in response["Location"]


@pytest.mark.django_db
def test_onboarding_cria_empresa_e_vincula_usuario(client, django_user_model):
    user = django_user_model.objects.create_user(username="novo", password="senha-teste")
    client.force_login(user)

    response = client.post(
        reverse("onboarding_empresa"),
        {"nome": "Nova Empresa", "documento": "123"},
    )

    assert response.status_code == 302
    perfil = PerfilUsuario.objects.get(usuario=user)
    assert perfil.empresa.nome == "Nova Empresa"


@pytest.mark.django_db
def test_detalhe_lancamento_mostra_totais(client, django_user_model):
    user = django_user_model.objects.create_user(username="bruno", password="senha-teste")
    empresa = Empresa.objects.create(nome="Empresa Teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa)
    client.force_login(user)
    caixa = ContaContabil.objects.create(
        empresa=empresa,
        codigo="1.1.1",
        nome="Caixa",
        tipo=ContaContabil.Tipo.ATIVO,
    )
    receita = ContaContabil.objects.create(
        empresa=empresa,
        codigo="3.1.1",
        nome="Receita",
        tipo=ContaContabil.Tipo.RECEITA,
    )
    lancamento = LancamentoContabil.objects.create(
        empresa=empresa,
        historico="Venda teste",
    )
    LancamentoItem.objects.create(lancamento=lancamento, conta=caixa, debito=Decimal("149.00"))
    LancamentoItem.objects.create(lancamento=lancamento, conta=receita, credito=Decimal("149.00"))

    response = client.get(reverse("lancamento_detail", args=[lancamento.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Balanceado" in content
    assert "149" in content


@pytest.mark.django_db
def test_usuario_ve_apenas_clientes_da_sua_empresa(client, django_user_model):
    empresa_a = Empresa.objects.create(nome="Empresa A")
    empresa_b = Empresa.objects.create(nome="Empresa B")
    Cliente.objects.create(empresa=empresa_a, nome="Cliente A")
    Cliente.objects.create(empresa=empresa_b, nome="Cliente B")
    user = django_user_model.objects.create_user(username="usuario-a", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa_a)
    client.force_login(user)

    response = client.get(reverse("cliente_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Cliente A" in content
    assert "Cliente B" not in content


@pytest.mark.django_db
def test_busca_clientes_filtra_dentro_da_empresa_do_usuario(client, django_user_model):
    empresa_a = Empresa.objects.create(nome="Empresa A")
    empresa_b = Empresa.objects.create(nome="Empresa B")
    Cliente.objects.create(empresa=empresa_a, nome="Cliente Encontrado", email="ok@example.com")
    Cliente.objects.create(empresa=empresa_a, nome="Cliente Oculto", email="outro@example.com")
    Cliente.objects.create(empresa=empresa_b, nome="Cliente Encontrado B", email="ok@example.com")
    user = django_user_model.objects.create_user(username="busca-cliente", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa_a)
    client.force_login(user)

    response = client.get(reverse("cliente_list"), {"q": "Encontrado"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "Cliente Encontrado" in content
    assert "Cliente Oculto" not in content
    assert "Cliente Encontrado B" not in content


@pytest.mark.django_db
def test_usuario_nao_abre_lancamento_de_outra_empresa(client, django_user_model):
    empresa_a = Empresa.objects.create(nome="Empresa A")
    empresa_b = Empresa.objects.create(nome="Empresa B")
    user = django_user_model.objects.create_user(username="usuario-a", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa_a)
    lancamento_b = LancamentoContabil.objects.create(
        empresa=empresa_b,
        historico="Lançamento de outra empresa",
    )
    client.force_login(user)

    response = client.get(reverse("lancamento_detail", args=[lancamento_b.pk]))

    assert response.status_code == 404
