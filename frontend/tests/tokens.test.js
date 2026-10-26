// Testes unitários das funções puras de js/tokens.js.

import test from "node:test";
import assert from "node:assert/strict";
import {
  CATEGORIAS,
  ORDEM_TIPOS,
  classeDoTipo,
  explicarToken,
  lexemaVisivel,
  mensagemDeErro,
  montarSegmentos,
  normalizarQuebras,
  rotuloDoTipo,
  simboloEstrutural,
} from "../js/tokens.js";
import { FIXTURES } from "./ajudantes.js";

const tokensDeTodasAsFixtures = Object.values(FIXTURES).flatMap((f) => f.resposta.tokens);

test("o catálogo cobre todos os tipos de token que o backend devolve", () => {
  for (const t of tokensDeTodasAsFixtures) {
    assert.ok(CATEGORIAS[t.tipo], `tipo sem categoria: ${t.tipo}`);
  }
});

test("as fixtures exercitam a maioria das categorias", () => {
  const vistos = new Set(tokensDeTodasAsFixtures.map((t) => t.tipo));
  assert.ok(vistos.size >= 10, `apenas ${vistos.size} tipos nas fixtures`);
});

test("cada categoria tem rótulo, classe CSS e ordem definida", () => {
  assert.equal(ORDEM_TIPOS.length, Object.keys(CATEGORIAS).length);
  for (const tipo of ORDEM_TIPOS) {
    assert.ok(rotuloDoTipo(tipo).length > 0);
    assert.match(classeDoTipo(tipo), /^t-/);
  }
});

test("tipo desconhecido não quebra: usa estilo estrutural e o próprio nome", () => {
  assert.equal(classeDoTipo("XYZ"), "t-estrutural");
  assert.equal(rotuloDoTipo("XYZ"), "XYZ");
});

test("símbolos de tokens invisíveis", () => {
  assert.equal(simboloEstrutural({ tipo: "NEWLINE" }), "↵");
  assert.equal(simboloEstrutural({ tipo: "INDENT" }), "→");
  assert.equal(simboloEstrutural({ tipo: "DEDENT" }), "←");
  assert.equal(simboloEstrutural({ tipo: "FIM_DE_ARQUIVO" }), "∎");
  assert.equal(simboloEstrutural({ tipo: "IDENTIFICADOR" }), null);
  assert.equal(lexemaVisivel({ tipo: "IDENTIFICADOR", lexema: "x" }), "x");
  assert.equal(lexemaVisivel({ tipo: "NEWLINE", lexema: "\n" }), "↵");
});

test("todo token das fixtures recebe uma explicação não vazia", () => {
  for (const t of tokensDeTodasAsFixtures) {
    assert.ok(explicarToken(t).length > 10, t.tipo);
  }
});

test("explicações mencionam o lexema e distinguem casos", () => {
  assert.match(explicarToken({ tipo: "PALAVRA_RESERVADA", lexema: "while" }), /while/);
  assert.match(explicarToken({ tipo: "OPERADOR_RELACIONAL", lexema: "==" }), /mais longo/);
  assert.doesNotMatch(explicarToken({ tipo: "OPERADOR_RELACIONAL", lexema: "<" }), /mais longo/);
  assert.match(explicarToken({ tipo: "INDENT", lexema: "    " }), /4 espaços/);
  assert.match(explicarToken({ tipo: "NEWLINE", lexema: "" }), /sem quebra de linha/);
  assert.match(explicarToken({ tipo: "DELIMITADOR", lexema: ":" }), /bloco/);
});

test("normalizarQuebras converte CRLF e CR em LF", () => {
  assert.equal(normalizarQuebras("a\r\nb\rc\n"), "a\nb\nc\n");
});

test("mensagemDeErro inclui linha, coluna e a explicação", () => {
  const m = mensagemDeErro({ linha: 2, coluna: 10, mensagem: "Caractere não reconhecido: '@'." });
  assert.equal(m, "Erro léxico na linha 2, coluna 10: Caractere não reconhecido: '@'.");
});

// ------------------------------------------------------------- segmentos
/** Reconstrói o código ignorando os marcadores (que são extras) e trocando ↵ por \n. */
function reconstruir(segmentos) {
  return segmentos
    .filter((s) => !s.marcador)
    .map((s) => (s.quebra ? "\n" : s.texto))
    .join("");
}

for (const [nome, f] of Object.entries(FIXTURES)) {
  test(`segmentos de "${nome}" reproduzem exatamente o código original`, () => {
    const segs = montarSegmentos(f.codigo, f.resposta.tokens, f.resposta.erros);
    assert.equal(reconstruir(segs), f.codigo);
  });
}

test("cada token com texto vira um segmento com o índice certo", () => {
  const f = FIXTURES.valido;
  const segs = montarSegmentos(f.codigo, f.resposta.tokens, f.resposta.erros);
  const idents = segs.filter((s) => s.token?.tipo === "IDENTIFICADOR");
  assert.deepEqual(idents.map((s) => s.texto), ["x", "x", "x", "x"].slice(0, idents.length));
  for (const s of segs.filter((s) => s.tipo === "token")) {
    assert.equal(f.resposta.tokens[s.indice], s.token);
  }
});

test("tokens sem texto (DEDENT, FIM) viram marcadores", () => {
  const f = FIXTURES.valido;
  const segs = montarSegmentos(f.codigo, f.resposta.tokens, []);
  const marcadores = segs.filter((s) => s.marcador).map((s) => s.texto);
  assert.deepEqual(marcadores, ["←", "∎"]);
});

test("erros léxicos viram segmentos do tipo erro na posição certa", () => {
  const f = FIXTURES.erros;
  const segs = montarSegmentos(f.codigo, f.resposta.tokens, f.resposta.erros);
  const erros = segs.filter((s) => s.tipo === "erro").map((s) => s.texto);
  assert.deepEqual(erros, f.resposta.erros.map((e) => e.lexema));
  assert.ok(erros.includes("@") && erros.includes("3.14.15") && erros.includes("12abc"));
});

test("erro sobreposto ao INDENT (tabulação) não duplica texto e marca o token", () => {
  const f = FIXTURES.tabulacao;
  const segs = montarSegmentos(f.codigo, f.resposta.tokens, f.resposta.erros);
  assert.equal(reconstruir(segs), f.codigo);
  const indent = segs.find((s) => s.token?.tipo === "INDENT");
  assert.ok(indent.comErro, "o INDENT deve carregar o erro de tabulação");
});

test("CRLF no código não desloca as posições", () => {
  const codigo = "a = 1\r\nb = 2\r\n";
  const tokens = [
    { tipo: "IDENTIFICADOR", lexema: "a", linha: 1, coluna: 1 },
    { tipo: "IDENTIFICADOR", lexema: "b", linha: 2, coluna: 1 },
  ];
  const segs = montarSegmentos(codigo, tokens, []);
  assert.deepEqual(segs.filter((s) => s.tipo === "token").map((s) => s.texto), ["a", "b"]);
  assert.equal(reconstruir(segs), "a = 1\nb = 2\n");
});

test("lista de tokens vazia devolve o código inteiro como texto", () => {
  assert.deepEqual(montarSegmentos("abc", [], []), [{ tipo: "texto", texto: "abc" }]);
});

test("token com posição além do fim do código não lança exceção", () => {
  const segs = montarSegmentos("x", [{ tipo: "FIM_DE_ARQUIVO", lexema: "", linha: 99, coluna: 1 }], []);
  assert.equal(reconstruir(segs), "x");
});
