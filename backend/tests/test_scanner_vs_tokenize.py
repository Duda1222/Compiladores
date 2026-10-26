"""Verificação cruzada do scanner contra o módulo ``tokenize`` da biblioteca
padrão do Python (a implementação de referência do tokenizador).

Vale apenas para programas DENTRO do subconjunto (sem erros léxicos e sem
parênteses abertos no fim do arquivo). Compara tipo, lexema e posição de cada
token, ignorando o que o ``tokenize`` emite a mais (COMMENT, NL).
"""

import io
import keyword
import random
import tokenize

import pytest

from scanner import analisar_lexico

# tokenize.OP é refinado pelo lexema
_RELACIONAIS = {"<", ">", "<=", ">=", "==", "!="}
_ARITMETICOS = {"+", "-", "*", "/"}


def _tipo_referencia(tok):
    if tok.type == tokenize.NAME:
        return "PALAVRA_RESERVADA" if keyword.iskeyword(tok.string) else "IDENTIFICADOR"
    if tok.type == tokenize.NUMBER:
        return "LITERAL_DECIMAL" if "." in tok.string else "LITERAL_INTEIRO"
    if tok.type == tokenize.OP:
        if tok.string in _RELACIONAIS:
            return "OPERADOR_RELACIONAL"
        if tok.string in _ARITMETICOS:
            return "OPERADOR_ARITMETICO"
        if tok.string == "=":
            return "OPERADOR_ATRIBUICAO"
        return "DELIMITADOR"
    return {
        tokenize.NEWLINE: "NEWLINE",
        tokenize.INDENT: "INDENT",
        tokenize.DEDENT: "DEDENT",
        tokenize.ENDMARKER: "FIM_DE_ARQUIVO",
    }.get(tok.type)


def referencia(codigo):
    saida = []
    for tok in tokenize.generate_tokens(io.StringIO(codigo).readline):
        tipo = _tipo_referencia(tok)
        if tipo is None:  # COMMENT, NL
            continue
        linha, col = tok.start
        saida.append((tipo, tok.string, linha, col + 1))
    return saida


def nosso(codigo):
    r = analisar_lexico(codigo)
    assert r.sucesso, r.erros
    return [(t.tipo, t.lexema, t.linha, t.coluna) for t in r.tokens]


def comparar(codigo, posicoes=True):
    esperado, obtido = referencia(codigo), nosso(codigo)
    if not posicoes:
        esperado = [e[:2] for e in esperado]
        obtido = [o[:2] for o in obtido]
    assert obtido == esperado, codigo


PROGRAMAS = [
    "x = 10\n",
    "x = 10",
    "y = 3.14\n",
    "a = 10\nb = 5\nresultado = (a + b) * 2 - a / b\n",
    "x = 7\nif x > 0:\n    x = x + 1\nelse:\n    x = x - 1\n",
    "x = 5\nwhile x != 0:\n    x = x - 1\n",
    "x = 6\nwhile x > 0:\n    if x > 3:\n        x = x - 2\n    else:\n        x = x - 1\n",
    "# comentário\nx = 4   # valor\n\n\ndobro = x * 2\n",
    "a = 1\nb = 2.5\nc = a + b - 1 * 2 / 4\nok = a == b\nok = a != b\nok = a < b\nok = a <= b\nok = a > b\nok = a >= b\n",
    "a = (1 +\n        2 +\n  3)\nb = 4\n",
    "if x:\n    y = 1\n\n\n    z = 2\n",
    "if x:\n    # só comentário no meio\n    y = 1\n# comentário na coluna 1\n    z = 2\n",
    "while a:\n    if b:\n        c = 1\nd = 2\n",
    "x = 1\n   \n\t\ny = 2\n",
    "x=1+2*3\n",
    "a<=b\n",
    "x = 0.5\ny = 00.5\nz = 0\n",
    "if x == 1:\n    pass\n",
    "",
    "\n\n",
    "# só comentário",
]


@pytest.mark.parametrize("codigo", PROGRAMAS)
def test_programas_fixos_iguais_ao_tokenize(codigo):
    comparar(codigo, posicoes=False)


@pytest.mark.parametrize("codigo", [p for p in PROGRAMAS if "\n   \n" not in p])
def test_posicoes_iguais_ao_tokenize_nos_programas_fixos(codigo):
    comparar(codigo)


def _gerar_programa(rng):
    """Gera um programa válido do subconjunto, com blocos aninhados."""
    nomes = ["x", "y", "valor", "_t", "a1"]
    linhas = []

    def expr(prof=0):
        if prof > 1 or rng.random() < 0.5:
            return rng.choice(nomes + ["0", "7", "42", "3.14", "0.5"])
        op = rng.choice(["+", "-", "*", "/"])
        e = f"{expr(prof + 1)} {op} {expr(prof + 1)}"
        return f"({e})" if rng.random() < 0.3 else e

    def cmp_():
        return f"{expr(1)} {rng.choice(['<', '>', '<=', '>=', '==', '!='])} {expr(1)}"

    def bloco(nivel, restante):
        n = rng.randint(1, 3)
        for _ in range(n):
            recuo = " " * (4 * nivel)
            r = rng.random()
            if r < 0.55 or restante <= 0:
                linhas.append(f"{recuo}{rng.choice(nomes)} = {expr()}" + ("  # nota" if rng.random() < 0.2 else ""))
            elif r < 0.8:
                linhas.append(f"{recuo}if {cmp_()}:")
                bloco(nivel + 1, restante - 1)
                if rng.random() < 0.5:
                    linhas.append(f"{recuo}else:")
                    bloco(nivel + 1, restante - 1)
            else:
                linhas.append(f"{recuo}while {cmp_()}:")
                bloco(nivel + 1, restante - 1)
            if rng.random() < 0.15:
                linhas.append("")
            if rng.random() < 0.1:
                linhas.append(f"{recuo}# comentário solto")

    bloco(0, 3)
    return "\n".join(linhas) + ("\n" if rng.random() < 0.8 else "")


def test_programas_aleatorios_do_subconjunto_iguais_ao_tokenize():
    rng = random.Random(2026)
    for _ in range(300):
        codigo = _gerar_programa(rng)
        comparar(codigo)
