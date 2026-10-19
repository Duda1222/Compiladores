import test from "node:test";
import assert from "node:assert/strict";
import {
  enviarCodigo,
  MSG_COMUNICACAO,
  MSG_INESPERADO,
} from "../js/api.js";
import { fetchFalso, respostaFalsa } from "./ajudantes.js";

test("envia POST JSON com o campo codigo para /api/analisar", async () => {
  const f = fetchFalso(() =>
    respostaFalsa(200, { recebido: true, mensagem: "ok", linhas: 1, caracteres: 6 })
  );
  await enviarCodigo("x = 10", { fetchFn: f });
  assert.equal(f.chamadas.length, 1);
  const { url, init } = f.chamadas[0];
  assert.equal(url, "/api/analisar");
  assert.equal(init.method, "POST");
  assert.equal(init.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(init.body), { codigo: "x = 10" });
});

test("envia o código sem alterá-lo (caracteres especiais e quebras de linha)", async () => {
  const codigo = "x = 1  # açaí ✓ <b>&\"'\\\n\twhile:\n";
  const f = fetchFalso(() => respostaFalsa(200, { recebido: true }));
  await enviarCodigo(codigo, { fetchFn: f });
  assert.equal(JSON.parse(f.chamadas[0].init.body).codigo, codigo);
});

test("resposta 200 vira tipo sucesso", async () => {
  const dados = { recebido: true, mensagem: "Código recebido com sucesso.", linhas: 2, caracteres: 9 };
  const r = await enviarCodigo("a", { fetchFn: fetchFalso(() => respostaFalsa(200, dados)) });
  assert.equal(r.tipo, "sucesso");
  assert.deepEqual(r.dados, dados);
});

test("4xx com mensagem vira tipo entrada", async () => {
  const corpo = { recebido: false, erro: "entrada_vazia", mensagem: "Informe um código-fonte antes de solicitar a análise." };
  const r = await enviarCodigo("a", { fetchFn: fetchFalso(() => respostaFalsa(422, corpo)) });
  assert.equal(r.tipo, "entrada");
  assert.equal(r.status, 422);
  assert.equal(r.mensagem, corpo.mensagem);
});

test("fetch que rejeita vira tipo comunicacao", async () => {
  const f = fetchFalso(() => {
    throw new TypeError("Failed to fetch");
  });
  const r = await enviarCodigo("a", { fetchFn: f });
  assert.deepEqual(r, { tipo: "comunicacao", mensagem: MSG_COMUNICACAO });
});

for (const status of [502, 503, 504]) {
  test(`${status} do proxy (HTML) vira tipo comunicacao`, async () => {
    const f = fetchFalso(() => respostaFalsa(status, null, { json: false }));
    const r = await enviarCodigo("a", { fetchFn: f });
    assert.equal(r.tipo, "comunicacao");
  });
}

test("500 vira erro inesperado genérico, sem repassar detalhes do servidor", async () => {
  const f = fetchFalso(() =>
    respostaFalsa(500, { recebido: false, erro: "erro_interno", mensagem: "Traceback /app/x.py" })
  );
  const r = await enviarCodigo("a", { fetchFn: f });
  assert.deepEqual(r, { tipo: "inesperado", mensagem: MSG_INESPERADO });
});

test("200 com corpo que não é JSON vira erro inesperado", async () => {
  const f = fetchFalso(() => respostaFalsa(200, null, { json: false }));
  const r = await enviarCodigo("a", { fetchFn: f });
  assert.equal(r.tipo, "inesperado");
});

test("timeout aborta a requisição e vira comunicacao", async () => {
  const f = fetchFalso(
    (_url, init) =>
      new Promise((_res, rej) => {
        init.signal.addEventListener("abort", () => rej(new DOMException("abort", "AbortError")));
      })
  );
  const r = await enviarCodigo("a", { fetchFn: f, timeoutMs: 20 });
  assert.equal(r.tipo, "comunicacao");
});
