import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import Cliente, ContaContabil, Empresa, Fornecedor, PerfilUsuario


def csv_file(name, content):
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


@pytest.mark.django_db
def test_importacao_csv_clientes_cria_registros_na_empresa_do_usuario(client, django_user_model):
    empresa = Empresa.objects.create(nome="Empresa CSV")
    user = django_user_model.objects.create_user(username="cliente-csv", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa)
    client.force_login(user)

    response = client.post(
        reverse("cliente_import"),
        {
            "arquivo": csv_file(
                "clientes.csv",
                "nome;documento;email;telefone\n"
                "Cliente Importado;123456;cliente@example.com;51999999999\n",
            )
        },
    )

    assert response.status_code == 302
    cliente = Cliente.objects.get(empresa=empresa, nome="Cliente Importado")
    assert cliente.documento == "123456"
    assert cliente.email == "cliente@example.com"


@pytest.mark.django_db
def test_importacao_csv_fornecedores_cria_registros_na_empresa_do_usuario(
    client, django_user_model
):
    empresa = Empresa.objects.create(nome="Empresa CSV")
    user = django_user_model.objects.create_user(
        username="fornecedor-csv", password="senha-teste"
    )
    PerfilUsuario.objects.create(usuario=user, empresa=empresa)
    client.force_login(user)

    response = client.post(
        reverse("fornecedor_import"),
        {
            "arquivo": csv_file(
                "fornecedores.csv",
                "nome;documento;email;telefone\n"
                "Fornecedor Importado;987654;fornecedor@example.com;51988888888\n",
            )
        },
    )

    assert response.status_code == 302
    fornecedor = Fornecedor.objects.get(empresa=empresa, nome="Fornecedor Importado")
    assert fornecedor.documento == "987654"
    assert fornecedor.email == "fornecedor@example.com"


@pytest.mark.django_db
def test_importacao_csv_plano_de_contas_cria_contas_na_empresa_do_usuario(
    client, django_user_model
):
    empresa = Empresa.objects.create(nome="Empresa CSV")
    user = django_user_model.objects.create_user(username="conta-csv", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa)
    client.force_login(user)

    response = client.post(
        reverse("conta_import"),
        {"arquivo": csv_file("contas.csv", "codigo;nome;tipo\n1.1.1;Caixa;ATIVO\n")},
    )

    assert response.status_code == 302
    conta = ContaContabil.objects.get(empresa=empresa, codigo="1.1.1")
    assert conta.nome == "Caixa"
    assert conta.tipo == ContaContabil.Tipo.ATIVO


@pytest.mark.django_db
def test_importacao_csv_rejeita_cabecalho_obrigatorio_ausente(client, django_user_model):
    empresa = Empresa.objects.create(nome="Empresa CSV")
    user = django_user_model.objects.create_user(username="erro-csv", password="senha-teste")
    PerfilUsuario.objects.create(usuario=user, empresa=empresa)
    client.force_login(user)

    response = client.post(
        reverse("conta_import"),
        {"arquivo": csv_file("contas.csv", "codigo;nome\n1.1.1;Caixa\n")},
    )

    assert response.status_code == 200
    assert "Cabeçalhos ausentes" in response.content.decode()
    assert not ContaContabil.objects.filter(empresa=empresa).exists()
