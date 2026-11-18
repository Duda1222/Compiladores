// Interface da análise sintática (jsdom + respostas reais do backend).
import test from "node:test";
import assert from "node:assert/strict";
import { iniciar } from "../js/app.js";
import { FIXTURES, criarDom, fetchFalso, respostaFalsa, textoDe } from "./ajudantes.js";

async function analisar(nome, opcoes = {}) {
  const dom = criarDom();
  const doc = dom.window.document;
  const f = fetchFalso(() => respostaFalsa(200, FIXTURES[nome].resposta));
  const api = iniciar(doc, { fetchFn: f, ...opcoes });
  doc.getElementById("codigo").value = FIXTURES[nome].codigo;
  await api.aoAnalisar();
  return { dom, doc };
}

const folhas = (no, acc = []) => {
  if (no.terminal) acc.push(no);
  (no.filhos ?? []).forEach((f) => folhas(f, acc));
  return acc;
};

// ------------------------------------------------------------------ sucesso
test("programa válido mostra a seção sintática com a árvore", async () => {
  const { doc } = await analisar("sintatico_valido");
  const sec = doc.getElementById("sec-sintatico");
  assert.ok(sec);
  assert.match(textoDe(sec), /Análise sintática concluída sem erros/);
  const arvore = doc.getElementById("arvore-ast");
  assert.equal(arvore.getAttribute("role"), "tree");
  assert.match(textoDe(arvore), /Programa/);
  assert.match(textoDe(arvore), /OperacaoBinaria \*/);
});

test("a seção sintática vem antes da contagem de tokens e depois do resumo", async () => {
  const { doc } = await analisar("sintatico_valido");
  const ids = [...doc.querySelectorAll("#resultado-conteudo > *")].map((e) => e.id || e.className);
  assert.ok(ids.indexOf("sec-sintatico") < ids.indexOf("sec-contagem"));
});

test("número de nós exibidos é igual ao da resposta", async () => {
  const { doc } = await analisar("sintatico_valido");
  const total = FIXTURES.sintatico_valido.resposta.sintatico.resumo.total_nos;
  assert.equal(doc.querySelectorAll("#arvore-ast li.no").length, total);
});

test("a tela traz a visão em texto indentado e o JSON", async () => {
  const { doc } = await analisar("sintatico_valido");
  assert.match(doc.querySelector("#ast-texto pre").textContent, /^Programa\n  Atribuicao/);
  const json = JSON.parse(doc.querySelector("#ast-json pre").textContent);
  assert.equal(json.tipo, "Programa");
});

test("recolher tudo esconde os filhos e expandir tudo mostra de novo", async () => {
  const { doc } = await analisar("sintatico_valido");
  const raiz = doc.getElementById("arvore-ast");
  doc.getElementById("btn-recolher").click();
  const ocultos = [...raiz.querySelectorAll("ul.no__filhos")].filter((u) => u.hidden);
  assert.equal(ocultos.length, raiz.querySelectorAll("ul.no__filhos").length);
  assert.equal(raiz.querySelector("button.no__toggle").getAttribute("aria-expanded"), "false");
  doc.getElementById("btn-expandir").click();
  assert.equal([...raiz.querySelectorAll("ul.no__filhos")].filter((u) => u.hidden).length, 0);
});

test("botão individual recolhe só aquele nó", async () => {
  const { doc } = await analisar("sintatico_valido");
  const raiz = doc.getElementById("arvore-ast");
  const toggle = raiz.querySelector("li.no > .no__linha > button.no__toggle");
  toggle.click();
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.match(toggle.getAttribute("aria-label"), /^Expandir/);
  toggle.click();
  assert.equal(toggle.getAttribute("aria-expanded"), "true");
});

test("clicar em um nó mostra regra, posição e realça o trecho do código", async () => {
  const { doc } = await analisar("sintatico_valido");
  const rotulos = [...doc.querySelectorAll("#arvore-ast .no__rotulo")];
  const alvo = rotulos.find((b) => b.textContent.includes("Atribuicao"));
  alvo.click();
  const painel = textoDe(doc.getElementById("painel-no"));
  assert.match(painel, /Regra da gramática/);
  assert.match(painel, /atribuicao → IDENTIFICADOR '=' expressao/);
  assert.match(painel, /linha 1, col\. 1 até linha 1, col\. 15/);
  assert.equal(doc.querySelector("#codigo-no mark").textContent, "x = 10 + 5 * 2");
  assert.equal(alvo.getAttribute("aria-current"), "true");
});

test("o realce não depende só de cor (borda, negrito e marcação <mark>)", async () => {
  const { doc } = await analisar("sintatico_valido");
  doc.querySelector("#arvore-ast .no__rotulo").click();
  assert.ok(doc.querySelector("#arvore-ast .no__rotulo--selecionado"));
  assert.ok(doc.querySelector("#codigo-no mark.trecho-no"));
});

test("filtro por tipo marca os nós com texto e informa a contagem", async () => {
  const { doc, dom } = await analisar("sintatico_valido");
  const filtro = doc.getElementById("filtro-tipo");
  filtro.value = "Numero";
  filtro.dispatchEvent(new dom.window.Event("change"));
  const marcados = doc.querySelectorAll("#arvore-ast li.no--filtrado");
  assert.ok(marcados.length >= 3);
  assert.equal(doc.querySelectorAll("#arvore-ast .marca-filtro").length, marcados.length);
  assert.match(textoDe(doc.getElementById("estado-filtro")), new RegExp(`^${marcados.length} nós encontrados do tipo Numero`));
  filtro.value = "";
  filtro.dispatchEvent(new dom.window.Event("change"));
  assert.equal(doc.querySelectorAll("#arvore-ast li.no--filtrado").length, 0);
});

test("exportar JSON entrega o arquivo ast.json com a AST completa", async () => {
  let baixado = null;
  const { doc } = await analisar("sintatico_valido", { baixar: (nome, texto) => (baixado = { nome, texto }) });
  doc.getElementById("btn-exportar-json").click();
  assert.equal(baixado.nome, "ast.json");
  assert.deepEqual(JSON.parse(baixado.texto), FIXTURES.sintatico_valido.resposta.sintatico.ast);
});

test("a explicação diferencia tokens, derivação e AST", async () => {
  const { doc } = await analisar("sintatico_valido");
  const t = textoDe(doc.getElementById("ajuda-sintatica"));
  assert.match(t, /Sequência de tokens/);
  assert.match(t, /Árvore de derivação/);
  assert.match(t, /AST/);
});

test("consistência: folhas da árvore de derivação = tokens da análise léxica", async () => {
  const { doc } = await analisar("sintatico_valido");
  const r = FIXTURES.sintatico_valido.resposta;
  const lexemas = folhas(r.sintatico.derivacao).map((f) => f.lexema);
  assert.deepEqual(lexemas, r.lexico.tokens.map((t) => t.lexema));
  assert.ok(doc.getElementById("derivacao"));
});

test("a árvore de derivação é exibida e é maior que a AST", async () => {
  const { doc } = await analisar("sintatico_valido");
  const nosDer = doc.querySelectorAll("#derivacao li.no").length;
  const nosAst = doc.querySelectorAll("#arvore-ast li.no").length;
  assert.ok(nosDer > nosAst);
});

test("a seção léxica continua presente (tabela de tokens e passo a passo)", async () => {
  const { doc } = await analisar("sintatico_valido");
  assert.ok(doc.getElementById("sec-tabela"));
  assert.ok(doc.getElementById("sec-contagem"));
});

// -------------------------------------------------------------------- erros
test("erro sintático lista linha, coluna, encontrado, esperado e regra", async () => {
  const { doc } = await analisar("sintatico_erro");
  const sec = doc.getElementById("sec-sintatico");
  assert.ok(sec.classList.contains("bloco--erro"));
  const t = textoDe(sec);
  assert.match(t, /Linha 1, coluna 9/);
  assert.match(t, /Erro sintático:/);
  assert.match(t, /Encontrado\s*fim da linha/);
  assert.match(t, /Esperado\s*identificador, número/);
  assert.match(t, /Regra da gramática/);
  assert.equal(sec.querySelectorAll("li.lista-erros__item").length,
    FIXTURES.sintatico_erro.resposta.sintatico.erros.length);
});

test("com erro sintático não há árvore e a tela explica o motivo", async () => {
  const { doc } = await analisar("sintatico_erro");
  assert.equal(doc.getElementById("arvore-ast"), null);
  assert.match(textoDe(doc.getElementById("sec-sintatico")), /Sem uma estrutura válida, não há AST/);
});

test("com erro sintático a análise léxica continua visível", async () => {
  const { doc } = await analisar("sintatico_erro");
  assert.ok(doc.getElementById("sec-tabela"));
});

test("erro léxico: parser não executado, com aviso e erros léxicos visíveis", async () => {
  const { doc } = await analisar("erros");
  const sec = doc.getElementById("sec-sintatico");
  assert.match(textoDe(sec), /Análise sintática não executada/);
  assert.match(textoDe(sec), /erros léxicos/);
  assert.equal(doc.getElementById("arvore-ast"), null);
  assert.ok(doc.getElementById("sec-erros"));
});

test("somente comentários: Programa vazio com explicação", async () => {
  const { doc } = await analisar("comentarios");
  assert.match(textoDe(doc.getElementById("sec-sintatico")), /Programa vazio/);
});

test("conteúdo hostil não é inserido como HTML", async () => {
  const resposta = JSON.parse(JSON.stringify(FIXTURES.sintatico_valido.resposta));
  resposta.sintatico.ast.filhos[0].filhos[0].atributos.nome = "<img src=x onerror=alert(1)>";
  const dom = criarDom();
  const doc = dom.window.document;
  const api = iniciar(doc, { fetchFn: fetchFalso(() => respostaFalsa(200, resposta)) });
  doc.getElementById("codigo").value = "<img src=x onerror=alert(1)> = 1\n";
  await api.aoAnalisar();
  assert.equal(doc.querySelector("#sec-sintatico img"), null);
  assert.match(doc.getElementById("arvore-ast").textContent, /<img src=x/);
});

test("resposta antiga sem o campo sintatico não quebra a tela", async () => {
  const resposta = { ...FIXTURES.valido.resposta };
  delete resposta.sintatico;
  const dom = criarDom();
  const doc = dom.window.document;
  const api = iniciar(doc, { fetchFn: fetchFalso(() => respostaFalsa(200, resposta)) });
  doc.getElementById("codigo").value = FIXTURES.valido.codigo;
  await api.aoAnalisar();
  assert.equal(doc.getElementById("sec-sintatico"), null);
  assert.ok(doc.getElementById("sec-tabela"));
});

test("a tela informa o limite de entrada", () => {
  const dom = criarDom();
  assert.match(dom.window.document.getElementById("aviso-limite").textContent, /100\.000 caracteres/);
});
