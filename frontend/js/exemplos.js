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
      "Tokens válidos, mas estrutura incorreta (expressão incompleta, parêntese sem fechar). O scanner tokeniza normalmente; o erro será apontado pelo parser na Etapa 4.",
    codigo: "x = 10 +\ny = (3 * 4\n",
  },
  {
    id: "operadores",
    titulo: "6. Todos os operadores",
    demonstra:
      "Operadores aritméticos, de atribuição e os seis relacionais (note que == e != têm dois caracteres).",
    codigo:
      "a = 1\nb = 2.5\nc = a + b - 1 * 2 / 4\nok = a == b\nok = a != b\nok = a < b\nok = a <= b\nok = a > b\nok = a >= b\n",
  },
  {
    id: "comentarios",
    titulo: "7. Comentários e linhas em branco",
    demonstra: "Comentários com # e linhas vazias são ignorados e não geram tokens.",
    codigo: "# calcula o dobro\nx = 4   # valor inicial\n\n\ndobro = x * 2\n",
  },
  {
    id: "blocos",
    titulo: "8. Blocos aninhados (INDENT/DEDENT)",
    demonstra:
      "while com if/else dentro: a indentação gera INDENT ao abrir e DEDENT ao fechar cada bloco.",
    codigo:
      "x = 6\nwhile x > 0:\n    if x > 3:\n        x = x - 2\n    else:\n        x = x - 1\n",
  },
  {
    id: "erros-lexicos",
    titulo: "9. Com erros léxicos",
    demonstra:
      "Caractere inválido (@), número malformado (3.14.15 e 12abc), string (ainda fora do subconjunto) e palavra reservada fora do subconjunto (def).",
    codigo:
      "preco = 10 @ 2\nvalor = 3.14.15\nnome = \"Ana\"\ny = 12abc\ndef f\n",
  },
];

export function buscarExemplo(id) {
  return EXEMPLOS.find((e) => e.id === id) ?? null;
}
