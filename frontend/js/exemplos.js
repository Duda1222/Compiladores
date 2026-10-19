// Exemplos de programas do subconjunto de Python definido na Etapa 1.
// Cada exemplo indica quais construções da linguagem ele pretende demonstrar.

export const EXEMPLOS = [
  {
    id: "atribuicao",
    titulo: "1. Atribuição e literais",
    demonstra: "Atribuição, identificadores, literais inteiros e decimais.",
    codigo: "x = 10\ny = 3.14\n",
  },
  {
    id: "aritmetica",
    titulo: "2. Expressões aritméticas",
    demonstra: "Operadores + - * /, parênteses e precedência.",
    codigo: "a = 10\nb = 5\nresultado = (a + b) * 2 - a / b\n",
  },
  {
    id: "condicional",
    titulo: "3. Estrutura condicional",
    demonstra: "if / else, operador relacional e indentação (INDENT/DEDENT).",
    codigo: "x = 7\nif x > 0:\n    x = x + 1\nelse:\n    x = x - 1\n",
  },
  {
    id: "repeticao",
    titulo: "4. Estrutura de repetição",
    demonstra: "while, operadores relacionais (>=, !=) e bloco indentado.",
    codigo: "x = 5\nwhile x != 0:\n    x = x - 1\n",
  },
  {
    id: "erro-intencional",
    titulo: "5. Com erro intencional",
    demonstra:
      "Expressão incompleta e parêntese sem fechar, para as etapas de análise futuras.",
    codigo: "x = 10 +\ny = (3 * 4\n",
  },
];

export function buscarExemplo(id) {
  return EXEMPLOS.find((e) => e.id === id) ?? null;
}
