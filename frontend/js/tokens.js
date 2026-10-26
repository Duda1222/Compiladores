// Catálogo das categorias de token e funções puras de apoio à visualização.
// Nada aqui mexe no DOM: tudo pode ser testado sem navegador.

/**
 * Para cada tipo de token: rótulo curto, classe CSS (cor) e uma explicação
 * em linguagem de estudante da regra que o scanner usou para reconhecê-lo.
 */
export const CATEGORIAS = {
  PALAVRA_RESERVADA: { rotulo: "Palavra reservada", classe: "t-reservada" },
  IDENTIFICADOR: { rotulo: "Identificador", classe: "t-identificador" },
  LITERAL_INTEIRO: { rotulo: "Literal inteiro", classe: "t-inteiro" },
  LITERAL_DECIMAL: { rotulo: "Literal decimal", classe: "t-decimal" },
  OPERADOR_ARITMETICO: { rotulo: "Operador aritmético", classe: "t-aritmetico" },
  OPERADOR_RELACIONAL: { rotulo: "Operador relacional", classe: "t-relacional" },
  OPERADOR_ATRIBUICAO: { rotulo: "Operador de atribuição", classe: "t-atribuicao" },
  DELIMITADOR: { rotulo: "Delimitador", classe: "t-delimitador" },
  NEWLINE: { rotulo: "Fim de linha", classe: "t-estrutural" },
  INDENT: { rotulo: "Indentação (abre bloco)", classe: "t-estrutural" },
  DEDENT: { rotulo: "Dedentação (fecha bloco)", classe: "t-estrutural" },
  FIM_DE_ARQUIVO: { rotulo: "Fim do arquivo", classe: "t-estrutural" },
};

export const ORDEM_TIPOS = Object.keys(CATEGORIAS);

export function classeDoTipo(tipo) {
  return CATEGORIAS[tipo]?.classe ?? "t-estrutural";
}

export function rotuloDoTipo(tipo) {
  return CATEGORIAS[tipo]?.rotulo ?? tipo;
}

/** Símbolo visível para tokens cujo lexema é invisível (quebra, indentação...). */
export function simboloEstrutural(token) {
  switch (token.tipo) {
    case "NEWLINE":
      return "↵";
    case "INDENT":
      return "→";
    case "DEDENT":
      return "←";
    case "FIM_DE_ARQUIVO":
      return "∎";
    default:
      return null;
  }
}

/** Texto a mostrar para o lexema de um token (usa símbolos quando preciso). */
export function lexemaVisivel(token) {
  return simboloEstrutural(token) ?? token.lexema;
}

const DELIMITADORES = {
  "(": "Abre parênteses: agrupa uma expressão e muda a ordem de avaliação.",
  ")": "Fecha parênteses: termina o agrupamento aberto por «(».",
  ":": "Dois-pontos: termina o cabeçalho de if, else ou while e anuncia o bloco indentado.",
};

/**
 * Explica, em uma ou duas frases, por que o scanner classificou o lexema
 * daquela forma. Serve ao modo "passo a passo".
 */
export function explicarToken(token) {
  const lex = token.lexema;
  switch (token.tipo) {
    case "PALAVRA_RESERVADA":
      return `«${lex}» está na lista de palavras reservadas: a linguagem já lhe deu um significado fixo, por isso ela não pode ser usada como nome de variável.`;
    case "IDENTIFICADOR":
      return `Começou com letra ou «_» e continuou com letras, dígitos ou «_». «${lex}» não está na lista de palavras reservadas, então é um identificador (nome definido pelo programador).`;
    case "LITERAL_INTEIRO":
      return `Sequência só de dígitos, sem ponto: é o número inteiro ${lex}.`;
    case "LITERAL_DECIMAL":
      return `Dígitos, um ponto e mais dígitos: é o número decimal ${lex}.`;
    case "OPERADOR_ARITMETICO":
      return `Operador aritmético «${lex}»: calcula um novo valor a partir de dois operandos.`;
    case "OPERADOR_RELACIONAL":
      return lex.length === 2
        ? `O scanner olhou também o caractere seguinte: juntos formam «${lex}». O scanner sempre escolhe o lexema mais longo possível.`
        : `Operador relacional «${lex}»: compara dois valores e resulta em verdadeiro ou falso.`;
    case "OPERADOR_ATRIBUICAO":
      return "Um «=» sozinho guarda um valor em uma variável. Para comparar valores, use «==».";
    case "DELIMITADOR":
      return DELIMITADORES[lex] ?? `Delimitador «${lex}».`;
    case "NEWLINE":
      return lex === ""
        ? "O arquivo terminou sem quebra de linha; o scanner cria o NEWLINE para fechar o comando."
        : "Em Python a quebra de linha termina o comando; por isso ela vira um token (NEWLINE).";
    case "INDENT":
      return `A linha começa mais à direita que a anterior (${lex.length} espaço${lex.length === 1 ? "" : "s"}): abre um bloco. O scanner guarda os níveis de indentação em uma pilha.`;
    case "DEDENT":
      return "A indentação voltou a um nível anterior da pilha: fecha um bloco. Pode haver vários DEDENT seguidos.";
    case "FIM_DE_ARQUIVO":
      return "Acabaram os caracteres do programa.";
    default:
      return "";
  }
}

// ------------------------------------------------------------------ posições
/** Mesma normalização de quebras de linha que o backend aplica. */
export function normalizarQuebras(codigo) {
  return codigo.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

/** Converte (linha, coluna), ambas começando em 1, em índice no texto. */
export function deslocamento(inicios, tamanho, linha, coluna) {
  if (linha - 1 >= inicios.length) return tamanho;
  return Math.min(inicios[linha - 1] + coluna - 1, tamanho);
}

/**
 * Divide o código em segmentos para o realce.
 *   { tipo: "texto", texto }
 *   { tipo: "token", indice, texto, token, marcador?: true }
 *   { tipo: "erro", indice, texto, erro }
 * Os segmentos, concatenados, reproduzem o código original (os marcadores de
 * tokens sem texto, como DEDENT e FIM, são extras inseridos na posição).
 *
 * @param {string} codigo   código enviado pelo usuário
 * @param {Array}  tokens   lista de tokens do backend
 * @param {Array}  erros    lista de erros léxicos do backend
 */
export function montarSegmentos(codigo, tokens, erros = []) {
  const texto = normalizarQuebras(codigo);
  const inicios = [0];
  for (let i = 0; i < texto.length; i++) {
    if (texto[i] === "\n") inicios.push(i + 1);
  }

  const eventos = [];
  tokens.forEach((token, indice) => {
    const ini = deslocamento(inicios, texto.length, token.linha, token.coluna);
    eventos.push({ ini, fim: ini + token.lexema.length, ordem: indice, token, indice });
  });
  erros.forEach((erro, k) => {
    const ini = deslocamento(inicios, texto.length, erro.linha, erro.coluna);
    eventos.push({ ini, fim: ini + erro.lexema.length, ordem: 1e9 + k, erro });
  });
  eventos.sort((a, b) => a.ini - b.ini || a.ordem - b.ordem);

  const segmentos = [];
  let cursor = 0;
  let ultimoTexto = null; // último segmento com texto real (para marcar erros sobrepostos)

  for (const ev of eventos) {
    let { ini, fim } = ev;
    const ehMarcador = ev.token && ev.token.lexema === "";
    if (ehMarcador) {
      if (ini > cursor) {
        segmentos.push({ tipo: "texto", texto: texto.slice(cursor, ini) });
        cursor = ini;
      }
      segmentos.push({
        tipo: "token",
        indice: ev.indice,
        texto: simboloEstrutural(ev.token) ?? "",
        token: ev.token,
        marcador: true,
      });
      continue;
    }
    if (ini < cursor) {
      // Sobreposição (ex.: erro de tabulação que também é o INDENT).
      if (fim <= cursor) {
        if (ev.erro && ultimoTexto) ultimoTexto.comErro = ev.erro;
        continue;
      }
      ini = cursor;
    }
    if (ini > cursor) {
      segmentos.push({ tipo: "texto", texto: texto.slice(cursor, ini) });
    }
    const trecho = texto.slice(ini, fim);
    let seg;
    if (ev.erro) {
      seg = { tipo: "erro", texto: trecho, erro: ev.erro };
    } else if (ev.token.tipo === "NEWLINE") {
      seg = { tipo: "token", indice: ev.indice, texto: "↵", token: ev.token, quebra: true };
    } else {
      seg = { tipo: "token", indice: ev.indice, texto: trecho, token: ev.token };
    }
    segmentos.push(seg);
    ultimoTexto = seg;
    cursor = fim;
  }
  if (cursor < texto.length) {
    segmentos.push({ tipo: "texto", texto: texto.slice(cursor) });
  }
  return segmentos;
}

/** Mensagem completa para o usuário, com localização. */
export function mensagemDeErro(erro) {
  return `Erro léxico na linha ${erro.linha}, coluna ${erro.coluna}: ${erro.mensagem}`;
}
