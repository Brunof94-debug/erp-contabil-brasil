import pytest
from django.core.management import call_command

from core.models import Cliente, ContaContabil, Empresa, LancamentoContabil, TituloFinanceiro


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
