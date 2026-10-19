"""Testes unitários das regras de validação."""

import pytest

from validacao import TAMANHO_MAXIMO, validar_corpo


def test_codigo_valido_e_aceito():
    r = validar_corpo({"codigo": "x = 10"})
    assert r.ok is True


def test_codigo_com_caracteres_especiais_e_aceito():
    r = validar_corpo({"codigo": "x = 10  # açaí ✓ <>&\"'\\n\t"})
    assert r.ok is True


def test_codigo_multilinha_com_indentacao_e_aceito():
    r = validar_corpo({"codigo": "while x > 0:\n    x = x - 1\n"})
    assert r.ok is True


def test_codigo_com_erro_intencional_tambem_e_aceito():
    # O backend não deve presumir que o código é válido (nem tentar parseá-lo).
    r = validar_corpo({"codigo": "if x >> :: ((("})
    assert r.ok is True


def test_texto_vazio():
    r = validar_corpo({"codigo": ""})
    assert (r.ok, r.status, r.erro) == (False, 422, "entrada_vazia")


@pytest.mark.parametrize("texto", [" ", "   ", "\n", "\t", " \n\t  \r\n"])
def test_somente_espacos(texto):
    r = validar_corpo({"codigo": texto})
    assert (r.ok, r.status, r.erro) == (False, 422, "entrada_somente_espacos")


def test_campo_ausente():
    r = validar_corpo({"outro": "x = 1"})
    assert (r.ok, r.status, r.erro) == (False, 400, "campo_ausente")


@pytest.mark.parametrize("valor", [None, 123, 1.5, True, ["x = 1"], {"a": 1}])
def test_campo_com_tipo_errado(valor):
    r = validar_corpo({"codigo": valor})
    assert (r.ok, r.status, r.erro) == (False, 400, "campo_invalido")


@pytest.mark.parametrize("corpo", [None, "x = 1", 10, ["codigo"]])
def test_corpo_que_nao_e_objeto(corpo):
    r = validar_corpo(corpo)
    assert (r.ok, r.status, r.erro) == (False, 400, "corpo_invalido")


def test_limite_de_tamanho():
    assert validar_corpo({"codigo": "a" * TAMANHO_MAXIMO}).ok is True
    r = validar_corpo({"codigo": "a" * (TAMANHO_MAXIMO + 1)})
    assert (r.ok, r.status, r.erro) == (False, 413, "entrada_muito_grande")
