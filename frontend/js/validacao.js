// Validação da entrada no frontend. O backend valida novamente: esta
// verificação existe apenas para dar retorno rápido ao usuário.

export const MSG_VAZIO = "Informe um código-fonte antes de solicitar a análise.";
export const MSG_SO_ESPACOS =
  "O código informado contém apenas espaços em branco. Escreva ou selecione um programa para analisar.";

/**
 * @param {unknown} codigo
 * @returns {{ok: true} | {ok: false, motivo: string, mensagem: string}}
 */
export function validarEntrada(codigo) {
  if (typeof codigo !== "string" || codigo.length === 0) {
    return { ok: false, motivo: "vazia", mensagem: MSG_VAZIO };
  }
  if (codigo.trim().length === 0) {
    return { ok: false, motivo: "somente_espacos", mensagem: MSG_SO_ESPACOS };
  }
  return { ok: true };
}
