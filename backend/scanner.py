"""Analisador léxico (scanner) do subconjunto de Python.

O scanner lê o programa-fonte caractere a caractere, agrupa os caracteres em
LEXEMAS e classifica cada lexema em um TOKEN (tipo + lexema + posição).
Não há expressões regulares no reconhecimento principal: o laço percorre o
texto e decide, pelo caractere atual, qual lexema está começando. Isso deixa
o funcionamento fácil de explicar em aula e de acompanhar passo a passo.

Python tem uma particularidade: a indentação faz parte da gramática. Por
isso, além dos tokens "comuns", o scanner gera NEWLINE, INDENT e DEDENT,
como o tokenizador oficial da linguagem.

O scanner NÃO verifica a estrutura do programa (isso é papel do parser,
Etapa 4): ``x = = 3`` é tokenizado normalmente.

Posições: ``linha`` e ``coluna`` começam em 1 e contam caracteres (não bytes).
"""

from __future__ import annotations

import keyword
from dataclasses import dataclass, field

# --------------------------------------------------------------- categorias
PALAVRA_RESERVADA = "PALAVRA_RESERVADA"
IDENTIFICADOR = "IDENTIFICADOR"
LITERAL_INTEIRO = "LITERAL_INTEIRO"
LITERAL_DECIMAL = "LITERAL_DECIMAL"
OPERADOR_ARITMETICO = "OPERADOR_ARITMETICO"
OPERADOR_RELACIONAL = "OPERADOR_RELACIONAL"
OPERADOR_ATRIBUICAO = "OPERADOR_ATRIBUICAO"
DELIMITADOR = "DELIMITADOR"
NEWLINE = "NEWLINE"
INDENT = "INDENT"
DEDENT = "DEDENT"
FIM_DE_ARQUIVO = "FIM_DE_ARQUIVO"
ERRO_LEXICO = "ERRO_LEXICO"
AVISO = "AVISO_FORA_DO_ESCOPO"

TIPOS_TOKEN = (
    PALAVRA_RESERVADA,
    IDENTIFICADOR,
    LITERAL_INTEIRO,
    LITERAL_DECIMAL,
    OPERADOR_ARITMETICO,
    OPERADOR_RELACIONAL,
    OPERADOR_ATRIBUICAO,
    DELIMITADOR,
    NEWLINE,
    INDENT,
    DEDENT,
    FIM_DE_ARQUIVO,
)

# ------------------------------------------------- subconjunto da linguagem
# Palavras reservadas que fazem parte do subconjunto (Etapa 1).
PALAVRAS_DO_SUBCONJUNTO = frozenset({"if", "else", "while"})
# Demais palavras reservadas do Python: o scanner as reconhece como reservadas
# (um identificador não pode ter esse nome), mas emite um aviso.
TODAS_PALAVRAS_PYTHON = frozenset(keyword.kwlist)

OPERADORES_ARITMETICOS = frozenset("+-*/")
DELIMITADORES = frozenset("():")
OPERADORES_COMPOSTOS = {"==", "!=", "<=", ">="}

# Limite de erros devolvidos (protege a resposta contra entradas gigantes
# cheias de caracteres inválidos). A contagem total continua exata.
MAX_ERROS = 200

# Nomes legíveis para caracteres invisíveis ou que confundem na mensagem.
_NOMES_ESPECIAIS = {
    "\x00": "\\x00 (caractere nulo)",
    "\x0b": "\\x0b (tabulação vertical)",
    "\x0c": "\\x0c (avanço de página)",
    "\\": "\\ (barra invertida)",
}

_MSG_DICA = "Verifique se ele faz parte do subconjunto suportado."


# ---------------------------------------------------------------- estruturas
@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    linha: int
    coluna: int

    def como_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "lexema": self.lexema,
            "linha": self.linha,
            "coluna": self.coluna,
        }


@dataclass(frozen=True)
class ErroLexico:
    lexema: str
    linha: int
    coluna: int
    mensagem: str

    def como_dict(self) -> dict:
        return {
            "tipo": ERRO_LEXICO,
            "lexema": self.lexema,
            "linha": self.linha,
            "coluna": self.coluna,
            "mensagem": self.mensagem,
        }


@dataclass(frozen=True)
class Aviso:
    lexema: str
    linha: int
    coluna: int
    mensagem: str

    def como_dict(self) -> dict:
        return {
            "tipo": AVISO,
            "lexema": self.lexema,
            "linha": self.linha,
            "coluna": self.coluna,
            "mensagem": self.mensagem,
        }


@dataclass
class ResultadoLexico:
    tokens: list[Token] = field(default_factory=list)
    erros: list[ErroLexico] = field(default_factory=list)
    avisos: list[Aviso] = field(default_factory=list)
    total_erros: int = 0  # inclui erros além de MAX_ERROS

    @property
    def sucesso(self) -> bool:
        return self.total_erros == 0

    def por_tipo(self) -> dict[str, int]:
        contagem: dict[str, int] = {}
        for t in self.tokens:
            contagem[t.tipo] = contagem.get(t.tipo, 0) + 1
        return contagem

    def como_dict(self) -> dict:
        return {
            "sucesso": self.sucesso,
            "tokens": [t.como_dict() for t in self.tokens],
            "erros": [e.como_dict() for e in self.erros],
            "avisos": [a.como_dict() for a in self.avisos],
            "resumo": {
                "total_tokens": len(self.tokens),
                "total_erros": self.total_erros,
                "erros_omitidos": self.total_erros - len(self.erros),
                "por_tipo": self.por_tipo(),
            },
        }


# ------------------------------------------------------------------ auxiliares
def _e_letra(c: str) -> bool:
    return ("a" <= c <= "z") or ("A" <= c <= "Z") or c == "_"


def _e_digito(c: str) -> bool:
    return "0" <= c <= "9"


def _mostrar(c: str) -> str:
    """Forma segura de citar um caractere numa mensagem."""
    if c in _NOMES_ESPECIAIS:
        return _NOMES_ESPECIAIS[c]
    if not c.isprintable():
        return f"\\u{ord(c):04x}" if ord(c) > 0xFF else f"\\x{ord(c):02x}"
    return c


def _normalizar_quebras(codigo: str) -> str:
    return codigo.replace("\r\n", "\n").replace("\r", "\n")


def classificar_numero(texto: str) -> tuple[str | None, str | None]:
    """Valida um lexema que começa com dígito (ou com '.').

    Devolve ``(tipo, None)`` quando é um literal válido ou
    ``(None, motivo)`` quando está malformado.

    Regras do subconjunto:
      inteiro  : ``0+`` ou ``[1-9][0-9]*``  (sem zeros à esquerda, como em Python)
      decimal  : dígitos ``.`` dígitos       (dos dois lados do ponto)
    """
    if texto.startswith("."):
        return None, "literal decimal sem parte inteira (escreva, por exemplo, 0.5)"

    # Letras logo depois dos dígitos: "12abc"
    i = 0
    while i < len(texto) and _e_digito(texto[i]):
        i += 1
    resto = texto[i:]
    if resto and (_e_letra(resto[0])):
        return None, (
            "um número não pode ser seguido de letras "
            "(identificadores não começam com dígito)"
        )

    parte_inteira = texto[:i]
    if resto == "":
        if set(parte_inteira) == {"0"} or parte_inteira[0] != "0":
            return LITERAL_INTEIRO, None
        return None, "inteiro com zeros à esquerda não é permitido (use 7, não 007)"

    # resto começa com '.'
    if resto.count(".") > 1:
        return None, "literal com mais de um ponto decimal"
    fracao = resto[1:]
    if fracao == "":
        return None, "literal decimal sem dígitos depois do ponto (escreva 3.0, não 3.)"
    if not all(_e_digito(c) for c in fracao):
        return None, "literal decimal com caracteres inválidos depois do ponto"
    return LITERAL_DECIMAL, None


# --------------------------------------------------------------------- scanner
class Scanner:
    """Percorre o código-fonte e produz tokens, erros e avisos."""

    def __init__(self, codigo: str):
        self.texto = _normalizar_quebras(codigo)
        self.n = len(self.texto)
        self.pos = 0
        self.linha = 1
        self.coluna = 1
        self.resultado = ResultadoLexico()
        self.pilha_indent = [0]
        self.profundidade_parenteses = 0
        self.linha_tem_token = False  # há token "de verdade" na linha lógica?

    # ------------------------------------------------------------ utilidades
    def _atual(self) -> str:
        return self.texto[self.pos] if self.pos < self.n else ""

    def _espiar(self, deslocamento: int = 1) -> str:
        p = self.pos + deslocamento
        return self.texto[p] if p < self.n else ""

    def _avancar(self, quantidade: int = 1) -> None:
        for _ in range(quantidade):
            if self.pos >= self.n:
                return
            if self.texto[self.pos] == "\n":
                self.linha += 1
                self.coluna = 1
            else:
                self.coluna += 1
            self.pos += 1

    def _emitir(self, tipo: str, lexema: str, linha: int, coluna: int) -> None:
        self.resultado.tokens.append(Token(tipo, lexema, linha, coluna))

    def _erro(self, lexema: str, linha: int, coluna: int, mensagem: str) -> None:
        self.resultado.total_erros += 1
        if len(self.resultado.erros) < MAX_ERROS:
            self.resultado.erros.append(ErroLexico(lexema, linha, coluna, mensagem))

    def _aviso(self, lexema: str, linha: int, coluna: int, mensagem: str) -> None:
        if len(self.resultado.avisos) < MAX_ERROS:
            self.resultado.avisos.append(Aviso(lexema, linha, coluna, mensagem))

    # ------------------------------------------------------------ indentação
    def _tratar_inicio_de_linha(self) -> bool:
        """Mede a indentação no início de uma linha lógica.

        Devolve ``False`` se a linha é vazia ou só tem comentário (nesse caso
        nenhum token é gerado) e ``True`` se há código para ler.
        """
        linha_ini, col_ini = self.linha, self.coluna
        largura = 0
        usou_tab = False
        inicio = self.pos
        while self._atual() in (" ", "\t"):
            if self._atual() == "\t":
                usou_tab = True
            largura += 1
            self._avancar()
        espacos = self.texto[inicio:self.pos]

        c = self._atual()
        if c == "" or c == "\n" or c == "#":
            return False  # linha em branco / só comentário: não afeta indentação

        if usou_tab:
            self._erro(
                "\t",
                linha_ini,
                col_ini + espacos.index("\t"),
                "Tabulação na indentação. Use espaços (4 por nível) para que a "
                "indentação seja a mesma em qualquer editor.",
            )
            # Para continuar a análise, cada tabulação conta como 4 espaços.
            largura = sum(4 if ch == "\t" else 1 for ch in espacos)

        atual = self.pilha_indent[-1]
        if largura > atual:
            self.pilha_indent.append(largura)
            self._emitir(INDENT, espacos, linha_ini, col_ini)
        elif largura < atual:
            niveis_abertos = list(self.pilha_indent)
            while largura < self.pilha_indent[-1]:
                self.pilha_indent.pop()
                self._emitir(DEDENT, "", self.linha, self.coluna)
            if largura != self.pilha_indent[-1]:
                self._erro(
                    espacos,
                    linha_ini,
                    col_ini,
                    f"Indentação inconsistente: {largura} espaços não corresponde "
                    f"a nenhum nível aberto (níveis abertos: "
                    f"{', '.join(str(x) for x in niveis_abertos)}).",
                )
                # Recuperação: registra o novo nível (sem gerar INDENT) para que
                # as linhas seguintes com a mesma indentação não repitam o erro.
                self.pilha_indent.append(largura)
        return True

    # -------------------------------------------------------------- lexemas
    def _ler_identificador_ou_reservada(self) -> None:
        linha, coluna = self.linha, self.coluna
        inicio = self.pos
        while _e_letra(self._atual()) or _e_digito(self._atual()):
            self._avancar()
        lexema = self.texto[inicio:self.pos]
        if lexema in TODAS_PALAVRAS_PYTHON:
            self._emitir(PALAVRA_RESERVADA, lexema, linha, coluna)
            if lexema not in PALAVRAS_DO_SUBCONJUNTO:
                self._aviso(
                    lexema,
                    linha,
                    coluna,
                    f"'{lexema}' é palavra reservada do Python, mas ainda não faz "
                    "parte do subconjunto. O scanner a reconhece; as próximas "
                    "etapas poderão não aceitá-la.",
                )
        else:
            self._emitir(IDENTIFICADOR, lexema, linha, coluna)
        self.linha_tem_token = True

    def _ler_numero(self) -> None:
        linha, coluna = self.linha, self.coluna
        inicio = self.pos
        # Consome tudo que "parece" parte do número para reportar um único erro
        # em vez de vários (ex.: "1.2.3" ou "12abc").
        while _e_letra(self._atual()) or _e_digito(self._atual()) or self._atual() == ".":
            self._avancar()
        lexema = self.texto[inicio:self.pos]
        tipo, motivo = classificar_numero(lexema)
        if tipo:
            self._emitir(tipo, lexema, linha, coluna)
        else:
            self._erro(
                lexema,
                linha,
                coluna,
                f"Literal numérico malformado '{lexema}': {motivo}.",
            )
        self.linha_tem_token = True

    def _ler_operador_ou_delimitador(self) -> None:
        linha, coluna = self.linha, self.coluna
        c = self._atual()
        prox = self._espiar()

        if c in "=!<>" and prox == "=":
            lexema = c + prox
            self._avancar(2)
            tipo = OPERADOR_RELACIONAL
            self._emitir(tipo, lexema, linha, coluna)
        elif c == "=":
            self._avancar()
            self._emitir(OPERADOR_ATRIBUICAO, "=", linha, coluna)
        elif c in "<>":
            self._avancar()
            self._emitir(OPERADOR_RELACIONAL, c, linha, coluna)
        elif c == "!":
            self._avancar()
            self._erro(
                "!",
                linha,
                coluna,
                "Caractere '!' sozinho não é um operador. Você quis escrever "
                "'!=' (diferente)?",
            )
        elif c in OPERADORES_ARITMETICOS:
            self._avancar()
            self._emitir(OPERADOR_ARITMETICO, c, linha, coluna)
        else:  # delimitadores
            self._avancar()
            self._emitir(DELIMITADOR, c, linha, coluna)
            if c == "(":
                self.profundidade_parenteses += 1
            elif c == ")" and self.profundidade_parenteses > 0:
                self.profundidade_parenteses -= 1
        self.linha_tem_token = True

    def _caractere_invalido(self) -> None:
        linha, coluna = self.linha, self.coluna
        inicio = self.pos
        c = self._atual()
        self._avancar()
        if c in "\"'":
            # Consome a string inteira (até a aspa de fechamento ou o fim da
            # linha) para relatar um único erro em vez de vários.
            while self._atual() not in ("", "\n") and self._atual() != c:
                self._avancar()
            fechada = self._atual() == c
            if fechada:
                self._avancar()
            lexema = self.texto[inicio:self.pos]
            if fechada:
                msg = (
                    f"String {lexema} não reconhecida: strings ainda não fazem "
                    "parte do subconjunto."
                )
            else:
                msg = (
                    f"String {lexema} sem aspa de fechamento na mesma linha; "
                    "além disso, strings ainda não fazem parte do subconjunto."
                )
            self._erro(lexema, linha, coluna, msg)
            return
        elif c in "{}[],;.%&|^~@$?`\\":
            msg = (
                f"Caractere não reconhecido: '{_mostrar(c)}'. Ele existe em "
                f"Python, mas ainda não faz parte do subconjunto suportado."
            )
        else:
            msg = f"Caractere não reconhecido: '{_mostrar(c)}'. {_MSG_DICA}"
        self._erro(c, linha, coluna, msg)

    # ------------------------------------------------------------ laço principal
    def executar(self) -> ResultadoLexico:
        inicio_de_linha = True
        while self.pos < self.n:
            if inicio_de_linha and self.profundidade_parenteses == 0:
                inicio_de_linha = False
                if not self._tratar_inicio_de_linha():
                    # linha vazia ou só comentário: consome comentário e quebra
                    self._pular_comentario()
                    if self._atual() == "\n":
                        self._avancar()
                        inicio_de_linha = True
                    continue
            c = self._atual()

            if c == "\n":
                linha, coluna = self.linha, self.coluna
                self._avancar()
                if self.profundidade_parenteses == 0:
                    if self.linha_tem_token:
                        self._emitir(NEWLINE, "\n", linha, coluna)
                    self.linha_tem_token = False
                    inicio_de_linha = True
                continue
            if c in (" ", "\t"):
                self._avancar()
            elif c == "#":
                self._pular_comentario()
            elif _e_letra(c):
                self._ler_identificador_ou_reservada()
            elif _e_digito(c):
                self._ler_numero()
            elif c == "." and _e_digito(self._espiar()):
                self._ler_numero()
            elif c in "=!<>" or c in OPERADORES_ARITMETICOS or c in DELIMITADORES:
                self._ler_operador_ou_delimitador()
            else:
                self._caractere_invalido()
                self.linha_tem_token = True

        self._finalizar()
        return self.resultado

    def _pular_comentario(self) -> None:
        if self._atual() == "#":
            while self._atual() not in ("", "\n"):
                self._avancar()

    def _finalizar(self) -> None:
        # Convenção do tokenizador do Python: se o arquivo não termina em
        # quebra de linha, os DEDENT e o FIM ficam no início da linha seguinte.
        sem_quebra_final = self.n > 0 and not self.texto.endswith("\n")
        linha_fim, coluna_fim = (self.linha + 1, 1) if sem_quebra_final else (self.linha, self.coluna)
        # Última linha sem quebra de linha: NEWLINE "implícito".
        if self.linha_tem_token:
            self._emitir(NEWLINE, "", self.linha, self.coluna)
            self.linha_tem_token = False
        while len(self.pilha_indent) > 1:
            self.pilha_indent.pop()
            self._emitir(DEDENT, "", linha_fim, coluna_fim)
        self._emitir(FIM_DE_ARQUIVO, "", linha_fim, coluna_fim)


def analisar_lexico(codigo: str) -> ResultadoLexico:
    """Ponto de entrada: tokeniza ``codigo`` e devolve tokens, erros e avisos."""
    return Scanner(codigo).executar()
