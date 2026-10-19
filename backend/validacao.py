"""Validação da entrada do endpoint de análise.

Fica separada de ``app.py`` para poder ser testada isoladamente e para
que as próximas etapas (análise léxica e sintática) possam reaproveitar
as mesmas regras de entrada.
"""

from __future__ import annotations

from dataclasses import dataclass

# Limite de caracteres aceito para um programa-fonte (proteção simples).
TAMANHO_MAXIMO = 100_000

MSG_CORPO_INVALIDO = (
    "A requisição deve conter um corpo JSON no formato {\"codigo\": \"...\"}."
)
MSG_CAMPO_AUSENTE = "O campo obrigatório \"codigo\" não foi informado."
MSG_CAMPO_TIPO = "O campo \"codigo\" deve ser um texto."
MSG_VAZIO = "Informe um código-fonte antes de solicitar a análise."
MSG_SO_ESPACOS = (
    "O código informado contém apenas espaços em branco. "
    "Escreva ou selecione um programa para analisar."
)
MSG_MUITO_GRANDE = (
    f"O código excede o limite de {TAMANHO_MAXIMO} caracteres."
)


@dataclass(frozen=True)
class ResultadoValidacao:
    """Resultado da validação: ``ok`` ou um erro com status HTTP e código."""

    ok: bool
    status: int = 200
    erro: str = ""
    mensagem: str = ""


def validar_corpo(corpo) -> ResultadoValidacao:
    """Valida o corpo já decodificado da requisição (``dict`` esperado)."""
    if not isinstance(corpo, dict):
        return ResultadoValidacao(False, 400, "corpo_invalido", MSG_CORPO_INVALIDO)

    if "codigo" not in corpo:
        return ResultadoValidacao(False, 400, "campo_ausente", MSG_CAMPO_AUSENTE)

    codigo = corpo["codigo"]
    if not isinstance(codigo, str):
        return ResultadoValidacao(False, 400, "campo_invalido", MSG_CAMPO_TIPO)

    if codigo == "":
        return ResultadoValidacao(False, 422, "entrada_vazia", MSG_VAZIO)

    if codigo.strip() == "":
        return ResultadoValidacao(False, 422, "entrada_somente_espacos", MSG_SO_ESPACOS)

    if len(codigo) > TAMANHO_MAXIMO:
        return ResultadoValidacao(False, 413, "entrada_muito_grande", MSG_MUITO_GRANDE)

    return ResultadoValidacao(True)
