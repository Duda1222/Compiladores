// Funções puras da apresentação sintática.
import test from "node:test";
import assert from "node:assert/strict";
import {
  arvoreEmTexto,
  deslocamento,
  jsonDaAst,
  posicaoDoNo,
  rotuloDoNo,
  tiposPresentes,
  trechoDoNo,
} from "../js/sintatico.js";
import { FIXTURES } from "./ajudantes.js";

const ast = FIXTURES.sintatico_valido.resposta.sintatico.ast;

test("rótulo mostra nome, lexema ou operador", () => {
  assert.equal(rotuloDoNo({ tipo: "Identificador", atributos: { nome: "x" } }), "Identificador x");
  assert.equal(rotuloDoNo({ tipo: "Numero", atributos: { lexema: "3.5" } }), "Numero 3.5");
  assert.equal(rotuloDoNo({ tipo: "OperacaoBinaria", atributos: { operador: "+" } }), "OperacaoBinaria +");
  assert.equal(rotuloDoNo({ tipo: "Bloco", atributos: {} }), "Bloco");
});

test("árvore em texto é indentada e começa no Programa", () => {
  const t = arvoreEmTexto(ast);
  const linhas = t.split("\n");
  assert.equal(linhas[0], "Programa");
  assert.equal(linhas[1], "  Atribuicao");
  assert.ok(linhas.includes("      OperacaoBinaria *") || linhas.some((l) => l.trim() === "OperacaoBinaria *"));
});

test("a árvore em texto tem uma linha por nó", () => {
  const conta = (n) => 1 + n.filhos.reduce((a, f) => a + conta(f), 0);
  assert.equal(arvoreEmTexto(ast).split("\n").length, conta(ast));
  assert.equal(conta(ast), FIXTURES.sintatico_valido.resposta.sintatico.resumo.total_nos);
});

test("tipos presentes vêm ordenados e sem repetição", () => {
  const tipos = tiposPresentes(ast);
  assert.deepEqual(tipos, [...new Set(tipos)].sort());
  assert.ok(tipos.includes("Condicional") && tipos.includes("Numero"));
});

test("posição legível", () => {
  assert.equal(
    posicaoDoNo({ linha: 1, coluna: 5, linha_fim: 1, coluna_fim: 10 }),
    "linha 1, col. 5 até linha 1, col. 10"
  );
});

test("deslocamento converte linha/coluna em índice", () => {
  const c = "ab\ncde\nf";
  assert.equal(deslocamento(c, 1, 1), 0);
  assert.equal(deslocamento(c, 2, 2), 4);
  assert.equal(deslocamento(c, 3, 1), 7);
  assert.equal(deslocamento(c, 9, 1), c.length);
  assert.equal(deslocamento("a\r\nb", 2, 1), 2);
});

test("trecho do nó devolve exatamente o texto do nó", () => {
  const codigo = FIXTURES.sintatico_valido.codigo;
  const percorre = (n, f) => {
    f(n);
    n.filhos.forEach((c) => percorre(c, f));
  };
  percorre(ast, (n) => {
    if (n.tipo === "Numero" || n.tipo === "Identificador") {
      const [, trecho] = trechoDoNo(codigo, n);
      assert.equal(trecho, n.atributos.lexema ?? n.atributos.nome);
    }
  });
});

test("o trecho de uma atribuição vai do alvo ao fim do valor", () => {
  const codigo = FIXTURES.sintatico_valido.codigo;
  const [, trecho] = trechoDoNo(codigo, ast.filhos[0]);
  assert.equal(trecho, "x = 10 + 5 * 2");
});

test("JSON exportado volta ao mesmo objeto", () => {
  assert.deepEqual(JSON.parse(jsonDaAst(ast)), ast);
});
