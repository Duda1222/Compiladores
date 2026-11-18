// Integração frontend <-> backend REAL para a análise sintática.
// Só roda com BACKEND_URL definida.
import test from "node:test";
import assert from "node:assert/strict";
import { iniciar } from "../js/app.js";
import { enviarCodigo } from "../js/api.js";
import { EXEMPLOS } from "../js/exemplos.js";
import { criarDom, textoDe } from "./ajudantes.js";

const base = process.env.BACKEND_URL;
const opcoes = { skip: base ? false : "defina BACKEND_URL para rodar" };

test("integração: precedência chega na AST (10 + 5 * 2)", opcoes, async () => {
  const r = await enviarCodigo("x = 10 + 5 * 2\n", { url: `${base}/api/analisar` });
  const soma = r.dados.sintatico.ast.filhos[0].filhos[1];
  assert.equal(soma.atributos.operador, "+");
  assert.equal(soma.filhos[1].atributos.operador, "*");
});

test("integração: erro sintático chega com ast nula", opcoes, async () => {
  const r = await enviarCodigo("x = = 3\n", { url: `${base}/api/analisar` });
  assert.equal(r.dados.sintatico.ast, null);
  assert.equal(r.dados.sintatico.erros[0].tipo, "ERRO_SINTATICO");
});

for (const ex of EXEMPLOS) {
  test(`integração: exemplo "${ex.id}" é exibido com a seção sintática`, opcoes, async () => {
    const dom = criarDom();
    const doc = dom.window.document;
    const api = iniciar(doc, { url: `${base}/api/analisar` });
    doc.getElementById("codigo").value = ex.codigo;
    await api.aoAnalisar();
    const sec = doc.getElementById("sec-sintatico");
    assert.ok(sec, "seção sintática ausente");
    assert.doesNotMatch(textoDe(doc.getElementById("resultado-conteudo")), /Erro inesperado|Falha de comunicação/);
  });
}
