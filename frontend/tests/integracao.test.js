// Teste de integração frontend <-> backend REAL.
// Só roda quando BACKEND_URL está definida (ex.: http://localhost:5000 ou
// http://localhost:8080 quando o Docker Compose está de pé). Caso contrário é
// ignorado, para não falhar em máquinas sem o backend em execução.

import test from "node:test";
import assert from "node:assert/strict";
import { iniciar } from "../js/app.js";
import { enviarCodigo, MSG_COMUNICACAO } from "../js/api.js";
import { criarDom, textoDe } from "./ajudantes.js";

const base = process.env.BACKEND_URL;
const opcoes = { skip: base ? false : "defina BACKEND_URL para rodar" };

test("integração: código válido é recebido pelo backend", opcoes, async () => {
  const r = await enviarCodigo("x = 10\nwhile x > 0:\n    x = x - 1\n", {
    url: `${base}/api/analisar`,
  });
  assert.equal(r.tipo, "sucesso");
  assert.equal(r.dados.recebido, true);
  assert.equal(r.dados.linhas, 3);
});

test("integração: backend rejeita texto vazio (422) com mensagem esperada", opcoes, async () => {
  const r = await enviarCodigo("", { url: `${base}/api/analisar` });
  assert.equal(r.tipo, "entrada");
  assert.equal(r.status, 422);
  assert.equal(r.mensagem, "Informe um código-fonte antes de solicitar a análise.");
});

test("integração: backend rejeita somente espaços (422)", opcoes, async () => {
  const r = await enviarCodigo("   \n  ", { url: `${base}/api/analisar` });
  assert.equal(r.tipo, "entrada");
  assert.equal(r.status, 422);
});

test("integração: interface completa contra o backend real", opcoes, async () => {
  const dom = criarDom();
  const doc = dom.window.document;
  const ui = iniciar(doc, { url: `${base}/api/analisar` });
  doc.getElementById("codigo").value = "a = 1\nb = 2\n";
  await ui.aoAnalisar();
  const t = textoDe(doc.getElementById("resultado-conteudo"));
  assert.match(t, /Código recebido com sucesso\./);
  assert.match(t, /Linhas: 2/);
});

test("integração: servidor fora do ar vira falha de comunicação", opcoes, async () => {
  const r = await enviarCodigo("x = 1", { url: "http://127.0.0.1:1/api/analisar", timeoutMs: 2000 });
  assert.deepEqual(r, { tipo: "comunicacao", mensagem: MSG_COMUNICACAO });
});
