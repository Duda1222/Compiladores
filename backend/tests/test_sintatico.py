"""Testes do parser e da AST (Etapa 4)."""

import ast as python_ast
import random

import pytest

import arvore as A
from scanner import analisar_lexico
from sintatico import MAX_ERROS_SINTATICOS, analisar_sintatico


def analisar(codigo):
    lex = analisar_lexico(codigo)
    assert lex.sucesso, f"o teste esperava código sem erro léxico: {lex.erros}"
    return analisar_sintatico(lex.tokens)


def arvore(codigo):
    r = analisar(codigo)
    assert r.sucesso, [e.mensagem for e in r.erros]
    return A.em_texto(r.ast)


def erros(codigo):
    r = analisar(codigo)
    assert not r.sucesso, "o teste esperava erro sintático"
    assert r.ast is None or not r.sucesso
    return r.erros


def linhas(texto):
    return [l.rstrip() for l in texto.strip("\n").split("\n")]


# ------------------------------------------------------------- construções
class TestConstrucoesValidas:
    def test_atribuicao_com_inteiro(self):
        assert arvore("x = 10\n") == "Programa\n  Atribuicao\n    Identificador x\n    Numero 10"

    def test_atribuicao_com_decimal(self):
        r = analisar("y = 3.14\n")
        num = r.ast.filhos[0].filhos[1]
        assert (num.tipo, num.atributos) == (A.NUMERO, {"lexema": "3.14", "tipo_numero": "decimal"})

    def test_identificador_com_underscore_e_digitos(self):
        assert "Identificador _x1" in arvore("_x1 = 0\n")

    def test_expressao_como_comando(self):
        assert arvore("x + 1\n") == "Programa\n  ExpressaoComando\n    OperacaoBinaria +\n      Identificador x\n      Numero 1"

    def test_apenas_um_identificador(self):
        assert "ExpressaoComando" in arvore("x\n")

    def test_if_sem_else(self):
        t = arvore("if x > 0:\n    y = 1\n")
        assert "Condicional" in t and t.count("Bloco") == 1

    def test_if_com_else(self):
        t = arvore("if x > 0:\n    y = 1\nelse:\n    y = 2\n")
        assert t.count("Bloco") == 2

    def test_papeis_do_condicional(self):
        no = analisar("if a:\n    b = 1\nelse:\n    b = 2\n").ast.filhos[0]
        assert [f.papel for f in no.filhos] == ["condicao", "entao", "senao"]

    def test_while(self):
        no = analisar("while x != 0:\n    x = x - 1\n").ast.filhos[0]
        assert no.tipo == A.REPETICAO
        assert [f.papel for f in no.filhos] == ["condicao", "corpo"]

    @pytest.mark.parametrize("op", ["<", ">", "<=", ">=", "==", "!="])
    def test_cada_operador_relacional(self, op):
        no = analisar(f"a {op} b\n").ast.filhos[0].filhos[0]
        assert no.tipo == A.COMPARACAO and no.atributos["operador"] == op

    @pytest.mark.parametrize("op", ["+", "-", "*", "/"])
    def test_cada_operador_aritmetico(self, op):
        no = analisar(f"a {op} b\n").ast.filhos[0].filhos[0]
        assert no.tipo == A.OPERACAO_BINARIA and no.atributos["operador"] == op

    def test_unario(self):
        no = analisar("x = -y\n").ast.filhos[0].filhos[1]
        assert no.tipo == A.OPERACAO_UNARIA and no.atributos["operador"] == "-"

    def test_unario_duplo(self):
        assert arvore("x = - -3\n").count("OperacaoUnaria") == 2

    def test_unario_dentro_de_binaria(self):
        assert arvore("x = 5 - -3\n").count("OperacaoUnaria") == 1

    def test_comentarios_e_linhas_em_branco_sao_ignorados(self):
        assert arvore("# oi\n\nx = 1  # fim\n\n") == arvore("x = 1\n")

    def test_arquivo_sem_quebra_final(self):
        assert arvore("x = 1") == arvore("x = 1\n")

    def test_varios_comandos(self):
        assert len(analisar("a = 1\nb = 2\nc = 3\n").ast.filhos) == 3

    def test_comando_apos_bloco(self):
        r = analisar("if a:\n    b = 1\nc = 2\n")
        assert [f.tipo for f in r.ast.filhos] == [A.CONDICIONAL, A.ATRIBUICAO]

    def test_continuacao_dentro_de_parenteses(self):
        assert arvore("x = (1 +\n     2)\n") == arvore("x = 1 + 2\n")


# --------------------------------------------- precedência e associatividade
class TestPrecedencia:
    def test_multiplicacao_antes_da_soma(self):
        assert linhas(arvore("10 + 5 * 2\n"))[2:] == [
            "    OperacaoBinaria +", "      Numero 10", "      OperacaoBinaria *",
            "        Numero 5", "        Numero 2"]

    def test_parenteses_mudam_a_ordem(self):
        assert linhas(arvore("(10 + 5) * 2\n"))[2:] == [
            "    OperacaoBinaria *", "      OperacaoBinaria +", "        Numero 10",
            "        Numero 5", "      Numero 2"]

    def test_subtracao_associa_a_esquerda(self):
        assert linhas(arvore("20 - 5 - 3\n"))[2:] == [
            "    OperacaoBinaria -", "      OperacaoBinaria -", "        Numero 20",
            "        Numero 5", "      Numero 3"]

    def test_divisao_associa_a_esquerda(self):
        r = analisar("8 / 4 / 2\n").ast.filhos[0].filhos[0]
        assert r.filhos[0].tipo == A.OPERACAO_BINARIA and r.filhos[1].tipo == A.NUMERO

    def test_relacional_tem_menor_precedencia_que_aritmetica(self):
        no = analisar("a + 1 > b * 2\n").ast.filhos[0].filhos[0]
        assert no.tipo == A.COMPARACAO
        assert [f.tipo for f in no.filhos] == [A.OPERACAO_BINARIA, A.OPERACAO_BINARIA]

    def test_unario_liga_mais_forte_que_multiplicacao(self):
        no = analisar("-a * b\n").ast.filhos[0].filhos[0]
        assert no.tipo == A.OPERACAO_BINARIA and no.filhos[0].tipo == A.OPERACAO_UNARIA

    def test_parenteses_nao_aparecem_na_ast(self):
        assert arvore("x = (((1)))\n") == arvore("x = 1\n")

    def test_parenteses_aninhados(self):
        assert arvore("x = ((1 + 2) * (3 - 4))\n").count("OperacaoBinaria") == 3


# ----------------------------------------------------------------- aninhamento
class TestAninhamento:
    def test_if_dentro_de_while(self):
        t = arvore("while a:\n    if b:\n        c = 1\n")
        assert t.index("Repeticao") < t.index("Condicional")

    def test_dois_niveis_de_if_com_else(self):
        codigo = ("if a:\n    if b:\n        x = 1\n    else:\n        x = 2\nelse:\n    x = 3\n")
        assert arvore(codigo).count("Condicional") == 2

    def test_else_pertence_ao_if_mais_proximo_pela_indentacao(self):
        codigo = "if a:\n    if b:\n        x = 1\nelse:\n    x = 2\n"
        externo = analisar(codigo).ast.filhos[0]
        interno = externo.filhos[1].filhos[0]
        assert len(externo.filhos) == 3 and len(interno.filhos) == 2

    def test_varios_dedents_seguidos(self):
        codigo = "while a:\n    while b:\n        while c:\n            x = 1\ny = 2\n"
        r = analisar(codigo)
        assert [f.tipo for f in r.ast.filhos] == [A.REPETICAO, A.ATRIBUICAO]

    def test_aninhamento_dentro_do_limite(self):
        codigo = ""
        for n in range(10):
            codigo += "    " * n + "while a:\n"
        codigo += "    " * 10 + "x = 1\n"
        assert analisar(codigo).sucesso


# ------------------------------------------------------------------- posições
class TestPosicoes:
    def test_posicao_de_atribuicao(self):
        no = analisar("  \nx = 10\n").ast.filhos[0]
        assert (no.linha, no.coluna, no.linha_fim, no.coluna_fim) == (2, 1, 2, 7)

    def test_posicao_de_operacao_binaria(self):
        no = analisar("y = 1 + 22\n").ast.filhos[0].filhos[1]
        assert (no.linha, no.coluna, no.linha_fim, no.coluna_fim) == (1, 5, 1, 11)

    def test_posicao_do_if_cobre_o_bloco(self):
        no = analisar("if a:\n    b = 1\n").ast.filhos[0]
        assert (no.linha, no.coluna, no.linha_fim, no.coluna_fim) == (1, 1, 2, 10)

    def test_posicao_de_identificador_alvo(self):
        alvo = analisar("abc = 1\n").ast.filhos[0].filhos[0]
        assert (alvo.coluna, alvo.coluna_fim) == (1, 4)

    def test_programa_cobre_o_arquivo(self):
        r = analisar("a = 1\nb = 2\n")
        assert (r.ast.linha, r.ast.coluna, r.ast.linha_fim, r.ast.coluna_fim) == (1, 1, 2, 6)


# ---------------------------------------------------------------- casos limite
class TestCasosLimite:
    def test_somente_comentarios_gera_programa_vazio(self):
        r = analisar("# nada\n")
        assert r.sucesso and r.ast.filhos == []

    def test_programa_vazio_tem_posicao_valida(self):
        r = analisar("# nada\n")
        assert (r.ast.linha, r.ast.coluna) == (1, 1)

    def test_espacos_e_linhas_em_branco(self):
        assert analisar("   \n\n   \n").sucesso

    def test_numero_enorme_nao_quebra(self):
        assert analisar("x = " + "9" * 6000 + "\n").sucesso

    def test_cadeia_longa_dentro_do_limite(self):
        assert analisar("x = " + " + ".join(["1"] * 100) + "\n").sucesso

    def test_cadeia_acima_do_limite_vira_erro_amigavel(self):
        r = analisar("x = " + " + ".join(["1"] * 400) + "\n")
        assert not r.sucesso and "profunda demais" in r.erros[0].mensagem

    def test_muitos_sinais_unarios_viram_erro_amigavel(self):
        r = analisar("x = " + "-" * 5000 + "1\n")
        assert not r.sucesso

    def test_parenteses_demais_viram_erro_amigavel(self):
        r = analisar("x = " + "(" * 200 + "1" + ")" * 200 + "\n")
        assert not r.sucesso and "aninhados demais" in r.erros[0].mensagem

    def test_blocos_demais_viram_erro_amigavel(self):
        codigo = ""
        for n in range(40):
            codigo += "    " * n + "while a:\n"
        codigo += "    " * 40 + "x = 1\n"
        r = analisar(codigo)
        assert not r.sucesso and any("aninhados demais" in e.mensagem for e in r.erros)

    def test_programa_grande_e_valido(self):
        codigo = "".join(f"v{i} = {i} * 2 + 1\n" for i in range(3000))
        r = analisar(codigo)
        assert r.sucesso and len(r.ast.filhos) == 3000


# ---------------------------------------------------------------------- erros
class TestErrosSintaticos:
    def teste_campos_do_erro(self):
        e = erros("x = 10 +\n")[0].como_dict()
        assert e["tipo"] == "ERRO_SINTATICO"
        assert {"linha", "coluna", "encontrado", "esperado", "mensagem"} <= set(e)
        assert isinstance(e["esperado"], list) and e["esperado"]

    def test_expressao_incompleta_no_fim_da_linha(self):
        e = erros("x = 10 +\n")[0]
        assert (e.linha, e.coluna, e.encontrado) == (1, 9, "fim da linha")
        assert "falta o operando" in e.mensagem

    def test_atribuicao_sem_valor(self):
        e = erros("x =\n")[0]
        assert e.encontrado == "fim da linha" and (e.linha, e.coluna) == (1, 4)

    def test_operadores_consecutivos(self):
        e = erros("x = 1 + * 2\n")[0]
        assert (e.linha, e.coluna, e.encontrado) == (1, 9, "*")
        assert "consecutivos" in e.mensagem

    def test_igual_igual_digitado_errado(self):
        e = erros("x = = 3\n")[0]
        assert "consecutivos" in e.mensagem and "==" in e.dica

    def test_parentese_nao_fechado_no_fim(self):
        e = erros("y = (3 * 4\n")[0]
        assert "não foi fechado" in e.mensagem and "linha 1, coluna 5" in e.mensagem
        assert "')'" in e.esperado

    def test_parentese_nao_fechado_com_codigo_depois(self):
        e = erros("y = (3 * 4\nz = 1\n")[0]
        assert (e.linha, e.coluna, e.encontrado) == (2, 1, "z")
        assert "continua aberto" in e.mensagem

    def test_parentese_fechando_sem_abrir(self):
        e = erros("x = 3)\n")[0]
        assert "sem o '(' correspondente" in e.mensagem and e.coluna == 6

    def test_parenteses_vazios(self):
        assert "vazios" in erros("x = ()\n")[0].mensagem

    def test_if_sem_dois_pontos(self):
        e = erros("if x > 0\n    y = 1\n")[0]
        assert "Faltou o ':'" in e.mensagem and e.esperado == ["':'"]

    def test_while_sem_dois_pontos(self):
        assert "Faltou o ':'" in erros("while x\n    y = 1\n")[0].mensagem

    def test_else_sem_dois_pontos(self):
        assert "Faltou o ':'" in erros("if a:\n    b = 1\nelse\n    b = 2\n")[0].mensagem

    def test_if_com_atribuicao_na_condicao(self):
        e = erros("if x = 3:\n    y = 1\n")[0]
        assert "'=='" in e.mensagem and e.coluna == 6

    def test_if_sem_condicao(self):
        e = erros("if :\n    y = 1\n")[0]
        assert e.encontrado == ":"

    def test_else_sem_if(self):
        e = erros("else:\n    x = 1\n")[0]
        assert "sem um 'if'" in e.mensagem and (e.linha, e.coluna) == (1, 1)

    def test_bloco_sem_indentacao(self):
        e = erros("if x:\ny = 1\n")[0]
        assert "indentado" in e.mensagem and (e.linha, e.coluna) == (2, 1)

    def test_bloco_no_fim_do_arquivo(self):
        e = erros("if x:\n")[0]
        assert e.encontrado == "fim do arquivo" and (e.linha, e.coluna) == (1, 6)

    def test_corpo_na_mesma_linha(self):
        e = erros("if x: y = 1\n")[0]
        assert "linha seguinte" in e.mensagem

    def test_indentacao_inesperada(self):
        e = erros("x = 1\n    y = 2\n")[0]
        assert "Indentação inesperada" in e.mensagem and e.linha == 2

    def test_palavra_reservada_como_variavel(self):
        e = erros("if = 3\n")[0]
        assert "não pode ser usada" in e.mensagem

    def test_palavra_reservada_fora_do_subconjunto(self):
        e = erros("def f\n")[0]
        assert "ainda não faz parte do subconjunto" in e.mensagem

    def test_elif_orienta_uso_de_else_if(self):
        e = erros("if a:\n    b = 1\nelif c:\n    b = 2\n")[0]
        assert "elif" in e.mensagem and "else" in e.dica

    def test_faltou_operador(self):
        e = erros("x 5\n")[0]
        assert "Faltou um operador" in e.mensagem and (e.linha, e.coluna) == (1, 3)

    def test_atribuicao_encadeada(self):
        assert "encadeada" in erros("a = b = 1\n")[0].mensagem

    def test_comparacao_encadeada(self):
        assert "encadeada" in erros("a < b < c\n")[0].mensagem

    def test_lado_esquerdo_invalido(self):
        e = erros("3 = x\n")[0]
        assert "lado esquerdo" in e.mensagem and e.coluna == 3

    def test_dois_pontos_solto(self):
        assert "':'" in erros("x = 1 :\n")[0].mensagem

    def test_comando_comeca_com_simbolo_invalido(self):
        e = erros(") x\n")[0]
        assert "início de um comando" in e.mensagem

    def test_erro_traz_regra_da_gramatica(self):
        assert "bloco →" in erros("if x:\ny = 1\n")[0].regra

    def test_mensagens_nao_vazam_detalhes_internos(self):
        for codigo in ["x = (\n", "if\n", "while :\n", "x = 1 +\n", "= 1\n"]:
            for e in erros(codigo):
                texto = str(e.como_dict())
                assert "Traceback" not in texto and "File \"" not in texto and ".py" not in texto


class TestRecuperacao:
    def test_varios_erros_independentes_sao_relatados(self):
        es = erros("x = 10 +\ny = 3 * * 2\nz = (1\n")
        assert [e.linha for e in es] == [1, 2, 3]

    def test_erro_nao_impede_comandos_validos_seguintes(self):
        es = erros("a = = 1\nb = 2\nc = 3 +\n")
        assert [e.linha for e in es] == [1, 3]

    def test_erro_no_cabecalho_do_if_pula_o_bloco_sem_cascata(self):
        es = erros("if x = 3:\n    y = 1\n    z = = 2\nw = 1\n")
        assert [e.linha for e in es] == [1]

    def test_else_do_if_com_erro_nao_gera_erro_em_cascata(self):
        es = erros("if x = 3:\n    y = 1\nelse:\n    y = 2\n")
        assert [e.linha for e in es] == [1]

    def test_erros_dentro_de_blocos_sao_relatados(self):
        es = erros("while a:\n    x = = 1\n    y = 2\n    z = 3 +\n")
        assert [e.linha for e in es] == [2, 4]

    def test_mais_de_um_else_orfao_conta_cada_um(self):
        es = erros("else:\n    a = 1\nelse:\n    b = 2\n")
        assert len(es) == 2

    def test_indentacao_inesperada_pula_o_bloco(self):
        es = erros("x = 1\n    y = = 2\n    z = 3\n")
        assert [e.linha for e in es] == [2]

    def test_limite_de_erros_listados_e_total_exato(self):
        codigo = "x = =\n" * 50
        r = analisar(codigo)
        assert len(r.erros) == MAX_ERROS_SINTATICOS and r.total_erros == 50
        assert r.como_dict()["resumo"]["erros_omitidos"] == 50 - MAX_ERROS_SINTATICOS

    def test_ast_e_nula_quando_ha_erro(self):
        r = analisar("a = 1\nb = =\n")
        assert r.ast is None and r.como_dict()["ast"] is None

    def test_analise_sempre_termina(self):
        # entradas aleatórias de tokens válidos: nunca lança exceção e sempre termina
        rnd = random.Random(7)
        pecas = ["x", "1", "3.5", "+", "-", "*", "/", "=", "==", "<", "(", ")", ":",
                 "if", "else", "while", "\n", "\n    ", "\n        ", " "]
        for _ in range(800):
            codigo = "".join(rnd.choice(pecas) for _ in range(rnd.randint(1, 25)))
            lex = analisar_lexico(codigo)
            if lex.sucesso:
                r = analisar_sintatico(lex.tokens)
                assert r.sucesso or r.total_erros >= 1


# --------------------------------------------------------- árvore de derivação
class TestDerivacao:
    def test_derivacao_tem_nao_terminais_e_terminais(self):
        d = analisar("x = 1 + 2\n").derivacao
        assert d["simbolo"] == "programa"

        def coleta(no, acc):
            acc.append(no)
            for f in no.get("filhos", []):
                coleta(f, acc)
            return acc

        todos = coleta(d, [])
        simbolos = {n["simbolo"] for n in todos}
        assert {"comando", "atribuicao", "expressao", "soma", "termo", "unario", "primario"} <= simbolos

    def test_derivacao_e_maior_que_a_ast(self):
        r = analisar("x = 1\n")

        def conta(no):
            return 1 + sum(conta(f) for f in no.get("filhos", []))

        assert conta(r.derivacao) > A.contar(r.ast)["total_nos"]

    def test_folhas_da_derivacao_reproduzem_os_tokens(self):
        codigo = "x = 7\nif x > 0:\n    y = (x + 1) * 2\nelse:\n    y = -x\n"
        lex = analisar_lexico(codigo)
        r = analisar_sintatico(lex.tokens)
        folhas = []

        def coleta(no):
            if no.get("terminal"):
                folhas.append((no["tipo"], no["lexema"], no["linha"], no["coluna"]))
            for f in no.get("filhos", []):
                coleta(f)

        coleta(r.derivacao)
        assert folhas == [(t.tipo, t.lexema, t.linha, t.coluna) for t in lex.tokens]


# -------------------------------------- comparação com o módulo ast do Python
OPS_PY = {python_ast.Add: "+", python_ast.Sub: "-", python_ast.Mult: "*",
          python_ast.Div: "/", python_ast.USub: "-", python_ast.UAdd: "+",
          python_ast.Lt: "<", python_ast.Gt: ">", python_ast.LtE: "<=",
          python_ast.GtE: ">=", python_ast.Eq: "==", python_ast.NotEq: "!="}


def py_texto(no, fonte, nivel=0):
    pad = "  " * nivel
    if isinstance(no, python_ast.Module):
        filhos = [py_texto(f, fonte, nivel + 1) for f in no.body]
        return "\n".join([pad + "Programa"] + filhos)
    if isinstance(no, python_ast.Assign):
        return "\n".join([pad + "Atribuicao", py_texto(no.targets[0], fonte, nivel + 1),
                          py_texto(no.value, fonte, nivel + 1)])
    if isinstance(no, python_ast.Expr):
        return "\n".join([pad + "ExpressaoComando", py_texto(no.value, fonte, nivel + 1)])
    if isinstance(no, python_ast.BinOp):
        return "\n".join([pad + f"OperacaoBinaria {OPS_PY[type(no.op)]}",
                          py_texto(no.left, fonte, nivel + 1), py_texto(no.right, fonte, nivel + 1)])
    if isinstance(no, python_ast.Compare):
        return "\n".join([pad + f"Comparacao {OPS_PY[type(no.ops[0])]}",
                          py_texto(no.left, fonte, nivel + 1),
                          py_texto(no.comparators[0], fonte, nivel + 1)])
    if isinstance(no, python_ast.UnaryOp):
        return "\n".join([pad + f"OperacaoUnaria {OPS_PY[type(no.op)]}",
                          py_texto(no.operand, fonte, nivel + 1)])
    if isinstance(no, python_ast.Name):
        return pad + f"Identificador {no.id}"
    if isinstance(no, python_ast.Constant):
        return pad + f"Numero {python_ast.get_source_segment(fonte, no)}"
    if isinstance(no, (python_ast.If, python_ast.While)):
        nome = "Condicional" if isinstance(no, python_ast.If) else "Repeticao"
        partes = [pad + nome, py_texto(no.test, fonte, nivel + 1),
                  "\n".join([pad + "  Bloco"] + [py_texto(f, fonte, nivel + 2) for f in no.body])]
        if no.orelse:
            partes.append("\n".join([pad + "  Bloco"] + [py_texto(f, fonte, nivel + 2) for f in no.orelse]))
        return "\n".join(partes)
    raise AssertionError(f"nó não previsto: {no}")


def gerar_expr(rnd, prof=0, parenteses=True):
    if prof > 3 or rnd.random() < 0.3:
        return rnd.choice(["x", "y", "valor", "1", "20", "0", "3.5", "10.25"])
    r = rnd.random()
    if r < 0.15:
        return rnd.choice(["-", "+"]) + gerar_expr(rnd, prof + 1, parenteses)
    if r < 0.3 and parenteses:
        return "(" + gerar_expr(rnd, prof + 1, parenteses) + ")"
    return (gerar_expr(rnd, prof + 1, parenteses) + " " + rnd.choice(["+", "-", "*", "/"]) +
            " " + gerar_expr(rnd, prof + 1, parenteses))


def gerar_programa(rnd, parenteses=True, nivel=0, linhas=None):
    linhas = [] if linhas is None else linhas
    pad = "    " * nivel
    for _ in range(rnd.randint(1, 3)):
        tipo = rnd.random()
        if tipo < 0.5 or nivel >= 2:
            linhas.append(f"{pad}{rnd.choice(['x', 'y', 'z'])} = {gerar_expr(rnd, 0, parenteses)}")
        elif tipo < 0.65:
            linhas.append(f"{pad}{gerar_expr(rnd, 0, parenteses)}")
        else:
            cond = gerar_expr(rnd, 1, parenteses) + " " + rnd.choice(["<", ">", "<=", ">=", "==", "!="]) + " " + gerar_expr(rnd, 2, parenteses)
            palavra = rnd.choice(["if", "while"])
            linhas.append(f"{pad}{palavra} {cond}:")
            gerar_programa(rnd, parenteses, nivel + 1, linhas)
            if palavra == "if" and rnd.random() < 0.5:
                linhas.append(f"{pad}else:")
                gerar_programa(rnd, parenteses, nivel + 1, linhas)
    return linhas


class TestContraModuloAstDoPython:
    """Referência externa: a estrutura da AST deve coincidir com a do Python."""

    @pytest.mark.parametrize("semente", range(200))
    def test_estrutura_igual_a_do_python(self, semente):
        rnd = random.Random(semente)
        codigo = "\n".join(gerar_programa(rnd)) + "\n"
        esperado = py_texto(python_ast.parse(codigo), codigo)
        assert arvore(codigo) == esperado, codigo

    @pytest.mark.parametrize("semente", range(100))
    def test_posicoes_iguais_as_do_python_sem_parenteses(self, semente):
        rnd = random.Random(1000 + semente)
        codigo = "\n".join(gerar_programa(rnd, parenteses=False)) + "\n"
        r = analisar(codigo)
        py = python_ast.parse(codigo)

        def confere(no, p):
            if isinstance(p, python_ast.Module):
                pares = zip(no.filhos, p.body)
            else:
                pares = []
            for n, q in pares:
                comparar(n, q)

        def comparar(n, q):
            if hasattr(q, "lineno"):
                assert (n.linha, n.coluna) == (q.lineno, q.col_offset + 1), (codigo, n.tipo)
            filhos_py = []
            if isinstance(q, python_ast.Assign):
                filhos_py = [q.targets[0], q.value]
            elif isinstance(q, python_ast.Expr):
                filhos_py = [q.value]
            elif isinstance(q, python_ast.BinOp):
                filhos_py = [q.left, q.right]
            elif isinstance(q, python_ast.Compare):
                filhos_py = [q.left, q.comparators[0]]
            elif isinstance(q, python_ast.UnaryOp):
                filhos_py = [q.operand]
            elif isinstance(q, (python_ast.If, python_ast.While)):
                filhos_py = [q.test]
                if hasattr(q, "end_lineno"):
                    pass
            if isinstance(q, (python_ast.BinOp, python_ast.Compare, python_ast.UnaryOp,
                              python_ast.Constant, python_ast.Name, python_ast.Assign, python_ast.Expr)):
                assert (n.linha_fim, n.coluna_fim) == (q.end_lineno, q.end_col_offset + 1), (codigo, n.tipo)
            if isinstance(q, (python_ast.If, python_ast.While)):
                comparar(n.filhos[0], q.test)
                corpo = n.filhos[1].filhos
                for a, b in zip(corpo, q.body):
                    comparar(a, b)
                if q.orelse:
                    for a, b in zip(n.filhos[2].filhos, q.orelse):
                        comparar(a, b)
                return
            for a, b in zip(n.filhos, filhos_py):
                comparar(a, b)

        confere(r.ast, py)
