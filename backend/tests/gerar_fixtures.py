"""Gera as respostas de exemplo usadas pelos testes do frontend.

As respostas vêm do scanner REAL (via endpoint Flask), assim os testes de
interface usam exatamente o contrato que o backend devolve.

Uso (a partir da pasta backend/):
    python tests/gerar_fixtures.py
"""

import json
import os
import sys

RAIZ_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ_BACKEND)

from app import app  # noqa: E402

DESTINO = os.path.join(os.path.dirname(RAIZ_BACKEND), "frontend", "tests", "fixtures")

CASOS = {
    "valido": "x = 10\nwhile x > 0:\n    x = x - 1\n",
    "erros": 'preco = 10 @ 2\nvalor = 3.14.15\nnome = "Ana"\ny = 12abc\ndef f\n',
    "comentarios": "# so um comentario\n",
    "html": "<b>x</b> = 1  # <script>alert(1)</script>\n",
    "tabulacao": "if x:\n\ty = 1\n",
    "decimais": "a = 2.5\nb = 3 >= a\n",
}


def gerar() -> dict:
    cliente = app.test_client()
    saida = {}
    for nome, codigo in CASOS.items():
        resposta = cliente.post("/api/analisar", json={"codigo": codigo})
        assert resposta.status_code == 200, nome
        saida[nome] = {"codigo": codigo, "resposta": resposta.get_json()}
    return saida


def serializar(dados: dict) -> str:
    return json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    os.makedirs(DESTINO, exist_ok=True)
    caminho = os.path.join(DESTINO, "respostas.json")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(serializar(gerar()))
    print("Fixtures gravadas em", caminho)
