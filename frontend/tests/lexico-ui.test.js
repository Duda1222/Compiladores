// Testes de interface da análise léxica (jsdom + respostas reais do backend).

import test from "node:test";
import assert from "node:assert/strict";
import { iniciar } from "../js/app.js";
import { EXEMPLOS } from "../js/exemplos.js";
import { FIXTURES, criarDom, fetchFalso, respostaFalsa, textoDe } from "./ajudantes.js";

function montar(nomeFixture, opcoes = {}) {
  const dom = criarDom();
  const doc = dom.window.document;
  const f = fetchFalso(() => respostaFalsa(200, FIXTURES[nomeFixture].resposta));
  const api = iniciar(doc, { fetchFn: f, ...opcoes });
  doc.getElementById("codigo").value = FIXTURES[nomeFixture].codigo;
  return { dom, doc, f, api, resultado: doc.getElementById("resultado-conteudo") };
}

async function analisar(nome, opcoes) {
  const ctx = montar(nome, opcoes);
  await ctx.api.aoAnalisar();
  return ctx;
}

const tokens = (nome) => FIXTURES[nome].resposta.tokens;

// ---------------------------------------------------------------- tabela
test("tabela mostra uma linha por token, com tipo, lexema, linha e coluna", async () => {
  const { doc } = await analisar("valido");
  const linhas = [...doc.querySelectorAll("#sec-tabela tbody tr")];
  assert.equal(linhas.length, tokens("valido").length);

  const cabecalhos = [...doc.querySelectorAll("#sec-tabela thead th")].map((th) => th.textContent);
  assert.deepEqual(cabecalhos, ["#", "Tipo", "Lexema", "Linha", "Coluna"]);

  const primeira = [...linhas[0].children].map((td) => td.textContent);
  assert.deepEqual(primeira, ["1", "IDENTIFICADOR", "x", "1", "1"]);
  const terceira = [...linhas[2].children].map((td) => td.textContent);
  assert.equal(terceira[1], "LITERAL_INTEIRO");
  assert.equal(terceira[2], "10");
  assert.equal(terceira[4], "5");
});

test("tokens invisíveis aparecem com símbolo e texto para leitores de tela", async () => {
  const { doc } = await analisar("valido");
  const texto = textoDe(doc.getElementById("sec-tabela"));
  assert.match(texto, /↵/);
  assert.match(texto, /→/);
  assert.match(texto, /←/);
  assert.match(texto, /Indentação \(abre bloco\)/);
});

test("a tabela tem cabeçalhos com escopo e fica numa região rolável (celular)", async () => {
  const { doc } = await analisar("valido");
  for (const th of doc.querySelectorAll("#sec-tabela th")) assert.equal(th.scope, "col");
  const regiao = doc.querySelector("#sec-tabela .tabela-rolavel");
  assert.equal(regiao.getAttribute("role"), "region");
  assert.equal(regiao.tabIndex, 0);
});

// ---------------------------------------------------------------- resumo
test("resumo informa quantidade de tokens, erros, linhas e caracteres", async () => {
  const { resultado } = await analisar("valido");
  const t = textoDe(resultado);
  assert.match(t, new RegExp(`${tokens("valido").length} tokens`));
  assert.match(t, /0 erros léxicos/);
  assert.match(t, /3 linhas/);
});

test("contagem por categoria bate com o resumo do backend", async () => {
  const { doc } = await analisar("valido");
  const chips = [...doc.querySelectorAll("#sec-contagem .chip")].map((c) => [
    c.querySelector(".chip__nome").textContent,
    c.querySelector(".chip__n").textContent,
  ]);
  const porTipo = FIXTURES.valido.resposta.resumo.por_tipo;
  assert.equal(chips.length, Object.keys(porTipo).length);
  for (const [tipo, n] of Object.entries(porTipo)) {
    assert.ok(chips.some(([t, q]) => t === tipo && q === `×${n}`), `${tipo} ×${n}`);
  }
  // total das contagens = total de tokens
  const soma = chips.reduce((acc, [, q]) => acc + Number(q.slice(1)), 0);
  assert.equal(soma, tokens("valido").length);
});

// ------------------------------------------------------- código colorido
test("o código destacado preserva o texto do programa", async () => {
  const { doc } = await analisar("valido");
  const pre = doc.querySelector("#sec-codigo pre");
  // ↵ ← ∎ são símbolos extras; as quebras de linha reais continuam no texto.
  assert.equal(pre.textContent.replace(/[↵←∎]/g, ""), FIXTURES.valido.codigo);
});

test("cada categoria recebe a sua classe de cor no código", async () => {
  const { doc } = await analisar("valido");
  const pre = doc.querySelector("#sec-codigo pre");
  assert.ok(pre.querySelector(".t-reservada"), "while");
  assert.ok(pre.querySelector(".t-identificador"));
  assert.ok(pre.querySelector(".t-inteiro"));
  assert.ok(pre.querySelector(".t-relacional"));
  assert.ok(pre.querySelector(".t-atribuicao"));
  assert.ok(pre.querySelector(".t-aritmetico"));
  assert.ok(pre.querySelector(".t-delimitador"));
  assert.equal(pre.querySelector(".t-reservada").textContent, "while");
});

test("cada trecho destacado informa tipo e posição (title)", async () => {
  const { doc } = await analisar("valido");
  const w = doc.querySelector("#sec-codigo .t-reservada");
  assert.match(w.title, /PALAVRA_RESERVADA · linha 2, coluna 1/);
});

test("sequência de tokens tem uma peça por token, na ordem", async () => {
  const { doc } = await analisar("valido");
  const pecas = [...doc.querySelectorAll("#sec-sequencia li")];
  assert.equal(pecas.length, tokens("valido").length);
  assert.equal(pecas[0].querySelector(".peca__lexema").textContent, "x");
  assert.equal(pecas[0].querySelector(".peca__tipo").textContent, "IDENTIFICADOR");
});

// ----------------------------------------------------------------- erros
test("erros léxicos aparecem com linha, coluna e mensagem clara", async () => {
  const { doc, resultado } = await analisar("erros");
  const itens = [...doc.querySelectorAll("#sec-erros li")];
  assert.equal(itens.length, FIXTURES.erros.resposta.erros.length);
  const texto = textoDe(doc.getElementById("sec-erros"));
  assert.match(texto, /Linha 1, coluna 12/);
  assert.match(texto, /Caractere não reconhecido: '@'/);
  assert.match(texto, /Linha 2, coluna 9/);
  assert.match(texto, /mais de um ponto decimal/);
  assert.match(texto, /strings ainda não fazem parte/);
  assert.match(texto, /seguido de letras/);
  assert.ok(resultado.classList.contains("resultado--erro-lexico"));
  assert.match(textoDe(resultado), /5 erros léxicos|4 erros léxicos/);
});

test("trechos com erro ficam marcados no código", async () => {
  const { doc } = await analisar("erros");
  const marcados = [...doc.querySelectorAll("#sec-codigo .erro-lexico")].map((e) => e.textContent);
  assert.ok(marcados.includes("@"));
  assert.ok(marcados.includes("3.14.15"));
  assert.ok(marcados.includes("12abc"));
});

test("a análise continua mesmo com erros: tokens válidos aparecem na tabela", async () => {
  const { doc } = await analisar("erros");
  const lexemas = [...doc.querySelectorAll("#sec-tabela tbody tr")].map((tr) => tr.children[2].textContent);
  assert.ok(lexemas.includes("preco"));
  assert.ok(lexemas.includes("valor"));
});

test("avisos de palavras fora do subconjunto são exibidos", async () => {
  const { doc } = await analisar("erros");
  assert.match(textoDe(doc.getElementById("sec-avisos")), /'def' é palavra reservada do Python/);
});

test("código sem erros não mostra a seção de erros", async () => {
  const { doc } = await analisar("valido");
  assert.equal(doc.getElementById("sec-erros"), null);
});

test("erro de tabulação na indentação não duplica o texto do código", async () => {
  const { doc } = await analisar("tabulacao");
  const pre = doc.querySelector("#sec-codigo pre");
  assert.equal(pre.textContent.replace(/[↵←∎]/g, ""), FIXTURES.tabulacao.codigo);
  assert.match(textoDe(doc.getElementById("sec-erros")), /Tabulação na indentação/);
});

test("apenas comentários: sem erros e com a tabela contendo só o fim do arquivo", async () => {
  const { doc, resultado } = await analisar("comentarios");
  assert.ok(resultado.classList.contains("resultado--sucesso"));
  assert.equal(doc.querySelectorAll("#sec-tabela tbody tr").length, 1);
});

// ---------------------------------------------------------- passo a passo
test("passo a passo: começa mostrando tudo, com orientação", async () => {
  const { doc } = await analisar("valido");
  assert.match(textoDe(doc.querySelector(".painel-passo")), /Clique em «Próximo»/);
  assert.equal(doc.getElementById("passo-anterior").disabled, true);
  assert.equal(doc.getElementById("passo-tudo").disabled, true);
  assert.equal(doc.querySelectorAll(".is-atual").length, 0);
});

test("Próximo avança token a token e explica a regra usada", async () => {
  const { doc } = await analisar("valido");
  const prox = doc.getElementById("passo-proximo");
  prox.click();
  let painel = textoDe(doc.querySelector(".painel-passo"));
  assert.match(painel, new RegExp(`Passo 1 de ${tokens("valido").length}`));
  assert.match(painel, /Lexema lido: x · linha 1, coluna 1/);
  assert.match(painel, /IDENTIFICADOR/);
  assert.match(painel, /Por quê\?/);
  prox.click();
  painel = textoDe(doc.querySelector(".painel-passo"));
  assert.match(painel, /Passo 2/);
  assert.match(painel, /OPERADOR_ATRIBUICAO/);
});

test("o token atual é realçado no código, na sequência e na tabela", async () => {
  const { doc } = await analisar("valido");
  doc.getElementById("passo-proximo").click();
  assert.equal(doc.querySelector("#sec-codigo .is-atual").textContent, "x");
  assert.equal(doc.querySelectorAll("#sec-tabela tr.is-atual").length, 1);
  assert.equal(doc.querySelectorAll("#sec-sequencia .is-atual").length, 1);
  assert.equal(doc.querySelector("#sec-tabela tr.is-atual").getAttribute("aria-current"), "step");
});

test("tokens ainda não lidos ficam esmaecidos e os lidos permanecem normais", async () => {
  const { doc } = await analisar("valido");
  const prox = doc.getElementById("passo-proximo");
  prox.click();
  prox.click();
  prox.click();
  const futuros = doc.querySelectorAll("#sec-sequencia .is-futuro").length;
  assert.equal(futuros, tokens("valido").length - 3);
});

test("Anterior volta um passo e fica desabilitado no primeiro", async () => {
  const { doc } = await analisar("valido");
  const ant = doc.getElementById("passo-anterior");
  doc.getElementById("passo-proximo").click();
  doc.getElementById("passo-proximo").click();
  assert.equal(ant.disabled, false);
  ant.click();
  assert.match(textoDe(doc.querySelector(".painel-passo")), /Passo 1 de/);
  assert.equal(ant.disabled, true);
});

test("no último passo, Próximo fica desabilitado", async () => {
  const { doc } = await analisar("valido");
  const prox = doc.getElementById("passo-proximo");
  for (let i = 0; i < tokens("valido").length; i++) prox.click();
  assert.match(textoDe(doc.querySelector(".painel-passo")), /FIM_DE_ARQUIVO/);
  assert.equal(prox.disabled, true);
});

test("Mostrar tudo remove o realce e restaura a visão completa", async () => {
  const { doc } = await analisar("valido");
  doc.getElementById("passo-proximo").click();
  doc.getElementById("passo-tudo").click();
  assert.equal(doc.querySelectorAll(".is-atual, .is-futuro").length, 0);
  assert.match(textoDe(doc.querySelector(".painel-passo")), /Clique em «Próximo»/);
});

test("Reproduzir percorre todos os tokens sozinho e depois para", async () => {
  const fila = [];
  const dom = criarDom();
  const d = dom.window.document;
  const f = fetchFalso(() => respostaFalsa(200, FIXTURES.valido.resposta));
  const ui = iniciar(d, {
    fetchFn: f,
    agendar: (fn, ms) => {
      fila.push({ fn, ms });
      return fila.length;
    },
    cancelar: () => {},
  });
  d.getElementById("codigo").value = FIXTURES.valido.codigo;
  await ui.aoAnalisar();

  const botao = d.getElementById("passo-reproduzir");
  botao.click();
  assert.equal(botao.textContent, "Pausar");
  assert.match(textoDe(d.querySelector(".painel-passo")), /Passo 1 de/);
  assert.equal(fila[0].ms, 900); // intervalo entre os passos
  let guarda = 0;
  while (fila.length && guarda++ < 500) fila.shift().fn();
  assert.match(textoDe(d.querySelector(".painel-passo")), new RegExp(`Passo ${tokens("valido").length} de`));
  assert.equal(botao.textContent, "Reproduzir");
});

test("Pausar interrompe a reprodução automática", async () => {
  const cancelados = [];
  const dom = criarDom();
  const d = dom.window.document;
  const f = fetchFalso(() => respostaFalsa(200, FIXTURES.valido.resposta));
  const ui = iniciar(d, { fetchFn: f, agendar: () => 42, cancelar: (id) => cancelados.push(id) });
  d.getElementById("codigo").value = FIXTURES.valido.codigo;
  await ui.aoAnalisar();
  const botao = d.getElementById("passo-reproduzir");
  botao.click();
  botao.click();
  assert.equal(botao.textContent, "Reproduzir");
  assert.deepEqual(cancelados, [42]);
});

test("nova análise substitui a anterior e zera o passo a passo", async () => {
  const { doc, api } = await analisar("valido");
  doc.getElementById("passo-proximo").click();
  await api.aoAnalisar();
  assert.match(textoDe(doc.querySelector(".painel-passo")), /Clique em «Próximo»/);
  assert.equal(doc.querySelectorAll("#sec-tabela").length, 1);
});

// ------------------------------------------------------------ segurança
test("código com HTML/script nunca é inserido como HTML", async () => {
  const { doc, resultado } = await analisar("html");
  assert.equal(resultado.querySelector("script"), null);
  assert.equal(resultado.querySelector("b"), null);
  assert.equal(resultado.querySelector("img"), null);
  const pre = doc.querySelector("#sec-codigo pre");
  assert.match(pre.textContent, /<b>/);
});

// ---------------------------------------------- explicações e responsivo
test("a tela explica o que são token e lexema", () => {
  const dom = criarDom();
  const ajuda = dom.window.document.getElementById("ajuda");
  assert.ok(ajuda);
  const t = textoDe(ajuda);
  assert.match(t, /Lexema/);
  assert.match(t, /Token/);
  assert.match(t, /INDENT/);
  assert.match(t, /Etapa 4/);
});

test("a página declara viewport para celulares", () => {
  const dom = criarDom();
  const meta = dom.window.document.querySelector('meta[name="viewport"]');
  assert.match(meta.content, /width=device-width/);
});

test("há exemplos que demonstram as categorias da etapa", () => {
  const ids = EXEMPLOS.map((e) => e.id);
  for (const id of ["operadores", "comentarios", "blocos", "erros-lexicos"]) {
    assert.ok(ids.includes(id), id);
  }
});

// ----------------------------------------------- regressão da Etapa 2
test("regressão: entrada vazia continua sem chamar o backend", async () => {
  const ctx = montar("valido");
  ctx.doc.getElementById("codigo").value = "";
  await ctx.api.aoAnalisar();
  assert.equal(ctx.f.chamadas.length, 0);
  assert.match(textoDe(ctx.resultado), /Informe um código-fonte/);
});

test("regressão: após um resultado léxico, Limpar volta ao texto orientativo", async () => {
  const { doc, resultado } = await analisar("valido");
  doc.getElementById("btn-limpar").click();
  assert.match(textoDe(resultado), /aparecerão aqui/i);
  assert.equal(doc.getElementById("sec-tabela"), null);
});

test("regressão: erro 500 depois de um resultado léxico mostra mensagem genérica", async () => {
  const dom = criarDom();
  const d = dom.window.document;
  let primeira = true;
  const f = fetchFalso(() =>
    primeira
      ? ((primeira = false), respostaFalsa(200, FIXTURES.valido.resposta))
      : respostaFalsa(500, { recebido: false, erro: "erro_interno", mensagem: "Traceback /app/x.py" })
  );
  const ui = iniciar(d, { fetchFn: f });
  d.getElementById("codigo").value = "x = 1";
  await ui.aoAnalisar();
  await ui.aoAnalisar();
  const t = textoDe(d.getElementById("resultado-conteudo"));
  assert.doesNotMatch(t, /Traceback|\/app\//);
  assert.match(t, /erro inesperado/i);
});
