"""Testes unitários do analisador léxico (scanner).

Organização (conforme o enunciado da Etapa 3, seção 6.1):
palavras reservadas, identificadores, literais, operadores, delimitadores,
comentários, espaços em branco, posição, erros léxicos e casos de borda.
Também há testes de indentação (INDENT/DEDENT) e de robustez.
"""

import random

import pytest

from scanner import (
    DEDENT,
    DELIMITADOR,
    FIM_DE_ARQUIVO,
    IDENTIFICADOR,
    INDENT,
    LITERAL_DECIMAL,
    LITERAL_INTEIRO,
    MAX_ERROS,
    NEWLINE,
    OPERADOR_ARITMETICO,
    OPERADOR_ATRIBUICAO,
    OPERADOR_RELACIONAL,
    PALAVRA_RESERVADA,
    analisar_lexico,
    classificar_numero,
)

# Tipos "estruturais" que não correspondem a texto visível no código.
ESTRUTURAIS = {NEWLINE, INDENT, DEDENT, FIM_DE_ARQUIVO}


def toks(codigo):
    """Tokens como lista de (tipo, lexema), sem os tokens estruturais."""
    return [
        (t.tipo, t.lexema)
        for t in analisar_lexico(codigo).tokens
        if t.tipo not in ESTRUTURAIS
    ]


def tipos(codigo):
    return [t.tipo for t in analisar_lexico(codigo).tokens]


# ------------------------------------------------------- palavras reservadas
@pytest.mark.parametrize("palavra", ["if", "else", "while"])
def test_palavras_reservadas_do_subconjunto(palavra):
    r = analisar_lexico(palavra)
    assert toks(palavra) == [(PALAVRA_RESERVADA, palavra)]
    assert r.avisos == []  # fazem parte do subconjunto: sem aviso


@pytest.mark.parametrize("palavra", ["def", "return", "for", "True", "None", "and"])
def test_outras_reservadas_do_python_geram_aviso_mas_sao_reconhecidas(palavra):
    r = analisar_lexico(palavra)
    assert toks(palavra) == [(PALAVRA_RESERVADA, palavra)]
    assert r.sucesso is True  # aviso não é erro
    assert len(r.avisos) == 1
    assert r.avisos[0].lexema == palavra


def test_palavra_reservada_e_sensivel_a_maiusculas():
    assert toks("If") == [(IDENTIFICADOR, "If")]
    assert toks("WHILE") == [(IDENTIFICADOR, "WHILE")]


def test_prefixo_de_reservada_e_identificador():
    assert toks("iff") == [(IDENTIFICADOR, "iff")]
    assert toks("elsewhere") == [(IDENTIFICADOR, "elsewhere")]
    assert toks("while1") == [(IDENTIFICADOR, "while1")]
    assert toks("if_") == [(IDENTIFICADOR, "if_")]


# ------------------------------------------------------------ identificadores
@pytest.mark.parametrize(
    "nome", ["x", "numero", "_x1", "__", "_", "resultado_final", "A1b2", "x10"]
)
def test_identificadores_validos(nome):
    assert toks(nome) == [(IDENTIFICADOR, nome)]


def test_identificador_nao_pode_comecar_com_digito():
    r = analisar_lexico("1abc")
    assert r.sucesso is False
    assert r.erros[0].lexema == "1abc"
    assert "letras" in r.erros[0].mensagem


def test_identificador_com_acento_nao_e_aceito_no_subconjunto():
    r = analisar_lexico("açaí = 1")
    assert r.sucesso is False
    lexemas_erro = [e.lexema for e in r.erros]
    assert "ç" in lexemas_erro and "í" in lexemas_erro
    assert (IDENTIFICADOR, "a") in toks("açaí = 1")  # continua após o erro


def test_identificador_separado_por_operador_sem_espacos():
    assert toks("a+b") == [
        (IDENTIFICADOR, "a"),
        (OPERADOR_ARITMETICO, "+"),
        (IDENTIFICADOR, "b"),
    ]


# -------------------------------------------------------------------- literais
@pytest.mark.parametrize("texto", ["0", "7", "10", "42", "123456789", "0000"])
def test_literais_inteiros(texto):
    assert toks(texto) == [(LITERAL_INTEIRO, texto)]


@pytest.mark.parametrize("texto", ["3.14", "0.5", "10.0", "00.5", "123.456"])
def test_literais_decimais(texto):
    assert toks(texto) == [(LITERAL_DECIMAL, texto)]


@pytest.mark.parametrize(
    "texto, trecho",
    [
        ("007", "zeros à esquerda"),
        ("3.", "sem dígitos depois do ponto"),
        (".5", "sem parte inteira"),
        ("1.2.3", "mais de um ponto"),
        ("12abc", "seguido de letras"),
        ("3.x", "inválidos"),
        ("1e5", "seguido de letras"),
    ],
)
def test_literais_malformados_geram_um_unico_erro(texto, trecho):
    r = analisar_lexico(texto)
    assert r.sucesso is False
    assert len(r.erros) == 1
    assert r.erros[0].lexema == texto
    assert trecho in r.erros[0].mensagem
    assert toks(texto) == []  # nada é emitido como token válido


def test_classificar_numero_direto():
    assert classificar_numero("5") == (LITERAL_INTEIRO, None)
    assert classificar_numero("5.5") == (LITERAL_DECIMAL, None)
    assert classificar_numero("05")[0] is None


def test_numero_colado_em_operador():
    assert toks("10+2.5") == [
        (LITERAL_INTEIRO, "10"),
        (OPERADOR_ARITMETICO, "+"),
        (LITERAL_DECIMAL, "2.5"),
    ]


# ------------------------------------------------------------------ operadores
@pytest.mark.parametrize("op", ["+", "-", "*", "/"])
def test_operadores_aritmeticos(op):
    assert toks(op) == [(OPERADOR_ARITMETICO, op)]


@pytest.mark.parametrize("op", ["<", ">", "<=", ">=", "==", "!="])
def test_operadores_relacionais_inclusive_compostos(op):
    assert toks(op) == [(OPERADOR_RELACIONAL, op)]


def test_atribuicao():
    assert toks("=") == [(OPERADOR_ATRIBUICAO, "=")]


def test_operador_composto_tem_prioridade_sobre_simples():
    assert toks("a<=b") == [
        (IDENTIFICADOR, "a"),
        (OPERADOR_RELACIONAL, "<="),
        (IDENTIFICADOR, "b"),
    ]
    assert toks("a==b")[1] == (OPERADOR_RELACIONAL, "==")


def test_operadores_com_espaco_no_meio_sao_dois_tokens():
    assert toks("< =") == [(OPERADOR_RELACIONAL, "<"), (OPERADOR_ATRIBUICAO, "=")]
    assert toks("= =") == [(OPERADOR_ATRIBUICAO, "="), (OPERADOR_ATRIBUICAO, "=")]


def test_tres_iguais_viram_igualdade_e_atribuicao():
    assert toks("===") == [(OPERADOR_RELACIONAL, "=="), (OPERADOR_ATRIBUICAO, "=")]


def test_exclamacao_sozinha_e_erro_com_sugestao():
    r = analisar_lexico("a ! b")
    assert r.sucesso is False
    assert r.erros[0].lexema == "!"
    assert "!=" in r.erros[0].mensagem
    assert toks("a ! b") == [(IDENTIFICADOR, "a"), (IDENTIFICADOR, "b")]


@pytest.mark.parametrize("op", ["**", "//", "%", "+=", "->", "<>"])
def test_operadores_fora_do_subconjunto_nao_viram_um_token_so(op):
    # "**" vira dois "*"; "%" é erro; "<>" vira "<" e ">"; etc.
    lexemas = [lex for _, lex in toks(op)]
    assert op not in lexemas


# ---------------------------------------------------------------- delimitadores
@pytest.mark.parametrize("d", ["(", ")", ":"])
def test_delimitadores(d):
    assert toks(d) == [(DELIMITADOR, d)]


@pytest.mark.parametrize("c", ["{", "}", "[", "]", ",", ";"])
def test_delimitadores_de_outras_linguagens_sao_erro(c):
    r = analisar_lexico(c)
    assert r.sucesso is False
    assert r.erros[0].lexema == c


# ------------------------------------------------------------------ comentários
def test_comentario_de_linha_e_ignorado():
    assert toks("# so um comentario") == []
    assert toks("x = 1  # comentário aqui") == [
        (IDENTIFICADOR, "x"),
        (OPERADOR_ATRIBUICAO, "="),
        (LITERAL_INTEIRO, "1"),
    ]


def test_comentario_pode_conter_caracteres_invalidos():
    r = analisar_lexico("x = 1  # @ $ ? ç 'aspas\n")
    assert r.sucesso is True


def test_comentario_termina_na_quebra_de_linha():
    r = analisar_lexico("# c1\nx = 1 # c2\ny = 2\n")
    assert r.sucesso is True
    assert [l for t, l in toks("# c1\nx = 1 # c2\ny = 2\n")] == [
        "x", "=", "1", "y", "=", "2",
    ]


def test_comentario_nao_gera_newline_proprio():
    assert tipos("# c\n# c\n") == [FIM_DE_ARQUIVO]


def test_comentario_entre_blocos_nao_altera_indentacao():
    codigo = "if x:\n    a = 1\n# comentário na coluna 1\n    b = 2\n"
    ts = tipos(codigo)
    assert ts.count(INDENT) == 1
    assert ts.count(DEDENT) == 1  # só no fim do arquivo


# ------------------------------------------------------------ espaços em branco
def test_espacos_e_tabs_no_meio_da_linha_sao_ignorados():
    assert toks("a   =\t1") == [
        (IDENTIFICADOR, "a"),
        (OPERADOR_ATRIBUICAO, "="),
        (LITERAL_INTEIRO, "1"),
    ]


def test_linhas_em_branco_nao_geram_tokens():
    assert tipos("\n\n   \n\t\n") == [FIM_DE_ARQUIVO]
    assert tipos("x = 1\n\n\ny = 2\n").count(NEWLINE) == 2


def test_quebras_de_linha_windows_e_mac_sao_normalizadas():
    for quebra in ("\r\n", "\r", "\n"):
        r = analisar_lexico(f"a = 1{quebra}b = 2{quebra}")
        ids = [(t.lexema, t.linha, t.coluna) for t in r.tokens if t.tipo == IDENTIFICADOR]
        assert ids == [("a", 1, 1), ("b", 2, 1)]


# --------------------------------------------------------------------- posição
def test_posicao_linha_e_coluna_comecam_em_1():
    r = analisar_lexico("int numero = 10;")
    primeiro = r.tokens[0]
    assert (primeiro.linha, primeiro.coluna) == (1, 1)


def test_posicoes_em_varias_linhas_e_colunas():
    r = analisar_lexico("x = 10\nresultado = x + 2\n")
    pos = {(t.lexema, t.linha): t.coluna for t in r.tokens if t.tipo in (IDENTIFICADOR, OPERADOR_ARITMETICO, LITERAL_INTEIRO)}
    assert pos[("x", 1)] == 1
    assert pos[("10", 1)] == 5
    assert pos[("resultado", 2)] == 1
    assert pos[("x", 2)] == 13
    assert pos[("+", 2)] == 15
    assert pos[("2", 2)] == 17


def test_posicao_conta_caracteres_e_nao_bytes():
    r = analisar_lexico("# ação ✓\nx = 1\n")
    x = next(t for t in r.tokens if t.lexema == "x")
    assert (x.linha, x.coluna) == (2, 1)
    r2 = analisar_lexico("x = ç + 1")
    assert (r2.erros[0].linha, r2.erros[0].coluna) == (1, 5)


def test_posicao_apos_comentario():
    r = analisar_lexico("a = 1  # c\nb = 2")
    b = next(t for t in r.tokens if t.lexema == "b")
    assert (b.linha, b.coluna) == (2, 1)


def test_todo_token_com_lexema_visivel_esta_na_posicao_informada():
    codigo = "x = 10\nwhile x != 0:\n    y = (x + 3.5) * 2  # fim\n    x = x - 1\n"
    linhas = codigo.split("\n")
    for t in analisar_lexico(codigo).tokens:
        if t.tipo in ESTRUTURAIS:
            continue
        trecho = linhas[t.linha - 1][t.coluna - 1 : t.coluna - 1 + len(t.lexema)]
        assert trecho == t.lexema, t


# ---------------------------------------------------------------- erros léxicos
@pytest.mark.parametrize("c", ["@", "$", "?", "`", "~", "^", "&", "|", "%", "\\"])
def test_caracteres_invalidos_geram_erro_com_localizacao(c):
    r = analisar_lexico(f"x = 1 {c} 2")
    assert r.sucesso is False
    assert len(r.erros) == 1
    e = r.erros[0]
    assert (e.lexema, e.linha, e.coluna) == (c, 1, 7)
    assert "Caractere não reconhecido" in e.mensagem


def test_erro_segue_o_formato_do_enunciado():
    e = analisar_lexico("x = 1\ny = 2 @ 3\n").erros[0].como_dict()
    assert set(e) == {"tipo", "lexema", "linha", "coluna", "mensagem"}
    assert e["tipo"] == "ERRO_LEXICO"
    assert (e["linha"], e["coluna"]) == (2, 7)
    assert e["mensagem"].startswith("Caractere não reconhecido: '@'")


def test_scanner_continua_apos_erro_e_acumula_todos():
    r = analisar_lexico("a = 1 @\nb = 2 $\nc = 3.4.5\n")
    assert [e.lexema for e in r.erros] == ["@", "$", "3.4.5"]
    assert [e.linha for e in r.erros] == [1, 2, 3]
    nomes = [lex for tp, lex in toks("a = 1 @\nb = 2 $\nc = 3.4.5\n") if tp == IDENTIFICADOR]
    assert nomes == ["a", "b", "c"]  # nada depois do primeiro erro foi perdido


def test_string_inteira_vira_um_unico_erro_com_mensagem_especifica():
    for texto, lexema in [('x = "oi"', '"oi"'), ("x = 'oi'", "'oi'")]:
        r = analisar_lexico(texto)
        assert r.sucesso is False
        assert len(r.erros) == 1
        assert r.erros[0].lexema == lexema
        assert (r.erros[0].linha, r.erros[0].coluna) == (1, 5)
        assert "string" in r.erros[0].mensagem.lower()
        assert toks(texto) == [(IDENTIFICADOR, "x"), (OPERADOR_ATRIBUICAO, "=")]


def test_string_sem_fechar_para_no_fim_da_linha():
    r = analisar_lexico('x = "oi\ny = 2\n')
    assert [e.lexema for e in r.erros] == ['"oi']
    assert "sem aspa de fechamento" in r.erros[0].mensagem
    assert (IDENTIFICADOR, "y") in toks('x = "oi\ny = 2\n')  # linha seguinte intacta


def test_aspas_dentro_de_comentario_sao_ignoradas():
    assert analisar_lexico("x = 1  # diz \"oi\n").sucesso is True


def test_caractere_de_controle_e_mostrado_de_forma_segura():
    r = analisar_lexico("x = 1\x00")
    assert r.sucesso is False
    assert "\x00" not in r.erros[0].mensagem
    assert "\\x00" in r.erros[0].mensagem


def test_erro_nao_expoe_detalhes_internos():
    r = analisar_lexico("@ $ ? 1.2.3 007")
    for e in r.erros:
        assert "Traceback" not in e.mensagem
        assert "scanner.py" not in e.mensagem


def test_limite_de_erros_devolvidos_mas_contagem_exata():
    r = analisar_lexico("@" * (MAX_ERROS + 50))
    assert len(r.erros) == MAX_ERROS
    assert r.total_erros == MAX_ERROS + 50
    resumo = r.como_dict()["resumo"]
    assert resumo["total_erros"] == MAX_ERROS + 50
    assert resumo["erros_omitidos"] == 50


# ------------------------------------------------- indentação (INDENT / DEDENT)
def test_bloco_simples_gera_indent_e_dedent():
    ts = tipos("if x:\n    y = 1\nz = 2\n")
    assert ts.count(INDENT) == 1
    assert ts.count(DEDENT) == 1
    assert ts.index(INDENT) < ts.index(DEDENT)


def test_posicao_de_indent_e_dedent():
    r = analisar_lexico("if x:\n    y = 1\nz = 2\n")
    indent = next(t for t in r.tokens if t.tipo == INDENT)
    dedent = next(t for t in r.tokens if t.tipo == DEDENT)
    assert (indent.linha, indent.coluna, indent.lexema) == (2, 1, "    ")
    assert (dedent.linha, dedent.coluna) == (3, 1)


def test_blocos_aninhados_e_dedent_multiplo():
    codigo = "while a:\n    if b:\n        c = 1\nd = 2\n"
    ts = tipos(codigo)
    assert ts.count(INDENT) == 2
    assert ts.count(DEDENT) == 2
    # os dois DEDENT saem juntos, antes de "d"
    i = ts.index(DEDENT)
    assert ts[i : i + 2] == [DEDENT, DEDENT]


def test_dedent_gerado_no_fim_do_arquivo():
    ts = tipos("if x:\n    y = 1")
    assert ts[-3:] == [NEWLINE, DEDENT, FIM_DE_ARQUIVO]


def test_indent_e_dedent_balanceados_em_codigo_sem_erro():
    codigo = "x = 5\nwhile x != 0:\n    if x > 2:\n        x = x - 2\n    else:\n        x = x - 1\n"
    r = analisar_lexico(codigo)
    assert r.sucesso
    ts = [t.tipo for t in r.tokens]
    assert ts.count(INDENT) == ts.count(DEDENT) == 3


def test_indentacao_inconsistente_e_erro_lexico():
    r = analisar_lexico("if x:\n    a = 1\n  b = 2\n")
    assert r.sucesso is False
    assert r.erros[0].linha == 3
    assert "Indentação inconsistente" in r.erros[0].mensagem
    assert "0, 4" in r.erros[0].mensagem  # níveis abertos antes do erro


def test_tabulacao_na_indentacao_e_erro_didatico():
    r = analisar_lexico("if x:\n\ty = 1\n")
    assert r.sucesso is False
    assert r.erros[0].lexema == "\t"
    assert (r.erros[0].linha, r.erros[0].coluna) == (2, 1)
    assert "espaços" in r.erros[0].mensagem


def test_linhas_em_branco_dentro_de_bloco_nao_geram_dedent():
    ts = tipos("if x:\n    a = 1\n\n\n    b = 2\n")
    assert ts.count(INDENT) == 1
    assert ts.count(DEDENT) == 1


def test_parenteses_abertos_suspendem_newline_e_indentacao():
    codigo = "a = (1 +\n        2 +\n  3)\nb = 4\n"
    r = analisar_lexico(codigo)
    assert r.sucesso is True
    ts = [t.tipo for t in r.tokens]
    assert INDENT not in ts and DEDENT not in ts
    assert ts.count(NEWLINE) == 2  # uma por linha lógica


def test_parentese_fechando_sem_abrir_nao_quebra():
    r = analisar_lexico("x = 1)\ny = 2\n")
    assert r.sucesso is True  # estrutura é problema do parser, não do scanner
    assert any(t.lexema == ")" for t in r.tokens)


def test_scanner_nao_valida_estrutura_sintatica():
    # tokens válidos, programa sintaticamente errado: deve tokenizar normalmente
    r = analisar_lexico("x = = 3 +\nif :\n(((\n")
    assert r.sucesso is True


# ------------------------------------------------------------ casos de borda
def test_codigo_vazio():
    r = analisar_lexico("")
    assert r.sucesso is True
    assert [t.tipo for t in r.tokens] == [FIM_DE_ARQUIVO]


def test_apenas_espacos():
    r = analisar_lexico("   \n\t  \n   ")
    assert r.sucesso is True
    assert [t.tipo for t in r.tokens] == [FIM_DE_ARQUIVO]


def test_apenas_comentarios():
    r = analisar_lexico("# a\n   # b\n# c")
    assert r.sucesso is True
    assert [t.tipo for t in r.tokens] == [FIM_DE_ARQUIVO]


def test_token_no_fim_do_arquivo_sem_quebra_de_linha():
    r = analisar_lexico("x = 10")
    ts = [(t.tipo, t.lexema) for t in r.tokens]
    assert ts[-3:] == [(LITERAL_INTEIRO, "10"), (NEWLINE, ""), (FIM_DE_ARQUIVO, "")]
    assert r.sucesso is True


def test_com_e_sem_quebra_final_dao_os_mesmos_tokens_visiveis():
    assert toks("x = 1") == toks("x = 1\n")


def test_arquivo_termina_em_erro():
    r = analisar_lexico("x = 1 @")
    assert r.sucesso is False
    assert r.tokens[-1].tipo == FIM_DE_ARQUIVO


def test_primeira_linha_indentada_gera_indent():
    # É o parser (Etapa 4) quem rejeita; o scanner só relata o token.
    assert INDENT in tipos("    x = 1\n")


def test_entrada_grande_e_processada():
    codigo = "x = 1\n" * 15000
    r = analisar_lexico(codigo)
    assert r.sucesso is True
    assert len(r.tokens) == 15000 * 4 + 1


# --------------------------------------------------- exemplo do enunciado
def test_exemplo_de_python_do_enunciado_equivalente():
    r = analisar_lexico("numero = 10\n")
    assert [(t.tipo, t.lexema, t.linha, t.coluna) for t in r.tokens[:3]] == [
        (IDENTIFICADOR, "numero", 1, 1),
        (OPERADOR_ATRIBUICAO, "=", 1, 8),
        (LITERAL_INTEIRO, "10", 1, 10),
    ]


def test_resumo_conta_tokens_por_tipo():
    d = analisar_lexico("x = 1 + 2\n").como_dict()
    assert d["resumo"]["total_tokens"] == len(d["tokens"])
    assert d["resumo"]["por_tipo"][IDENTIFICADOR] == 1
    assert d["resumo"]["por_tipo"][LITERAL_INTEIRO] == 2
    assert d["resumo"]["por_tipo"][OPERADOR_ARITMETICO] == 1


# ------------------------------------------------------ robustez (aleatório)
def test_nunca_levanta_excecao_com_entradas_aleatorias():
    alfabeto = list("abcxyz_0123456789 \t\n\r.+-*/=!<>():#@$?'\"\\{}[],;%&|^~`çí✓\x00\x0c") + ["if", "while", "else", "def"]
    rng = random.Random(12345)
    for _ in range(600):
        codigo = "".join(rng.choice(alfabeto) for _ in range(rng.randint(0, 80)))
        r = analisar_lexico(codigo)
        assert r.tokens[-1].tipo == FIM_DE_ARQUIVO
        linhas = codigo.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        for t in r.tokens:
            assert 1 <= t.linha <= len(linhas) + 1
            assert t.coluna >= 1
            if t.tipo not in ESTRUTURAIS:
                trecho = linhas[t.linha - 1][t.coluna - 1 : t.coluna - 1 + len(t.lexema)]
                assert trecho == t.lexema
        for e in r.erros:
            assert e.mensagem
            assert 1 <= e.linha <= len(linhas)
