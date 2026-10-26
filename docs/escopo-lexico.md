# Escopo léxico do subconjunto de Python

Documento de referência do scanner (`backend/scanner.py`). Tudo o que está aqui é o que o scanner **realmente** reconhece; testes automatizados cobrem cada linha das tabelas.

Posições: `linha` e `coluna` começam em **1** e contam **caracteres** (não bytes).

## 1. Categorias de token

| Categoria (`tipo`) | Regra de formação | Exemplos |
| --- | --- | --- |
| `PALAVRA_RESERVADA` | Palavras da lista de reservadas do Python. Do subconjunto: `if`, `else`, `while`. As demais (`def`, `return`, `for`, `True`...) também são reconhecidas, mas geram um **aviso** | `if`, `else`, `while` |
| `IDENTIFICADOR` | `[A-Za-z_][A-Za-z0-9_]*` (somente ASCII), que não seja palavra reservada. Diferencia maiúsculas de minúsculas (`If` é identificador) | `x`, `numero`, `_x1`, `A1b2` |
| `LITERAL_INTEIRO` | `0+` ou `[1-9][0-9]*` (sem zeros à esquerda, como em Python) | `0`, `10`, `42` |
| `LITERAL_DECIMAL` | dígitos `.` dígitos (dígitos dos **dois** lados do ponto) | `3.14`, `0.5`, `10.0` |
| `OPERADOR_ARITMETICO` | um de `+ - * /` | `+`, `/` |
| `OPERADOR_RELACIONAL` | um de `< > <= >= == !=` (o scanner sempre escolhe o lexema mais longo) | `<=`, `==`, `!=` |
| `OPERADOR_ATRIBUICAO` | `=` | `=` |
| `DELIMITADOR` | um de `( ) :` | `(`, `:` |
| `NEWLINE` | fim de uma linha lógica com código. Lexema `"\n"`, ou `""` quando o arquivo termina sem quebra | `↵` |
| `INDENT` | linha com indentação **maior** que a anterior (abre bloco). O lexema são os espaços | `→` |
| `DEDENT` | indentação **volta** a um nível anterior (fecha bloco). Lexema vazio; pode haver vários seguidos | `←` |
| `FIM_DE_ARQUIVO` | último token, sempre presente. Lexema vazio | `∎` |

Operadores lógicos (`and`, `or`, `not`) são palavras reservadas do Python: reconhecidas como `PALAVRA_RESERVADA` com aviso. Não há operadores lógicos simbólicos nem de atribuição composta (`+=`) no subconjunto.

## 2. Comentários, espaços e quebras de linha

| Elemento | Tratamento |
| --- | --- |
| Comentário `# ...` | Ignorado até o fim da linha (não gera token; pode conter qualquer caractere) |
| Comentário de bloco | Python não tem; não há suporte |
| Espaços e tabulações **no meio** da linha | Ignorados |
| Linhas em branco ou só com comentário | Ignoradas: não geram tokens nem alteram a indentação |
| Quebras `\n`, `\r\n` e `\r` | Normalizadas para `\n` antes da análise (as colunas não mudam) |
| Quebra de linha dentro de `( ... )` | Ignorada (a expressão pode continuar na linha seguinte), como em Python |
| Indentação no início da linha | Gera `INDENT` / `DEDENT` usando uma pilha de níveis |

## 3. Erros léxicos

O scanner **não para no primeiro erro**: relata, pula o trecho inválido e continua. Cada erro tem `tipo: "ERRO_LEXICO"`, `lexema`, `linha`, `coluna` e `mensagem`.

| Situação | Exemplo | Lexema do erro | Mensagem (resumo) |
| --- | --- | --- | --- |
| Caractere fora do subconjunto | `x = 1 @ 2` | `@` | "Caractere não reconhecido: '@'..." (vale para `$ ? ~ ^ & \| % ` , ; { } [ ] .` e acentuados) |
| `!` sozinho | `a ! b` | `!` | sugere `!=` |
| Literal malformado | `3.14.15`, `12abc`, `3.`, `.5`, `007`, `1e5` | o trecho inteiro | explica a regra violada |
| String (ainda não suportada) | `"Ana"`, `'oi'` | a string inteira | "strings ainda não fazem parte do subconjunto" |
| String sem fechar | `"oi` | até o fim da linha | informa a falta da aspa de fechamento |
| Tabulação na indentação | `\ty = 1` | `\t` | pede espaços (4 por nível) |
| Indentação inconsistente | recuo que não casa com nenhum nível aberto | os espaços | lista os níveis abertos |
| Caractere de controle | `\x00` | o caractere | mostrado de forma segura (`\x00`) |

Quando há mais de 200 erros, a resposta lista os 200 primeiros e informa quantos foram omitidos (`resumo.erros_omitidos`); a contagem total continua exata.

## 4. Avisos

`AVISO_FORA_DO_ESCOPO`: palavra reservada do Python que ainda não faz parte do subconjunto (ex.: `def`). Não é erro: `sucesso` continua `true`. Serve para alertar que as próximas etapas poderão rejeitá-la.

## 5. O que o scanner **não** faz

- Não verifica a estrutura: `x = = 3 +` ou `if :` são tokenizados normalmente (isso é o parser, Etapa 4). O mesmo vale para parênteses desbalanceados.
- Não aceita strings, listas, chamadas de função, `,`, `;`, `.`, `%`, `**`, `//`, `+=` etc.
- Não aceita identificadores com letras acentuadas (ASCII apenas).
- Não trata continuação de linha com `\`.
