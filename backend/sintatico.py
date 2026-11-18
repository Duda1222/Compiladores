"""Analisador sintático (parser) do subconjunto de Python.

Estratégia: **descendente recursivo preditivo** (LL(1), com um único ponto
de olhada de 2 tokens: ``IDENTIFICADOR '='`` distingue atribuição de
expressão). Cada símbolo não terminal da gramática (docs/gramatica.md) é uma
função; a precedência vem da forma da gramática (um nível por função) e a
associatividade à esquerda vem dos laços ``{ ... }``.

O parser recebe a lista de tokens do scanner (Etapa 3) e devolve:
  * a AST (``arvore.No``), quando não há erro sintático;
  * a árvore de derivação (concreta), para comparar com a AST;
  * os erros sintáticos, com linha, coluna, token encontrado e esperados.

Recuperação de erros (modo pânico): ao encontrar um erro, o parser o registra,
descarta tokens até o fim da linha (e o bloco indentado que dependia dela) e
continua no próximo comando. Para evitar erros em cascata, um ``else`` que
sobra depois de um ``if`` com erro é descartado sem novo erro.
Limite: 20 erros listados (a contagem total continua exata).

Posições: as do scanner (linha e coluna a partir de 1).
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field

import arvore as A
from scanner import (
    DEDENT,
    DELIMITADOR,
    FIM_DE_ARQUIVO,
    IDENTIFICADOR,
    INDENT,
    LITERAL_DECIMAL,
    LITERAL_INTEIRO,
    NEWLINE,
    OPERADOR_ARITMETICO,
    OPERADOR_ATRIBUICAO,
    OPERADOR_RELACIONAL,
    PALAVRA_RESERVADA,
    Token,
)

ERRO_SINTATICO = "ERRO_SINTATICO"
MAX_ERROS_SINTATICOS = 20
MAX_ANINHAMENTO = 25  # parênteses e blocos

ESP_OPERANDO = ["identificador", "número", "'('", "'-'", "'+'"]
ESP_INICIO_COMANDO = ["identificador", "número", "'('", "'if'", "'while'"]


# ---------------------------------------------------------------- resultados
@dataclass
class ErroSintatico(Exception):
    linha: int
    coluna: int
    encontrado: str
    esperado: list
    mensagem: str
    regra: str = ""
    dica: str = ""

    def como_dict(self) -> dict:
        d = {
            "tipo": ERRO_SINTATICO,
            "linha": self.linha,
            "coluna": self.coluna,
            "encontrado": self.encontrado,
            "esperado": list(self.esperado),
            "mensagem": self.mensagem,
        }
        if self.regra:
            d["regra"] = self.regra
        if self.dica:
            d["dica"] = self.dica
        return d


@dataclass
class ResultadoSintatico:
    erros: list = field(default_factory=list)
    total_erros: int = 0
    ast: A.No | None = None
    derivacao: dict | None = None

    @property
    def sucesso(self) -> bool:
        return self.total_erros == 0 and self.ast is not None

    def como_dict(self) -> dict:
        d = {
            "executado": True,
            "sucesso": self.sucesso,
            "ast": self.ast.como_dict() if self.sucesso else None,
            "derivacao": self.derivacao if self.sucesso else None,
            "erros": [e.como_dict() for e in self.erros],
            "resumo": {
                "total_erros": self.total_erros,
                "erros_omitidos": self.total_erros - len(self.erros),
            },
        }
        if self.sucesso:
            d["resumo"].update(A.contar(self.ast))
        return d


def resultado_nao_executado(motivo: str) -> dict:
    """Formato devolvido quando o parser não roda (erros léxicos)."""
    return {
        "executado": False,
        "sucesso": False,
        "ast": None,
        "derivacao": None,
        "erros": [],
        "mensagem": motivo,
        "resumo": {"total_erros": 0, "erros_omitidos": 0},
    }


# ----------------------------------------------------------------- auxiliares
def _juntar(itens: list[str]) -> str:
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " ou " + itens[-1]


def _fim_do_token(t: Token) -> tuple[int, int]:
    return (t.linha, t.coluna + len(t.lexema))


def _encontrado(t: Token) -> str:
    return {
        FIM_DE_ARQUIVO: "fim do arquivo",
        NEWLINE: "fim da linha",
        INDENT: "indentação",
        DEDENT: "fim do bloco",
    }.get(t.tipo, t.lexema)


def _descrever(t: Token) -> str:
    if t.tipo == FIM_DE_ARQUIVO:
        return "o fim do arquivo"
    if t.tipo == NEWLINE:
        return "o fim da linha"
    if t.tipo == INDENT:
        return "uma indentação inesperada"
    if t.tipo == DEDENT:
        return "o fim do bloco"
    if t.tipo == IDENTIFICADOR:
        return f"o identificador '{t.lexema}'"
    if t.tipo in (LITERAL_INTEIRO, LITERAL_DECIMAL):
        return f"o número '{t.lexema}'"
    if t.tipo == PALAVRA_RESERVADA:
        return f"a palavra reservada '{t.lexema}'"
    return f"'{t.lexema}'"


def _e_arit(t: Token, *ops: str) -> bool:
    return t.tipo == OPERADOR_ARITMETICO and t.lexema in ops


def _e_reservada(t: Token, *palavras: str) -> bool:
    return t.tipo == PALAVRA_RESERVADA and t.lexema in palavras


def _e_operador(t: Token) -> bool:
    return t.tipo in (OPERADOR_ARITMETICO, OPERADOR_RELACIONAL, OPERADOR_ATRIBUICAO)


def _e_inicio_operando(t: Token) -> bool:
    return t.tipo in (IDENTIFICADOR, LITERAL_INTEIRO, LITERAL_DECIMAL) or (
        t.tipo == DELIMITADOR and t.lexema == "("
    )



# --------------------------------------------------------------------- parser
class Parser:
    def __init__(self, tokens: list[Token]):
        self.t = tokens
        self.i = 0
        self.erros: list[ErroSintatico] = []
        self.total_erros = 0
        self.parens: list[Token] = []
        self.nivel_bloco = 0
        self.suprimir_else = False
        self.ultimo_fim = (1, 1)
        self.raiz_derivacao: dict = {"simbolo": "<raiz>", "filhos": []}
        self.pilha = [self.raiz_derivacao]

    # ------------------------------------------------------------- tokens
    @property
    def cur(self) -> Token:
        return self.t[self.i]

    def _peek(self, n: int = 1) -> Token:
        return self.t[min(self.i + n, len(self.t) - 1)]

    def _anterior(self) -> Token | None:
        return self.t[self.i - 1] if self.i > 0 else None

    def _consumir(self) -> Token:
        tok = self.t[self.i]
        if self.i < len(self.t) - 1:
            self.i += 1
        if tok.tipo not in (NEWLINE, INDENT, DEDENT, FIM_DE_ARQUIVO):
            self.ultimo_fim = _fim_do_token(tok)
        simbolo = tok.tipo if tok.tipo in (
            IDENTIFICADOR, LITERAL_INTEIRO, LITERAL_DECIMAL, NEWLINE, INDENT,
            DEDENT, FIM_DE_ARQUIVO, OPERADOR_RELACIONAL,
        ) else tok.lexema
        self.pilha[-1]["filhos"].append({
            "simbolo": simbolo,
            "terminal": True,
            "tipo": tok.tipo,
            "lexema": tok.lexema,
            "linha": tok.linha,
            "coluna": tok.coluna,
        })
        return tok

    @contextmanager
    def _regra(self, nome: str):
        no = {"simbolo": nome, "filhos": []}
        self.pilha[-1]["filhos"].append(no)
        self.pilha.append(no)
        try:
            yield
        finally:
            self.pilha.pop()

    def _no(self, tipo, inicio, atributos=None, filhos=()):
        no = A.criar_no(tipo, inicio, self.ultimo_fim, atributos, filhos)
        if no.altura > A.MAX_ALTURA:
            raise self._erro(
                self.t[max(self.i - 1, 0)],
                f"A expressão ou estrutura é profunda demais para ser exibida "
                f"(limite de {A.MAX_ALTURA} níveis na árvore).",
                [], "",
                "Divida a expressão em partes menores.",
            )
        return no

    # --------------------------------------------------------------- erros
    def _posicao_do_erro(self, tok: Token) -> tuple[int, int]:
        """No fim do arquivo (ou no NEWLINE sintético de fim de arquivo), aponta
        para o fim do último token com conteúdo, e não para uma linha inexistente."""
        if tok.tipo == FIM_DE_ARQUIVO or (tok.tipo == NEWLINE and tok.lexema == ""):
            for k in range(len(self.t) - 1, -1, -1):
                ultimo = self.t[k]
                if ultimo.tipo not in (FIM_DE_ARQUIVO, DEDENT, INDENT, NEWLINE):
                    return _fim_do_token(ultimo)
        return tok.linha, tok.coluna

    def _erro(self, tok, mensagem, esperado, regra="", dica="") -> ErroSintatico:
        linha, coluna = self._posicao_do_erro(tok)
        return ErroSintatico(linha, coluna, _encontrado(tok), list(esperado),
                             mensagem, regra, dica)

    def _dica_parenteses(self) -> str:
        if self.parens:
            p = self.parens[-1]
            return (f"O parêntese '(' aberto na linha {p.linha}, coluna {p.coluna} "
                    f"ainda não foi fechado.")
        return ""

    def _erro_palavra_reservada(self, tok: Token, onde: str, esperado, regra):
        if tok.lexema in ("if", "else", "while"):
            msg = (f"A palavra reservada '{tok.lexema}' não pode ser usada {onde}. "
                   f"Palavras reservadas têm função fixa na linguagem.")
            dica = "Escolha outro nome para a variável."
        else:
            msg = (f"'{tok.lexema}' é palavra reservada do Python, mas ainda não faz "
                   f"parte do subconjunto suportado, então não pode ser usada {onde}.")
            dica = "O subconjunto aceita apenas atribuições, expressões, if/else e while."
            if tok.lexema == "elif":
                dica = "Use 'else:' com um 'if' dentro dele no lugar de 'elif'."
        return self._erro(tok, msg, esperado, regra, dica)

    def _erro_operando(self, tok: Token) -> ErroSintatico:
        """Esperava-se o início de um operando (primario) e veio outra coisa."""
        regra = "primario → LITERAL_INTEIRO | LITERAL_DECIMAL | IDENTIFICADOR | '(' expressao ')'"
        ant = self._anterior()
        dica_p = self._dica_parenteses()
        if tok.tipo == PALAVRA_RESERVADA:
            return self._erro_palavra_reservada(
                tok, "como operando de uma expressão", ESP_OPERANDO, regra)
        if tok.tipo in (NEWLINE, FIM_DE_ARQUIVO):
            if ant is not None and _e_operador(ant):
                msg = (f"A expressão termina em '{ant.lexema}', mas falta o operando "
                       f"à direita dele (esperava {_juntar(ESP_OPERANDO[:3])}).")
            else:
                msg = (f"Fim da linha inesperado: a expressão está incompleta "
                       f"(esperava {_juntar(ESP_OPERANDO[:3])}).")
            if tok.tipo == FIM_DE_ARQUIVO:
                msg = "Fim do arquivo inesperado: a expressão está incompleta."
            return self._erro(tok, msg, ESP_OPERANDO, regra, dica_p)
        if _e_operador(tok) and ant is not None and _e_operador(ant):
            dica = "Se queria comparar valores, use '==' (um único '=' é atribuição)." \
                if tok.lexema == "=" or ant.lexema == "=" else \
                "Escreva um número ou uma variável entre os dois operadores."
            msg = (f"Operadores consecutivos: '{ant.lexema}' seguido de '{tok.lexema}'. "
                   f"Falta um operando entre eles.")
            return self._erro(tok, msg, ESP_OPERANDO, regra, (dica_p + " " + dica).strip())
        if tok.tipo == DELIMITADOR and tok.lexema == ")" and ant is not None \
                and ant.tipo == DELIMITADOR and ant.lexema == "(":
            return self._erro(tok, "Parênteses vazios: '()' não contém uma expressão.",
                              ESP_OPERANDO, regra)
        if tok.tipo == INDENT:
            return self._erro(tok, "Indentação inesperada: este recuo não abre nenhum bloco.",
                              ESP_OPERANDO, regra,
                              "Só se recua a linha depois de um 'if', 'else' ou 'while' terminado em ':'.")
        if tok.tipo == DEDENT:
            return self._erro(tok, "O bloco terminou, mas a expressão ainda estava incompleta.",
                              ESP_OPERANDO, regra, dica_p)
        msg = f"Esperava {_juntar(ESP_OPERANDO[:3])}, mas encontrei {_descrever(tok)}."
        return self._erro(tok, msg, ESP_OPERANDO, regra, dica_p)

    # ------------------------------------------------------------ programa
    def programa(self) -> A.No | None:
        comandos: list[A.No] = []
        with self._regra("programa"):
            while self.cur.tipo != FIM_DE_ARQUIVO:
                if self.cur.tipo == DEDENT:
                    self._consumir()
                    continue
                self._comando_recuperavel(comandos)
            self._consumir()
        fim = self.ultimo_fim if comandos else (1, 1)
        no = A.criar_no(A.PROGRAMA, (1, 1), fim, {},
                        [("comando", c) for c in comandos])
        return no

    def _registrar(self, e: ErroSintatico):
        self.total_erros += 1
        if any(x.linha == e.linha and x.coluna == e.coluna for x in self.erros):
            self.total_erros -= 1  # mesma posição: provável cascata
            return
        if len(self.erros) < MAX_ERROS_SINTATICOS:
            self.erros.append(e)

    def _comando_recuperavel(self, destino: list):
        inicio = self.i
        era_if = _e_reservada(self.cur, "if")
        try:
            if _e_reservada(self.cur, "else") and self.suprimir_else:
                self.suprimir_else = False
                self._sincronizar()
                return
            no = self._comando()
            destino.append(no)
            self.suprimir_else = False
        except ErroSintatico as e:
            self._registrar(e)
            self.parens = []
            self._sincronizar()
            self.suprimir_else = era_if
            if self.i == inicio and self.cur.tipo != FIM_DE_ARQUIVO:
                self._consumir()  # garante progresso

    # --------------------------------------------------------- recuperação
    def _sincronizar(self):
        """Modo pânico: descarta até o fim da linha e o bloco dependente."""
        if self.cur.tipo == INDENT:
            self._pular_bloco()
            return
        while self.cur.tipo not in (NEWLINE, DEDENT, FIM_DE_ARQUIVO):
            self._descartar()
        if self.cur.tipo == NEWLINE:
            self._descartar()
        if self.cur.tipo == INDENT:
            self._pular_bloco()

    def _descartar(self):
        if self.i < len(self.t) - 1:
            self.i += 1

    def _pular_bloco(self):
        profundidade = 0
        while self.cur.tipo != FIM_DE_ARQUIVO:
            tok = self.cur
            self._descartar()
            if tok.tipo == INDENT:
                profundidade += 1
            elif tok.tipo == DEDENT:
                profundidade -= 1
                if profundidade <= 0:
                    return

    # ------------------------------------------------------------- comandos
    def _comando(self) -> A.No:
        with self._regra("comando"):
            t = self.cur
            if t.tipo == PALAVRA_RESERVADA:
                if t.lexema == "if":
                    return self._condicional()
                if t.lexema == "while":
                    return self._repeticao()
                if t.lexema == "else":
                    raise self._erro(
                        t,
                        "'else' sem um 'if' correspondente: ele só pode aparecer "
                        "logo depois do bloco de um 'if', na mesma indentação.",
                        ESP_INICIO_COMANDO,
                        "condicional → 'if' expressao ':' bloco [ 'else' ':' bloco ]",
                        "Confira se o 'else' está alinhado com o 'if' e se o 'if' não tem erro.",
                    )
                raise self._erro_palavra_reservada(
                    t, "como início de comando", ESP_INICIO_COMANDO,
                    "comando → comando_simples | condicional | repeticao")
            if t.tipo == INDENT:
                raise self._erro(
                    t, "Indentação inesperada: este recuo não abre nenhum bloco.",
                    ESP_INICIO_COMANDO, "comando → comando_simples | condicional | repeticao",
                    "Só se recua a linha depois de um 'if', 'else' ou 'while' terminado em ':'.")
            if not (_e_inicio_operando(t) or _e_arit(t, "+", "-")):
                raise self._erro(
                    t,
                    f"Esperava o início de um comando ({_juntar(ESP_INICIO_COMANDO)}), "
                    f"mas encontrei {_descrever(t)}.",
                    ESP_INICIO_COMANDO,
                    "comando → comando_simples | condicional | repeticao",
                )
            return self._comando_simples()

    def _comando_simples(self) -> A.No:
        with self._regra("comando_simples"):
            inicio = (self.cur.linha, self.cur.coluna)
            if self.cur.tipo == IDENTIFICADOR and self._peek().tipo == OPERADOR_ATRIBUICAO:
                no = self._atribuicao()
            else:
                expr = self._expressao()
                no = self._no(A.EXPRESSAO_COMANDO, inicio, {}, [("expressao", expr)])
                if self.cur.tipo == OPERADOR_ATRIBUICAO:
                    raise self._erro(
                        self.cur,
                        "O lado esquerdo de uma atribuição deve ser apenas um "
                        "identificador (nome de variável).",
                        ["identificador antes de '='"],
                        "atribuicao → IDENTIFICADOR '=' expressao",
                        "Exemplo correto: x = 3 + 4",
                    )
            self._fim_de_comando()
            return no

    def _fim_de_comando(self):
        t = self.cur
        if t.tipo == NEWLINE:
            self._consumir()
            return
        if t.tipo == FIM_DE_ARQUIVO:
            return
        regra = "comando_simples → ( atribuicao | expressao ) NEWLINE"
        esperado = ["operador", "fim da linha"]
        if t.tipo == OPERADOR_ATRIBUICAO:
            raise self._erro(
                t, "Atribuição encadeada (a = b = c) não faz parte do subconjunto: "
                   "cada linha tem uma única atribuição.",
                ["fim da linha"], regra, "Escreva uma atribuição por linha.")
        if t.tipo == OPERADOR_RELACIONAL:
            raise self._erro(
                t, f"Comparação encadeada: já existe um operador relacional nesta "
                   f"expressão e '{t.lexema}' é um segundo. O subconjunto aceita "
                   f"uma comparação por expressão.",
                ["fim da linha"], regra, "Separe em duas comparações ou use variáveis auxiliares.")
        if t.tipo == DELIMITADOR and t.lexema == ")":
            raise self._erro(
                t, "Parêntese ')' sem o '(' correspondente.", esperado, regra,
                "Confira se todos os '(' foram abertos antes de fechar.")
        if t.tipo == DELIMITADOR and t.lexema == ":":
            raise self._erro(
                t, "O ':' só pode aparecer no fim de uma linha com 'if', 'else' ou 'while'.",
                esperado, regra)
        if t.tipo == INDENT:
            raise self._erro(
                t, "Indentação inesperada: este recuo não abre nenhum bloco.",
                ["fim da linha"], regra,
                "Só se recua a linha depois de um 'if', 'else' ou 'while' terminado em ':'.")
        if t.tipo == PALAVRA_RESERVADA:
            raise self._erro_palavra_reservada(
                t, "no meio de uma expressão", esperado, regra)
        if _e_inicio_operando(t):
            ant = self._anterior()
            raise self._erro(
                t,
                f"Faltou um operador (ou o fim da linha) entre "
                f"{_descrever(ant) if ant else 'o termo anterior'} e {_descrever(t)}.",
                esperado, regra,
                "Dois valores seguidos precisam de um operador (+, -, *, /...). "
                "Para guardar um valor, use '='.")
        raise self._erro(
            t, f"Esperava um operador ou o fim da linha, mas encontrei {_descrever(t)}.",
            esperado, regra)

    def _atribuicao(self) -> A.No:
        with self._regra("atribuicao"):
            alvo_tok = self._consumir()
            self._consumir()  # '='
            alvo = self._no(
                A.IDENTIFICADOR, (alvo_tok.linha, alvo_tok.coluna),
                {"nome": alvo_tok.lexema})
            alvo.linha_fim, alvo.coluna_fim = _fim_do_token(alvo_tok)
            valor = self._expressao()
            return self._no(A.ATRIBUICAO, (alvo_tok.linha, alvo_tok.coluna), {},
                            [("alvo", alvo), ("valor", valor)])

    def _esperar_dois_pontos(self, kw: Token):
        t = self.cur
        if t.tipo == DELIMITADOR and t.lexema == ":":
            self._consumir()
            return
        regra = {
            "if": "condicional → 'if' expressao ':' bloco [ 'else' ':' bloco ]",
            "else": "condicional → 'if' expressao ':' bloco [ 'else' ':' bloco ]",
            "while": "repeticao → 'while' expressao ':' bloco",
        }[kw.lexema]
        if t.tipo == OPERADOR_ATRIBUICAO and kw.lexema != "else":
            raise self._erro(
                t, f"Encontrei '=' (atribuição) dentro da condição do '{kw.lexema}'. "
                   f"Para comparar valores o operador é '=='.",
                ["':'", "operador"], regra, "Troque '=' por '=='.")
        if t.tipo in (NEWLINE, FIM_DE_ARQUIVO):
            raise self._erro(
                t, f"Faltou o ':' no fim da linha do '{kw.lexema}' "
                   f"(linha {kw.linha}).",
                ["':'"], regra, f"Escreva '{kw.lexema}' ... ':' e, na linha seguinte, o bloco indentado.")
        if kw.lexema == "else":
            raise self._erro(
                t, f"Depois de 'else' esperava ':', mas encontrei {_descrever(t)}.",
                ["':'"], regra, "O else não tem condição: escreva apenas 'else:'.")
        raise self._erro(
            t, f"Esperava ':' (ou um operador) no fim do cabeçalho do '{kw.lexema}', "
               f"mas encontrei {_descrever(t)}.",
            ["':'", "operador"], regra)

    def _rejeitar_reservada_como_variavel(self):
        """``if = 3``: a palavra reservada foi usada como nome de variável."""
        if self._peek().tipo == OPERADOR_ATRIBUICAO:
            raise self._erro_palavra_reservada(
                self.cur, "como nome de variável", ["identificador"],
                "atribuicao → IDENTIFICADOR '=' expressao")

    def _condicional(self) -> A.No:
        with self._regra("condicional"):
            self._rejeitar_reservada_como_variavel()
            kw = self._consumir()
            cond = self._expressao()
            self._esperar_dois_pontos(kw)
            entao = self._bloco(kw)
            filhos = [("condicao", cond), ("entao", entao)]
            if _e_reservada(self.cur, "else"):
                kw2 = self._consumir()
                self._esperar_dois_pontos(kw2)
                filhos.append(("senao", self._bloco(kw2)))
            return self._no(A.CONDICIONAL, (kw.linha, kw.coluna), {}, filhos)

    def _repeticao(self) -> A.No:
        with self._regra("repeticao"):
            self._rejeitar_reservada_como_variavel()
            kw = self._consumir()
            cond = self._expressao()
            self._esperar_dois_pontos(kw)
            corpo = self._bloco(kw)
            return self._no(A.REPETICAO, (kw.linha, kw.coluna), {},
                            [("condicao", cond), ("corpo", corpo)])

    def _bloco(self, kw: Token) -> A.No:
        regra = "bloco → NEWLINE INDENT comando { comando } DEDENT"
        with self._regra("bloco"):
            t = self.cur
            if t.tipo != NEWLINE:
                raise self._erro(
                    t, f"O corpo do '{kw.lexema}' deve começar na linha seguinte, "
                       f"indentado; encontrei {_descrever(t)} logo depois do ':'.",
                    ["fim da linha"], regra,
                    "Escreva o ':' no fim da linha e coloque os comandos abaixo, recuados.")
            self._consumir()
            t = self.cur
            if t.tipo != INDENT:
                if t.tipo == FIM_DE_ARQUIVO:
                    msg = (f"Fim do arquivo inesperado: o '{kw.lexema}' da linha "
                           f"{kw.linha} precisa de um bloco indentado.")
                else:
                    msg = (f"Esperava um bloco indentado depois do ':' do '{kw.lexema}' "
                           f"(linha {kw.linha}), mas a linha seguinte não está recuada.")
                raise self._erro(t, msg, ["indentação"], regra,
                                 "Recue (4 espaços) os comandos que pertencem ao bloco.")
            if self.nivel_bloco >= MAX_ANINHAMENTO:
                raise self._erro(
                    t, f"Blocos aninhados demais (limite de {MAX_ANINHAMENTO} níveis).",
                    [], regra)
            self._consumir()
            self.nivel_bloco += 1
            comandos: list[A.No] = []
            try:
                while self.cur.tipo not in (DEDENT, FIM_DE_ARQUIVO):
                    self._comando_recuperavel(comandos)
            finally:
                self.nivel_bloco -= 1
            if self.cur.tipo == DEDENT:
                self._consumir()
            inicio = (comandos[0].linha, comandos[0].coluna) if comandos else (kw.linha, kw.coluna)
            return self._no(A.BLOCO, inicio, {}, [("comando", c) for c in comandos])

    # ----------------------------------------------------------- expressões
    def _expressao(self) -> A.No:
        with self._regra("expressao"):
            esq = self._soma()
            if self.cur.tipo == OPERADOR_RELACIONAL:
                op = self._consumir()
                dir_ = self._soma()
                return self._no(
                    A.COMPARACAO, (esq.linha, esq.coluna),
                    {"operador": op.lexema, "categoria": "relacional"},
                    [("esquerda", esq), ("direita", dir_)])
            return esq

    def _soma(self) -> A.No:
        with self._regra("soma"):
            no = self._termo()
            while _e_arit(self.cur, "+", "-"):
                op = self._consumir()
                dir_ = self._termo()
                no = self._no(
                    A.OPERACAO_BINARIA, (no.linha, no.coluna),
                    {"operador": op.lexema, "categoria": "aritmetica"},
                    [("esquerda", no), ("direita", dir_)])
            return no

    def _termo(self) -> A.No:
        with self._regra("termo"):
            no = self._unario()
            while _e_arit(self.cur, "*", "/"):
                op = self._consumir()
                dir_ = self._unario()
                no = self._no(
                    A.OPERACAO_BINARIA, (no.linha, no.coluna),
                    {"operador": op.lexema, "categoria": "aritmetica"},
                    [("esquerda", no), ("direita", dir_)])
            return no

    def _unario(self) -> A.No:
        with self._regra("unario"):
            if _e_arit(self.cur, "+", "-"):
                op = self._consumir()
                operando = self._unario()
                return self._no(
                    A.OPERACAO_UNARIA, (op.linha, op.coluna),
                    {"operador": op.lexema}, [("operando", operando)])
            return self._primario()

    def _primario(self) -> A.No:
        with self._regra("primario"):
            t = self.cur
            if t.tipo == IDENTIFICADOR:
                self._consumir()
                return self._no(A.IDENTIFICADOR, (t.linha, t.coluna), {"nome": t.lexema})
            if t.tipo in (LITERAL_INTEIRO, LITERAL_DECIMAL):
                self._consumir()
                tipo_num = "inteiro" if t.tipo == LITERAL_INTEIRO else "decimal"
                return self._no(A.NUMERO, (t.linha, t.coluna),
                                {"lexema": t.lexema, "tipo_numero": tipo_num})
            if t.tipo == DELIMITADOR and t.lexema == "(":
                return self._parenteses()
            raise self._erro_operando(t)

    def _parenteses(self) -> A.No:
        abre = self._consumir()
        if len(self.parens) >= MAX_ANINHAMENTO:
            raise self._erro(
                abre, f"Parênteses aninhados demais (limite de {MAX_ANINHAMENTO} níveis).",
                [], "primario → '(' expressao ')'")
        self.parens.append(abre)
        interno = self._expressao()
        t = self.cur
        if t.tipo == DELIMITADOR and t.lexema == ")":
            self._consumir()
            self.parens.pop()
            return interno
        regra = "primario → '(' expressao ')'"
        esperado = ["')'", "operador"]
        if t.tipo in (NEWLINE, FIM_DE_ARQUIVO, DEDENT):
            msg = (f"O parêntese '(' aberto na linha {abre.linha}, coluna {abre.coluna} "
                   f"não foi fechado: esperava ')'.")
        elif _e_inicio_operando(t):
            msg = (f"Esperava ')' (ou um operador) antes de {_descrever(t)}; "
                   f"o '(' da linha {abre.linha}, coluna {abre.coluna} continua aberto.")
        else:
            msg = f"Esperava ')' ou um operador, mas encontrei {_descrever(t)}."
        raise self._erro(t, msg, esperado, regra,
                         f"Feche com ')' o '(' da linha {abre.linha}, coluna {abre.coluna}.")


# ------------------------------------------------------------------ interface
def analisar_sintatico(tokens: list[Token]) -> ResultadoSintatico:
    """Analisa a lista de tokens. Nunca lança exceção para entradas inválidas."""
    p = Parser(tokens)
    try:
        ast = p.programa()
    except RecursionError:
        e = ErroSintatico(1, 1, "", [], "O programa tem estruturas aninhadas demais para "
                          "serem analisadas.", "", "Simplifique o aninhamento.")
        return ResultadoSintatico(erros=[e], total_erros=1)
    if p.total_erros:
        return ResultadoSintatico(erros=p.erros, total_erros=p.total_erros)
    derivacao = p.raiz_derivacao["filhos"][0]
    return ResultadoSintatico(ast=ast, derivacao=derivacao)
