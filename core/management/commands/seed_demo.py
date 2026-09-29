from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    Cliente,
    ContaContabil,
    Empresa,
    Fornecedor,
    LancamentoContabil,
    LancamentoItem,
    PerfilUsuario,
    TituloFinanceiro,
)


class Command(BaseCommand):
    help = "Cria dados demonstrativos seguros para desenvolvimento local."

    def handle(self, *args, **options):
        empresa, _created = Empresa.objects.get_or_create(
            nome="Empresa Demonstração",
            defaults={"documento": "00.000.000/0000-00"},
        )
        usuario, created = get_user_model().objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com"},
        )
        if created:
            usuario.set_password("demo12345")
            usuario.save(update_fields=["password"])
        PerfilUsuario.objects.get_or_create(usuario=usuario, empresa=empresa)

        Cliente.objects.get_or_create(
            empresa=empresa,
            nome="Cliente Exemplo",
            defaults={"email": "cliente@example.com"},
        )
        cliente = Cliente.objects.get(empresa=empresa, nome="Cliente Exemplo")
        fornecedor, _created = Fornecedor.objects.get_or_create(
            empresa=empresa,
            nome="Fornecedor Exemplo",
            defaults={"email": "fornecedor@example.com"},
        )

        caixa, _created = ContaContabil.objects.get_or_create(
            empresa=empresa,
            codigo="1.1.1",
            defaults={"nome": "Caixa", "tipo": ContaContabil.Tipo.ATIVO},
        )
        receita, _created = ContaContabil.objects.get_or_create(
            empresa=empresa,
            codigo="3.1.1",
            defaults={"nome": "Receita de Serviços", "tipo": ContaContabil.Tipo.RECEITA},
        )

        lancamento, created = LancamentoContabil.objects.get_or_create(
            empresa=empresa,
            historico="Venda demonstrativa de serviço",
        )
        if created:
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

        TituloFinanceiro.objects.get_or_create(
            empresa=empresa,
            tipo=TituloFinanceiro.Tipo.RECEBER,
            descricao="Mensalidade exemplo",
            defaults={
                "cliente": cliente,
                "valor": Decimal("149.00"),
                "vencimento": timezone.localdate(),
            },
        )
        TituloFinanceiro.objects.get_or_create(
            empresa=empresa,
            tipo=TituloFinanceiro.Tipo.PAGAR,
            descricao="Despesa exemplo",
            defaults={
                "fornecedor": fornecedor,
                "valor": Decimal("59.90"),
                "vencimento": timezone.localdate(),
            },
        )

        self.stdout.write(self.style.SUCCESS("Dados demonstrativos criados/atualizados."))
