from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from core.models import ContaContabil, Empresa, LancamentoContabil, LancamentoItem


@pytest.fixture
def empresa(db):
    return Empresa.objects.create(nome="Empresa Teste")


@pytest.fixture
def contas(empresa):
    caixa = ContaContabil.objects.create(
        empresa=empresa,
        codigo="1.1.1",
        nome="Caixa",
        tipo=ContaContabil.Tipo.ATIVO,
    )
    receita = ContaContabil.objects.create(
        empresa=empresa,
        codigo="3.1.1",
        nome="Receita de Serviços",
        tipo=ContaContabil.Tipo.RECEITA,
    )
    return caixa, receita


@pytest.mark.django_db
def test_lancamento_balanceado_passaria_na_validacao(empresa, contas):
    caixa, receita = contas
    lancamento = LancamentoContabil.objects.create(
        empresa=empresa,
        historico="Venda de serviço",
    )
    LancamentoItem.objects.create(
        lancamento=lancamento,
        conta=caixa,
        debito=Decimal("149.00"),
    )
    LancamentoItem.objects.create(
        lancamento=lancamento,
        conta=receita,
        credito=Decimal("149.00"),
    )

    lancamento.clean()
    assert lancamento.esta_balanceado() is True
    assert lancamento.diferenca() == Decimal("0.00")


@pytest.mark.django_db
def test_lancamento_desbalanceado_falha(empresa, contas):
    caixa, receita = contas
    lancamento = LancamentoContabil.objects.create(
        empresa=empresa,
        historico="Venda com erro",
    )
    LancamentoItem.objects.create(
        lancamento=lancamento,
        conta=caixa,
        debito=Decimal("149.00"),
    )
    LancamentoItem.objects.create(
        lancamento=lancamento,
        conta=receita,
        credito=Decimal("100.00"),
    )

    with pytest.raises(ValidationError):
        lancamento.clean()


@pytest.mark.django_db
def test_linha_nao_pode_ter_debito_e_credito_ao_mesmo_tempo(empresa, contas):
    caixa, _receita = contas
    lancamento = LancamentoContabil.objects.create(
        empresa=empresa,
        historico="Linha inválida",
    )
    item = LancamentoItem(
        lancamento=lancamento,
        conta=caixa,
        debito=Decimal("10.00"),
        credito=Decimal("10.00"),
    )

    with pytest.raises(ValidationError):
        item.clean()
