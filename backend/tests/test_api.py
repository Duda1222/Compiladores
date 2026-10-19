"""Testes dos endpoints da API (contrato HTTP) e de regressão da Etapa 1."""

import json

import pytest

import app as modulo_app
from validacao import TAMANHO_MAXIMO


# ---------------------------------------------------------------- regressão
def test_regressao_hello(client):
    r = client.get("/api/hello")
    assert r.status_code == 200
    assert r.get_json() == {"message": "Hello, World!"}


def test_regressao_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


# --------------------------------------------------------- requisição válida
def test_analisar_codigo_valido(client):
    r = client.post("/api/analisar", json={"codigo": "x = 10"})
    assert r.status_code == 200
    assert r.is_json
    corpo = r.get_json()
    assert corpo["recebido"] is True
    assert corpo["mensagem"] == "Código recebido com sucesso."
    assert corpo["linhas"] == 1
    assert corpo["caracteres"] == 6


def test_analisar_conta_linhas_e_caracteres_do_que_foi_enviado(client):
    codigo = "x = 3\nwhile x > 0:\n    x = x - 1\n"
    corpo = client.post("/api/analisar", json={"codigo": codigo}).get_json()
    assert corpo["linhas"] == 3
    assert corpo["caracteres"] == len(codigo)


def test_analisar_resposta_depende_da_entrada(client):
    a = client.post("/api/analisar", json={"codigo": "a"}).get_json()
    b = client.post("/api/analisar", json={"codigo": "a\nb\nc"}).get_json()
    assert a["linhas"] != b["linhas"]


def test_analisar_aceita_caracteres_especiais(client):
    codigo = "x = 1  # açaí ✓ <script>&\"'"
    r = client.post("/api/analisar", json={"codigo": codigo})
    assert r.status_code == 200
    assert r.get_json()["caracteres"] == len(codigo)


def test_analisar_aceita_codigo_invalido_como_python(client):
    r = client.post("/api/analisar", json={"codigo": "if x >> :: ((("})
    assert r.status_code == 200
    assert r.get_json()["recebido"] is True


def test_analisar_aceita_tamanho_maximo(client):
    r = client.post("/api/analisar", json={"codigo": "a" * TAMANHO_MAXIMO})
    assert r.status_code == 200


# -------------------------------------------------------- requisição inválida
def test_analisar_texto_vazio(client):
    r = client.post("/api/analisar", json={"codigo": ""})
    assert r.status_code == 422
    corpo = r.get_json()
    assert corpo["recebido"] is False
    assert corpo["erro"] == "entrada_vazia"
    assert corpo["mensagem"] == "Informe um código-fonte antes de solicitar a análise."


@pytest.mark.parametrize("texto", ["   ", "\n\n", "\t \n"])
def test_analisar_somente_espacos(client, texto):
    r = client.post("/api/analisar", json={"codigo": texto})
    assert r.status_code == 422
    assert r.get_json()["erro"] == "entrada_somente_espacos"


def test_analisar_campo_ausente(client):
    r = client.post("/api/analisar", json={"outro": "x"})
    assert r.status_code == 400
    assert r.get_json()["erro"] == "campo_ausente"


@pytest.mark.parametrize("valor", [None, 1, ["x"], {"a": 1}, True])
def test_analisar_campo_com_tipo_invalido(client, valor):
    r = client.post("/api/analisar", json={"codigo": valor})
    assert r.status_code == 400
    assert r.get_json()["erro"] == "campo_invalido"


def test_analisar_json_malformado(client):
    r = client.post(
        "/api/analisar", data="{codigo: x", content_type="application/json"
    )
    assert r.status_code == 400
    assert r.get_json()["erro"] == "corpo_invalido"


def test_analisar_sem_corpo(client):
    r = client.post("/api/analisar")
    assert r.status_code == 400
    assert r.get_json()["erro"] == "corpo_invalido"


def test_analisar_content_type_incorreto(client):
    r = client.post(
        "/api/analisar",
        data=json.dumps({"codigo": "x = 1"}),
        content_type="text/plain",
    )
    assert r.status_code == 400
    assert r.get_json()["erro"] == "corpo_invalido"


def test_analisar_json_que_nao_e_objeto(client):
    r = client.post("/api/analisar", json=["x = 1"])
    assert r.status_code == 400
    assert r.get_json()["erro"] == "corpo_invalido"


def test_analisar_acima_do_limite(client):
    r = client.post("/api/analisar", json={"codigo": "a" * (TAMANHO_MAXIMO + 1)})
    assert r.status_code == 413
    assert r.get_json()["erro"] == "entrada_muito_grande"


# ------------------------------------------------------------ erros gerais
def test_metodo_nao_permitido(client):
    r = client.get("/api/analisar")
    assert r.status_code == 405
    corpo = r.get_json()
    assert corpo["recebido"] is False
    assert corpo["erro"] == "requisicao_invalida"


def test_rota_inexistente_devolve_json(client):
    r = client.get("/api/nao-existe")
    assert r.status_code == 404
    assert r.is_json
    assert r.get_json()["recebido"] is False


def test_erro_inesperado_nao_expoe_detalhes(client, monkeypatch):
    def quebra(_corpo):
        raise RuntimeError("segredo /app/interno.py SENHA=123")

    monkeypatch.setattr(modulo_app, "validar_corpo", quebra)
    r = client.post("/api/analisar", json={"codigo": "x = 1"})
    assert r.status_code == 500
    texto = r.get_data(as_text=True)
    assert "segredo" not in texto
    assert "interno.py" not in texto
    assert "SENHA" not in texto
    assert "Traceback" not in texto
    corpo = r.get_json()
    assert corpo["erro"] == "erro_interno"
    assert corpo["recebido"] is False
