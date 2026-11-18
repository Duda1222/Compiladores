# Compilador Educacional

Software educacional web para o ensino de **análise léxica e análise sintática** de um subconjunto da linguagem **Python**, com visualização passo a passo voltada a estudantes de graduação em Ciência da Computação.

**Autora:** Maria Eduarda Almeida Lopes
**Disciplina:** Compiladores. Trabalho 4, quarta etapa: análise sintática e árvore sintática abstrata (AST), sobre a análise léxica da Etapa 3.

![Interface da aplicação](docs/img/interface.png)

Etapa 4: [AST](docs/img/interface-ast.png) · [erros sintáticos](docs/img/interface-erros-sintaticos.png) · [parser não executado por erro léxico](docs/img/interface-sintatico-nao-executado.png) · [AST no celular](docs/img/interface-ast-celular.png).

Etapa 3: [passo a passo](docs/img/interface-passo-a-passo.png) · [erros léxicos](docs/img/interface-erros-lexicos.png) · [versão para celular](docs/img/interface-celular.png).

## Objetivo

Oferecer uma "porta de entrada" para o compilador educacional: o estudante escreve ou escolhe um programa, solicita a análise e **vê como o scanner (analisador léxico) o transforma em tokens**, com categorias, lexemas e posições (linha e coluna), destaque colorido, explicação passo a passo e erros léxicos didáticos.

**Estado atual:** a Etapa 4 acrescenta a **análise sintática** (parser) e a **AST** ao scanner da Etapa 3. O parser confere a estrutura do programa (`x = = 3 +` é rejeitado, com linha, coluna e explicação), constrói a AST e a interface a exibe como árvore. **A análise semântica (Etapa 5) ainda não foi implementada**: o parser aceita `y = x + 1` mesmo que `x` nunca tenha sido definido.

Fluxo: ![Fluxo do compilador](docs/img/fluxo-compilador.png)

Para quem está começando, veja o [tutorial](docs/tutorial.md). Documentação da Etapa 4: [gramática](docs/gramatica.md) · [AST](docs/ast.md) · [estratégia do parser, erros e decisões](docs/sintatico.md) · [registro de testes](docs/testes.md).

## Linguagem escolhida e subconjunto

**Linguagem analisada:** Python (a mesma das etapas anteriores; a base foi preservada e ampliada).

**Por que Python:**

- é a linguagem de entrada em grande parte dos cursos de graduação, então o aluno já a conhece e pode focar no processo de compilação, e não na sintaxe;
- sua sintaxe é enxuta, o que ajuda a manter gramática e tokens pequenos;
- a indentação obriga o scanner a gerar tokens `NEWLINE`, `INDENT` e `DEDENT`, um caso real em que o léxico não se resume a separar palavras. A interface mostra esses tokens "invisíveis" de forma didática.

### Escopo léxico (resumo)

| Categoria | Exemplos |
| --- | --- |
| Palavras reservadas do subconjunto | `if`, `else`, `while` |
| Identificadores | `numero`, `resultado`, `_x1` (`[A-Za-z_][A-Za-z0-9_]*`) |
| Literais inteiros | `0`, `10`, `42` (sem zeros à esquerda) |
| Literais decimais | `3.14`, `0.5` |
| Operadores aritméticos | `+`, `-`, `*`, `/` |
| Operadores relacionais | `<`, `>`, `<=`, `>=`, `==`, `!=` |
| Atribuição | `=` |
| Delimitadores | `(`, `)`, `:` |
| Comentários | `# até o fim da linha` (ignorados) |
| Espaços em branco | ignorados no meio da linha; no início da linha geram `INDENT`/`DEDENT` |
| Quebra de linha | token `NEWLINE` (exceto em linhas vazias, só com comentário, ou dentro de parênteses) |
| Caracteres não reconhecidos | geram **erro léxico** com linha e coluna; o scanner continua |

A tabela completa (regras, mensagens de erro, o que **não** é reconhecido) está em [`docs/escopo-lexico.md`](docs/escopo-lexico.md).

Ficam para etapas posteriores: funções, listas, strings, classes e demais construções. Strings, por exemplo, geram erro léxico específico.

### Gramática (resumo)

A gramática completa (EBNF, terminais ↔ categorias de token, precedência, FIRST/FOLLOW, exemplos válidos e inválidos) está em [`docs/gramatica.md`](docs/gramatica.md). Resumo:

```ebnf
programa        = { comando } , FIM_DE_ARQUIVO ;
comando         = comando_simples | condicional | repeticao ;
comando_simples = ( atribuicao | expressao ) , NEWLINE ;
atribuicao      = IDENTIFICADOR , "=" , expressao ;
condicional     = "if" , expressao , ":" , bloco , [ "else" , ":" , bloco ] ;
repeticao       = "while" , expressao , ":" , bloco ;
bloco           = NEWLINE , INDENT , comando , { comando } , DEDENT ;
expressao       = soma , [ OPERADOR_RELACIONAL , soma ] ;
soma            = termo , { ( "+" | "-" ) , termo } ;
termo           = unario , { ( "*" | "/" ) , unario } ;
unario          = ( "+" | "-" ) , unario | primario ;
primario        = LITERAL_INTEIRO | LITERAL_DECIMAL | IDENTIFICADOR | "(" , expressao , ")" ;
```

Precedência (menor → maior): relacionais, `+ -`, `* /`, unário, parênteses. `+ - * /` associam à esquerda (`20 - 5 - 3` = `(20 - 5) - 3`).

## Diferencial em relação aos trabalhos estudados

A comparação completa (11 ferramentas, 14 critérios, com a página ou seção de cada evidência) está no documento da Etapa 3. O que se pode afirmar **a partir daquela matriz** é:

| O que este software tem (Etapa 3) | Situação nos trabalhos estudados |
| --- | --- |
| Interface web, entrada de código, exemplos, análise léxica, passo a passo, diagnóstico de erros e explicações | Graciano Junior et al. (2022) também reúne web, passo a passo, léxica/sintática e explicação teórica, mas sobre uma pseudolinguagem. **Não se reivindica originalidade nessa combinação.** |
| Linguagem **Python** (subconjunto) | Nas fontes lidas, nenhuma analisa Python |
| Tokens **`INDENT` e `DEDENT`** gerados por pilha de níveis e mostrados passo a passo | Nas fontes lidas, nenhuma trata desses tokens |
| Scanner **verificado automaticamente contra o `tokenize`** do Python (tipo, lexema, linha e coluna de cada token, em 300 programas gerados aleatoriamente e em programas fixos) | Não aparece nas fontes lidas |
| Erros léxicos em português, com linha, coluna e motivo, que não interrompem a análise | Há retorno de erros em outras ferramentas; aqui é em texto didático, e não só cor |
| Documentação do escopo léxico, da gramática e da AST, tutorial inicial e registro de testes no repositório | **Não foi comparado** na matriz, então não se afirma diferença |

**Importante:** "não aparece nas fontes lidas" não prova que não exista. A matriz usa só as informações dos artigos. Também **não há**, neste software, análise semântica (Etapa 5), geração de código, avaliação com estudantes nem medida de aprendizagem. A análise sintática e a AST (Etapa 4) usam uma abordagem clássica (descendente recursivo) e **não se reivindica novidade** nelas; o que se pode afirmar é que a AST foi verificada contra a do módulo `ast` do Python (ver [`docs/testes.md`](docs/testes.md)). Não se afirma que o software seja superior aos existentes.

## Tecnologias

- **Frontend:** HTML, CSS e JavaScript puro (módulos ES), servido pelo **Nginx**. Não há framework nem etapa de build.
- **Backend:** **Python 3.12 + Flask**, executado com **Gunicorn**.
- **Parser (Etapa 4):** **descendente recursivo preditivo**, escrito à mão em Python puro (`backend/sintatico.py`, AST em `backend/arvore.py`), sem dependências novas.
  - *Justificativa:* cada regra da gramática vira uma função com o mesmo nome, então o código lê como a gramática, é fácil de explicar em aula e permite mensagens de erro específicas por regra. Comparação com LL(1) por tabela e geradores (ANTLR, Lark) em [`docs/sintatico.md`](docs/sintatico.md).
- **Scanner:** escrito em **Python puro**, dentro do backend (`backend/scanner.py`), sem bibliotecas externas.
  - *Justificativa:* o backend já é Python; um scanner artesanal (laço que lê caractere por caractere) é fácil de explicar e depurar em aula, e dispensa dependências novas no Docker. A indentação (pilha de níveis) e os erros com localização ficam sob controle total.
- **Orquestração:** Docker e Docker Compose.
- **Testes:** `pytest` (backend e scanner), `node:test` + `jsdom` (frontend), script de smoke test em Bash (implantação).

## Estrutura do repositório

```
.
├── backend/                  # API em Python (Flask + Gunicorn)
│   ├── app.py                # rotas e tratamento de erros
│   ├── validacao.py          # regras de validação da entrada
│   ├── scanner.py            # analisador léxico (Etapa 3)
│   ├── sintatico.py          # analisador sintático / parser (Etapa 4)
│   ├── arvore.py             # nós e formato da AST (Etapa 4)
│   ├── tests/                # testes do scanner, dos endpoints e das validações (pytest)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── frontend/                 # Interface web estática servida pelo Nginx
│   ├── index.html            # estrutura da tela
│   ├── css/estilo.css        # estilos
│   ├── js/
│   │   ├── app.js            # ligação entre a tela e os módulos
│   │   ├── api.js            # comunicação com o backend
│   │   ├── validacao.js      # validação da entrada no navegador
│   │   ├── exemplos.js       # programas de exemplo
│   │   ├── tokens.js         # categorias, explicações e realce (funções puras)
│   │   ├── resultado.js      # tabela, código colorido e passo a passo
│   │   └── sintatico.js      # AST, árvore de derivação e erros sintáticos (Etapa 4)
│   ├── tests/                # testes de unidade, interface e integração
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── scripts/
│   ├── smoke_test.sh         # teste de implantação / ponta a ponta
│   └── testar_tudo.sh        # backend + frontend sem Docker
├── docs/
│   ├── escopo-lexico.md      # tabela completa do escopo léxico
│   ├── gramatica.md          # gramática EBNF, precedência, FIRST/FOLLOW (Etapa 4)
│   ├── ast.md                # tipos de nó e formato JSON da AST (Etapa 4)
│   ├── sintatico.md          # estratégia do parser, erros, decisões, fluxograma (Etapa 4)
│   ├── fluxo.mmd             # fluxograma em Mermaid (fonte)
│   ├── tutorial.md           # tutorial inicial para estudantes
│   ├── testes.md             # registro dos testes
│   └── img/                  # capturas de tela
├── config/                   # reservada para as próximas etapas
├── docker-compose.yml
├── .gitignore
├── .dockerignore
└── README.md
```

O frontend exibe a interface e encaminha as chamadas `/api/*` ao backend por meio do Nginx. O navegador só conversa com o Nginx (porta 8080); o nome `backend` é resolvido apenas dentro da rede do Docker Compose. Não há banco de dados e **não foram criadas variáveis de ambiente, portas nem dependências novas** na Etapa 4 (a única mudança no Docker é o `backend/Dockerfile` copiar `arvore.py` e `sintatico.py`). Não há segredos no repositório.

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) 24 ou superior
- Docker Compose v2 (plugin `docker compose`, já incluído no Docker Desktop e nas versões recentes do Docker Engine)
- Porta **8080** livre na máquina

Para conferir as versões:

```bash
docker --version
docker compose version
```

## Como executar

Clone o repositório e, na raiz dele, suba os contêineres:

```bash
git clone https://github.com/Duda1222/Compiladores
cd Compiladores
docker compose up --build -d
```

Depois abra no navegador: <http://localhost:8080>.

## Como encerrar

```bash
docker compose down
```

Para remover também as imagens construídas:

```bash
docker compose down --rmi local
```

## Como usar a interface

1. **Escolher um exemplo (opcional):** são onze, de atribuições simples a blocos aninhados, programas com erros léxicos e com erros sintáticos.
2. **Escrever ou editar o código** no editor.
3. **Analisar:** clique em **Analisar código**. A área **Resultados** mostra, nesta ordem:
   - resumo (tokens, erros, linhas, caracteres);
   - **erros léxicos** (se houver), com linha, coluna e mensagem, e **avisos**;
   - **análise sintática (Etapa 4)**: se não há erro léxico, a **AST** como árvore expansível, com botões *Expandir tudo* / *Recolher tudo*, filtro por tipo de nó, exportação em JSON, e um painel que mostra, ao clicar num nó, a regra da gramática, a posição e o trecho de código correspondente (destacado). Há também a AST em texto indentado, em JSON e a **árvore de derivação** (para comparar). Se há erro sintático, aparece a lista de erros (linha, coluna, encontrado, esperado, regra violada e dica) e **não há AST**. Se há erro léxico, a seção avisa que o parser não foi executado;
   - **tokens por categoria** (contagem);
   - **código com tokens destacados** (uma cor e um estilo de sublinhado por categoria; `↵ → ← ∎` mostram os tokens invisíveis);
   - **passo a passo**: *Próximo*, *Anterior*, *Reproduzir*/*Pausar* e *Mostrar tudo*; cada passo explica por que o lexema virou aquele token, e o que ainda não foi lido fica esmaecido;
   - **sequência de tokens** (o código original "vira" esta lista) e **tabela de tokens** (`#`, tipo, lexema, linha, coluna).
4. Os blocos "O que é um token? E um lexema?" e "O que é análise sintática? E uma AST?" explicam os conceitos na própria tela. O limite de entrada (100.000 caracteres) aparece sob o editor.
5. **Mensagens de entrada** (vazio, só espaços, falha de comunicação, erro inesperado) continuam como na Etapa 2.

O layout é responsivo (usa uma coluna em telas estreitas, a tabela rola para os lados e os botões têm área de toque confortável), então pode ser aberto no navegador do celular. Não é um aplicativo móvel nativo.

O código **não é presumido válido**: um programa com erros é aceito e analisado normalmente.

## Exemplos de programas disponíveis

| # | Exemplo | O que demonstra |
| --- | --- | --- |
| 1 | Atribuição e literais | identificadores, inteiros e decimais |
| 2 | Expressões aritméticas | `+ - * /` e parênteses |
| 3 | Estrutura condicional | `if`/`else`, relacional, `INDENT`/`DEDENT` |
| 4 | Estrutura de repetição | `while`, `!=` |
| 5 | Com erro intencional | tokens válidos em estrutura errada (o parser aponta operando faltando e parêntese sem fechar) |
| 6 | Todos os operadores | aritméticos, atribuição e os seis relacionais |
| 7 | Comentários e linhas em branco | ignorados pelo scanner |
| 8 | Blocos aninhados | vários `INDENT`/`DEDENT` |
| 9 | Com erros léxicos | `@`, `3.14.15`, `12abc`, string e `def` (aviso); o parser **não** roda |
| 10 | Precedência e associatividade (AST) | `10 + 5 * 2`, `20 - 5 - 3`, `(10 + 5) * 2`, unário |
| 11 | Com erros sintáticos | operando faltando, `=` no lugar de `==`, operadores seguidos, `else` sem `if` |

Os textos exatos estão em `frontend/js/exemplos.js`.

## Comunicação frontend ↔ backend

**Requisição**

```
POST /api/analisar
Content-Type: application/json

{ "codigo": "numero = 10\n" }
```

**Resposta (HTTP 200)** — também quando há erros léxicos ou sintáticos: o pedido foi processado e os campos `sucesso` dizem o que passou. Os campos planos da Etapa 3 (`sucesso`, `tokens`, `erros`, `avisos`, `resumo`, `mensagem`) foram **mantidos** na raiz; a Etapa 4 acrescenta os blocos `lexico` (cópia desses campos) e `sintatico` (abaixo).

```json
{
  "recebido": true,
  "sucesso": true,
  "mensagem": "Análise léxica concluída sem erros.",
  "linhas": 1,
  "caracteres": 12,
  "tokens": [
    { "tipo": "IDENTIFICADOR",       "lexema": "numero", "linha": 1, "coluna": 1 },
    { "tipo": "OPERADOR_ATRIBUICAO", "lexema": "=",      "linha": 1, "coluna": 8 },
    { "tipo": "LITERAL_INTEIRO",     "lexema": "10",     "linha": 1, "coluna": 10 },
    { "tipo": "NEWLINE",             "lexema": "\n",     "linha": 1, "coluna": 12 },
    { "tipo": "FIM_DE_ARQUIVO",      "lexema": "",       "linha": 2, "coluna": 1 }
  ],
  "erros": [],
  "avisos": [],
  "resumo": { "total_tokens": 5, "total_erros": 0, "erros_omitidos": 0,
              "por_tipo": { "IDENTIFICADOR": 1, "OPERADOR_ATRIBUICAO": 1, "LITERAL_INTEIRO": 1, "NEWLINE": 1, "FIM_DE_ARQUIVO": 1 } }
}
```

**Com erro léxico** (`x = 10 @ 2`): `"sucesso": false`, `"mensagem": "Análise léxica concluída com 1 erro léxico."` e

```json
"erros": [
  { "tipo": "ERRO_LEXICO", "lexema": "@", "linha": 1, "coluna": 8,
    "mensagem": "Caractere não reconhecido: '@'. Ele existe em Python, mas ainda não faz parte do subconjunto suportado." }
]
```

A interface exibe: *"Linha 1, coluna 8 — Caractere não reconhecido: '@'..."*. Os tokens válidos continuam na lista (o scanner não para no primeiro erro).

| Campo | Descrição |
| --- | --- |
| `recebido` | `true` se o pedido foi aceito e processado (mantido da Etapa 2) |
| `sucesso` | `true` se não houve erro léxico (avisos não contam como erro) |
| `tokens[]` | `tipo`, `lexema`, `linha`, `coluna`. Tipos em [`docs/escopo-lexico.md`](docs/escopo-lexico.md) |
| `erros[]` | `tipo` = `ERRO_LEXICO`, `lexema`, `linha`, `coluna`, `mensagem` (máx. 200 itens) |
| `avisos[]` | `tipo` = `AVISO_FORA_DO_ESCOPO`, mesmos campos |
| `resumo` | totais e contagem `por_tipo`; `erros_omitidos` > 0 quando passou de 200 erros |
| `linhas`, `caracteres` | tamanho do texto enviado |
| `lexico` | `sucesso`, `tokens`, `erros`, `avisos`, `resumo` (Etapa 4: mesmo conteúdo dos campos planos) |
| `sintatico` | resultado do parser, descrito abaixo |

### Contrato da análise sintática (Etapa 4)

```json
"sintatico": {
  "executado": true,
  "sucesso": true,
  "ast": { "tipo": "Programa", "papel": null, "regra": "programa → { comando } FIM_DE_ARQUIVO",
           "linha": 1, "coluna": 1, "linha_fim": 1, "coluna_fim": 11, "atributos": {}, "filhos": [ ... ] },
  "derivacao": { "simbolo": "programa", "filhos": [ ... ] },
  "erros": [],
  "mensagem": "Análise sintática concluída sem erros.",
  "resumo": { "total_erros": 0, "erros_omitidos": 0, "total_nos": 6, "altura": 4, "por_tipo": { "...": 1 } }
}
```

**Com erro sintático** (`x = 10 +`): `sucesso: false`, `ast: null`, `derivacao: null` e

```json
"erros": [
  { "tipo": "ERRO_SINTATICO", "linha": 1, "coluna": 9, "encontrado": "fim da linha",
    "esperado": ["identificador", "número", "'('", "'-'", "'+'"],
    "mensagem": "A expressão termina em '+', mas falta o operando à direita dele (esperava identificador, número ou '(').",
    "regra": "primario → LITERAL_INTEIRO | LITERAL_DECIMAL | IDENTIFICADOR | '(' expressao ')'" }
]
```

**Com erro léxico** (`x = 10 @ 2`): o parser **não é executado**: `"sintatico": { "executado": false, "sucesso": false, "ast": null, "erros": [], "mensagem": "A análise sintática não foi executada porque há erros léxicos..." }`. Os erros léxicos continuam em `lexico.erros`. Decisão e justificativa em [`docs/sintatico.md`](docs/sintatico.md), seção 3.

| Campo de `sintatico` | Descrição |
| --- | --- |
| `executado` | `false` somente quando havia erro léxico |
| `sucesso` | `true` se a estrutura é válida |
| `ast` | árvore (formato em [`docs/ast.md`](docs/ast.md)) ou `null` |
| `derivacao` | árvore de derivação (não terminais e tokens como folhas) ou `null` |
| `erros[]` | `tipo` = `ERRO_SINTATICO`, `linha`, `coluna`, `encontrado`, `esperado[]`, `mensagem`; opcionais: `regra`, `dica`. Máx. 20 itens |
| `resumo` | `total_erros`, `erros_omitidos`; com sucesso também `total_nos`, `altura`, `por_tipo` |

O parser relata **vários erros** por análise (modo pânico: descarta o resto da linha e o bloco dependente e continua), com supressão de cascatas; detalhes em [`docs/sintatico.md`](docs/sintatico.md), seção 5.

**Respostas de erro de entrada** (inalteradas desde a Etapa 2)

```json
{ "recebido": false, "erro": "entrada_vazia", "mensagem": "Informe um código-fonte antes de solicitar a análise." }
```

| Situação | HTTP | `erro` |
| --- | --- | --- |
| Corpo ausente, malformado, sem `Content-Type: application/json` ou que não é um objeto | 400 | `corpo_invalido` |
| Campo `codigo` ausente | 400 | `campo_ausente` |
| Campo `codigo` que não é texto | 400 | `campo_invalido` |
| Texto vazio | 422 | `entrada_vazia` |
| Somente espaços em branco | 422 | `entrada_somente_espacos` |
| Código acima de 100.000 caracteres | 413 | `entrada_muito_grande` |
| Rota inexistente ou método não permitido | 404 / 405 | `requisicao_invalida` |
| Erro inesperado no servidor | 500 | `erro_interno` (mensagem genérica; detalhes só no log) |

Também existem `GET /api/health` (`{"status":"ok"}`, usado pelo healthcheck do Compose) e `GET /api/hello` (mantido da Etapa 1).

A validação ocorre **nos dois lados**. O scanner nunca expõe stack traces: qualquer falha inesperada vira `erro_interno` genérico.

### Exemplos de entrada e saída do parser

| Entrada | Saída |
| --- | --- |
| `x = 10 + 5 * 2` | `Programa › Atribuicao › [Identificador x, OperacaoBinaria + › [Numero 10, OperacaoBinaria * › [Numero 5, Numero 2]]]` |
| `20 - 5 - 3` | `OperacaoBinaria - › [OperacaoBinaria - › [20, 5], 3]` (associa à esquerda) |
| `(10 + 5) * 2` | `OperacaoBinaria * › [OperacaoBinaria + › [10, 5], 2]` (parênteses somem) |
| `x = 10 +` | erro 1:9, encontrado "fim da linha": falta o operando à direita de `+` |
| `if x = 3:` | erro 1:6: "Para comparar valores o operador é '=='" |
| `y = (3 * 4` | erro: o parêntese aberto na linha 1, coluna 5 não foi fechado |
| `else:` | erro 1:1: `else` sem `if` |
| `# só comentário` | `Programa` vazio (válido) |

### Exemplos de entrada e saída do scanner

| Entrada | Saída (tipo:lexema) |
| --- | --- |
| `x = 10` | `IDENTIFICADOR:x` `OPERADOR_ATRIBUICAO:=` `LITERAL_INTEIRO:10` `NEWLINE` `FIM_DE_ARQUIVO` |
| `a <= b` | `IDENTIFICADOR:a` `OPERADOR_RELACIONAL:<=` `IDENTIFICADOR:b` ... |
| `if x:`⏎`····y = 1` | `PALAVRA_RESERVADA:if` `IDENTIFICADOR:x` `DELIMITADOR::` `NEWLINE` `INDENT` `IDENTIFICADOR:y` ... `DEDENT` `FIM_DE_ARQUIVO` |
| `x = 3.14.15` | erro léxico: *Literal numérico malformado '3.14.15': literal com mais de um ponto decimal.* |
| `# só comentário` | apenas `FIM_DE_ARQUIVO` |

## Testes

Instalação das dependências de teste e execução (sem Docker):

```bash
./scripts/testar_tudo.sh
```

Ou separadamente:

```bash
# backend: scanner, endpoints, validação
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
python -m pytest -q tests/test_scanner.py     # só o scanner

# frontend: unitários, interface (jsdom) e regressão
cd frontend
npm install
npm test

# integração frontend <-> backend real (com o backend em execução na porta 5000)
BACKEND_URL=http://localhost:5000 npm test
```

As respostas usadas nos testes do frontend são geradas pelo **scanner real** (`python tests/gerar_fixtures.py`, na pasta `backend`) e um teste do backend avisa se elas ficarem desatualizadas, garantindo que frontend e backend usem o mesmo contrato.

Teste de implantação (com a aplicação de pé via Docker Compose):

```bash
docker compose up --build -d
./scripts/smoke_test.sh
```

**Resultados relevantes** (detalhes, falhas corrigidas e pendências em [`docs/testes.md`](docs/testes.md); executados em cópia limpa do repositório):

- backend: **650** testes aprovados, 0 reprovados (398 do parser/AST, 21 do endpoint com análise sintática, 126 do scanner, 42 de verificação cruzada com o `tokenize`, 40 do endpoint da Etapa 3, 22 de validação, 1 de fixtures);
- a AST foi comparada com a do módulo `ast` do Python: estrutura em **200** programas aleatórios e posições (início e fim de cada nó) em **100**;
- frontend: **161** aprovados, 0 reprovados (20 de integração ignorados sem `BACKEND_URL`);
- integração frontend ↔ backend real: **181** aprovados, 0 reprovados;
- regressão das Etapas 1 a 3: todos os testes anteriores continuam passando, **sem alterá-los**;
- smoke test: as **22** verificações da parte de API passaram contra o backend (sem Nginx). **O smoke test completo e o `docker compose up --build` desta etapa não foram executados**, porque o ambiente de desenvolvimento não tinha Docker. Rode `docker compose up --build -d && ./scripts/smoke_test.sh` num clone limpo para validar (na Etapa 3 isso foi feito com Docker real: 24/24).

## Solução de problemas

- **Porta 8080 em uso:** altere o mapeamento em `docker-compose.yml` (por exemplo `"8081:80"`) e acesse a nova porta (`BASE_URL=http://localhost:8081 ./scripts/smoke_test.sh`).
- **Ver logs:** `docker compose logs -f`.
- **Reconstruir do zero:** `docker compose down --rmi local && docker compose up --build -d`.

## Limitações conhecidas

- **Sem análise semântica** (Etapa 5): variáveis usadas sem atribuição, tipos e divisão por zero **não** são verificados.
- Se há **erro léxico**, o parser não roda: um programa com erro léxico e sintático mostra só o léxico até ser corrigido.
- A recuperação de erros é simples (modo pânico por linha): depois de um erro, o resto da linha é descartado, então um segundo erro na mesma linha só aparece após corrigir o primeiro. Limite de 20 erros listados.
- Uma comparação por expressão (`a < b < c` é rejeitado) e sem `and`/`or`/`not`, `elif`, `for`, funções, listas, strings, `%`, `//`, `**`, `+=`, atribuição encadeada. Não existem os nós `Funcao`, `ChamadaFuncao` e `Retorno`.
- Limites de proteção: 25 níveis de parênteses, 25 de blocos, AST com até 150 níveis (ex.: mais de ~150 operadores encadeados geram erro amigável), 100.000 caracteres de entrada.
- **Não implementados (opcionais):** construção passo a passo/animada da árvore e a integração com Ollama/Llama 3.2.
- Strings, listas, vírgula, ponto e vírgula, `%`, `**`, `//`, `+=`, identificadores com acento e continuação de linha com `\` **não** são reconhecidos (erro léxico). Tabulação na indentação é rejeitada (use espaços).
- O editor é um campo de texto simples, sem realce em tempo real nem numeração de linhas.
- Não há teste automatizado em navegador real (a interface é testada em jsdom e conferida manualmente em Chromium, no desktop e em largura de celular).
- Não há avaliação com estudantes: **não se afirma** ganho de aprendizagem.
- Não é um aplicativo móvel; apenas a página web é responsiva.

## Próximas etapas

**Etapa 5:** análise semântica sobre a AST desta etapa (tabela de símbolos, variáveis definidas antes do uso, tipos numéricos inteiro × decimal, divisão por zero constante), encaixada no fluxo após o parser (ver o fluxograma acima).
