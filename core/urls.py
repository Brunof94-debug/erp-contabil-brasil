from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("healthz/", views.healthz, name="healthz"),
    path("cadastro/", views.CadastroUsuarioView.as_view(), name="signup"),
    path("onboarding/empresa/", views.EmpresaOnboardingView.as_view(), name="onboarding_empresa"),
    path("empresas/", views.EmpresaListView.as_view(), name="empresa_list"),
    path("empresas/nova/", views.EmpresaCreateView.as_view(), name="empresa_create"),
    path("empresas/<uuid:pk>/editar/", views.EmpresaUpdateView.as_view(), name="empresa_update"),
    path("empresas/<uuid:pk>/excluir/", views.EmpresaDeleteView.as_view(), name="empresa_delete"),
    path("clientes/", views.ClienteListView.as_view(), name="cliente_list"),
    path("clientes/importar/", views.ClienteCsvImportView.as_view(), name="cliente_import"),
    path("clientes/novo/", views.ClienteCreateView.as_view(), name="cliente_create"),
    path("clientes/<uuid:pk>/editar/", views.ClienteUpdateView.as_view(), name="cliente_update"),
    path("clientes/<uuid:pk>/excluir/", views.ClienteDeleteView.as_view(), name="cliente_delete"),
    path("fornecedores/", views.FornecedorListView.as_view(), name="fornecedor_list"),
    path(
        "fornecedores/importar/",
        views.FornecedorCsvImportView.as_view(),
        name="fornecedor_import",
    ),
    path("fornecedores/novo/", views.FornecedorCreateView.as_view(), name="fornecedor_create"),
    path(
        "fornecedores/<uuid:pk>/editar/",
        views.FornecedorUpdateView.as_view(),
        name="fornecedor_update",
    ),
    path(
        "fornecedores/<uuid:pk>/excluir/",
        views.FornecedorDeleteView.as_view(),
        name="fornecedor_delete",
    ),
    path("plano-de-contas/", views.ContaListView.as_view(), name="conta_list"),
    path("plano-de-contas/importar/", views.ContaCsvImportView.as_view(), name="conta_import"),
    path("plano-de-contas/nova/", views.ContaCreateView.as_view(), name="conta_create"),
    path("plano-de-contas/<uuid:pk>/editar/", views.ContaUpdateView.as_view(), name="conta_update"),
    path(
        "plano-de-contas/<uuid:pk>/excluir/",
        views.ContaDeleteView.as_view(),
        name="conta_delete",
    ),
    path("lancamentos/", views.LancamentoListView.as_view(), name="lancamento_list"),
    path("lancamentos/novo/", views.LancamentoCreateView.as_view(), name="lancamento_create"),
    path(
        "lancamentos/<uuid:pk>/",
        views.LancamentoDetailView.as_view(),
        name="lancamento_detail",
    ),
    path(
        "lancamentos/<uuid:pk>/editar/",
        views.LancamentoUpdateView.as_view(),
        name="lancamento_update",
    ),
    path(
        "lancamentos/<uuid:pk>/excluir/",
        views.LancamentoDeleteView.as_view(),
        name="lancamento_delete",
    ),
    path("financeiro/receber/", views.ReceberListView.as_view(), name="receber_list"),
    path("financeiro/receber/exportar.csv", views.ReceberCsvView.as_view(), name="receber_csv"),
    path("financeiro/receber/novo/", views.ReceberCreateView.as_view(), name="receber_create"),
    path(
        "financeiro/receber/<uuid:pk>/editar/",
        views.ReceberUpdateView.as_view(),
        name="receber_update",
    ),
    path(
        "financeiro/receber/<uuid:pk>/excluir/",
        views.ReceberDeleteView.as_view(),
        name="receber_delete",
    ),
    path("financeiro/pagar/", views.PagarListView.as_view(), name="pagar_list"),
    path("financeiro/pagar/exportar.csv", views.PagarCsvView.as_view(), name="pagar_csv"),
    path(
        "financeiro/relatorios/",
        views.RelatorioFinanceiroView.as_view(),
        name="financeiro_report",
    ),
    path(
        "financeiro/relatorios/exportar.csv",
        views.RelatorioFinanceiroCsvView.as_view(),
        name="financeiro_report_csv",
    ),
    path("financeiro/pagar/novo/", views.PagarCreateView.as_view(), name="pagar_create"),
    path(
        "financeiro/pagar/<uuid:pk>/editar/",
        views.PagarUpdateView.as_view(),
        name="pagar_update",
    ),
    path(
        "financeiro/pagar/<uuid:pk>/excluir/",
        views.PagarDeleteView.as_view(),
        name="pagar_delete",
    ),
]
