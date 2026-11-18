# Gramática do subconjunto de Python (Etapa 4)

Documento de referência do parser (`backend/sintatico.py`). A gramática abaixo é exatamente a que o código implementa: cada símbolo não terminal é uma função do parser, e os testes automatizados cobrem cada regra.

## 1. Símbolo inicial, terminais e não terminais

- **Símbolo inicial:** `programa`
- **Terminais:** são as categorias de token da Etapa 3 (ver [`escopo-lexico.md`](escopo-lexico.md)). O parser não reimplementa o scanner: ele consome a lista de tokens que o scanner devolve.
- **Não terminais:** `programa`, `comando`, `comando_simples`, `atribuicao`, `condicional`, `repeticao`, `bloco`, `expressao`, `soma`, `termo`, `unario`, `primario`.

### Mapeamento terminal da gramática → categoria de token (Etapa 3)

| Terminal na gramática | Categoria do scanner | Lexemas |
| --- | --- | --- |
| `IDENTIFICADOR` | `IDENTIFICADOR` | `x`, `total_1` |
| `LITERAL_INTEIRO` | `LITERAL_INTEIRO` | `0`, `42` |
| `LITERAL_DECIMAL` | `LITERAL_DECIMAL` | `3.14` |
| `'if'`, `'else'`, `'while'` | `PALAVRA_RESERVADA` | `if`, `else`, `while` |
| `'='` | `OPERADOR_ATRIBUICAO` | `=` |
| `'+'` `'-'` `'*'` `'/'` | `OPERADOR_ARITMETICO` | `+ - * /` |
| `OPERADOR_RELACIONAL` | `OPERADOR_RELACIONAL` | `< > <= >= == !=` |
| `'('` `')'` `':'` | `DELIMITADOR` | `( ) :` |
| `NEWLINE`, `INDENT`, `DEDENT` | `NEWLINE`, `INDENT`, `DEDENT` | fim de linha, abre e fecha bloco |
| `FIM_DE_ARQUIVO` | `FIM_DE_ARQUIVO` | (vazio) |

Comentários e linhas em branco não geram token (decisão da Etapa 3), então a gramática não os menciona.

## 2. Produções (EBNF)

Notação: `{ x }` = zero ou mais; `[ x ]` = opcional; `( a | b )` = escolha; texto entre aspas = lexema literal; MAIÚSCULAS = categoria de token.

```ebnf
programa        = { comando } , FIM_DE_ARQUIVO ;

comando         = comando_simples
                | condicional
                | repeticao ;

comando_simples = ( atribuicao | expressao ) , NEWLINE ;
atribuicao      = IDENTIFICADOR , "=" , expressao ;

condicional     = "if" , expressao , ":" , bloco , [ "else" , ":" , bloco ] ;
repeticao       = "while" , expressao , ":" , bloco ;
bloco           = NEWLINE , INDENT , comando , { comando } , DEDENT ;

expressao       = soma , [ OPERADOR_RELACIONAL , soma ] ;
soma            = termo , { ( "+" | "-" ) , termo } ;
termo           = unario , { ( "*" | "/" ) , unario } ;
unario          = ( "+" | "-" ) , unario | primario ;
primario        = LITERAL_INTEIRO | LITERAL_DECIMAL | IDENTIFICADOR
                | "(" , expressao , ")" ;
```

Em BNF pura (sem `{ }` e `[ ]`), as repetições de `soma` e `termo` ficam à esquerda recursivas (`soma → soma '+' termo | termo`). O parser usa a forma EBNF com laço, equivalente e adequada à descida recursiva (a recursão à esquerda causaria laço infinito).

## 3. Precedência e associatividade

Da **menor** para a **maior** precedência (quanto mais fundo na gramática, mais forte o operador liga):

| Nível | Regra | Operadores | Associatividade |
| --- | --- | --- | --- |
| 1 (menor) | `expressao` | `< > <= >= == !=` | **não associativa**: no máximo um operador relacional por expressão |
| 2 | `soma` | `+` `-` | à esquerda |
| 3 | `termo` | `*` `/` | à esquerda |
| 4 | `unario` | `+` `-` (prefixos) | à direita (`- -x`) |
| 5 (maior) | `primario` | literais, identificadores, `( expressao )` | — |

Consequências, todas verificadas nos testes (inclusive contra o módulo `ast` do Python):

- `10 + 5 * 2` → `10 + (5 * 2)`;
- `20 - 5 - 3` → `(20 - 5) - 3`;
- `(10 + 5) * 2` → os parênteses mudam a árvore;
- `a + 1 > b * 2` → compara as duas somas;
- `a < b < c` **não** é aceito (em Python é válido, mas significa `a < b and b < c`; o subconjunto não tem `and`). O parser explica isso.

## 4. FIRST e FOLLOW (para a análise preditiva)

| Não terminal | FIRST | FOLLOW |
| --- | --- | --- |
| `primario` | `IDENTIFICADOR` `LITERAL_INTEIRO` `LITERAL_DECIMAL` `(` | `*` `/` `+` `-` `OPERADOR_RELACIONAL` `)` `:` `NEWLINE` |
| `unario` | `+` `-` `IDENTIFICADOR` `LITERAL_INTEIRO` `LITERAL_DECIMAL` `(` | `*` `/` `+` `-` `OPERADOR_RELACIONAL` `)` `:` `NEWLINE` |
| `termo` | igual a `unario` | `+` `-` `OPERADOR_RELACIONAL` `)` `:` `NEWLINE` |
| `soma` | igual a `unario` | `OPERADOR_RELACIONAL` `)` `:` `NEWLINE` |
| `expressao` | igual a `unario` | `)` `:` `NEWLINE` |
| `atribuicao` | `IDENTIFICADOR` | `NEWLINE` |
| `comando_simples` | `IDENTIFICADOR` `LITERAL_INTEIRO` `LITERAL_DECIMAL` `(` `+` `-` | FIRST de `comando` ∪ `DEDENT` `FIM_DE_ARQUIVO` |
| `condicional` | `if` | igual a `comando` |
| `repeticao` | `while` | igual a `comando` |
| `bloco` | `NEWLINE` | `else` e FOLLOW de `comando` |
| `comando` | FIRST de `comando_simples` ∪ `if` `while` | FIRST de `comando` ∪ `DEDENT` `FIM_DE_ARQUIVO` |

(`else` aparece no FOLLOW de `bloco`, e não no de `comando`, porque só pode vir logo depois do bloco do `if`, já fechado pelo `DEDENT`.)

## 5. Por que a gramática é (quase) LL(1)

Em cada ponto de decisão o próximo token escolhe a produção sem ambiguidade:

- `comando`: `if`, `while` ou início de expressão;
- laços de `soma`/`termo`: `+ -` ou `* /` continuam; qualquer outro token encerra;
- `condicional`: o `else` opcional é decidido por `else` no próximo token (o chamado *else pendente* se resolve pela **indentação**: o `else` pertence ao `if` do mesmo nível, porque o bloco interno terminou com `DEDENT` antes);
- `primario`: literal, identificador ou `(`.

**Única exceção, documentada:** `comando_simples` começa com `IDENTIFICADOR` tanto em `atribuicao` (`x = 1`) quanto em `expressao` (`x + 1`). O parser olha **dois tokens** (`IDENTIFICADOR` seguido de `=`) para decidir. Portanto, a gramática é LL(2) nesse único ponto; fatorando à esquerda (`IDENTIFICADOR ( "=" expressao | resto_da_expressao )`) viraria LL(1), mas ao custo de uma gramática menos legível para fins didáticos.

## 6. Construções suportadas e não suportadas

| Suportado | Não suportado nesta etapa (erro sintático ou léxico explicativo) |
| --- | --- |
| Atribuição simples `x = expr` | Atribuição encadeada `a = b = 1`, composta `+=` |
| Expressão como comando (`x + 1`) | Chamadas de função, `def`, `return`, `class`, `import` |
| `if` / `else` e `while` com bloco indentado | `elif`, `for`, `break`, `continue`, `pass` |
| Operadores `+ - * /` e prefixos `+ -` | `%`, `//`, `**`, operadores lógicos (`and`, `or`, `not`) |
| Seis operadores relacionais (uma comparação por expressão) | Comparações encadeadas `a < b < c` |
| Inteiros e decimais | Strings, listas, booleanos (`True`, `False`), `None` |
| Parênteses | Corpo do `if` na mesma linha (`if x: y = 1`) |

Palavras reservadas fora do subconjunto (`def`, `elif`, `True`...) são reconhecidas pelo scanner com um **aviso** e rejeitadas pelo parser com um erro explicativo. Funções, chamadas e `return` ficam como evolução futura (os nós `Funcao`, `ChamadaFuncao` e `Retorno`, citados no enunciado, **não existem** nesta AST porque a linguagem escolhida ainda não os tem).

## 7. Exemplos

### Programas válidos

```python
x = 10 + 5 * 2
```
```python
resultado = (10 + 5) * 2
```
```python
x = 7
while x > 0:
    if x > 3:
        x = x - 2
    else:
        x = x - 1
```
```python
# só comentário: programa vazio, também válido
```

### Programas inválidos (cada um é um teste automatizado)

| Código | Por que é inválido | Regra violada |
| --- | --- | --- |
| `x = 10 +` | falta o operando à direita de `+` | `soma → termo { ('+'\|'-') termo }` |
| `x = = 3` | dois operadores seguidos | `primario` |
| `y = (3 * 4` | parêntese não fechado | `primario → '(' expressao ')'` |
| `if x > 0` (sem `:`) | falta `:` no cabeçalho | `condicional` |
| `if x = 3:` | `=` (atribuição) onde se esperava comparação | `condicional` |
| `else:` sozinho | `else` sem `if` | `comando` |
| `if x:` + linha sem recuo | falta o bloco indentado | `bloco` |
| `x 5` | falta operador entre dois valores | `comando_simples` |
| `a = b = 1` | atribuição encadeada | `comando_simples` |
| `3 = x` | lado esquerdo não é identificador | `atribuicao` |
| `if = 3` | palavra reservada usada como variável | `atribuicao` |
| `def f` | palavra reservada fora do subconjunto | `comando` |

## 8. Coerência com o scanner

O parser só roda sobre tokens produzidos pelo scanner real, e há testes que garantem isso: as folhas da árvore de derivação reproduzem, uma a uma, a lista de tokens (tipo, lexema, linha e coluna). Entradas com erro léxico **não** chegam ao parser (ver [`sintatico.md`](sintatico.md), seção 4).
