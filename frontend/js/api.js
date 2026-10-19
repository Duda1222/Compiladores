// Comunicação com o backend (POST /api/analisar).
//
// Contrato:
//   requisição : { "codigo": "<texto>" }
//   sucesso    : 200 { "recebido": true, "mensagem": "...", "linhas": n, "caracteres": n }
//   erro       : 4xx { "recebido": false, "erro": "<codigo>", "mensagem": "..." }

export const MSG_COMUNICACAO =
  "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.";
export const MSG_INESPERADO =
  "Ocorreu um erro inesperado. Tente novamente em instantes.";

/**
 * Envia o código ao backend e devolve um resultado já classificado:
 *  - { tipo: "sucesso", dados }
 *  - { tipo: "entrada", status, mensagem }     problema na entrada (4xx)
 *  - { tipo: "comunicacao", mensagem }         servidor inacessível
 *  - { tipo: "inesperado", mensagem }          resposta inesperada (5xx etc.)
 * Nunca lança exceção.
 */
export async function enviarCodigo(codigo, opcoes = {}) {
  const {
    fetchFn = globalThis.fetch,
    url = "/api/analisar",
    timeoutMs = 10000,
  } = opcoes;

  const controlador = new AbortController();
  const temporizador = setTimeout(() => controlador.abort(), timeoutMs);

  let resposta;
  try {
    resposta = await fetchFn(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codigo }),
      signal: controlador.signal,
    });
  } catch {
    return { tipo: "comunicacao", mensagem: MSG_COMUNICACAO };
  } finally {
    clearTimeout(temporizador);
  }

  // O servidor (ou o proxy) não respondeu de fato: 502/503/504.
  if ([502, 503, 504].includes(resposta.status)) {
    return { tipo: "comunicacao", mensagem: MSG_COMUNICACAO };
  }

  let dados = null;
  try {
    dados = await resposta.json();
  } catch {
    dados = null;
  }

  if (resposta.ok && dados && dados.recebido === true) {
    return { tipo: "sucesso", dados };
  }

  if (
    resposta.status >= 400 &&
    resposta.status < 500 &&
    dados &&
    typeof dados.mensagem === "string"
  ) {
    return { tipo: "entrada", status: resposta.status, mensagem: dados.mensagem };
  }

  return { tipo: "inesperado", mensagem: MSG_INESPERADO };
}
