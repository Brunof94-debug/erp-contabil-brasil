from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import (
    Cliente,
    ContaContabil,
    Empresa,
    Fornecedor,
    LancamentoContabil,
    LancamentoItem,
    TituloFinanceiro,
)


class CadastroUsuarioForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="E-mail",
        help_text="Use um e-mail válido para recuperação de acesso.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "Usuário",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["nome", "documento", "ativa"]
        labels = {
            "nome": "Nome da empresa",
            "documento": "CNPJ/CPF",
            "ativa": "Empresa ativa",
        }
        help_texts = {
            "documento": "Opcional no MVP. Use apenas se fizer sentido para a demonstração.",
        }


class OnboardingEmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["nome", "documento"]
        labels = {
            "nome": "Nome da empresa",
            "documento": "CNPJ/CPF da empresa ou responsável",
        }
        help_texts = {
            "documento": "Opcional nesta fase. Pode ser preenchido depois.",
        }


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["empresa", "nome", "documento", "email", "telefone", "ativa"]
        labels = {
            "documento": "CPF/CNPJ",
            "ativa": "Cliente ativo",
        }
        help_texts = {
            "documento": "Opcional. Ajuda a diferenciar clientes com nomes parecidos.",
            "email": "Opcional. Usado apenas para contato operacional.",
        }


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ["empresa", "nome", "documento", "email", "telefone", "ativa"]
        labels = {
            "documento": "CPF/CNPJ",
            "ativa": "Fornecedor ativo",
        }
        help_texts = {
            "documento": "Opcional. Ajuda a organizar obrigações e pagamentos.",
            "email": "Opcional. Usado apenas para contato operacional.",
        }


class ContaContabilForm(forms.ModelForm):
    class Meta:
        model = ContaContabil
        fields = ["empresa", "codigo", "nome", "tipo", "conta_pai", "ativa"]
        labels = {
            "codigo": "Código contábil",
            "conta_pai": "Conta superior",
            "ativa": "Conta ativa",
        }
        help_texts = {
            "codigo": "Exemplo: 1.1.1 para caixa ou bancos.",
            "conta_pai": "Opcional. Use para montar hierarquia do plano de contas.",
        }


class LancamentoContabilForm(forms.ModelForm):
    class Meta:
        model = LancamentoContabil
        fields = ["empresa", "data", "historico", "status"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "historico": "Histórico",
        }
        help_texts = {
            "historico": "Descreva o fato contábil com clareza.",
            "status": "Rascunho permite revisar antes de considerar o lançamento postado.",
        }


class TituloFinanceiroForm(forms.ModelForm):
    class Meta:
        model = TituloFinanceiro
        fields = [
            "empresa",
            "tipo",
            "descricao",
            "valor",
            "vencimento",
            "data_pagamento",
            "status",
            "cliente",
            "fornecedor",
            "observacoes",
        ]
        widgets = {
            "vencimento": forms.DateInput(attrs={"type": "date"}),
            "data_pagamento": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "descricao": "Descrição",
            "data_pagamento": "Data de pagamento/recebimento",
            "observacoes": "Observações",
        }
        help_texts = {
            "valor": "Informe o valor positivo do título.",
            "data_pagamento": "Preencha somente quando o status for pago/recebido.",
            "cliente": "Use cliente em contas a receber.",
            "fornecedor": "Use fornecedor em contas a pagar.",
        }


class CsvUploadForm(forms.Form):
    arquivo = forms.FileField(
        label="Arquivo CSV",
        help_text="Use CSV com cabeçalhos. Separadores aceitos: vírgula ou ponto e vírgula.",
    )


LancamentoItemFormSet = inlineformset_factory(
    LancamentoContabil,
    LancamentoItem,
    fields=["conta", "debito", "credito", "complemento"],
    extra=2,
    can_delete=True,
)


def limitar_formulario_a_empresa(form: forms.ModelForm, empresa: Empresa | None) -> None:
    if not empresa:
        return
    if "empresa" in form.fields:
        form.fields["empresa"].queryset = Empresa.objects.filter(pk=empresa.pk)
        form.fields["empresa"].initial = empresa
        form.fields["empresa"].widget = forms.HiddenInput()
    if "conta_pai" in form.fields:
        form.fields["conta_pai"].queryset = ContaContabil.objects.filter(empresa=empresa)
    if "cliente" in form.fields:
        form.fields["cliente"].queryset = Cliente.objects.filter(empresa=empresa, ativa=True)
    if "fornecedor" in form.fields:
        form.fields["fornecedor"].queryset = Fornecedor.objects.filter(empresa=empresa, ativa=True)


def limitar_formset_lancamento_a_empresa(formset, empresa: Empresa | None) -> None:
    if not empresa:
        return
    for form in formset.forms:
        if "conta" in form.fields:
            form.fields["conta"].queryset = ContaContabil.objects.filter(
                empresa=empresa,
                ativa=True,
            )
