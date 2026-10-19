// Testes de interface: usam o index.html real dentro do jsdom.

import test from "node:test";
import assert from "node:assert/strict";
import { iniciar } from "../js/app.js";
import { EXEMPLOS } from "../js/exemplos.js";
import { MSG_COMUNICACAO, MSG_INESPERADO } from "../js/api.js";
import { criarDom, fetchFalso, respostaFalsa, textoDe } from "./ajudantes.js";

function montar(fetchFn) {
  const dom = criarDom();
  const doc = dom.window.document;
  const f = fetchFn ?? fetchFalso(() => respostaFalsa(200, { recebido: true, mensagem: "Código recebido com sucesso.", linhas: 1, caracteres: 1 }));
  const api = iniciar(doc, { fetchFn: f });
  return {
    dom,
    doc,
    f,
    api,
    codigo: doc.getElementById("codigo"),
    exemplos: doc.getElementById("exemplos"),
    analisar: doc.getElementById("btn-analisar"),
    limpar: doc.getElementById("btn-limpar"),
    resultado: doc.getElementById("resultado-conteudo"),
    descricao: doc.getElementById("descricao-exemplo"),
  };
}

function escolher(ctx, id) {
  ctx.exemplos.value = id;
  ctx.exemplos.dispatchEvent(new ctx.dom.window.Event("change"));
}

// ------------------------------------------------------- elementos da tela
test("identifica o sistema e a linguagem analisada", () => {
  const { doc } = montar();
  assert.match(textoDe(doc.querySelector("h1")), /Compilador Educacional/);
  assert.match(textoDe(doc.getElementById("linguagem")), /Python/);
});

test("exibe o nome da autora", () => {
  const { doc } = montar();
  assert.match(textoDe(doc.querySelector("footer")), /Maria Eduarda Almeida Lopes/);
});

test("possui área de código, botão de análise, resultados e seletor de exemplos", () => {
  const ctx = montar();
  assert.equal(ctx.codigo.tagName, "TEXTAREA");
  assert.equal(ctx.analisar.tagName, "BUTTON");
  assert.match(textoDe(ctx.analisar), /Analisar/);
  assert.ok(ctx.resultado);
  assert.equal(ctx.exemplos.tagName, "SELECT");
});

test("área de resultados começa com texto orientativo", () => {
  const { resultado } = montar();
  assert.match(textoDe(resultado), /resultados da análise aparecerão aqui/i);
});

test("o campo de código e o seletor possuem rótulos associados", () => {
  const { doc } = montar();
  assert.ok(doc.querySelector('label[for="codigo"]'));
  assert.ok(doc.querySelector('label[for="exemplos"]'));
});

test("seletor lista todos os exemplos (e a opção inicial)", () => {
  const { exemplos } = montar();
  assert.equal(exemplos.options.length, EXEMPLOS.length + 1);
});

// ------------------------------------------------------------- exemplos
for (const ex of EXEMPLOS) {
  test(`selecionar "${ex.id}" preenche o editor com o código do exemplo`, () => {
    const ctx = montar();
    escolher(ctx, ex.id);
    assert.equal(ctx.codigo.value, ex.codigo);
    assert.match(ctx.descricao.textContent, /Demonstra:/);
  });
}

test("escolher outro exemplo substitui o conteúdo anterior", () => {
  const ctx = montar();
  escolher(ctx, EXEMPLOS[0].id);
  escolher(ctx, EXEMPLOS[1].id);
  assert.equal(ctx.codigo.value, EXEMPLOS[1].codigo);
  assert.ok(!ctx.codigo.value.includes(EXEMPLOS[0].codigo));
});

test("exemplo carregado pode ser editado e o texto editado é preservado", () => {
  const ctx = montar();
  escolher(ctx, EXEMPLOS[0].id);
  ctx.codigo.value = ctx.codigo.value + "z = 99\n";
  assert.ok(ctx.codigo.value.endsWith("z = 99\n"));
});

test("selecionar exemplo não dispara envio ao backend", () => {
  const ctx = montar();
  escolher(ctx, EXEMPLOS[2].id);
  assert.equal(ctx.f.chamadas.length, 0);
});

test("voltar à opção inicial do seletor não apaga o código", () => {
  const ctx = montar();
  escolher(ctx, EXEMPLOS[0].id);
  escolher(ctx, "");
  assert.equal(ctx.codigo.value, EXEMPLOS[0].codigo);
});

test("selecionar exemplo limpa mensagem de erro anterior", async () => {
  const ctx = montar();
  ctx.codigo.value = "";
  await ctx.api.aoAnalisar();
  assert.match(textoDe(ctx.resultado), /Informe um código-fonte/);
  escolher(ctx, EXEMPLOS[0].id);
  assert.doesNotMatch(textoDe(ctx.resultado), /Informe um código-fonte/);
});

// -------------------------------------------------------- edição de código
test("o texto digitado permanece após uma análise bem-sucedida", async () => {
  const ctx = montar();
  ctx.codigo.value = "a = 1\nb = 2\n";
  await ctx.api.aoAnalisar();
  assert.equal(ctx.codigo.value, "a = 1\nb = 2\n");
});

test("o texto digitado permanece após erro de comunicação", async () => {
  const f = fetchFalso(() => {
    throw new TypeError("Failed to fetch");
  });
  const ctx = montar(f);
  ctx.codigo.value = "a = 1\n";
  await ctx.api.aoAnalisar();
  assert.equal(ctx.codigo.value, "a = 1\n");
});

test("Limpar esvazia o editor e o seletor e restaura o texto orientativo", async () => {
  const ctx = montar();
  escolher(ctx, EXEMPLOS[0].id);
  await ctx.api.aoAnalisar();
  ctx.limpar.click();
  assert.equal(ctx.codigo.value, "");
  assert.equal(ctx.exemplos.value, "");
  assert.equal(ctx.descricao.textContent, "");
  assert.match(textoDe(ctx.resultado), /aparecerão aqui/i);
});

// -------------------------------------------------- envio e validações
test("código válido é enviado ao backend exatamente como digitado", async () => {
  const ctx = montar();
  const codigo = "x = 10  # açaí ✓ <b>&\"'\n\twhile:\n";
  ctx.codigo.value = codigo;
  await ctx.api.aoAnalisar();
  assert.equal(ctx.f.chamadas.length, 1);
  assert.equal(ctx.f.chamadas[0].url, "/api/analisar");
  assert.deepEqual(JSON.parse(ctx.f.chamadas[0].init.body), { codigo });
});

test("clicar no botão dispara o envio", async () => {
  const ctx = montar();
  ctx.codigo.value = "x = 1";
  ctx.analisar.click();
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(ctx.f.chamadas.length, 1);
});

test("sucesso mostra a mensagem do backend, linhas e caracteres", async () => {
  const f = fetchFalso(() =>
    respostaFalsa(200, { recebido: true, mensagem: "Código recebido com sucesso.", linhas: 3, caracteres: 31 })
  );
  const ctx = montar(f);
  ctx.codigo.value = "a = 1\nb = 2\nc = 3\n";
  await ctx.api.aoAnalisar();
  const t = textoDe(ctx.resultado);
  assert.match(t, /Código recebido com sucesso\./);
  assert.match(t, /Linhas: 3/);
  assert.match(t, /Caracteres: 31/);
  assert.match(t, /próximas etapas/);
  assert.ok(ctx.resultado.classList.contains("resultado--sucesso"));
});

test("entrada vazia: mostra mensagem e NÃO chama o backend", async () => {
  const ctx = montar();
  ctx.codigo.value = "";
  await ctx.api.aoAnalisar();
  assert.equal(ctx.f.chamadas.length, 0);
  assert.match(textoDe(ctx.resultado), /Informe um código-fonte antes de solicitar a análise\./);
  assert.ok(ctx.resultado.classList.contains("resultado--erro-entrada"));
});

test("somente espaços: mostra orientação e NÃO chama o backend", async () => {
  const ctx = montar();
  ctx.codigo.value = "  \n\t  \n";
  await ctx.api.aoAnalisar();
  assert.equal(ctx.f.chamadas.length, 0);
  assert.match(textoDe(ctx.resultado), /apenas espaços em branco/);
});

test("rejeição 4xx do backend aparece como erro de entrada", async () => {
  const f = fetchFalso(() =>
    respostaFalsa(400, { recebido: false, erro: "campo_ausente", mensagem: 'O campo obrigatório "codigo" não foi informado.' })
  );
  const ctx = montar(f);
  ctx.codigo.value = "x = 1";
  await ctx.api.aoAnalisar();
  assert.match(textoDe(ctx.resultado), /campo obrigatório/);
  assert.ok(ctx.resultado.classList.contains("resultado--erro-entrada"));
});

test("falha de comunicação mostra a mensagem esperada", async () => {
  const f = fetchFalso(() => {
    throw new TypeError("Failed to fetch");
  });
  const ctx = montar(f);
  ctx.codigo.value = "x = 1";
  await ctx.api.aoAnalisar();
  assert.match(textoDe(ctx.resultado), new RegExp(MSG_COMUNICACAO.slice(0, 40)));
  assert.equal(
    MSG_COMUNICACAO,
    "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente."
  );
  assert.ok(ctx.resultado.classList.contains("resultado--erro-comunicacao"));
});

test("erro 500 mostra mensagem genérica sem expor detalhes internos", async () => {
  const f = fetchFalso(() =>
    respostaFalsa(500, { recebido: false, erro: "erro_interno", mensagem: "Traceback (most recent call last): /app/app.py" })
  );
  const ctx = montar(f);
  ctx.codigo.value = "x = 1";
  await ctx.api.aoAnalisar();
  const t = textoDe(ctx.resultado);
  assert.match(t, new RegExp(MSG_INESPERADO));
  assert.doesNotMatch(t, /Traceback|\/app\//);
  assert.ok(ctx.resultado.classList.contains("resultado--erro-inesperado"));
});

test("interface volta a um estado utilizável após falha (botão reabilitado)", async () => {
  const f = fetchFalso(() => {
    throw new TypeError("Failed to fetch");
  });
  const ctx = montar(f);
  ctx.codigo.value = "x = 1";
  await ctx.api.aoAnalisar();
  assert.equal(ctx.analisar.disabled, false);
});

test("botão fica desabilitado durante o envio e é reabilitado ao final", async () => {
  let liberar;
  const f = fetchFalso(
    () =>
      new Promise((res) => {
        liberar = () => res(respostaFalsa(200, { recebido: true, mensagem: "ok", linhas: 1, caracteres: 1 }));
      })
  );
  const ctx = montar(f);
  ctx.codigo.value = "x = 1";
  const pendente = ctx.api.aoAnalisar();
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(ctx.analisar.disabled, true);
  assert.match(textoDe(ctx.resultado), /Enviando/);
  liberar();
  await pendente;
  assert.equal(ctx.analisar.disabled, false);
});

test("depois de um erro, uma nova análise válida funciona (regressão)", async () => {
  const ctx = montar();
  ctx.codigo.value = "";
  await ctx.api.aoAnalisar();
  ctx.codigo.value = "x = 1";
  await ctx.api.aoAnalisar();
  assert.equal(ctx.f.chamadas.length, 1);
  assert.match(textoDe(ctx.resultado), /Código recebido com sucesso\./);
});

test("o código do usuário nunca é inserido como HTML na área de resultados", async () => {
  const f = fetchFalso(() =>
    respostaFalsa(200, { recebido: true, mensagem: "<img src=x onerror=alert(1)>", linhas: 1, caracteres: 1 })
  );
  const ctx = montar(f);
  ctx.codigo.value = "<script>alert(1)</script>";
  await ctx.api.aoAnalisar();
  assert.equal(ctx.resultado.querySelector("img"), null);
  assert.equal(ctx.resultado.querySelector("script"), null);
});
