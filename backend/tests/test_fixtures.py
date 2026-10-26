"""Garante que as respostas usadas nos testes do frontend continuam iguais
ao que o backend devolve hoje (se o scanner mudar, este teste avisa)."""

import os

from gerar_fixtures import DESTINO, gerar, serializar


def test_fixtures_do_frontend_estao_sincronizadas_com_o_scanner():
    caminho = os.path.join(DESTINO, "respostas.json")
    with open(caminho, encoding="utf-8") as f:
        gravado = f.read()
    assert gravado == serializar(gerar()), (
        "Fixtures desatualizadas. Rode: python tests/gerar_fixtures.py (na pasta backend)"
    )
