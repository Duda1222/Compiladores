"""Testes do endpoint /api/analisar com a análise sintática (Etapa 4)."""

import app as modulo_app


def post(client, codigo):
    return client.post("/api/analisar", json={"codigo": codigo})


def test_contrato_com_programa_valido(client):
    r = post(client, "x = 10 + 5 * 2\n")
    assert r.status_code == 200
    d = r.get_json()
    assert d["lexico"]["sucesso"] is True
    assert d["sintatico"]["executado"] is True
    assert d["sintatico"]["sucesso"] is True
    assert d["sintatico"]["erros"] == []
    ast = d["sintatico"]["ast"]
    assert ast["tipo"] == "Programa"
    for no in (ast, ast["filhos"][0]):
        assert {"tipo", "linha", "coluna", "atributos", "filhos"} <= set(no)


def test_campos_da_etapa_3_foram_preservados(client):
    d = post(client, "x = 1\n").get_json()
    for campo in ("recebido", "sucesso", "mensagem", "linhas", "caracteres",
                  "tokens", "erros", "avisos", "resumo"):
        assert campo in d
    assert d["mensagem"] == "Análise léxica concluída sem erros."


def test_bloco_lexico_igual_aos_campos_planos(client):
    d = post(client, "x = 1\nif x:\n    y = 2\n").get_json()
    for campo in ("sucesso", "tokens", "erros", "avisos", "resumo"):
        assert d["lexico"][campo] == d[campo]


def test_erro_sintatico_devolve_ast_nula_e_http_200(client):
    r = post(client, "x = 10 +\n")
    assert r.status_code == 200
    s = r.get_json()["sintatico"]
    assert s["sucesso"] is False and s["ast"] is None and s["derivacao"] is None
    e = s["erros"][0]
    assert e["tipo"] == "ERRO_SINTATICO"
    assert (e["linha"], e["coluna"], e["encontrado"]) == (1, 9, "fim da linha")
    assert isinstance(e["esperado"], list) and e["mensagem"]
    assert s["mensagem"] == "Análise sintática concluída com 1 erro sintático."


def test_erro_sintatico_nao_marca_o_lexico_como_falho(client):
    d = post(client, "x = = 3\n").get_json()
    assert d["lexico"]["sucesso"] is True and d["sucesso"] is True
    assert d["sintatico"]["sucesso"] is False
    assert len(d["lexico"]["tokens"]) > 0


def test_varios_erros_sintaticos(client):
    s = post(client, "x = 1 +\ny = 2 * * 3\n").get_json()["sintatico"]
    assert len(s["erros"]) == 2
    assert s["mensagem"] == "Análise sintática concluída com 2 erros sintáticos."


def test_erro_lexico_nao_executa_o_parser(client):
    d = post(client, "x = 10 @ 2\n").get_json()
    assert d["lexico"]["sucesso"] is False and d["sucesso"] is False
    s = d["sintatico"]
    assert s["executado"] is False and s["sucesso"] is False
    assert s["ast"] is None and s["erros"] == []
    assert "erros léxicos" in s["mensagem"]
    assert len(d["lexico"]["erros"]) == 1


def test_erro_lexico_e_sintatico_juntos_mostram_so_o_lexico(client):
    d = post(client, "x = = @\n").get_json()
    assert d["sintatico"]["executado"] is False
    assert d["lexico"]["erros"][0]["tipo"] == "ERRO_LEXICO"


def test_somente_comentarios_gera_programa_vazio(client):
    s = post(client, "# so um comentario\n").get_json()["sintatico"]
    assert s["sucesso"] is True and s["ast"]["filhos"] == []


def test_derivacao_acompanha_a_ast_no_sucesso(client):
    s = post(client, "x = 1\n").get_json()["sintatico"]
    assert s["derivacao"]["simbolo"] == "programa"


def test_resumo_da_ast(client):
    r = post(client, "x = 1 + 2\n").get_json()["sintatico"]["resumo"]
    assert r["total_nos"] == 6 and r["altura"] == 4
    assert r["por_tipo"]["OperacaoBinaria"] == 1


def test_programa_do_enunciado_com_if_while(client):
    codigo = "x = 7\nwhile x > 0:\n    if x > 3:\n        x = x - 2\n    else:\n        x = x - 1\n"
    s = post(client, codigo).get_json()["sintatico"]
    assert s["sucesso"] is True


# ------------------------------------------------- regressão das Etapas 1 e 2
def test_entrada_vazia_continua_422(client):
    r = post(client, "")
    assert r.status_code == 422 and r.get_json()["erro"] == "entrada_vazia"


def test_somente_espacos_continua_422(client):
    assert post(client, "   \n").status_code == 422


def test_entrada_grande_demais_continua_413(client):
    assert post(client, "x" * 100001).status_code == 413


def test_corpo_invalido_continua_400(client):
    r = client.post("/api/analisar", data="nao json", content_type="text/plain")
    assert r.status_code == 400


def test_metodo_nao_permitido_continua_405(client):
    assert client.get("/api/analisar").status_code == 405


def test_hello_e_health_continuam_funcionando(client):
    assert client.get("/api/hello").get_json() == {"message": "Hello, World!"}
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_entrada_no_limite_nao_quebra(client):
    codigo = "x = 1\n" * 16666  # ~99,9 mil caracteres
    r = post(client, codigo)
    assert r.status_code == 200 and r.get_json()["sintatico"]["sucesso"] is True


def test_falha_inesperada_no_parser_vira_500_generico(client, monkeypatch):
    def quebra(_):
        raise RuntimeError("detalhe interno secreto /app/sintatico.py")

    monkeypatch.setattr(modulo_app, "analisar_sintatico", quebra)
    r = post(client, "x = 1\n")
    assert r.status_code == 500
    corpo = r.get_data(as_text=True)
    assert "secreto" not in corpo and "Traceback" not in corpo
    assert r.get_json()["erro"] == "erro_interno"


def test_entradas_hostis_nao_derrubam_o_servidor(client):
    for codigo in ["(" * 5000, ")" * 5000, "if " * 3000, "-" * 20000 + "1",
                   "\n".join("    " * n + "while a:" for n in range(60)) + "\n" + "    " * 60 + "x=1",
                   "<script>alert(1)</script>"]:
        r = post(client, codigo)
        assert r.status_code in (200, 413), codigo[:20]
        assert "Traceback" not in r.get_data(as_text=True)
