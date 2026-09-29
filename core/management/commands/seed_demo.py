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
        hoje = timezone.localdate()
        empresa = self._empresa()
        self._usuario_demo(empresa)
        clientes = self._clientes(empresa)
        fornecedores = self._fornecedores(empresa)
        contas = self._plano_de_contas(empresa)
        self._lancamentos(empresa, contas, hoje)
        self._titulos(empresa, clientes, fornecedores, hoje)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo atualizada: usuário demo/demo12345, cadastros, lançamentos e financeiro."
            )
        )

    def _empresa(self):
        empresa, _created = Empresa.objects.get_or_create(
            nome="Contábil Aurora Demo",
            defaults={"documento": "00.000.000/0001-00"},
        )
        return empresa

    def _usuario_demo(self, empresa):
        usuario, created = get_user_model().objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com"},
        )
        if created:
            usuario.set_password("demo12345")
            usuario.save(update_fields=["password"])
        PerfilUsuario.objects.get_or_create(usuario=usuario, empresa=empresa)

    def _clientes(self, empresa):
        dados = [
            ("Padaria Central Ltda.", "financeiro@padariacentral.example"),
            ("Clínica Vida Plena", "contas@vidaplena.example"),
            ("Mercado Boa Compra", "adm@boacompra.example"),
        ]
        clientes = {}
        for nome, email in dados:
            cliente, _created = Cliente.objects.get_or_create(
                empresa=empresa,
                nome=nome,
                defaults={"email": email, "telefone": "(51) 3000-0000"},
            )
            clientes[nome] = cliente
        return clientes

    def _fornecedores(self, empresa):
        dados = [
            ("Nuvem Tecnologia", "financeiro@nuvem.example"),
            ("Escritório Sul Coworking", "cobranca@coworking.example"),
            ("Energia Metropolitana", "contas@energia.example"),
        ]
        fornecedores = {}
        for nome, email in dados:
            fornecedor, _created = Fornecedor.objects.get_or_create(
                empresa=empresa,
                nome=nome,
                defaults={"email": email, "telefone": "(51) 4000-0000"},
            )
            fornecedores[nome] = fornecedor
        return fornecedores

    def _plano_de_contas(self, empresa):
        dados = [
            ("1.1.1", "Caixa e bancos", ContaContabil.Tipo.ATIVO),
            ("1.1.2", "Clientes a receber", ContaContabil.Tipo.ATIVO),
            ("2.1.1", "Fornecedores a pagar", ContaContabil.Tipo.PASSIVO),
            ("3.1.1", "Receita de serviços contábeis", ContaContabil.Tipo.RECEITA),
            ("4.1.1", "Despesas operacionais", ContaContabil.Tipo.DESPESA),
            ("4.1.2", "Despesas com tecnologia", ContaContabil.Tipo.DESPESA),
        ]
        contas = {}
        for codigo, nome, tipo in dados:
            conta, _created = ContaContabil.objects.get_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={"nome": nome, "tipo": tipo},
            )
            contas[codigo] = conta
        return contas

    def _lancamentos(self, empresa, contas, hoje):
        self._lancamento_balanceado(
            empresa=empresa,
            historico="Recebimento de honorários contábeis",
            data=hoje,
            debito=(contas["1.1.1"], Decimal("1490.00")),
            credito=(contas["3.1.1"], Decimal("1490.00")),
        )
        self._lancamento_balanceado(
            empresa=empresa,
            historico="Pagamento de infraestrutura em nuvem",
            data=hoje,
            debito=(contas["4.1.2"], Decimal("289.90")),
            credito=(contas["1.1.1"], Decimal("289.90")),
        )
        self._lancamento_balanceado(
            empresa=empresa,
            historico="Provisionamento de despesa operacional",
            data=hoje.replace(day=1),
            debito=(contas["4.1.1"], Decimal("450.00")),
            credito=(contas["2.1.1"], Decimal("450.00")),
        )

    def _lancamento_balanceado(self, empresa, historico, data, debito, credito):
        lancamento, created = LancamentoContabil.objects.get_or_create(
            empresa=empresa,
            historico=historico,
            defaults={
                "data": data,
                "status": LancamentoContabil.Status.POSTADO,
            },
        )
        if not created:
            return
        conta_debito, valor_debito = debito
        conta_credito, valor_credito = credito
        LancamentoItem.objects.create(
            lancamento=lancamento,
            conta=conta_debito,
            debito=valor_debito,
        )
        LancamentoItem.objects.create(
            lancamento=lancamento,
            conta=conta_credito,
            credito=valor_credito,
        )

    def _titulos(self, empresa, clientes, fornecedores, hoje):
        titulos = [
            {
                "tipo": TituloFinanceiro.Tipo.RECEBER,
                "descricao": "Honorários mensais — Padaria Central",
                "cliente": clientes["Padaria Central Ltda."],
                "valor": Decimal("149.00"),
                "vencimento": hoje,
            },
            {
                "tipo": TituloFinanceiro.Tipo.RECEBER,
                "descricao": "Implantação contábil — Clínica Vida Plena",
                "cliente": clientes["Clínica Vida Plena"],
                "valor": Decimal("690.00"),
                "vencimento": hoje + timezone.timedelta(days=7),
            },
            {
                "tipo": TituloFinanceiro.Tipo.PAGAR,
                "descricao": "Servidor em nuvem",
                "fornecedor": fornecedores["Nuvem Tecnologia"],
                "valor": Decimal("289.90"),
                "vencimento": hoje + timezone.timedelta(days=3),
            },
            {
                "tipo": TituloFinanceiro.Tipo.PAGAR,
                "descricao": "Coworking mensal",
                "fornecedor": fornecedores["Escritório Sul Coworking"],
                "valor": Decimal("450.00"),
                "vencimento": hoje - timezone.timedelta(days=2),
            },
        ]
        for dados in titulos:
            defaults = {
                "valor": dados["valor"],
                "vencimento": dados["vencimento"],
            }
            if "cliente" in dados:
                defaults["cliente"] = dados["cliente"]
            if "fornecedor" in dados:
                defaults["fornecedor"] = dados["fornecedor"]
            TituloFinanceiro.objects.get_or_create(
                empresa=empresa,
                tipo=dados["tipo"],
                descricao=dados["descricao"],
                defaults=defaults,
            )
