import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from core.models import (
    Cliente,
    ContaContabil,
    Empresa,
    LancamentoContabil,
    PerfilUsuario,
    TituloFinanceiro,
)


@pytest.mark.django_db
def test_seed_demo_cria_dados_profissionais_e_e_idempotente():
    call_command("seed_demo")
    call_command("seed_demo")

    empresa = Empresa.objects.get(nome="Contábil Aurora Demo")
    assert Cliente.objects.filter(empresa=empresa).count() == 3
    assert ContaContabil.objects.filter(empresa=empresa).count() == 6
    assert LancamentoContabil.objects.filter(empresa=empresa).count() == 3
    assert TituloFinanceiro.objects.filter(empresa=empresa).count() == 4
    assert LancamentoContabil.objects.filter(
        empresa=empresa,
        status=LancamentoContabil.Status.POSTADO,
    ).count() == 3


@pytest.mark.django_db
def test_seed_demo_reaproveita_usuario_demo_com_perfil_existente():
    empresa_antiga = Empresa.objects.create(nome="Empresa antiga")
    usuario = get_user_model().objects.create_user(username="demo", password="demo12345")
    PerfilUsuario.objects.create(usuario=usuario, empresa=empresa_antiga)

    call_command("seed_demo")

    empresa_demo = Empresa.objects.get(nome="Contábil Aurora Demo")
    usuario.refresh_from_db()
    assert usuario.perfil_erp.empresa == empresa_demo
