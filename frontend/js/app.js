// Ligação entre a interface (DOM) e os módulos de validação, exemplos e API.

import { EXEMPLOS, buscarExemplo } from "./exemplos.js";
import { validarEntrada } from "./validacao.js";
import { enviarCodigo } from "./api.js";
import { renderizarLexico } from "./resultado.js";

const MSG_PLACEHOLDER = "Os resultados da análise aparecerão aqui.";

/**
 * Inicializa a tela. Recebe o documento e, opcionalmente, opções de envio
 * (fetchFn, url, timeoutMs), o que permite testar sem um servidor real.
 */
export function iniciar(doc = document, opcoes = {}) {
  const el = {
    codigo: doc.getElementById("codigo"),
    exemplos: doc.getElementById("exemplos"),
    descricao: doc.getElementById("descricao-exemplo"),
    analisar: doc.getElementById("btn-analisar"),
    limpar: doc.getElementById("btn-limpar"),
    resultado: doc.getElementById("resultado-conteudo"),
  };

  // Preenche o seletor de exemplos.
  for (const ex of EXEMPLOS) {
    const op = doc.createElement("option");
    op.value = ex.id;
    op.textContent = ex.titulo;
    el.exemplos.appendChild(op);
  }

  // Controle do passo a passo da análise exibida (para parar a reprodução
  // automática quando a tela é substituída por outro resultado).
  let controlePasso = null;

  function mostrar(tipo, titulo, linhas = []) {
    controlePasso?.parar();
    controlePasso = null;
    el.resultado.className = `resultado resultado--${tipo}`;
    el.resultado.replaceChildren();
    const h = doc.createElement("p");
    h.className = "resultado__titulo";
    h.textContent = titulo;
    el.resultado.appendChild(h);
    for (const texto of linhas) {
      const p = doc.createElement("p");
      p.textContent = texto;
      el.resultado.appendChild(p);
    }
  }

  function mostrarPlaceholder() {
    controlePasso?.parar();
    controlePasso = null;
    el.resultado.className = "resultado resultado--vazio";
    el.resultado.replaceChildren();
    const p = doc.createElement("p");
    p.textContent = MSG_PLACEHOLDER;
    el.resultado.appendChild(p);
  }

  function aoSelecionarExemplo() {
    const ex = buscarExemplo(el.exemplos.value);
    if (!ex) {
      el.descricao.textContent = "";
      return;
    }
    el.codigo.value = ex.codigo;
    el.descricao.textContent = `Demonstra: ${ex.demonstra}`;
    mostrarPlaceholder();
    el.codigo.focus();
  }

  function aoLimpar() {
    el.codigo.value = "";
    el.exemplos.value = "";
    el.descricao.textContent = "";
    mostrarPlaceholder();
    el.codigo.focus();
  }

  async function aoAnalisar() {
    const codigo = el.codigo.value;

    const validacao = validarEntrada(codigo);
    if (!validacao.ok) {
      mostrar("erro-entrada", "Entrada inválida", [validacao.mensagem]);
      return;
    }

    el.analisar.disabled = true;
    mostrar("carregando", "Enviando código ao servidor…");
    try {
      const r = await enviarCodigo(codigo, opcoes);
      if (r.tipo === "sucesso") {
        controlePasso?.parar();
        controlePasso = renderizarLexico(doc, el.resultado, r.dados, codigo, opcoes);
      } else if (r.tipo === "entrada") {
        mostrar("erro-entrada", "Entrada inválida", [r.mensagem]);
      } else if (r.tipo === "comunicacao") {
        mostrar("erro-comunicacao", "Falha de comunicação", [r.mensagem]);
      } else {
        mostrar("erro-inesperado", "Erro inesperado", [r.mensagem]);
      }
    } catch {
      mostrar("erro-inesperado", "Erro inesperado", [
        "Ocorreu um erro inesperado. Tente novamente em instantes.",
      ]);
    } finally {
      el.analisar.disabled = false;
    }
  }

  el.exemplos.addEventListener("change", aoSelecionarExemplo);
  el.analisar.addEventListener("click", aoAnalisar);
  el.limpar.addEventListener("click", aoLimpar);

  mostrarPlaceholder();
  return { aoAnalisar, aoSelecionarExemplo, aoLimpar };
}

// No navegador, inicia automaticamente quando a página carrega.
if (typeof document !== "undefined" && document.getElementById("btn-analisar")) {
  iniciar(document);
}
