"""Backend do software educacional de compiladores.

Endpoints:
  GET  /api/health    -> verificação de saúde (usada pelo Docker Compose)
  GET  /api/hello     -> mensagem da Etapa 1 (mantida para regressão)
  POST /api/analisar  -> recebe o código-fonte e devolve uma resposta estruturada

Fluxo: entrada -> validação -> scanner (Etapa 3) -> parser (Etapa 4) -> resposta.
Se o scanner encontrar erros léxicos, o parser NÃO é executado (decisão
documentada em docs/sintatico.md): a resposta traz "sintatico.executado": false.
A análise semântica será a Etapa 5.
"""

import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from scanner import analisar_lexico
from sintatico import analisar_sintatico, resultado_nao_executado
from validacao import validar_corpo

app = Flask(__name__)
log = logging.getLogger("compilador")


def erro(status: int, codigo_erro: str, mensagem: str):
    """Monta uma resposta de erro padronizada."""
    resposta = jsonify(recebido=False, erro=codigo_erro, mensagem=mensagem)
    return resposta, status


@app.get("/api/hello")
def hello():
    return jsonify(message="Hello, World!")


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.post("/api/analisar")
def analisar():
    corpo = request.get_json(silent=True)
    resultado = validar_corpo(corpo)
    if not resultado.ok:
        return erro(resultado.status, resultado.erro, resultado.mensagem)

    codigo = corpo["codigo"]
    lexico = analisar_lexico(codigo)
    resposta = lexico.como_dict()

    if lexico.sucesso:
        mensagem = "Análise léxica concluída sem erros."
    elif lexico.total_erros == 1:
        mensagem = "Análise léxica concluída com 1 erro léxico."
    else:
        mensagem = f"Análise léxica concluída com {lexico.total_erros} erros léxicos."

    sintatico = _executar_parser(lexico)

    # Um programa com erros é uma resposta válida (HTTP 200): o pedido foi
    # processado e os campos "sucesso" dizem o que passou. Os campos planos da
    # Etapa 3 (sucesso, tokens, erros, avisos, resumo) foram mantidos; "lexico"
    # e "sintatico" são o contrato da Etapa 4.
    return jsonify(
        recebido=True,
        mensagem=mensagem,
        linhas=len(codigo.splitlines()),
        caracteres=len(codigo),
        lexico={
            "sucesso": resposta["sucesso"],
            "tokens": resposta["tokens"],
            "erros": resposta["erros"],
            "avisos": resposta["avisos"],
            "resumo": resposta["resumo"],
        },
        sintatico=sintatico,
        **resposta,
    )


def _executar_parser(lexico) -> dict:
    """Roda o parser somente se não houve erro léxico."""
    if not lexico.sucesso:
        return resultado_nao_executado(
            "A análise sintática não foi executada porque há erros léxicos. "
            "Corrija-os primeiro: o parser só trabalha com uma sequência de tokens válida."
        )
    resultado = analisar_sintatico(lexico.tokens)
    d = resultado.como_dict()
    n = resultado.total_erros
    if resultado.sucesso:
        d["mensagem"] = "Análise sintática concluída sem erros."
    elif n == 1:
        d["mensagem"] = "Análise sintática concluída com 1 erro sintático."
    else:
        d["mensagem"] = f"Análise sintática concluída com {n} erros sintáticos."
    return d


@app.errorhandler(HTTPException)
def tratar_http(e: HTTPException):
    mensagens = {
        404: "Recurso não encontrado.",
        405: "Método não permitido para este recurso.",
    }
    mensagem = mensagens.get(e.code, "A requisição não pôde ser processada.")
    return erro(e.code, "requisicao_invalida", mensagem)


@app.errorhandler(Exception)
def tratar_inesperado(e: Exception):
    # Detalhes técnicos ficam apenas no log do servidor, nunca na resposta.
    log.exception("Erro inesperado")
    return erro(
        500,
        "erro_interno",
        "Ocorreu um erro inesperado. Tente novamente em instantes.",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
