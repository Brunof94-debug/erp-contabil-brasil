from django.contrib import admin

from .models import (
    AuditLog,
    Cliente,
    ContaContabil,
    Empresa,
    Fornecedor,
    LancamentoContabil,
    LancamentoItem,
    PerfilUsuario,
    TituloFinanceiro,
)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome", "documento", "ativa", "created_at")
    search_fields = ("nome", "documento")
    list_filter = ("ativa",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "email", "ativa")
    search_fields = ("nome", "documento", "email")
    list_filter = ("empresa", "ativa")


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "email", "ativa")
    search_fields = ("nome", "documento", "email")
    list_filter = ("empresa", "ativa")


@admin.register(ContaContabil)
class ContaContabilAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "empresa", "tipo", "ativa")
    search_fields = ("codigo", "nome")
    list_filter = ("empresa", "tipo", "ativa")


class LancamentoItemInline(admin.TabularInline):
    model = LancamentoItem
    extra = 2


@admin.register(LancamentoContabil)
class LancamentoContabilAdmin(admin.ModelAdmin):
    list_display = ("data", "empresa", "historico", "status", "created_at")
    search_fields = ("historico",)
    list_filter = ("empresa", "status", "data")
    inlines = [LancamentoItemInline]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "empresa", "usuario", "acao", "entidade", "entidade_id")
    search_fields = ("acao", "entidade", "entidade_id")
    list_filter = ("empresa", "acao", "entidade")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "empresa", "ativo", "created_at")
    search_fields = ("usuario__username", "usuario__email", "empresa__nome")
    list_filter = ("empresa", "ativo")


@admin.register(TituloFinanceiro)
class TituloFinanceiroAdmin(admin.ModelAdmin):
    list_display = ("descricao", "empresa", "tipo", "valor", "vencimento", "status")
    search_fields = ("descricao", "cliente__nome", "fornecedor__nome")
    list_filter = ("empresa", "tipo", "status", "vencimento")
