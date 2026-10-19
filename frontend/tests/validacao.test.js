import test from "node:test";
import assert from "node:assert/strict";
import { validarEntrada, MSG_VAZIO, MSG_SO_ESPACOS } from "../js/validacao.js";

test("código válido é aceito", () => {
  assert.deepEqual(validarEntrada("x = 10"), { ok: true });
});

test("código multilinha com indentação é aceito", () => {
  assert.equal(validarEntrada("while x > 0:\n    x = x - 1\n").ok, true);
});

test("caracteres especiais são aceitos", () => {
  assert.equal(validarEntrada("x = 1 # açaí ✓ <script>&\"'\\").ok, true);
});

test("código com erro intencional também é aceito", () => {
  assert.equal(validarEntrada("if x >> :: (((").ok, true);
});

test("texto vazio é rejeitado com a mensagem esperada", () => {
  const r = validarEntrada("");
  assert.equal(r.ok, false);
  assert.equal(r.motivo, "vazia");
  assert.equal(r.mensagem, MSG_VAZIO);
  assert.equal(MSG_VAZIO, "Informe um código-fonte antes de solicitar a análise.");
});

for (const texto of [" ", "   ", "\n", "\t", " \n\t \r\n"]) {
  test(`somente espaços é rejeitado: ${JSON.stringify(texto)}`, () => {
    const r = validarEntrada(texto);
    assert.equal(r.ok, false);
    assert.equal(r.motivo, "somente_espacos");
    assert.equal(r.mensagem, MSG_SO_ESPACOS);
  });
}

test("valores que não são texto são rejeitados", () => {
  for (const v of [undefined, null, 42, {}, []]) {
    assert.equal(validarEntrada(v).ok, false);
  }
});
