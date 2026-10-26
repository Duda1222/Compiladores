"""Testes dos endpoints da API (contrato HTTP) e de regressão da Etapa 1."""

import json

import pytest

import app as modulo_app
from validacao import TAMANHO_MAXIMO


# ---------------------------------------------------------------- regressão
def test_regressao_hello(client):
    r = client.get("/api/hello")
    assert r.status_code == 200
    assert r.get_json() == {"message": "Hello, World!"}


def test_regressao_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


# --------------------------------------------------------- requisição válida
def test_analisar_codigo_valido(client):
    r = client.post("/api/analisar", json={"codigo": "x = 10"})
    assert r.status_code == 200
    assert r.is_json
    corpo = r.get_json()
    assert corpo["recebido"] is True
    assert corpo["mensagem"] == "Análise léxica concluída sem erros."
    assert corpo["linhas"] == 1
    assert corpo["caracteres"] == 6


def test_analisar_conta_linhas_e_caracteres_do_que_foi_enviado(client):
    codigo = "x = 3\nwhile x > 0:\n    x = x - 1\n"
    corpo = client.post("/api/analisar", json={"codigo": codigo}).get_json()
    assert corpo["linhas"] == 3
    assert corpo["caracteres"] == len(codigo)


def test_analisar_resposta_depende_da_entrada(client):
    a = client.post("/api/analisar", json={"codigo": "a"}).get_json()
    b = client.post("/api/analisar", json={"codigo": "a\nb\nc"}).get_json()
    assert a["linhas"] != b["linhas"]


def test_analisar_aceita_caracteres_especiais(client):
    codigo = "x = 1  # açaí ✓ <script>&\"'"
    r = client.post("/api/analisar", json={"codigo": codigo})
    assert r.status_code == 200
    assert r.get_json()["caracteres"] == len(codigo)


def test_analisar_aceita_codigo_invalido_como_python(client):
    r = client.post("/api/analisar", json={"codigo": "if x >> :: ((("})
    assert r.status_code == 200
    assert r.get_json()["recebido"] is True


def test_analisar_aceita_tamanho_maximo(client):
    r = client.post("/api/analisar", json={"codigo": "a" * TAMANHO_MAXIMO})
    assert r.status_code == 200


# -------------------------------------------------------- requisição inválida
def test_analisar_texto_vazio(client):
    r = client.post("/api/analisar", json={"codigo": ""})
    assert r.status_code == 422
    corpo = r.get_json()
    assert corpo["recebido"] is False
    assert corpo["erro"] == "entrada_vazia"
    assert corpo["mensagem"] == "Informe um código-fonte antes de solicitar a análise."


@pytest.mark.parametrize("texto", ["   ", "\n\n", "\t \n"])
def test_analisar_somente_espacos(client, texto):
    r = client.post("/api/analisar", json={"codigo": texto})
    assert r.status_code == 422
    assert r.get_json()["erro"] == "entrada_somente_espacos"


def test_analisar_campo_ausente(client):
    r = client.post("/api/analisar", json={"outro": "x"})
    assert r.status_code == 400
    assert r.get_json()["erro"] == "campo_ausente"


@pytest.mark.parametrize("valor", [None, 1, ["x"], {"a": 1}, True])
def test_analisar_campo_com_tipo_invalido(client, valor):
    r = client.post("/api/analisar", json={"codigo": valor})
    assert r.status_code == 400
    assert r.get_json()["erro"] == "campo_invalido"


def test_analisar_json_malformado(client):
    r = client.post(
        "/api/analisar", data="{codigo: x", content_type="application/json"
    )
    assert r.status_code == 400
    assert r.get_json()["erro"] == "corpo_invalido"


def test_analisar_sem_corpo(client):
    r = client.post("/api/analisar")
    assert r.status_code == 400
    assert r.get_json()["erro"] == "corpo_invalido"


def test_analisar_content_type_incorreto(client):
    r = client.post(
        "/api/analisar",
        data=json.dumps({"codigo": "x = 1"}),
        content_type="text/plain",
    )
    assert r.status_code == 400
    assert r.get_json()["erro"] == "corpo_invalido"


def test_analisar_json_que_nao_e_objeto(client):
    r = client.post("/api/analisar", json=["x = 1"])
    assert r.status_code == 400
    assert r.get_json()["erro"] == "corpo_invalido"


def test_analisar_acima_do_limite(client):
    r = client.post("/api/analisar", json={"codigo": "a" * (TAMANHO_MAXIMO + 1)})
    assert r.status_code == 413
    assert r.get_json()["erro"] == "entrada_muito_grande"


# ------------------------------------------------------------ erros gerais
def test_metodo_nao_permitido(client):
    r = client.get("/api/analisar")
    assert r.status_code == 405
    corpo = r.get_json()
    assert corpo["recebido"] is False
    assert corpo["erro"] == "requisicao_invalida"


def test_rota_inexistente_devolve_json(client):
    r = client.get("/api/nao-existe")
    assert r.status_code == 404
    assert r.is_json
    assert r.get_json()["recebido"] is False


def test_erro_inesperado_nao_expoe_detalhes(client, monkeypatch):
    def quebra(_corpo):
        raise RuntimeError("segredo /app/interno.py SENHA=123")

    monkeypatch.setattr(modulo_app, "validar_corpo", quebra)
    r = client.post("/api/analisar", json={"codigo": "x = 1"})
    assert r.status_code == 500
    texto = r.get_data(as_text=True)
    assert "segredo" not in texto
    assert "interno.py" not in texto
    assert "SENHA" not in texto
    assert "Traceback" not in texto
    corpo = r.get_json()
    assert corpo["erro"] == "erro_interno"
    assert corpo["recebido"] is False


# ===================================================================== Etapa 3
# Contrato do endpoint com o scanner: tokens, erros, avisos e resumo.
def _post(client, codigo):
    return client.post("/api/analisar", json={"codigo": codigo})


def test_etapa3_resposta_tem_todas_as_chaves_do_contrato(client):
    r = _post(client, "x = 10")
    assert r.status_code == 200
    corpo = r.get_json()
    for chave in ("recebido", "sucesso", "mensagem", "linhas", "caracteres",
                  "tokens", "erros", "avisos", "resumo"):
        assert chave in corpo, chave
    assert set(corpo["resumo"]) == {"total_tokens", "total_erros", "erros_omitidos", "por_tipo"}


def test_etapa3_codigo_valido_devolve_tokens_e_sucesso_true(client):
    corpo = _post(client, "numero = 10\n").get_json()
    assert corpo["sucesso"] is True
    assert corpo["erros"] == []
    esperado = [
        {"tipo": "IDENTIFICADOR", "lexema": "numero", "linha": 1, "coluna": 1},
        {"tipo": "OPERADOR_ATRIBUICAO", "lexema": "=", "linha": 1, "coluna": 8},
        {"tipo": "LITERAL_INTEIRO", "lexema": "10", "linha": 1, "coluna": 10},
    ]
    assert corpo["tokens"][:3] == esperado


def test_etapa3_cada_token_tem_exatamente_os_campos_do_contrato(client):
    corpo = _post(client, "while x > 0:\n    x = x - 1\n").get_json()
    assert corpo["tokens"]
    for t in corpo["tokens"]:
        assert set(t) == {"tipo", "lexema", "linha", "coluna"}
        assert isinstance(t["linha"], int) and isinstance(t["coluna"], int)


def test_etapa3_erro_lexico_devolve_sucesso_false_e_lista_de_erros(client):
    r = _post(client, "x = 10\ny = 5 @ 2\n")
    assert r.status_code == 200  # pedido processado; o resultado é que falhou
    corpo = r.get_json()
    assert corpo["recebido"] is True
    assert corpo["sucesso"] is False
    assert len(corpo["erros"]) == 1
    assert corpo["erros"][0] == {
        "tipo": "ERRO_LEXICO",
        "lexema": "@",
        "linha": 2,
        "coluna": 7,
        "mensagem": corpo["erros"][0]["mensagem"],
    }
    assert "Caractere não reconhecido: '@'" in corpo["erros"][0]["mensagem"]
    assert "1 erro léxico" in corpo["mensagem"]


def test_etapa3_varios_erros_sao_acumulados_e_tokens_validos_mantidos(client):
    corpo = _post(client, "a = 1 @\nb = 2 $\nc = 3.4.5\n").get_json()
    assert corpo["sucesso"] is False
    assert [e["lexema"] for e in corpo["erros"]] == ["@", "$", "3.4.5"]
    assert "3 erros léxicos" in corpo["mensagem"]
    assert [t["lexema"] for t in corpo["tokens"] if t["tipo"] == "IDENTIFICADOR"] == ["a", "b", "c"]
    assert corpo["resumo"]["total_erros"] == 3


def test_etapa3_programa_sintaticamente_errado_mas_lexicamente_valido(client):
    corpo = _post(client, "x = = 3 +\nif :\n(((\n").get_json()
    assert corpo["sucesso"] is True
    assert corpo["erros"] == []


def test_etapa3_avisos_para_reservadas_fora_do_subconjunto(client):
    corpo = _post(client, "def f").get_json()
    assert corpo["sucesso"] is True
    assert corpo["avisos"][0]["lexema"] == "def"
    assert corpo["avisos"][0]["tipo"] == "AVISO_FORA_DO_ESCOPO"


def test_etapa3_resumo_por_tipo_confere_com_a_lista_de_tokens(client):
    corpo = _post(client, "x = 1 + 2\nwhile x > 0:\n    x = x - 1\n").get_json()
    contagem = {}
    for t in corpo["tokens"]:
        contagem[t["tipo"]] = contagem.get(t["tipo"], 0) + 1
    assert corpo["resumo"]["por_tipo"] == contagem
    assert corpo["resumo"]["total_tokens"] == len(corpo["tokens"])


def test_etapa3_tokens_de_indentacao_aparecem_na_resposta(client):
    tipos = [t["tipo"] for t in _post(client, "if x:\n    y = 1\n").get_json()["tokens"]]
    assert "INDENT" in tipos and "DEDENT" in tipos and tipos[-1] == "FIM_DE_ARQUIVO"


def test_etapa3_entrada_vazia_continua_como_na_etapa_2(client):
    for texto, erro in (("", "entrada_vazia"), ("  \n\t", "entrada_somente_espacos")):
        r = _post(client, texto)
        assert r.status_code == 422
        corpo = r.get_json()
        assert corpo["erro"] == erro and corpo["recebido"] is False
        assert "tokens" not in corpo


def test_etapa3_apenas_comentarios_tem_sucesso_sem_tokens_visiveis(client):
    corpo = _post(client, "# nada aqui").get_json()
    assert corpo["sucesso"] is True
    assert [t["tipo"] for t in corpo["tokens"]] == ["FIM_DE_ARQUIVO"]


def test_etapa3_entrada_grande_com_muitos_erros_limita_a_lista(client):
    corpo = _post(client, "@" * 5000).get_json()
    assert corpo["sucesso"] is False
    assert len(corpo["erros"]) == 200
    assert corpo["resumo"]["total_erros"] == 5000
    assert corpo["resumo"]["erros_omitidos"] == 4800


def test_etapa3_falha_inesperada_no_scanner_nao_expoe_detalhes(client, monkeypatch):
    def quebra(_codigo):
        raise RuntimeError("segredo /app/scanner.py SENHA=123")

    monkeypatch.setattr(modulo_app, "analisar_lexico", quebra)
    r = _post(client, "x = 1")
    assert r.status_code == 500
    texto = r.get_data(as_text=True)
    assert "segredo" not in texto and "SENHA" not in texto and "Traceback" not in texto
    assert r.get_json()["erro"] == "erro_interno"


def test_etapa3_resposta_e_json_utf8(client):
    r = _post(client, "x = ç")
    assert r.is_json
    assert "ç" in r.get_json()["erros"][0]["lexema"]
