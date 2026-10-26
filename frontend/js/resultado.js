// Apresentação didática do resultado da análise léxica.
//
// Monta, só com a API do DOM (nunca innerHTML), as seções:
//   resumo · erros · avisos · contagem por categoria · código com tokens
//   destacados · passo a passo · sequência de tokens · tabela de tokens.

import {
  ORDEM_TIPOS,
  classeDoTipo,
  explicarToken,
  lexemaVisivel,
  mensagemDeErro,
  montarSegmentos,
  rotuloDoTipo,
  simboloEstrutural,
} from "./tokens.js";

const INTERVALO_REPRODUCAO_MS = 900;

function criar(doc, tag, classe, texto) {
  const el = doc.createElement(tag);
  if (classe) el.className = classe;
  if (texto !== undefined) el.textContent = texto;
  return el;
}

function secao(doc, titulo, id) {
  const s = criar(doc, "section", "bloco");
  if (id) s.id = id;
  const h = criar(doc, "h3", "bloco__titulo", titulo);
  s.appendChild(h);
  return s;
}

function pluralizar(n, singular, plural) {
  return `${n} ${n === 1 ? singular : plural}`;
}

/**
 * Desenha o resultado léxico dentro de ``raiz``.
 *
 * @param {Document} doc
 * @param {HTMLElement} raiz        contêiner (será esvaziado)
 * @param {object} dados            resposta do backend
 * @param {string} codigo           código analisado (para o realce)
 * @param {object} [opcoes]
 * @param {(fn:Function, ms:number)=>any} [opcoes.agendar]  substituto de setTimeout
 * @param {(id:any)=>void} [opcoes.cancelar]                substituto de clearTimeout
 * @returns controle do passo a passo (útil para testes)
 */
export function renderizarLexico(doc, raiz, dados, codigo, opcoes = {}) {
  const agendar = opcoes.agendar ?? ((fn, ms) => setTimeout(fn, ms));
  const cancelar = opcoes.cancelar ?? ((id) => clearTimeout(id));

  const tokens = Array.isArray(dados.tokens) ? dados.tokens : [];
  const erros = Array.isArray(dados.erros) ? dados.erros : [];
  const avisos = Array.isArray(dados.avisos) ? dados.avisos : [];
  const resumo = dados.resumo ?? {};
  const totalErros = resumo.total_erros ?? erros.length;

  raiz.className = `resultado ${dados.sucesso ? "resultado--sucesso" : "resultado--erro-lexico"}`;
  raiz.replaceChildren();

  // ------------------------------------------------------------- resumo
  const cab = criar(doc, "div", "resumo");
  cab.appendChild(criar(doc, "p", "resultado__titulo", dados.mensagem ?? "Análise léxica concluída."));
  cab.appendChild(
    criar(
      doc,
      "p",
      "resumo__numeros",
      `${pluralizar(tokens.length, "token", "tokens")} · ${pluralizar(totalErros, "erro léxico", "erros léxicos")}` +
        ` · ${pluralizar(dados.linhas ?? 0, "linha", "linhas")} · ${pluralizar(dados.caracteres ?? 0, "caractere", "caracteres")}`
    )
  );
  raiz.appendChild(cab);

  // -------------------------------------------------------------- erros
  if (erros.length > 0) {
    const s = secao(doc, "Erros léxicos", "sec-erros");
    s.classList.add("bloco--erro");
    const ul = criar(doc, "ul", "lista-erros");
    for (const e of erros) {
      const li = criar(doc, "li", "lista-erros__item");
      li.appendChild(criar(doc, "span", "posicao", `Linha ${e.linha}, coluna ${e.coluna}`));
      li.appendChild(criar(doc, "span", "lista-erros__msg", e.mensagem));
      li.setAttribute("aria-label", mensagemDeErro(e));
      ul.appendChild(li);
    }
    s.appendChild(ul);
    const omitidos = resumo.erros_omitidos ?? 0;
    if (omitidos > 0) {
      s.appendChild(
        criar(doc, "p", "nota", `Mostrando os ${erros.length} primeiros erros; outros ${omitidos} não foram listados.`)
      );
    }
    s.appendChild(
      criar(
        doc,
        "p",
        "nota",
        "O scanner não para no primeiro erro: ele pula o trecho inválido e continua, para você ver todos os problemas de uma vez."
      )
    );
    raiz.appendChild(s);
  }

  // ------------------------------------------------------------- avisos
  if (avisos.length > 0) {
    const s = secao(doc, "Avisos", "sec-avisos");
    s.classList.add("bloco--aviso");
    const ul = criar(doc, "ul", "lista-erros");
    for (const a of avisos) {
      const li = criar(doc, "li", "lista-erros__item");
      li.appendChild(criar(doc, "span", "posicao", `Linha ${a.linha}, coluna ${a.coluna}`));
      li.appendChild(criar(doc, "span", "lista-erros__msg", a.mensagem));
      ul.appendChild(li);
    }
    s.appendChild(ul);
    raiz.appendChild(s);
  }

  // ------------------------------------------------- contagem por categoria
  const porTipo = resumo.por_tipo ?? {};
  const sContagem = secao(doc, "Tokens por categoria", "sec-contagem");
  const legenda = criar(doc, "ul", "legenda");
  for (const tipo of ORDEM_TIPOS) {
    const n = porTipo[tipo] ?? 0;
    if (n === 0) continue;
    const li = criar(doc, "li", `chip ${classeDoTipo(tipo)}`);
    li.appendChild(criar(doc, "span", "chip__nome", tipo));
    li.appendChild(criar(doc, "span", "chip__n", `×${n}`));
    li.setAttribute("aria-label", `${rotuloDoTipo(tipo)}: ${pluralizar(n, "token", "tokens")}`);
    legenda.appendChild(li);
  }
  if (!legenda.children.length) {
    legenda.appendChild(criar(doc, "li", "nota", "Nenhum token."));
  }
  sContagem.appendChild(legenda);
  raiz.appendChild(sContagem);

  // ----------------------------------------------- código com tokens
  const sCodigo = secao(doc, "Código com tokens destacados", "sec-codigo");
  sCodigo.appendChild(
    criar(
      doc,
      "p",
      "nota",
      "Cada cor é uma categoria. Os símbolos ↵ → ← ∎ mostram tokens invisíveis: fim de linha, abre bloco, fecha bloco e fim do arquivo."
    )
  );
  const pre = criar(doc, "pre", "codigo-tokens");
  pre.setAttribute("aria-label", "Código-fonte com cada token destacado");
  const spansPorIndice = new Map();
  for (const seg of montarSegmentos(codigo, tokens, erros)) {
    if (seg.tipo === "texto") {
      pre.appendChild(doc.createTextNode(seg.texto));
      continue;
    }
    if (seg.tipo === "erro") {
      const span = criar(doc, "span", "tok erro-lexico", seg.texto);
      span.title = mensagemDeErro(seg.erro);
      pre.appendChild(span);
      continue;
    }
    const t = seg.token;
    const span = criar(doc, "span", `tok ${classeDoTipo(t.tipo)}`, seg.texto);
    if (seg.marcador || seg.quebra || simboloEstrutural(t)) span.classList.add("tok--simbolo");
    if (seg.comErro) span.classList.add("erro-lexico");
    span.title = `${t.tipo} · linha ${t.linha}, coluna ${t.coluna}`;
    spansPorIndice.set(seg.indice, span);
    pre.appendChild(span);
    if (seg.quebra) pre.appendChild(doc.createTextNode("\n"));
  }
  sCodigo.appendChild(pre);
  raiz.appendChild(sCodigo);

  // -------------------------------------------------------- passo a passo
  const sPasso = secao(doc, "Passo a passo do scanner", "sec-passo");
  sPasso.appendChild(
    criar(
      doc,
      "p",
      "nota",
      "Veja o scanner lendo o programa da esquerda para a direita, um token de cada vez. O trecho ainda não lido fica esmaecido."
    )
  );
  const controles = criar(doc, "div", "controles-passo");
  const btnAnterior = criar(doc, "button", "botao botao--secundario", "◀ Anterior");
  const btnProximo = criar(doc, "button", "botao", "Próximo ▶");
  const btnReproduzir = criar(doc, "button", "botao botao--secundario", "Reproduzir");
  const btnTudo = criar(doc, "button", "botao botao--secundario", "Mostrar tudo");
  for (const b of [btnAnterior, btnProximo, btnReproduzir, btnTudo]) b.type = "button";
  btnAnterior.id = "passo-anterior";
  btnProximo.id = "passo-proximo";
  btnReproduzir.id = "passo-reproduzir";
  btnTudo.id = "passo-tudo";
  controles.append(btnAnterior, btnProximo, btnReproduzir, btnTudo);
  sPasso.appendChild(controles);

  const painel = criar(doc, "div", "painel-passo");
  painel.setAttribute("aria-live", "polite");
  sPasso.appendChild(painel);
  raiz.appendChild(sPasso);

  // ------------------------------------------------ sequência de tokens
  const sSeq = secao(doc, "Sequência de tokens", "sec-sequencia");
  sSeq.appendChild(
    criar(doc, "p", "nota", "É o que o scanner entrega ao parser: o código original vira esta lista de peças.")
  );
  const seq = criar(doc, "ol", "sequencia");
  const itensSeq = [];
  tokens.forEach((t, i) => {
    const li = criar(doc, "li", `peca ${classeDoTipo(t.tipo)}`);
    li.appendChild(criar(doc, "span", "peca__lexema", lexemaVisivel(t)));
    li.appendChild(criar(doc, "span", "peca__tipo", t.tipo));
    li.title = `Token ${i + 1}: ${t.tipo} · linha ${t.linha}, coluna ${t.coluna}`;
    seq.appendChild(li);
    itensSeq.push(li);
  });
  sSeq.appendChild(seq);
  raiz.appendChild(sSeq);

  // ------------------------------------------------------------- tabela
  const sTab = secao(doc, "Tabela de tokens", "sec-tabela");
  sTab.appendChild(
    criar(
      doc,
      "p",
      "nota",
      "Token é a peça classificada (tipo + lexema + posição). Lexema é o trecho exato do texto que forma o token."
    )
  );
  const envoltorio = criar(doc, "div", "tabela-rolavel");
  envoltorio.tabIndex = 0;
  envoltorio.setAttribute("role", "region");
  envoltorio.setAttribute("aria-label", "Tabela de tokens (role para os lados em telas pequenas)");
  const tabela = criar(doc, "table", "tabela-tokens");
  tabela.appendChild(criar(doc, "caption", "sr-only", `Tokens identificados: ${tokens.length}`));
  const cabeca = criar(doc, "thead");
  const trh = criar(doc, "tr");
  for (const nome of ["#", "Tipo", "Lexema", "Linha", "Coluna"]) {
    const th = criar(doc, "th", "", nome);
    th.scope = "col";
    trh.appendChild(th);
  }
  cabeca.appendChild(trh);
  tabela.appendChild(cabeca);
  const corpo = criar(doc, "tbody");
  const linhasTabela = [];
  tokens.forEach((t, i) => {
    const tr = criar(doc, "tr");
    tr.appendChild(criar(doc, "td", "num", String(i + 1)));
    const tdTipo = criar(doc, "td");
    tdTipo.appendChild(criar(doc, "span", `selo-tipo ${classeDoTipo(t.tipo)}`, t.tipo));
    tr.appendChild(tdTipo);
    const tdLex = criar(doc, "td");
    const code = criar(doc, "code", "", lexemaVisivel(t));
    tdLex.appendChild(code);
    if (simboloEstrutural(t)) {
      tdLex.appendChild(criar(doc, "span", "sr-only", ` (${rotuloDoTipo(t.tipo)})`));
    }
    tr.appendChild(tdLex);
    tr.appendChild(criar(doc, "td", "num", String(t.linha)));
    tr.appendChild(criar(doc, "td", "num", String(t.coluna)));
    corpo.appendChild(tr);
    linhasTabela.push(tr);
  });
  tabela.appendChild(corpo);
  envoltorio.appendChild(tabela);
  sTab.appendChild(envoltorio);
  raiz.appendChild(sTab);

  // ----------------------------------------------- lógica do passo a passo
  let passo = null; // null = mostrando tudo; número = índice do token atual
  let temporizador = null;
  let reproduzindo = false;

  function parar() {
    reproduzindo = false;
    if (temporizador !== null) cancelar(temporizador);
    temporizador = null;
    btnReproduzir.textContent = "Reproduzir";
  }

  function atualizar() {
    // realce no código, na sequência e na tabela
    tokens.forEach((_, i) => {
      const estado = passo === null ? "normal" : i < passo ? "lido" : i === passo ? "atual" : "futuro";
      const alvos = [spansPorIndice.get(i), itensSeq[i], linhasTabela[i]];
      for (const el of alvos) {
        if (!el) continue;
        el.classList.toggle("is-atual", estado === "atual");
        el.classList.toggle("is-futuro", estado === "futuro");
        if (estado === "atual") el.setAttribute("aria-current", "step");
        else el.removeAttribute("aria-current");
      }
    });

    painel.replaceChildren();
    if (passo === null) {
      painel.appendChild(
        criar(doc, "p", "nota", "Clique em «Próximo» para acompanhar o scanner token por token.")
      );
    } else {
      const t = tokens[passo];
      painel.appendChild(
        criar(doc, "p", "painel-passo__titulo", `Passo ${passo + 1} de ${tokens.length}`)
      );
      const linhaLex = criar(doc, "p");
      linhaLex.appendChild(doc.createTextNode("Lexema lido: "));
      linhaLex.appendChild(criar(doc, "code", "", lexemaVisivel(t)));
      linhaLex.appendChild(doc.createTextNode(` · linha ${t.linha}, coluna ${t.coluna}`));
      painel.appendChild(linhaLex);
      const linhaTipo = criar(doc, "p");
      linhaTipo.appendChild(doc.createTextNode("Classificado como "));
      linhaTipo.appendChild(criar(doc, "span", `selo-tipo ${classeDoTipo(t.tipo)}`, t.tipo));
      linhaTipo.appendChild(doc.createTextNode(` (${rotuloDoTipo(t.tipo)})`));
      painel.appendChild(linhaTipo);
      painel.appendChild(criar(doc, "p", "painel-passo__porque", `Por quê? ${explicarToken(t)}`));

      const alvo = spansPorIndice.get(passo);
      if (alvo && typeof alvo.scrollIntoView === "function") {
        alvo.scrollIntoView({ block: "nearest", inline: "nearest" });
      }
    }

    const n = tokens.length;
    btnAnterior.disabled = passo === null || passo === 0;
    btnProximo.disabled = n === 0 || (passo !== null && passo >= n - 1);
    btnTudo.disabled = passo === null;
    btnReproduzir.disabled = n === 0;
  }

  function proximo() {
    if (!tokens.length) return;
    if (passo === null) passo = 0;
    else if (passo < tokens.length - 1) passo += 1;
    else parar();
    atualizar();
  }

  function anterior() {
    if (passo === null || passo === 0) return;
    passo -= 1;
    atualizar();
  }

  function mostrarTudo() {
    parar();
    passo = null;
    atualizar();
  }

  function tique() {
    temporizador = null;
    if (!reproduzindo) return;
    if (passo !== null && passo >= tokens.length - 1) {
      parar();
      return;
    }
    proximo();
    if (reproduzindo && passo < tokens.length - 1) {
      temporizador = agendar(tique, INTERVALO_REPRODUCAO_MS);
    } else {
      parar();
    }
  }

  function alternarReproducao() {
    if (reproduzindo) {
      parar();
      return;
    }
    if (passo !== null && passo >= tokens.length - 1) passo = null; // recomeça
    reproduzindo = true;
    btnReproduzir.textContent = "Pausar";
    tique();
  }

  btnProximo.addEventListener("click", () => {
    parar();
    proximo();
  });
  btnAnterior.addEventListener("click", () => {
    parar();
    anterior();
  });
  btnReproduzir.addEventListener("click", alternarReproducao);
  btnTudo.addEventListener("click", mostrarTudo);

  atualizar();
  return { proximo, anterior, mostrarTudo, alternarReproducao, parar, get passo() { return passo; } };
}
