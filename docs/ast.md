# AST: tipos de nó e formato JSON (Etapa 4)

Implementação: `backend/arvore.py`. A AST é devolvida em `sintatico.ast` pelo endpoint `POST /api/analisar`.

## 1. Sequência de tokens × árvore de derivação × AST

| | Sequência de tokens | Árvore de derivação (concreta) | AST |
| --- | --- | --- | --- |
| Produzida por | scanner | parser (cada chamada de função de regra) | parser (só o que tem significado) |
| Estrutura | lista plana | árvore com **todos** os símbolos da gramática | árvore enxuta |
| Contém | tokens com tipo, lexema, linha e coluna | não terminais (`soma`, `termo`, `unario`...) e tokens como folhas | operações, identificadores, números, comandos |
| `NEWLINE`, `INDENT`, `DEDENT`, `:` | sim | sim (como folhas) | **não** |
| Parênteses | sim (`(`, `)`) | sim | **não** (a forma da árvore já expressa a ordem) |
| Usada para | análise léxica | mostrar **como** a gramática foi aplicada | análise semântica e geração de código (próximas etapas) |

Exemplo para `x = (1 + 2) * 3`:

```
Sequência de tokens:  x  =  (  1  +  2  )  *  3  NEWLINE  FIM_DE_ARQUIVO

Árvore de derivação (resumo):          AST:
programa                               Programa
└ comando                              └ Atribuicao
  └ comando_simples                      ├ Identificador x
    ├ atribuicao                         └ OperacaoBinaria *
    │ ├ x (IDENTIFICADOR)                  ├ OperacaoBinaria +
    │ ├ =                                  │ ├ Numero 1
    │ └ expressao                          │ └ Numero 2
    │   └ soma                             └ Numero 3
    │     └ termo
    │       ├ unario → primario → ( expressao → soma → termo ... ) 
    │       ├ *
    │       └ unario → primario → 3
    └ NEWLINE
```

A interface mostra as duas árvores (a de derivação dentro de uma seção recolhível), para o estudante comparar.

## 2. Tipos de nó

| Tipo | Quando aparece | Atributos | Filhos (papel) | Regra da gramática |
| --- | --- | --- | --- | --- |
| `Programa` | raiz | — | `comando` (0 ou mais) | `programa` |
| `Atribuicao` | `x = expr` | — | `alvo` (Identificador), `valor` | `atribuicao` |
| `ExpressaoComando` | expressão usada como comando | — | `expressao` | `comando_simples` |
| `Condicional` | `if` / `else` | — | `condicao`, `entao` (Bloco), `senao` (Bloco, opcional) | `condicional` |
| `Repeticao` | `while` | — | `condicao`, `corpo` (Bloco) | `repeticao` |
| `Bloco` | corpo indentado | — | `comando` (1 ou mais) | `bloco` |
| `OperacaoBinaria` | `+ - * /` | `operador`, `categoria` = `aritmetica` | `esquerda`, `direita` | `soma`, `termo` |
| `Comparacao` | `< > <= >= == !=` | `operador`, `categoria` = `relacional` | `esquerda`, `direita` | `expressao` |
| `OperacaoUnaria` | `-x`, `+x` | `operador` | `operando` | `unario` |
| `Identificador` | nome de variável | `nome` | — | `primario` |
| `Numero` | literal | `lexema`, `tipo_numero` = `inteiro` ou `decimal` | — | `primario` |

O enunciado cita também `Funcao`, `ChamadaFuncao` e `Retorno`. Esses nós **não existem** aqui porque o subconjunto de Python escolhido nas Etapas 1 a 3 não tem funções; quando ganhar, bastará criar os tipos novos em `arvore.py` e as regras em `sintatico.py`.

## 3. Formato JSON

Cada nó tem sempre os mesmos campos:

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `tipo` | texto | um dos tipos acima |
| `papel` | texto ou `null` | função do nó dentro do pai (`esquerda`, `condicao`...); `null` na raiz |
| `regra` | texto | regra da gramática que gera o nó (exibida na interface) |
| `linha`, `coluna` | inteiros | início do nó (a partir de 1) |
| `linha_fim`, `coluna_fim` | inteiros | posição **logo após** o último caractere do nó (intervalo semiaberto) |
| `atributos` | objeto | depende do tipo (tabela acima) |
| `filhos` | lista | nós filhos, na ordem do código |

Exemplo real (`x = 10 + 5`), campos abreviados com `…` apenas aqui na documentação:

```json
{
  "tipo": "Programa", "papel": null, "linha": 1, "coluna": 1, "linha_fim": 1, "coluna_fim": 11,
  "atributos": {},
  "filhos": [{
    "tipo": "Atribuicao", "papel": "comando", "linha": 1, "coluna": 1, "linha_fim": 1, "coluna_fim": 11,
    "atributos": {},
    "filhos": [
      { "tipo": "Identificador", "papel": "alvo", "linha": 1, "coluna": 1, "linha_fim": 1, "coluna_fim": 2,
        "atributos": { "nome": "x" }, "filhos": [] },
      { "tipo": "OperacaoBinaria", "papel": "valor", "linha": 1, "coluna": 5, "linha_fim": 1, "coluna_fim": 11,
        "atributos": { "operador": "+", "categoria": "aritmetica" },
        "filhos": [
          { "tipo": "Numero", "papel": "esquerda", "atributos": { "lexema": "10", "tipo_numero": "inteiro" }, "filhos": [], "…": "…" },
          { "tipo": "Numero", "papel": "direita",  "atributos": { "lexema": "5",  "tipo_numero": "inteiro" }, "filhos": [], "…": "…" }
        ] }
    ]
  }]
}
```

Decisões:

- **Posição dos parênteses:** `(1 + 2)` produz o nó `OperacaoBinaria` com posição de `1 + 2` (sem os parênteses). Os parênteses existem só na árvore de derivação.
- **Posições conferidas:** em programas sem parênteses, início e fim de cada nó foram comparados com os do módulo `ast` do Python (100 programas gerados; `backend/tests/test_sintatico.py`). Com parênteses o Python inclui os parênteses na posição do nó, então a comparação de **estrutura** (200 programas) é feita, e a de **posição** não.
- **Números grandes:** o literal é guardado como texto (`lexema`), nunca convertido, para evitar estouro e perda de precisão.
- **Limite de altura:** 150 níveis (`MAX_ALTURA`). Uma expressão como `1 + 1 + ... ` com mais de 150 termos gera um erro sintático amigável, pois a árvore de uma cadeia associativa à esquerda cresce em profundidade e travaria a serialização e a interface.
