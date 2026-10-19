import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { JSDOM } from "jsdom";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(path.join(raiz, "index.html"), "utf8");

/** Cria um DOM novo a partir do index.html real (sem executar os scripts). */
export function criarDom() {
  return new JSDOM(html);
}

/** Resposta falsa compatível com o que o módulo api.js usa de fetch. */
export function respostaFalsa(status, corpo, { json = true } = {}) {
  return {
    status,
    ok: status >= 200 && status < 300,
    async json() {
      if (!json) throw new SyntaxError("não é JSON");
      return corpo;
    },
  };
}

/** fetch falso que registra as chamadas e devolve o que for configurado. */
export function fetchFalso(comportamento) {
  const chamadas = [];
  const fn = async (url, init) => {
    chamadas.push({ url, init });
    return comportamento(url, init);
  };
  fn.chamadas = chamadas;
  return fn;
}

export const textoDe = (el) => el.textContent.replace(/\s+/g, " ").trim();
