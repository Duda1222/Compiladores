import test from "node:test";
import assert from "node:assert/strict";
import { EXEMPLOS, buscarExemplo } from "../js/exemplos.js";
import { validarEntrada } from "../js/validacao.js";

test("existem pelo menos três exemplos", () => {
  assert.ok(EXEMPLOS.length >= 3);
});

test("ids são únicos", () => {
  const ids = EXEMPLOS.map((e) => e.id);
  assert.equal(new Set(ids).size, ids.length);
});

for (const ex of EXEMPLOS) {
  test(`exemplo "${ex.id}" tem título, descrição e código aceito pela validação`, () => {
    assert.ok(ex.titulo.length > 0);
    assert.ok(ex.demonstra.length > 0);
    assert.equal(validarEntrada(ex.codigo).ok, true);
    assert.equal(buscarExemplo(ex.id), ex);
  });
}

test("buscarExemplo devolve null para id desconhecido", () => {
  assert.equal(buscarExemplo("nao-existe"), null);
  assert.equal(buscarExemplo(""), null);
});
