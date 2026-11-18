# Tutorial: como o scanner enxerga o seu código

Guia inicial para estudantes que usam o Compilador Educacional pela primeira vez. Dura cerca de 10 minutos.

## 1. A ideia

Um compilador não lê o programa "de uma vez". A primeira fase, o **scanner** (analisador léxico), percorre o texto caractere por caractere e o separa em pedaços com significado:

- **Lexema** é o trecho exato do texto: `while`, `x`, `3.14`, `==`.
- **Token** é o lexema já classificado: `3.14` → `LITERAL_DECIMAL`, linha 2, coluna 5.

Analogia: separar uma frase em palavras e dizer se cada uma é substantivo, verbo, pontuação...

## 2. Primeira análise

1. Abra `http://localhost:8080`.
2. Em **Exemplos**, escolha *1. Atribuição e literais* e clique em **Analisar código**.
3. Leia, de cima para baixo: o resumo, a contagem por categoria e o código colorido. Cada cor é uma categoria (e o sublinhado também muda, para quem não distingue cores).
4. Confira a **Tabela de tokens**: `x` é `IDENTIFICADOR`, `=` é `OPERADOR_ATRIBUICAO`, `10` é `LITERAL_INTEIRO`.

## 3. Passo a passo

Na seção **Passo a passo do scanner**, clique em **Próximo ▶**. A cada clique o scanner "lê" um token: ele é destacado no código, na sequência e na tabela, e um quadro explica **por que** ele foi classificado assim. O que ainda não foi lido fica esmaecido. **Reproduzir** faz isso sozinho; **Mostrar tudo** volta à visão completa.

## 4. A indentação do Python também é lida

Escolha *3. Estrutura condicional* e analise. Repare nos tokens que não existem "no texto":

| Símbolo | Token | Significado |
| --- | --- | --- |
| ↵ | `NEWLINE` | o comando terminou |
| → | `INDENT` | a linha entrou mais para a direita: abre um bloco |
| ← | `DEDENT` | voltou para um nível anterior: fecha um bloco |
| ∎ | `FIM_DE_ARQUIVO` | acabou o programa |

Em Python esses tokens são o que torna possível escrever blocos sem chaves.

## 5. Provocando erros

Escolha *9. Com erros léxicos* e analise. O scanner **não para no primeiro erro**: mostra todos, com linha e coluna, e continua tokenizando o resto.

Experimente também:

| Digite | O que acontece |
| --- | --- |
| `x = 5 @ 2` | caractere `@` não reconhecido |
| `y = 3.14.15` | literal com dois pontos |
| `z = 007` | zeros à esquerda não são permitidos |
| `a = 12abc` | número seguido de letras |
| `a ! b` | `!` sozinho (o scanner sugere `!=`) |
| `x = = 3 +` | **sem erro léxico**: os tokens são válidos. Quem reclamará é o parser (Etapa 4) |

## 6. Desafios

1. Qual a diferença de token entre `=` e `==`? Digite `a == b` e `a = b` e compare.
2. Escreva `iff = 1`. Por que `iff` não é palavra reservada?
3. Quantos `DEDENT` aparecem ao fechar dois blocos aninhados de uma vez? (Exemplo 8.)
4. O que muda na tabela ao colocar `# comentário` no fim de uma linha?

## Próximo passo: o parser e a AST (Etapa 4)

O scanner só entende **palavras**. Quem confere a **frase** é o **parser** (analisador sintático): ele verifica se os tokens formam um programa válido segundo a gramática ([`gramatica.md`](gramatica.md)) e monta uma árvore, a **AST**.

1. Escolha o exemplo *10. Precedência e associatividade (AST)* e clique em **Analisar código**.
2. Na seção **Análise sintática**, clique no nó `OperacaoBinaria +` da primeira linha: o painel mostra a regra da gramática, a posição e **o trecho do código** (`10 + 5 * 2`) destacado.
3. Repare que o `*` está **mais fundo** que o `+`: é assim que a árvore diz "multiplique primeiro". Em `c = (10 + 5) * 2` os parênteses mudam a árvore e **somem** dela.
4. Abra **Árvore de derivação** e compare: ela mostra todas as regras usadas (soma, termo, unário...), por isso é bem maior que a AST.
5. Escolha o exemplo *11. Com erros sintáticos*. Cada erro traz linha, coluna, o que foi encontrado, o que era esperado e a regra violada. **Corrija sempre o primeiro**: os seguintes podem ser consequência dele.
6. No exemplo *9. Com erros léxicos* o parser **não roda**, pois a lista de tokens está incompleta. Corrija os erros léxicos primeiro.
