// Apresentação didática da análise sintática: AST, árvore de derivação e erros.
//
// Tudo é montado com a API do DOM (nunca innerHTML). Funções puras ficam
// separadas das que mexem na tela, para serem testadas sem navegador.

function criar(doc, tag, classe, texto) {
  const el = doc.createElement(tag);
  if (classe) el.className = classe;
  if (texto !== undefined) el.textContent = texto;
  return el;
}

// ----------------------------------------------------------------- puras
/** Texto curto de um nó da AST: "OperacaoBinaria +", "Identificador x"... */
export function rotuloDoNo(no) {
  const a = no.atributos ?? {};
  if (a.nome !== undefined) return `${no.tipo} ${a.nome}`;
  if (a.lexema !== undefined) return `${no.tipo} ${a.lexema}`;
  if (a.operador !== undefined) return `${no.tipo} ${a.operador}`;
  return no.tipo;
}

/** Árvore indentada em texto (a visão mínima exigida: legível sem cor). */
export function arvoreEmTexto(no, nivel = 0) {
  const linhas = [`${"  ".repeat(nivel)}${rotuloDoNo(no)}`];
  for (const f of no.filhos ?? []) linhas.push(arvoreEmTexto(f, nivel + 1));
  return linhas.join("\n");
}

/** Posição legível: "linha 1, col. 5 a linha 1, col. 10". */
export function posicaoDoNo(no) {
  return `linha ${no.linha}, col. ${no.coluna} até linha ${no.linha_fim}, col. ${no.coluna_fim}`;
}

/** Todos os tipos de nó presentes, em ordem alfabética. */
export function tiposPresentes(no, acc = new Set()) {
  acc.add(no.tipo);
  for (const f of no.filhos ?? []) tiposPresentes(f, acc);
  return [...acc].sort();
}

/** Converte (linha, coluna) 1-based em deslocamento dentro do texto. */
export function deslocamento(codigo, linha, coluna) {
  const texto = codigo.replace(/\r\n|\r/g, "\n");
  let inicioLinha = 0;
  for (let l = 1; l < linha; l++) {
    const prox = texto.indexOf("\n", inicioLinha);
    if (prox === -1) return texto.length;
    inicioLinha = prox + 1;
  }
  return Math.min(inicioLinha + Math.max(coluna - 1, 0), texto.length);
}

/** Divide o código em [antes, trecho, depois] para o realce de um nó. */
export function trechoDoNo(codigo, no) {
  const texto = codigo.replace(/\r\n|\r/g, "\n");
  const ini = deslocamento(texto, no.linha, no.coluna);
  const fim = Math.max(deslocamento(texto, no.linha_fim, no.coluna_fim), ini);
  return [texto.slice(0, ini), texto.slice(ini, fim), texto.slice(fim)];
}

/** Nome do arquivo e conteúdo da exportação em JSON. */
export function jsonDaAst(ast) {
  return JSON.stringify(ast, null, 2);
}

// ------------------------------------------------------------------ erros
function itemDeErro(doc, e) {
  const li = criar(doc, "li", "lista-erros__item lista-erros__item--sintatico");
  li.appendChild(criar(doc, "span", "posicao", `Linha ${e.linha}, coluna ${e.coluna}`));
  const corpo = criar(doc, "span", "lista-erros__msg");
  corpo.appendChild(criar(doc, "strong", null, "Erro sintático: "));
  corpo.appendChild(doc.createTextNode(e.mensagem));
  li.appendChild(corpo);
  const detalhes = criar(doc, "dl", "detalhes-erro");
  const linha = (rotulo, valor) => {
    detalhes.appendChild(criar(doc, "dt", null, rotulo));
    detalhes.appendChild(criar(doc, "dd", null, valor));
  };
  linha("Encontrado", e.encontrado ?? "");
  if (Array.isArray(e.esperado) && e.esperado.length) linha("Esperado", e.esperado.join(", "));
  if (e.regra) linha("Regra da gramática", e.regra);
  if (e.dica) linha("Dica", e.dica);
  li.appendChild(detalhes);
  return li;
}

// ------------------------------------------------------------------ árvore
/**
 * Constrói a lista aninhada de uma árvore.
 * adaptador: { rotulo(no), filhos(no), papel(no), tipo(no) }
 */
function montarNo(doc, no, adaptador, ctx, nivel) {
  const li = criar(doc, "li", "no");
  li.setAttribute("role", "treeitem");
  li.dataset.tipo = adaptador.tipo(no);
  const filhos = adaptador.filhos(no);
  const linha = criar(doc, "div", "no__linha");

  let botaoToggle = null;
  if (filhos.length > 0) {
    botaoToggle = criar(doc, "button", "no__toggle", "−");
    botaoToggle.type = "button";
    botaoToggle.setAttribute("aria-expanded", "true");
    botaoToggle.setAttribute("aria-label", `Recolher ${adaptador.rotulo(no)}`);
    linha.appendChild(botaoToggle);
  } else {
    linha.appendChild(criar(doc, "span", "no__toggle no__toggle--folha", "•"));
  }

  const papel = adaptador.papel(no);
  const botao = criar(doc, "button", "no__rotulo");
  botao.type = "button";
  if (papel) botao.appendChild(criar(doc, "span", "no__papel", `${papel}: `));
  botao.appendChild(criar(doc, "span", "no__nome", adaptador.rotulo(no)));
  botao.addEventListener("click", () => ctx.aoSelecionar(no, botao));
  linha.appendChild(botao);
  li.appendChild(linha);

  if (filhos.length > 0) {
    const ul = criar(doc, "ul", "no__filhos");
    ul.setAttribute("role", "group");
    for (const f of filhos) ul.appendChild(montarNo(doc, f, adaptador, ctx, nivel + 1));
    li.appendChild(ul);
    botaoToggle.addEventListener("click", () => alternar(li, botaoToggle, ul));
  }
  li.__no = no;
  return li;
}

function alternar(li, botao, ul, abrir) {
  const abrirAgora = abrir ?? ul.hidden;
  ul.hidden = !abrirAgora;
  botao.textContent = abrirAgora ? "−" : "+";
  botao.setAttribute("aria-expanded", String(abrirAgora));
  const nome = li.querySelector(".no__nome")?.textContent ?? "nó";
  botao.setAttribute("aria-label", `${abrirAgora ? "Recolher" : "Expandir"} ${nome}`);
}

function expandirTudo(raiz, abrir) {
  for (const li of raiz.querySelectorAll("li.no")) {
    const botao = li.querySelector(":scope > .no__linha > button.no__toggle");
    const ul = li.querySelector(":scope > ul.no__filhos");
    if (botao && ul) alternar(li, botao, ul, abrir);
  }
}

const ADAPTADOR_AST = {
  rotulo: rotuloDoNo,
  filhos: (n) => n.filhos ?? [],
  papel: (n) => n.papel,
  tipo: (n) => n.tipo,
};

const ADAPTADOR_DERIVACAO = {
  rotulo: (n) => (n.terminal ? `${n.lexema === "" ? n.simbolo : n.lexema}  (${n.tipo})` : n.simbolo),
  filhos: (n) => n.filhos ?? [],
  papel: () => null,
  tipo: (n) => (n.terminal ? "terminal" : n.simbolo),
};

// ------------------------------------------------------------- explicação
function explicacao(doc) {
  const d = criar(doc, "details", "ajuda ajuda--sintatica");
  d.id = "ajuda-sintatica";
  d.appendChild(criar(doc, "summary", null, "O que é análise sintática? E uma AST?"));
  const corpo = criar(doc, "div", "ajuda__corpo");
  const p = (t) => corpo.appendChild(criar(doc, "p", null, t));
  p(
    "O parser (analisador sintático) recebe a sequência de tokens do scanner e verifica se ela " +
      "obedece à gramática da linguagem. Se obedece, ele constrói uma árvore; se não, aponta onde a estrutura quebrou."
  );
  const ul = criar(doc, "ul");
  for (const t of [
    "Sequência de tokens: uma lista plana, sem estrutura (saída do scanner).",
    "Árvore de derivação (concreta): mostra cada regra da gramática aplicada, inclusive os símbolos auxiliares (soma, termo, unário...) e os dois-pontos, NEWLINE, INDENT e DEDENT.",
    "AST (árvore sintática abstrata): guarda só o que tem significado. Parênteses somem, porque a própria forma da árvore já mostra a ordem das operações.",
  ]) ul.appendChild(criar(doc, "li", null, t));
  corpo.appendChild(ul);
  p("Clique em um nó para ver a regra da gramática que o gerou e o trecho do código correspondente.");
  d.appendChild(corpo);
  return d;
}

// ---------------------------------------------------------------- principal
/**
 * Desenha a seção de análise sintática e a devolve (o chamador a insere).
 * @param {Document} doc
 * @param {object} sintatico  campo "sintatico" da resposta do backend
 * @param {string} codigo     código analisado (para o realce)
 * @param {object} [opcoes]   { baixar(nome, texto) } para testes
 */
export function criarSecaoSintatica(doc, sintatico, codigo, opcoes = {}) {
  const sec = criar(doc, "section", "bloco bloco--sintatico");
  sec.id = "sec-sintatico";
  sec.appendChild(criar(doc, "h3", "bloco__titulo", "Análise sintática (parser)"));

  const erros = Array.isArray(sintatico.erros) ? sintatico.erros : [];

  // ------------------------------------------------------ não executada
  if (sintatico.executado === false) {
    sec.classList.add("bloco--aviso");
    sec.appendChild(
      criar(doc, "p", "resultado__titulo", "Análise sintática não executada")
    );
    sec.appendChild(
      criar(
        doc,
        "p",
        null,
        sintatico.mensagem ??
          "A análise sintática não foi executada porque há erros léxicos. Corrija-os primeiro."
      )
    );
    sec.appendChild(
      criar(
        doc,
        "p",
        "nota",
        "Por que não? O parser só entende uma sequência de tokens válida; com erros léxicos ele geraria mensagens enganosas. Os erros léxicos continuam listados acima."
      )
    );
    return sec;
  }

  // --------------------------------------------------------------- erros
  if (!sintatico.sucesso) {
    sec.classList.add("bloco--erro");
    sec.appendChild(criar(doc, "p", "resultado__titulo", sintatico.mensagem ?? "Erros sintáticos."));
    const ul = criar(doc, "ul", "lista-erros");
    for (const e of erros) ul.appendChild(itemDeErro(doc, e));
    sec.appendChild(ul);
    const omitidos = sintatico.resumo?.erros_omitidos ?? 0;
    if (omitidos > 0) {
      sec.appendChild(
        criar(doc, "p", "nota", `Mostrando os ${erros.length} primeiros erros; outros ${omitidos} não foram listados.`)
      );
    }
    sec.appendChild(
      criar(
        doc,
        "p",
        "nota",
        "Como o parser se recupera: depois de um erro ele descarta o resto da linha (e o bloco que dependia dela) e continua, para mostrar vários problemas de uma vez. Corrija sempre o primeiro: os seguintes podem ser consequência dele. Sem uma estrutura válida, não há AST."
      )
    );
    sec.appendChild(explicacao(doc));
    return sec;
  }

  // ------------------------------------------------------------- sucesso
  sec.classList.add("bloco--sucesso");
  const ast = sintatico.ast;
  const resumo = sintatico.resumo ?? {};
  sec.appendChild(criar(doc, "p", "resultado__titulo", sintatico.mensagem ?? "Análise sintática concluída."));
  sec.appendChild(
    criar(doc, "p", "resumo__numeros", `${resumo.total_nos ?? "?"} nós · altura ${resumo.altura ?? "?"}`)
  );
  if (!ast.filhos || ast.filhos.length === 0) {
    sec.appendChild(
      criar(doc, "p", "nota", "O programa não tem comandos (só comentários ou linhas em branco): a AST é um Programa vazio.")
    );
  }
  sec.appendChild(explicacao(doc));

  // --------------------------------------------------------------- barra
  const barra = criar(doc, "div", "barra-arvore");
  const bExp = criar(doc, "button", "botao botao--secundario", "Expandir tudo");
  const bRec = criar(doc, "button", "botao botao--secundario", "Recolher tudo");
  const bJson = criar(doc, "button", "botao botao--secundario", "Exportar AST em JSON");
  for (const b of [bExp, bRec, bJson]) b.type = "button";
  bExp.id = "btn-expandir";
  bRec.id = "btn-recolher";
  bJson.id = "btn-exportar-json";
  const rotuloFiltro = criar(doc, "label", null, "Filtrar por tipo de nó");
  rotuloFiltro.htmlFor = "filtro-tipo";
  const filtro = criar(doc, "select");
  filtro.id = "filtro-tipo";
  const opTodos = criar(doc, "option", null, "Todos os tipos");
  opTodos.value = "";
  filtro.appendChild(opTodos);
  for (const t of tiposPresentes(ast)) {
    const o = criar(doc, "option", null, t);
    o.value = t;
    filtro.appendChild(o);
  }
  barra.append(bExp, bRec, rotuloFiltro, filtro, bJson);
  sec.appendChild(barra);
  const estadoFiltro = criar(doc, "p", "nota", "");
  estadoFiltro.id = "estado-filtro";
  estadoFiltro.setAttribute("aria-live", "polite");
  sec.appendChild(estadoFiltro);

  // ----------------------------------------------------- árvore + código
  const grade = criar(doc, "div", "grade-arvore");
  const colArvore = criar(doc, "div", "grade-arvore__arvore");
  const ulRaiz = criar(doc, "ul", "arvore");
  ulRaiz.id = "arvore-ast";
  ulRaiz.setAttribute("role", "tree");
  ulRaiz.setAttribute("aria-label", "Árvore sintática abstrata");
  colArvore.appendChild(ulRaiz);

  const colDetalhe = criar(doc, "div", "grade-arvore__detalhe");
  const painel = criar(doc, "div", "painel-no");
  painel.id = "painel-no";
  painel.setAttribute("aria-live", "polite");
  painel.appendChild(criar(doc, "p", "nota", "Clique em um nó para ver sua regra, posição e o trecho de código."));
  const pre = criar(doc, "pre", "codigo-no");
  pre.id = "codigo-no";
  pre.setAttribute("aria-label", "Código com o trecho do nó selecionado destacado");
  pre.textContent = codigo;
  colDetalhe.append(painel, pre);
  grade.append(colArvore, colDetalhe);
  sec.appendChild(grade);

  let selecionado = null;
  function aoSelecionar(no, botao) {
    selecionado?.classList.remove("no__rotulo--selecionado");
    selecionado = botao;
    botao.classList.add("no__rotulo--selecionado");
    botao.setAttribute("aria-current", "true");

    painel.replaceChildren();
    painel.appendChild(criar(doc, "p", "painel-no__titulo", `Nó selecionado: ${rotuloDoNo(no)}`));
    const dl = criar(doc, "dl", "detalhes-erro");
    const linha = (r, v) => {
      dl.appendChild(criar(doc, "dt", null, r));
      dl.appendChild(criar(doc, "dd", null, v));
    };
    linha("Tipo", no.tipo);
    if (no.papel) linha("Papel no nó pai", no.papel);
    linha("Regra da gramática", no.regra ?? "");
    linha("Posição", posicaoDoNo(no));
    const attrs = Object.entries(no.atributos ?? {})
      .map(([k, v]) => `${k} = ${v}`)
      .join(", ");
    if (attrs) linha("Atributos", attrs);
    linha("Filhos", String(no.filhos?.length ?? 0));
    painel.appendChild(dl);

    const [antes, trecho, depois] = trechoDoNo(codigo, no);
    pre.replaceChildren();
    pre.appendChild(doc.createTextNode(antes));
    const marca = criar(doc, "mark", "trecho-no", trecho);
    pre.appendChild(marca);
    pre.appendChild(doc.createTextNode(depois));
  }

  const ctx = { aoSelecionar };
  ulRaiz.appendChild(montarNo(doc, ast, ADAPTADOR_AST, ctx, 0));

  bExp.addEventListener("click", () => expandirTudo(ulRaiz, true));
  bRec.addEventListener("click", () => expandirTudo(ulRaiz, false));

  filtro.addEventListener("change", () => {
    const tipo = filtro.value;
    for (const li of ulRaiz.querySelectorAll("li.no")) {
      li.classList.remove("no--filtrado");
      li.querySelector(":scope > .no__linha .marca-filtro")?.remove();
    }
    if (!tipo) {
      estadoFiltro.textContent = "";
      return;
    }
    expandirTudo(ulRaiz, true);
    const achados = [...ulRaiz.querySelectorAll("li.no")].filter((li) => li.dataset.tipo === tipo);
    for (const li of achados) {
      li.classList.add("no--filtrado");
      li.querySelector(":scope > .no__linha").appendChild(criar(doc, "span", "marca-filtro", " ◀ filtro"));
    }
    estadoFiltro.textContent = `${achados.length} ${achados.length === 1 ? "nó encontrado" : "nós encontrados"} do tipo ${tipo}.`;
  });

  bJson.addEventListener("click", () => {
    const texto = jsonDaAst(ast);
    if (opcoes.baixar) return opcoes.baixar("ast.json", texto);
    try {
      const url = URL.createObjectURL(new Blob([texto], { type: "application/json" }));
      const a = criar(doc, "a");
      a.href = url;
      a.download = "ast.json";
      doc.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      /* sem suporte a download: o JSON continua visível abaixo */
    }
  });

  // ------------------------------------------- visões alternativas (texto)
  const dTexto = criar(doc, "details", "alternativa");
  dTexto.id = "ast-texto";
  dTexto.appendChild(criar(doc, "summary", null, "AST em texto indentado"));
  dTexto.appendChild(criar(doc, "pre", "bloco-texto", arvoreEmTexto(ast)));
  sec.appendChild(dTexto);

  const dJson = criar(doc, "details", "alternativa");
  dJson.id = "ast-json";
  dJson.appendChild(criar(doc, "summary", null, "AST em JSON (tipo, linha, coluna, atributos, filhos)"));
  dJson.appendChild(criar(doc, "pre", "bloco-texto", jsonDaAst(ast)));
  sec.appendChild(dJson);

  if (sintatico.derivacao) {
    const dDer = criar(doc, "details", "alternativa");
    dDer.id = "derivacao";
    dDer.appendChild(
      criar(doc, "summary", null, "Árvore de derivação (concreta): compare com a AST acima")
    );
    dDer.appendChild(
      criar(
        doc,
        "p",
        "nota",
        "Aqui aparece cada regra aplicada (programa, comando, expressao, soma, termo, unario, primario...) e os tokens como folhas, na ordem do código. Note como ela é bem maior que a AST."
      )
    );
    const ulDer = criar(doc, "ul", "arvore");
    ulDer.setAttribute("role", "tree");
    ulDer.setAttribute("aria-label", "Árvore de derivação");
    ulDer.appendChild(montarNo(doc, sintatico.derivacao, ADAPTADOR_DERIVACAO, { aoSelecionar() {} }, 0));
    dDer.appendChild(ulDer);
    sec.appendChild(dDer);
  }

  return sec;
}

/** Insere a seção sintática dentro do resultado já desenhado pelo léxico. */
export function renderizarSintatico(doc, raiz, dados, codigo, opcoes = {}) {
  if (!dados || typeof dados.sintatico !== "object" || dados.sintatico === null) return null;
  const sec = criarSecaoSintatica(doc, dados.sintatico, codigo, opcoes);
  const referencia = raiz.querySelector("#sec-contagem");
  if (referencia) raiz.insertBefore(sec, referencia);
  else raiz.appendChild(sec);
  return sec;
}
