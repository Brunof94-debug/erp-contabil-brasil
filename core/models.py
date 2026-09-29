from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class TimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Empresa(TimeStampedModel):
    nome = models.CharField(max_length=180)
    documento = models.CharField(max_length=32, blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "empresa"
        verbose_name_plural = "empresas"

    def __str__(self) -> str:
        return self.nome


class PerfilUsuario(TimeStampedModel):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_erp",
    )
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="usuarios")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "perfil de usuário"
        verbose_name_plural = "perfis de usuário"

    def __str__(self) -> str:
        return f"{self.usuario} — {self.empresa}"


class PessoaBase(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    nome = models.CharField(max_length=180)
    documento = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=40, blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Cliente(PessoaBase):
    class Meta(PessoaBase.Meta):
        verbose_name = "cliente"
        verbose_name_plural = "clientes"


class Fornecedor(PessoaBase):
    class Meta(PessoaBase.Meta):
        verbose_name = "fornecedor"
        verbose_name_plural = "fornecedores"


class ContaContabil(TimeStampedModel):
    class Tipo(models.TextChoices):
        ATIVO = "ATIVO", "Ativo"
        PASSIVO = "PASSIVO", "Passivo"
        PATRIMONIO = "PATRIMONIO", "Patrimônio líquido"
        RECEITA = "RECEITA", "Receita"
        DESPESA = "DESPESA", "Despesa"

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=32)
    nome = models.CharField(max_length=180)
    tipo = models.CharField(max_length=16, choices=Tipo.choices)
    conta_pai = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="subcontas",
    )
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["empresa__nome", "codigo"]
        constraints = [
            models.UniqueConstraint(fields=["empresa", "codigo"], name="unique_conta_por_empresa")
        ]
        verbose_name = "conta contábil"
        verbose_name_plural = "plano de contas"

    def __str__(self) -> str:
        return f"{self.codigo} — {self.nome}"


class LancamentoContabil(TimeStampedModel):
    class Status(models.TextChoices):
        RASCUNHO = "RASCUNHO", "Rascunho"
        POSTADO = "POSTADO", "Postado"
        CANCELADO = "CANCELADO", "Cancelado"

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    data = models.DateField(default=timezone.localdate)
    historico = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RASCUNHO)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lancamentos_criados",
    )

    class Meta:
        ordering = ["-data", "-created_at"]
        verbose_name = "lançamento contábil"
        verbose_name_plural = "lançamentos contábeis"

    def __str__(self) -> str:
        return f"{self.data:%d/%m/%Y} — {self.historico}"

    def totais(self) -> tuple[Decimal, Decimal]:
        linhas = self.itens.aggregate(
            total_debito=Sum("debito"),
            total_credito=Sum("credito"),
        )
        return (
            linhas["total_debito"] or Decimal("0.00"),
            linhas["total_credito"] or Decimal("0.00"),
        )

    def diferenca(self) -> Decimal:
        total_debito, total_credito = self.totais()
        return total_debito - total_credito

    def esta_balanceado(self) -> bool:
        total_debito, total_credito = self.totais()
        return total_debito == total_credito and total_debito > 0

    def clean(self) -> None:
        super().clean()
        if not self.pk:
            return

        itens = list(self.itens.all())
        if len(itens) < 2:
            raise ValidationError("O lançamento deve ter pelo menos duas linhas.")

        total_debito, total_credito = self.totais()
        if total_debito != total_credito:
            raise ValidationError("O total de débitos deve ser igual ao total de créditos.")


class LancamentoItem(TimeStampedModel):
    lancamento = models.ForeignKey(
        LancamentoContabil,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    conta = models.ForeignKey(ContaContabil, on_delete=models.PROTECT)
    debito = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    credito = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    complemento = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "item de lançamento"
        verbose_name_plural = "itens de lançamento"

    def __str__(self) -> str:
        return f"{self.conta} D:{self.debito} C:{self.credito}"

    def clean(self) -> None:
        super().clean()
        if self.debito < 0 or self.credito < 0:
            raise ValidationError("Débito e crédito não podem ser negativos.")
        if self.debito and self.credito:
            raise ValidationError("Uma linha não pode ter débito e crédito ao mesmo tempo.")
        if not self.debito and not self.credito:
            raise ValidationError("Uma linha precisa ter débito ou crédito.")


class TituloFinanceiro(TimeStampedModel):
    class Tipo(models.TextChoices):
        RECEBER = "RECEBER", "A receber"
        PAGAR = "PAGAR", "A pagar"

    class Status(models.TextChoices):
        ABERTO = "ABERTO", "Aberto"
        PAGO = "PAGO", "Pago/recebido"
        CANCELADO = "CANCELADO", "Cancelado"

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    descricao = models.CharField(max_length=180)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ABERTO)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="titulos_a_receber",
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="titulos_a_pagar",
    )
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ["vencimento", "descricao"]
        verbose_name = "título financeiro"
        verbose_name_plural = "títulos financeiros"

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} — {self.descricao} — R$ {self.valor}"

    def clean(self) -> None:
        super().clean()
        if self.valor <= 0:
            raise ValidationError("O valor precisa ser maior que zero.")
        if self.tipo == self.Tipo.RECEBER and self.fornecedor_id:
            raise ValidationError("Conta a receber não deve ter fornecedor.")
        if self.tipo == self.Tipo.PAGAR and self.cliente_id:
            raise ValidationError("Conta a pagar não deve ter cliente.")
        if self.status == self.Status.PAGO and not self.data_pagamento:
            raise ValidationError("Informe a data de pagamento/recebimento.")
        if self.status != self.Status.PAGO and self.data_pagamento:
            raise ValidationError("Data de pagamento só deve existir em títulos pagos/recebidos.")

    @property
    def esta_em_aberto(self) -> bool:
        return self.status == self.Status.ABERTO


class AuditLog(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    acao = models.CharField(max_length=80)
    entidade = models.CharField(max_length=120)
    entidade_id = models.CharField(max_length=80, blank=True)
    detalhes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "log de auditoria"
        verbose_name_plural = "logs de auditoria"

    def __str__(self) -> str:
        return f"{self.acao} {self.entidade} em {self.created_at:%d/%m/%Y %H:%M}"
