"""Casos de teste documentados em docs/casos-de-teste.md (CT-01 a CT-18).

Cada caso segue o modelo: ID, categoria, entrada, resultado esperado.
Os casos semânticos (CT-S01, CT-S02) ficam pendentes até a Etapa 5.
"""

import pytest

from app import app

VALIDOS = [
    ("CT-01", "x = 10\n", 4),
    ("CT-02", "a = 2 + 3 * 4\n", 8),
    ("CT-03", "if x > 0:\n    y = 1\nelse:\n    y = 2\n", 13),
    ("CT-04", "while i < 10:\n    i = i + 1\n", 11),
    ("CT-05", "x = (1 + 2) * -3\n", 9),
]

# (id, entrada, linha, coluna do primeiro erro léxico)
LEXICOS = [
    ("CT-06", "x = 10 @ 2\n", 1, 8),
    ("CT-07", "x = 3.\n", 1, 5),
    ("CT-08", "if x > 0:\n    y = 1\n  z = 2\n", 3, 1),
    ("CT-17", "x = 1 @\ny = (\n", 1, 7),
]

# (id, entrada, linha, coluna, trecho esperado na mensagem)
SINTATICOS = [
    ("CT-09", "x = 10 +\n", 1, 9, "falta o operando"),
    ("CT-10", "if x > 0\n    y = 1\n", 1, 9, "Faltou o ':'"),
    ("CT-11", "x = (1 + 2\n", 1, 11, "não foi fechado"),
    ("CT-12", "else:\n    x = 1\n", 1, 1, "'else' sem um 'if'"),
    ("CT-13", "while x:\ny = 1\n", 2, 1, "bloco indentado"),
    ("CT-14", "if = 3\n", 1, 1, "palavra reservada"),
    ("CT-15", "a < b < c\n", 1, 7, "Comparação encadeada"),
    ("CT-18", "(" * 26 + "1" + ")" * 26 + "\n", 1, 26, "aninhados demais"),
]


@pytest.fixture()
def cliente():
    return app.test_client()


def analisar(cliente, codigo):
    resposta = cliente.post("/api/analisar", json={"codigo": codigo})
    return resposta.status_code, resposta.get_json()


@pytest.mark.parametrize("id_,codigo,nos", VALIDOS)
def test_validos(cliente, id_, codigo, nos):
    status, j = analisar(cliente, codigo)
    assert status == 200
    assert j["lexico"]["erros"] == []
    assert j["sintatico"]["executado"] is True
    assert j["sintatico"]["sucesso"] is True
    assert j["sintatico"]["resumo"]["total_nos"] == nos


@pytest.mark.parametrize("id_,codigo,linha,coluna", LEXICOS)
def test_erros_lexicos_nao_executam_o_parser(cliente, id_, codigo, linha, coluna):
    status, j = analisar(cliente, codigo)
    assert status == 200
    assert len(j["lexico"]["erros"]) == 1
    erro = j["lexico"]["erros"][0]
    assert (erro["linha"], erro["coluna"]) == (linha, coluna)
    assert j["sintatico"]["executado"] is False
    assert j["sintatico"]["ast"] is None
    assert j["sintatico"]["erros"] == []


@pytest.mark.parametrize("id_,codigo,linha,coluna,trecho", SINTATICOS)
def test_erros_sintaticos(cliente, id_, codigo, linha, coluna, trecho):
    status, j = analisar(cliente, codigo)
    assert status == 200
    assert j["lexico"]["erros"] == []
    assert j["sintatico"]["executado"] is True
    assert j["sintatico"]["sucesso"] is False
    assert j["sintatico"]["ast"] is None
    erros = j["sintatico"]["erros"]
    assert len(erros) == 1
    assert (erros[0]["linha"], erros[0]["coluna"]) == (linha, coluna)
    assert trecho in erros[0]["mensagem"]
    for campo in ("encontrado", "esperado", "mensagem"):
        assert campo in erros[0]


def test_ct16_codigo_vazio(cliente):
    status, _ = analisar(cliente, "")
    assert status == 422


@pytest.mark.skip(reason="CT-S01: análise semântica é a Etapa 5 (variável não definida)")
def test_ct_s01_variavel_nao_definida(cliente):
    ...


@pytest.mark.skip(reason="CT-S02: análise semântica é a Etapa 5 (divisão por zero)")
def test_ct_s02_divisao_por_zero(cliente):
    ...
