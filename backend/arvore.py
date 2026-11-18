"""Árvore sintática abstrata (AST) do subconjunto de Python.

A AST guarda só o que importa para o significado do programa. Parênteses,
dois-pontos, NEWLINE, INDENT e DEDENT servem para RECONHECER a estrutura,
mas não aparecem aqui (eles aparecem na árvore de derivação, que o parser
também devolve para comparação).

Formato JSON de cada nó (documentado em docs/ast.md):

    {
      "tipo":       "OperacaoBinaria",     # tipo do nó
      "papel":      "esquerda",            # função do nó dentro do pai (ou null)
      "regra":      "soma → termo { ('+' | '-') termo }",
      "linha": 1, "coluna": 5,             # início (1-based)
      "linha_fim": 1, "coluna_fim": 10,    # posição logo APÓS o último caractere
      "atributos":  {"operador": "+", ...},
      "filhos":     [ ...nós... ]
    }
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Tipos de nó
PROGRAMA = "Programa"
ATRIBUICAO = "Atribuicao"
EXPRESSAO_COMANDO = "ExpressaoComando"
CONDICIONAL = "Condicional"
REPETICAO = "Repeticao"
BLOCO = "Bloco"
OPERACAO_BINARIA = "OperacaoBinaria"
COMPARACAO = "Comparacao"
OPERACAO_UNARIA = "OperacaoUnaria"
IDENTIFICADOR = "Identificador"
NUMERO = "Numero"

TIPOS_NO = (
    PROGRAMA,
    ATRIBUICAO,
    EXPRESSAO_COMANDO,
    CONDICIONAL,
    REPETICAO,
    BLOCO,
    OPERACAO_BINARIA,
    COMPARACAO,
    OPERACAO_UNARIA,
    IDENTIFICADOR,
    NUMERO,
)

# Regra da gramática que gera cada tipo de nó (ver docs/gramatica.md).
REGRA_DO_NO = {
    PROGRAMA: "programa → { comando } FIM_DE_ARQUIVO",
    ATRIBUICAO: "atribuicao → IDENTIFICADOR '=' expressao",
    EXPRESSAO_COMANDO: "comando_simples → expressao NEWLINE",
    CONDICIONAL: "condicional → 'if' expressao ':' bloco [ 'else' ':' bloco ]",
    REPETICAO: "repeticao → 'while' expressao ':' bloco",
    BLOCO: "bloco → NEWLINE INDENT comando { comando } DEDENT",
    OPERACAO_BINARIA: "soma → termo { ('+' | '-') termo }  |  termo → unario { ('*' | '/') unario }",
    COMPARACAO: "expressao → soma [ OPERADOR_RELACIONAL soma ]",
    OPERACAO_UNARIA: "unario → ('+' | '-') unario",
    IDENTIFICADOR: "primario → IDENTIFICADOR",
    NUMERO: "primario → LITERAL_INTEIRO | LITERAL_DECIMAL",
}

# Limite de altura da árvore: protege a serialização e a interface contra
# entradas absurdamente aninhadas (ex.: 5000 sinais de menos seguidos).
MAX_ALTURA = 150


@dataclass
class No:
    tipo: str
    linha: int
    coluna: int
    linha_fim: int
    coluna_fim: int
    atributos: dict = field(default_factory=dict)
    filhos: list["No"] = field(default_factory=list)
    papel: str | None = None
    altura: int = 1

    @property
    def regra(self) -> str:
        return REGRA_DO_NO[self.tipo]

    def como_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "papel": self.papel,
            "regra": self.regra,
            "linha": self.linha,
            "coluna": self.coluna,
            "linha_fim": self.linha_fim,
            "coluna_fim": self.coluna_fim,
            "atributos": dict(self.atributos),
            "filhos": [f.como_dict() for f in self.filhos],
        }


def criar_no(tipo, inicio, fim, atributos=None, filhos=()):
    """Cria um nó. ``filhos`` é uma sequência de pares ``(papel, nó)``."""
    lista = []
    altura = 0
    for papel, filho in filhos:
        filho.papel = papel
        lista.append(filho)
        altura = max(altura, filho.altura)
    return No(
        tipo=tipo,
        linha=inicio[0],
        coluna=inicio[1],
        linha_fim=fim[0],
        coluna_fim=fim[1],
        atributos=atributos or {},
        filhos=lista,
        altura=altura + 1,
    )


def contar(no: No) -> dict:
    """Estatísticas da árvore: total de nós, altura e contagem por tipo."""
    por_tipo: dict[str, int] = {}
    pilha = [no]
    total = 0
    while pilha:
        atual = pilha.pop()
        total += 1
        por_tipo[atual.tipo] = por_tipo.get(atual.tipo, 0) + 1
        pilha.extend(atual.filhos)
    return {"total_nos": total, "altura": no.altura, "por_tipo": por_tipo}


def em_texto(no: No, nivel: int = 0) -> str:
    """Árvore indentada em texto (usada nos testes e na documentação)."""
    detalhe = ""
    if "nome" in no.atributos:
        detalhe = f" {no.atributos['nome']}"
    elif "lexema" in no.atributos:
        detalhe = f" {no.atributos['lexema']}"
    elif "operador" in no.atributos:
        detalhe = f" {no.atributos['operador']}"
    linhas = ["  " * nivel + no.tipo + detalhe]
    for f in no.filhos:
        linhas.append(em_texto(f, nivel + 1))
    return "\n".join(linhas)
