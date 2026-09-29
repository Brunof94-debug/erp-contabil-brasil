import csv
import io

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
    View,
)

from .forms import (
    CadastroUsuarioForm,
    ClienteForm,
    ContaContabilForm,
    CsvUploadForm,
    EmpresaForm,
    FornecedorForm,
    LancamentoContabilForm,
    LancamentoItemFormSet,
    OnboardingEmpresaForm,
    TituloFinanceiroForm,
    limitar_formset_lancamento_a_empresa,
    limitar_formulario_a_empresa,
)
from .models import (
    Cliente,
    ContaContabil,
    Empresa,
    Fornecedor,
    LancamentoContabil,
    PerfilUsuario,
    TituloFinanceiro,
)


def dashboard(request):
    empresa = empresa_do_usuario(request.user) if request.user.is_authenticated else None
    if request.user.is_authenticated and not request.user.is_superuser and not empresa:
        return redirect("onboarding_empresa")
    empresas = Empresa.objects.all()
    clientes = Cliente.objects.all()
    fornecedores = Fornecedor.objects.all()
    contas = ContaContabil.objects.all()
    lancamentos = LancamentoContabil.objects.all()
    titulos = TituloFinanceiro.objects.all()
    if empresa:
        empresas = empresas.filter(pk=empresa.pk)
        clientes = clientes.filter(empresa=empresa)
        fornecedores = fornecedores.filter(empresa=empresa)
        contas = contas.filter(empresa=empresa)
        lancamentos = lancamentos.filter(empresa=empresa)
        titulos = titulos.filter(empresa=empresa)

    titulos_abertos = titulos.filter(status=TituloFinanceiro.Status.ABERTO)
    receber_aberto = titulos_abertos.filter(tipo=TituloFinanceiro.Tipo.RECEBER)
    pagar_aberto = titulos_abertos.filter(tipo=TituloFinanceiro.Tipo.PAGAR)
    total_a_receber_aberto = sum(titulo.valor for titulo in receber_aberto)
    total_a_pagar_aberto = sum(titulo.valor for titulo in pagar_aberto)
    saldo_previsto = total_a_receber_aberto - total_a_pagar_aberto
    total_fluxo = total_a_receber_aberto + total_a_pagar_aberto
    receber_percentual = 0
    pagar_percentual = 0
    if total_fluxo:
        receber_percentual = round((total_a_receber_aberto / total_fluxo) * 100)
        pagar_percentual = 100 - receber_percentual

    context = {
        "empresa_ativa": empresa,
        "total_empresas": empresas.count(),
        "total_clientes": clientes.count(),
        "total_fornecedores": fornecedores.count(),
        "total_contas": contas.count(),
        "total_lancamentos": lancamentos.count(),
        "total_a_receber_aberto": total_a_receber_aberto,
        "total_a_pagar_aberto": total_a_pagar_aberto,
        "saldo_previsto": saldo_previsto,
        "titulos_vencidos_count": titulos_abertos.filter(
            vencimento__lt=timezone.localdate(),
        ).count(),
        "receber_percentual": receber_percentual,
        "pagar_percentual": pagar_percentual,
        "lancamentos_por_status": lancamentos.values("status")
        .annotate(total=Count("id"))
        .order_by("status"),
    }
    return render(request, "core/dashboard.html", context)


def healthz(request):
    from django.http import JsonResponse

    return JsonResponse({"status": "ok", "service": "erp-contabil-brasil"})


class CadastroUsuarioView(CreateView):
    form_class = CadastroUsuarioForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("onboarding_empresa")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Conta criada. Agora configure sua empresa.")
        return response


class AppLoginRequiredMixin(LoginRequiredMixin):
    login_url = "login"


def empresa_do_usuario(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return None
    try:
        perfil = user.perfil_erp
    except PerfilUsuario.DoesNotExist:
        return None
    if not perfil.ativo or not perfil.empresa.ativa:
        return None
    return perfil.empresa


class OnboardingRequiredMixin(AppLoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_superuser:
            if not empresa_do_usuario(request.user):
                return redirect("onboarding_empresa")
        return super().dispatch(request, *args, **kwargs)


class EmpresaOnboardingView(AppLoginRequiredMixin, CreateView):
    model = Empresa
    form_class = OnboardingEmpresaForm
    template_name = "core/onboarding_empresa.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or empresa_do_usuario(request.user):
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            empresa = form.save()
            PerfilUsuario.objects.create(usuario=self.request.user, empresa=empresa)
        messages.success(self.request, "Empresa criada. Seu acesso já está vinculado a ela.")
        return redirect(self.success_url)


class EmpresaScopedMixin(OnboardingRequiredMixin):
    empresa_field = "empresa"

    def empresa_ativa(self):
        return empresa_do_usuario(self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        empresa = self.empresa_ativa()
        if self.request.user.is_superuser:
            return queryset
        if not empresa:
            return queryset.none()
        if self.model is Empresa:
            return queryset.filter(pk=empresa.pk)
        return queryset.filter(**{self.empresa_field: empresa})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_superuser:
            limitar_formulario_a_empresa(form, self.empresa_ativa())
        return form

    def form_valid(self, form):
        empresa = self.empresa_ativa()
        if empresa and hasattr(form.instance, self.empresa_field):
            setattr(form.instance, self.empresa_field, empresa)
        return super().form_valid(form)


class SearchableListMixin:
    search_fields = []

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query and self.search_fields:
            filters = Q()
            for field in self.search_fields:
                filters |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(filters)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["has_search"] = bool(self.search_fields)
        return context


class EmpresaListView(EmpresaScopedMixin, ListView):
    model = Empresa
    template_name = "core/list.html"
    context_object_name = "objects"
    extra_context = {
        "title": "Empresas",
        "create_url_name": "empresa_create",
        "edit_url_name": "empresa_update",
        "delete_url_name": "empresa_delete",
        "columns": ["nome", "documento", "ativa"],
    }


class EmpresaCreateView(AppLoginRequiredMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = "core/form.html"
    success_url = reverse_lazy("empresa_list")
    extra_context = {"title": "Nova empresa"}

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            if empresa_do_usuario(request.user):
                target = "empresa_list"
            else:
                target = "onboarding_empresa"
            return redirect(target)
        return super().dispatch(request, *args, **kwargs)


class EmpresaUpdateView(EmpresaScopedMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = "core/form.html"
    success_url = reverse_lazy("empresa_list")
    extra_context = {"title": "Editar empresa"}


class EmpresaDeleteView(EmpresaScopedMixin, DeleteView):
    model = Empresa
    template_name = "core/confirm_delete.html"
    success_url = reverse_lazy("empresa_list")
    extra_context = {"title": "Excluir empresa"}


class ClienteListView(SearchableListMixin, EmpresaScopedMixin, ListView):
    model = Cliente
    template_name = "core/list.html"
    context_object_name = "objects"
    search_fields = ["nome", "documento", "email", "telefone"]
    extra_context = {
        "title": "Clientes",
        "create_url_name": "cliente_create",
        "edit_url_name": "cliente_update",
        "delete_url_name": "cliente_delete",
        "columns": ["nome", "empresa", "email", "ativa"],
    }


class ClienteCreateView(EmpresaScopedMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "core/form.html"
    success_url = reverse_lazy("cliente_list")
    extra_context = {"title": "Novo cliente"}


class ClienteUpdateView(EmpresaScopedMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "core/form.html"
    success_url = reverse_lazy("cliente_list")
    extra_context = {"title": "Editar cliente"}


class ClienteDeleteView(EmpresaScopedMixin, DeleteView):
    model = Cliente
    template_name = "core/confirm_delete.html"
    success_url = reverse_lazy("cliente_list")
    extra_context = {"title": "Excluir cliente"}


class FornecedorListView(SearchableListMixin, EmpresaScopedMixin, ListView):
    model = Fornecedor
    template_name = "core/list.html"
    context_object_name = "objects"
    search_fields = ["nome", "documento", "email", "telefone"]
    extra_context = {
        "title": "Fornecedores",
        "create_url_name": "fornecedor_create",
        "edit_url_name": "fornecedor_update",
        "delete_url_name": "fornecedor_delete",
        "columns": ["nome", "empresa", "email", "ativa"],
    }


class FornecedorCreateView(EmpresaScopedMixin, CreateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = "core/form.html"
    success_url = reverse_lazy("fornecedor_list")
    extra_context = {"title": "Novo fornecedor"}


class FornecedorUpdateView(EmpresaScopedMixin, UpdateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = "core/form.html"
    success_url = reverse_lazy("fornecedor_list")
    extra_context = {"title": "Editar fornecedor"}


class FornecedorDeleteView(EmpresaScopedMixin, DeleteView):
    model = Fornecedor
    template_name = "core/confirm_delete.html"
    success_url = reverse_lazy("fornecedor_list")
    extra_context = {"title": "Excluir fornecedor"}


class ContaListView(SearchableListMixin, EmpresaScopedMixin, ListView):
    model = ContaContabil
    template_name = "core/list.html"
    context_object_name = "objects"
    search_fields = ["codigo", "nome", "tipo"]
    extra_context = {
        "title": "Plano de contas",
        "create_url_name": "conta_create",
        "edit_url_name": "conta_update",
        "delete_url_name": "conta_delete",
        "columns": ["codigo", "nome", "tipo", "ativa"],
    }


class ContaCreateView(EmpresaScopedMixin, CreateView):
    model = ContaContabil
    form_class = ContaContabilForm
    template_name = "core/form.html"
    success_url = reverse_lazy("conta_list")
    extra_context = {"title": "Nova conta contábil"}


class ContaUpdateView(EmpresaScopedMixin, UpdateView):
    model = ContaContabil
    form_class = ContaContabilForm
    template_name = "core/form.html"
    success_url = reverse_lazy("conta_list")
    extra_context = {"title": "Editar conta contábil"}


class ContaDeleteView(EmpresaScopedMixin, DeleteView):
    model = ContaContabil
    template_name = "core/confirm_delete.html"
    success_url = reverse_lazy("conta_list")
    extra_context = {"title": "Excluir conta contábil"}


class LancamentoListView(SearchableListMixin, EmpresaScopedMixin, ListView):
    model = LancamentoContabil
    template_name = "core/lancamento_list.html"
    context_object_name = "objects"
    search_fields = ["historico", "status"]


class LancamentoDetailView(EmpresaScopedMixin, DetailView):
    model = LancamentoContabil
    template_name = "core/lancamento_detail.html"
    context_object_name = "lancamento"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_debito, total_credito = self.object.totais()
        context["total_debito"] = total_debito
        context["total_credito"] = total_credito
        context["diferenca"] = self.object.diferenca()
        context["esta_balanceado"] = self.object.esta_balanceado()
        return context


class LancamentoCreateView(EmpresaScopedMixin, CreateView):
    model = LancamentoContabil
    form_class = LancamentoContabilForm
    template_name = "core/lancamento_form.html"
    success_url = reverse_lazy("lancamento_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Novo lançamento contábil"
        context["formset"] = LancamentoItemFormSet(self.request.POST or None)
        if not self.request.user.is_superuser:
            limitar_formset_lancamento_a_empresa(context["formset"], self.empresa_ativa())
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.criado_por = self.request.user
            if self.empresa_ativa():
                self.object.empresa = self.empresa_ativa()
            self.object.save()
            if formset.is_valid():
                formset.instance = self.object
                formset.save()
                try:
                    self.object.clean()
                except ValidationError as exc:
                    form.add_error(None, exc)
                    transaction.set_rollback(True)
                    return self.form_invalid(form)
                return redirect(self.success_url)
        return self.form_invalid(form)


class LancamentoUpdateView(EmpresaScopedMixin, UpdateView):
    model = LancamentoContabil
    form_class = LancamentoContabilForm
    template_name = "core/lancamento_form.html"
    success_url = reverse_lazy("lancamento_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Editar lançamento contábil"
        context["formset"] = LancamentoItemFormSet(
            self.request.POST or None,
            instance=self.object,
        )
        if not self.request.user.is_superuser:
            limitar_formset_lancamento_a_empresa(context["formset"], self.empresa_ativa())
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        with transaction.atomic():
            self.object = form.save()
            if formset.is_valid():
                formset.save()
                try:
                    self.object.clean()
                except ValidationError as exc:
                    form.add_error(None, exc)
                    transaction.set_rollback(True)
                    return self.form_invalid(form)
                return redirect(self.success_url)
        return self.form_invalid(form)


class LancamentoDeleteView(EmpresaScopedMixin, DeleteView):
    model = LancamentoContabil
    template_name = "core/confirm_delete.html"
    success_url = reverse_lazy("lancamento_list")
    extra_context = {"title": "Excluir lançamento"}


class TituloFinanceiroBaseMixin(EmpresaScopedMixin):
    model = TituloFinanceiro
    form_class = TituloFinanceiroForm

    tipo = None
    list_title = "Títulos financeiros"
    create_title = "Novo título financeiro"
    update_title = "Editar título financeiro"
    success_url_name = "financeiro_receber_list"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.tipo:
            queryset = queryset.filter(tipo=self.tipo)
        return queryset

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.tipo:
            form.fields["tipo"].initial = self.tipo
            form.fields["tipo"].widget = form.fields["tipo"].hidden_widget()
        return form

    def form_valid(self, form):
        if self.tipo:
            form.instance.tipo = self.tipo
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)


class TituloFinanceiroListView(SearchableListMixin, TituloFinanceiroBaseMixin, ListView):
    template_name = "core/financeiro_list.html"
    context_object_name = "objects"
    search_fields = [
        "descricao",
        "status",
        "cliente__nome",
        "fornecedor__nome",
        "observacoes",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.list_title
        context["create_url_name"] = self.create_url_name
        context["edit_url_name"] = self.edit_url_name
        context["delete_url_name"] = self.delete_url_name
        titulos_abertos = self.get_queryset().filter(status=TituloFinanceiro.Status.ABERTO)
        context["total_aberto"] = sum(
            titulo.valor for titulo in titulos_abertos
        )
        return context


class TituloFinanceiroCreateView(TituloFinanceiroBaseMixin, CreateView):
    template_name = "core/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.create_title
        return context


class TituloFinanceiroUpdateView(TituloFinanceiroBaseMixin, UpdateView):
    template_name = "core/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.update_title
        return context


class TituloFinanceiroDeleteView(TituloFinanceiroBaseMixin, DeleteView):
    template_name = "core/confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Excluir título financeiro"
        return context


class ReceberListView(TituloFinanceiroListView):
    tipo = TituloFinanceiro.Tipo.RECEBER
    list_title = "Contas a receber"
    create_url_name = "receber_create"
    edit_url_name = "receber_update"
    delete_url_name = "receber_delete"
    success_url_name = "receber_list"


class ReceberCreateView(TituloFinanceiroCreateView):
    tipo = TituloFinanceiro.Tipo.RECEBER
    create_title = "Nova conta a receber"
    success_url_name = "receber_list"


class ReceberUpdateView(TituloFinanceiroUpdateView):
    tipo = TituloFinanceiro.Tipo.RECEBER
    update_title = "Editar conta a receber"
    success_url_name = "receber_list"


class ReceberDeleteView(TituloFinanceiroDeleteView):
    tipo = TituloFinanceiro.Tipo.RECEBER
    success_url_name = "receber_list"


class PagarListView(TituloFinanceiroListView):
    tipo = TituloFinanceiro.Tipo.PAGAR
    list_title = "Contas a pagar"
    create_url_name = "pagar_create"
    edit_url_name = "pagar_update"
    delete_url_name = "pagar_delete"
    success_url_name = "pagar_list"


class PagarCreateView(TituloFinanceiroCreateView):
    tipo = TituloFinanceiro.Tipo.PAGAR
    create_title = "Nova conta a pagar"
    success_url_name = "pagar_list"


class PagarUpdateView(TituloFinanceiroUpdateView):
    tipo = TituloFinanceiro.Tipo.PAGAR
    update_title = "Editar conta a pagar"
    success_url_name = "pagar_list"


class PagarDeleteView(TituloFinanceiroDeleteView):
    tipo = TituloFinanceiro.Tipo.PAGAR
    success_url_name = "pagar_list"


class RelatorioFinanceiroView(OnboardingRequiredMixin, ListView):
    model = TituloFinanceiro
    template_name = "core/relatorio_financeiro.html"
    context_object_name = "titulos"

    def get_queryset(self):
        queryset = TituloFinanceiro.objects.select_related(
            "empresa",
            "cliente",
            "fornecedor",
        )
        empresa = empresa_do_usuario(self.request.user)
        if self.request.user.is_superuser:
            return queryset
        if not empresa:
            return queryset.none()
        return queryset.filter(empresa=empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.localdate()
        titulos = self.get_queryset()
        abertos = titulos.filter(status=TituloFinanceiro.Status.ABERTO)
        vencidos = abertos.filter(vencimento__lt=hoje)
        receber_aberto = abertos.filter(tipo=TituloFinanceiro.Tipo.RECEBER)
        pagar_aberto = abertos.filter(tipo=TituloFinanceiro.Tipo.PAGAR)
        context["hoje"] = hoje
        context["total_receber_aberto"] = sum(titulo.valor for titulo in receber_aberto)
        context["total_pagar_aberto"] = sum(titulo.valor for titulo in pagar_aberto)
        context["saldo_previsto"] = context["total_receber_aberto"] - context["total_pagar_aberto"]
        context["titulos_vencidos"] = vencidos.order_by("vencimento", "descricao")
        context["total_vencido"] = sum(titulo.valor for titulo in vencidos)
        context["resumo_mensal"] = self._resumo_mensal(abertos)
        return context

    def _resumo_mensal(self, titulos):
        meses = {}
        for titulo in titulos.annotate(mes=TruncMonth("vencimento")).order_by("mes"):
            mes = titulo.mes.date() if hasattr(titulo.mes, "date") else titulo.mes
            chave = mes.replace(day=1)
            if chave not in meses:
                meses[chave] = {
                    "mes": chave,
                    "receber": 0,
                    "pagar": 0,
                    "saldo": 0,
                }
            if titulo.tipo == TituloFinanceiro.Tipo.RECEBER:
                meses[chave]["receber"] += titulo.valor
            else:
                meses[chave]["pagar"] += titulo.valor
            meses[chave]["saldo"] = meses[chave]["receber"] - meses[chave]["pagar"]
        return meses.values()


class TituloFinanceiroCsvView(OnboardingRequiredMixin, View):
    tipo = None
    filename = "titulos.csv"

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}"'
        response.write("\ufeff")
        writer = csv.writer(response, delimiter=";")
        writer.writerow(
            [
                "tipo",
                "descricao",
                "valor",
                "vencimento",
                "status",
                "data_pagamento",
                "cliente",
                "fornecedor",
                "empresa",
            ]
        )
        for titulo in self.get_queryset():
            writer.writerow(
                [
                    titulo.get_tipo_display(),
                    titulo.descricao,
                    titulo.valor,
                    titulo.vencimento.isoformat(),
                    titulo.get_status_display(),
                    titulo.data_pagamento.isoformat() if titulo.data_pagamento else "",
                    titulo.cliente.nome if titulo.cliente else "",
                    titulo.fornecedor.nome if titulo.fornecedor else "",
                    titulo.empresa.nome,
                ]
            )
        return response

    def get_queryset(self):
        queryset = TituloFinanceiro.objects.select_related("empresa", "cliente", "fornecedor")
        empresa = empresa_do_usuario(self.request.user)
        if not self.request.user.is_superuser:
            if not empresa:
                return queryset.none()
            queryset = queryset.filter(empresa=empresa)
        if self.tipo:
            queryset = queryset.filter(tipo=self.tipo)
        return queryset.order_by("vencimento", "descricao")


class ReceberCsvView(TituloFinanceiroCsvView):
    tipo = TituloFinanceiro.Tipo.RECEBER
    filename = "contas-a-receber.csv"


class PagarCsvView(TituloFinanceiroCsvView):
    tipo = TituloFinanceiro.Tipo.PAGAR
    filename = "contas-a-pagar.csv"


class RelatorioFinanceiroCsvView(RelatorioFinanceiroView):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="fluxo-previsto.csv"'
        response.write("\ufeff")
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["mes", "receber", "pagar", "saldo"])
        titulos = self.get_queryset().filter(status=TituloFinanceiro.Status.ABERTO)
        for item in self._resumo_mensal(titulos):
            writer.writerow(
                [
                    item["mes"].isoformat(),
                    item["receber"],
                    item["pagar"],
                    item["saldo"],
                ]
            )
        return response


class CsvImportView(OnboardingRequiredMixin, FormView):
    form_class = CsvUploadForm
    template_name = "core/import_csv.html"
    title = "Importar CSV"
    description = ""
    success_url_name = "dashboard"
    required_headers = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
        context["description"] = self.description
        context["required_headers"] = self.required_headers
        return context

    def form_valid(self, form):
        empresa = empresa_do_usuario(self.request.user)
        if not empresa and not self.request.user.is_superuser:
            return redirect("onboarding_empresa")
        try:
            rows = self._read_rows(form.cleaned_data["arquivo"])
            total = self.import_rows(rows, empresa)
        except ValueError as exc:
            form.add_error("arquivo", str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f"Importação concluída: {total} registro(s).")
        return redirect(reverse_lazy(self.success_url_name))

    def _read_rows(self, uploaded_file):
        content = uploaded_file.read().decode("utf-8-sig")
        sample = content[:2048]
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        reader = csv.DictReader(io.StringIO(content), dialect=dialect)
        headers = reader.fieldnames or []
        missing = [header for header in self.required_headers if header not in headers]
        if missing:
            raise ValueError(f"Cabeçalhos ausentes: {', '.join(missing)}.")
        return list(reader)

    def import_rows(self, rows, empresa):
        raise NotImplementedError


class ClienteCsvImportView(CsvImportView):
    title = "Importar clientes"
    description = "Cabeçalhos: nome, documento, email, telefone."
    required_headers = ["nome"]
    success_url_name = "cliente_list"

    def import_rows(self, rows, empresa):
        total = 0
        for row in rows:
            nome = (row.get("nome") or "").strip()
            if not nome:
                continue
            Cliente.objects.update_or_create(
                empresa=empresa,
                nome=nome,
                defaults={
                    "documento": (row.get("documento") or "").strip(),
                    "email": (row.get("email") or "").strip(),
                    "telefone": (row.get("telefone") or "").strip(),
                    "ativa": True,
                },
            )
            total += 1
        return total


class FornecedorCsvImportView(CsvImportView):
    title = "Importar fornecedores"
    description = "Cabeçalhos: nome, documento, email, telefone."
    required_headers = ["nome"]
    success_url_name = "fornecedor_list"

    def import_rows(self, rows, empresa):
        total = 0
        for row in rows:
            nome = (row.get("nome") or "").strip()
            if not nome:
                continue
            Fornecedor.objects.update_or_create(
                empresa=empresa,
                nome=nome,
                defaults={
                    "documento": (row.get("documento") or "").strip(),
                    "email": (row.get("email") or "").strip(),
                    "telefone": (row.get("telefone") or "").strip(),
                    "ativa": True,
                },
            )
            total += 1
        return total


class ContaCsvImportView(CsvImportView):
    title = "Importar plano de contas"
    description = (
        "Cabeçalhos: codigo, nome, tipo. "
        "Tipos: ATIVO, PASSIVO, PATRIMONIO, RECEITA, DESPESA."
    )
    required_headers = ["codigo", "nome", "tipo"]
    success_url_name = "conta_list"

    def import_rows(self, rows, empresa):
        total = 0
        tipos_validos = {choice[0] for choice in ContaContabil.Tipo.choices}
        for row in rows:
            codigo = (row.get("codigo") or "").strip()
            nome = (row.get("nome") or "").strip()
            tipo = (row.get("tipo") or "").strip().upper()
            if not codigo or not nome:
                continue
            if tipo not in tipos_validos:
                raise ValueError(f"Tipo inválido para a conta {codigo}: {tipo}.")
            ContaContabil.objects.update_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={"nome": nome, "tipo": tipo, "ativa": True},
            )
            total += 1
        return total
