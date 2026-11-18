# Casos de teste (Etapa 4)

Modelo de cada caso: **ID**, **categoria**, **entrada**, **resultado esperado**. O código correspondente está em `backend/tests/test_casos_etapa4.py` (`cd backend && python -m pytest tests/test_casos_etapa4.py`). `↵` marca quebra de linha. Os resultados abaixo foram executados contra o backend desta versão.

| ID | Categoria | Entrada | Resultado esperado |
| --- | --- | --- | --- |
| CT-01 | Válido | `x = 10↵` | sem erros; AST com 4 nós |
| CT-02 | Válido | `a = 2 + 3 * 4↵` | sem erros; `*` abaixo de `+` (8 nós) |
| CT-03 | Válido | `if x > 0:` / `    y = 1` / `else:` / `    y = 2` | sem erros; Condicional com dois blocos (13 nós) |
| CT-04 | Válido | `while i < 10:` / `    i = i + 1` | sem erros; Repeticao (11 nós) |
| CT-05 | Válido | `x = (1 + 2) * -3↵` | sem erros; parênteses não geram nó, unário gera (9 nós) |
| CT-06 | Erro léxico | `x = 10 @ 2↵` | 1 erro léxico (`@`, 1:8); `sintatico.executado = false` |
| CT-07 | Erro léxico | `x = 3.↵` | 1 erro léxico: decimal sem dígitos após o ponto (1:5); parser não executa |
| CT-08 | Erro léxico | `if x > 0:` / `    y = 1` / `  z = 2` | 1 erro léxico: indentação inconsistente (3:1); parser não executa |
| CT-09 | Erro sintático | `x = 10 +↵` | 1 erro em 1:9, encontrado "fim da linha"; sem AST |
| CT-10 | Erro sintático | `if x > 0↵` / `    y = 1` | 1 erro: falta o `:` do `if` (1:9) |
| CT-11 | Erro sintático | `x = (1 + 2↵` | 1 erro: o `(` da coluna 5 não foi fechado (1:11) |
| CT-12 | Erro sintático | `else:` / `    x = 1` | 1 erro: `else` sem `if` (1:1) |
| CT-13 | Erro sintático | `while x:` / `y = 1` | 1 erro em 2:1: faltou bloco indentado |
| CT-14 | Erro sintático | `if = 3↵` | 1 erro: palavra reservada usada como variável (1:1) |
| CT-15 | Erro sintático | `a < b < c↵` | 1 erro em 1:7: comparação encadeada |
| CT-16 | Limite | código vazio | HTTP 422 |
| CT-17 | Combinado | `x = 1 @` / `y = (` | só o erro léxico aparece (o parser não roda) |
| CT-18 | Limite | 26 `(` + `1` + 26 `)` | 1 erro sintático: parênteses aninhados demais (limite 25) |
| CT-S01 | Semântico | `x = y + 1↵` | **pendente (Etapa 5)**: hoje é aceito sem avisos |
| CT-S02 | Semântico | `x = 10 / 0↵` | **pendente (Etapa 5)**: hoje é aceito sem avisos |

CT-S01 e CT-S02 estão marcados como `skip` nos testes: documentam a lacuna conhecida, não um comportamento esperado agora.
