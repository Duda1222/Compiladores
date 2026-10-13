"""Backend mínimo do software educacional de compiladores.

Nesta etapa existe apenas um endpoint de saúde e um endpoint que devolve
a mensagem "Hello, World!". As fases de análise léxica e sintática serão
adicionadas nas próximas etapas.
"""

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/api/hello")
def hello():
    return jsonify(message="Hello, World!")


@app.get("/api/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
