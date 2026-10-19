"""Backend do software educacional de compiladores.

Endpoints:
  GET  /api/health    -> verificação de saúde (usada pelo Docker Compose)
  GET  /api/hello     -> mensagem da Etapa 1 (mantida para regressão)
  POST /api/analisar  -> recebe o código-fonte e devolve uma resposta estruturada

Nesta etapa o backend apenas RECEBE e VALIDA o código. As análises léxica,
sintática e semântica serão adicionadas nas próximas etapas.
"""

import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

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
    return jsonify(
        recebido=True,
        mensagem="Código recebido com sucesso.",
        linhas=len(codigo.splitlines()),
        caracteres=len(codigo),
    )


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
