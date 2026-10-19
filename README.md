# Compilador Educacional

Software educacional web para o ensino de **análise léxica e análise sintática** de um subconjunto da linguagem **Python**, com visualização passo a passo voltada a estudantes de graduação em Ciência da Computação.

**Autora:** Maria Eduarda Almeida Lopes
**Disciplina:** Compiladores. Trabalho 2, segunda etapa: interface web e entrada de código-fonte.

![Interface da aplicação](docs/img/interface.png)

## Objetivo

Oferecer uma "porta de entrada" para o compilador educacional: o estudante escreve ou escolhe um programa, solicita a análise e vê a resposta da aplicação. Nesta etapa a aplicação **recebe e valida** o código. **As análises léxica, sintática e semântica ainda não estão implementadas**; serão feitas nas próximas etapas.

## Linguagem escolhida e subconjunto

**Linguagem analisada:** Python.

**Por que Python:**

- é a linguagem de entrada em grande parte dos cursos de graduação, então o aluno já a conhece e pode focar no processo de compilação, e não na sintaxe;
- sua sintaxe é enxuta, o que ajuda a manter gramática e tokens pequenos nas primeiras etapas;
- a indentação obriga o analisador léxico a gerar tokens `INDENT` e `DEDENT`, um caso real em que o léxico não se resume a separar palavras.

**Subconjunto inicial (a ser tratado primeiro):**

| Construção | Exemplo |
| --- | --- |
| Atribuição e identificadores | `x = 10` |
| Literais inteiros e decimais | `42`, `3.14` |
| Operadores aritméticos | `+`, `-`, `*`, `/` |
| Operadores relacionais | `<`, `>`, `<=`, `>=`, `==`, `!=` |
| Condicional | `if x > 0:` / `else:` |
| Repetição | `while x > 0:` |
| Parênteses em expressões | `(a + b) * c` |

Ficam para etapas posteriores: funções, listas, strings, classes e demais construções. A análise semântica também fica para depois.

## Tecnologias

- **Frontend:** HTML, CSS e JavaScript puro (módulos ES), servido pelo **Nginx**. Não há framework nem etapa de build.
- **Backend:** **Python 3.12 + Flask**, executado com **Gunicorn**.
- **Orquestração:** Docker e Docker Compose.
- **Testes:** `pytest` (backend), `node:test` + `jsdom` (frontend), script de smoke test em Bash (implantação).

## Estrutura do repositório

```
.
├── backend/                  # API em Python (Flask + Gunicorn)
│   ├── app.py                # rotas e tratamento de erros
│   ├── validacao.py          # regras de validação da entrada
│   ├── tests/                # testes unitários e de endpoints (pytest)
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
│   │   └── exemplos.js       # programas de exemplo
│   ├── tests/                # testes de unidade, interface e integração
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── scripts/
│   ├── smoke_test.sh         # teste de implantação / ponta a ponta
│   └── testar_tudo.sh        # backend + frontend sem Docker
├── docs/
│   ├── testes.md             # registro dos testes
│   └── img/interface.png
├── config/                   # reservada para as próximas etapas
├── docker-compose.yml
├── .gitignore
├── .dockerignore
└── README.md
```

O frontend exibe a interface e encaminha as chamadas `/api/*` ao backend por meio do Nginx. O navegador só conversa com o Nginx (porta 8080); o nome `backend` é resolvido apenas dentro da rede do Docker Compose. Nesta etapa não há banco de dados.

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

1. **Escolher um exemplo (opcional):** no seletor "Exemplos", escolha um programa. O código aparece no editor e uma linha abaixo do seletor explica o que ele demonstra.
2. **Escrever ou editar o código:** o editor é um campo de texto com fonte monoespaçada. Você pode digitar, colar, apagar ou alterar o código de um exemplo antes de analisar. O texto permanece no editor até você alterá-lo ou clicar em **Limpar**.
3. **Analisar:** clique em **Analisar código**. O código é enviado ao backend e a resposta aparece na área **Resultados**.
4. **Mensagens possíveis:**
   - sucesso: "Código recebido com sucesso.", com número de linhas e de caracteres;
   - entrada vazia: "Informe um código-fonte antes de solicitar a análise.";
   - somente espaços: orientação para escrever ou selecionar um programa;
   - falha de comunicação: "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.";
   - erro inesperado: mensagem genérica, sem detalhes internos.

O código **não é presumido válido**: um programa com erros é aceito e enviado normalmente, pois nas próximas etapas ele servirá para demonstrar a detecção de erros.

## Exemplos de programas disponíveis

| # | Exemplo | Construções demonstradas |
| --- | --- | --- |
| 1 | Atribuição e literais | Atribuição, identificadores, literais inteiros e decimais |
| 2 | Expressões aritméticas | Operadores `+ - * /`, parênteses e precedência |
| 3 | Estrutura condicional | `if` / `else`, operador relacional e indentação (`INDENT`/`DEDENT`) |
| 4 | Estrutura de repetição | `while`, operadores relacionais (`!=`) e bloco indentado |
| 5 | Com erro intencional | Expressão incompleta e parêntese sem fechar, para as etapas de análise futuras |

Os textos exatos estão em `frontend/js/exemplos.js`.

## Comunicação frontend ↔ backend

Ao clicar em **Analisar código**, o frontend envia uma requisição HTTP real ao backend, pelo Nginx.

**Requisição**

```
POST /api/analisar
Content-Type: application/json

{ "codigo": "x = 10" }
```

**Resposta de sucesso** (`200`)

```json
{ "recebido": true, "mensagem": "Código recebido com sucesso.", "linhas": 1, "caracteres": 6 }
```

**Respostas de erro**

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

A validação ocorre **nos dois lados**: o frontend avisa antes de enviar, mas o backend valida sempre, sem depender do navegador.

## Testes

Instalação das dependências de teste e execução (sem Docker):

```bash
./scripts/testar_tudo.sh
```

Ou separadamente:

```bash
# backend
cd backend
pip install -r requirements-dev.txt
python -m pytest -q

# frontend
cd frontend
npm install
npm test

# integração frontend <-> backend real (com o backend em execução na porta 5000)
BACKEND_URL=http://localhost:5000 npm test
```

Teste de implantação (com a aplicação de pé via Docker Compose):

```bash
docker compose up --build -d
./scripts/smoke_test.sh
```

**Resultados relevantes** (detalhes e pendências em [`docs/testes.md`](docs/testes.md)):

- backend: 48 testes aprovados, 0 reprovados;
- frontend: 61 testes aprovados, 0 reprovados (5 testes de integração são ignorados sem `BACKEND_URL`);
- integração frontend ↔ backend real: 66 aprovados, 0 reprovados;
- smoke test: 15 verificações aprovadas, executadas contra uma emulação do Nginx; a execução com o Docker Compose real está registrada como pendente em `docs/testes.md`.

## Solução de problemas

- **Porta 8080 em uso:** altere o mapeamento em `docker-compose.yml` (por exemplo `"8081:80"`) e acesse a nova porta (`BASE_URL=http://localhost:8081 ./scripts/smoke_test.sh`).
- **Ver logs:** `docker compose logs -f`.
- **Reconstruir do zero:** `docker compose down --rmi local && docker compose up --build -d`.

## Limitações conhecidas

- O backend apenas recebe e valida o código; **não há análise léxica, sintática ou semântica** nesta versão.
- O editor é um campo de texto simples, sem realce de sintaxe, numeração de linhas ou autocompletar.
- O limite de entrada é de 100.000 caracteres.
- Não há teste automatizado em navegador real (a interface é testada em jsdom).

## Próximas etapas

Análise léxica (expressões regulares e autômatos), análise sintática (gramática, FIRST/FOLLOW, tabela preditiva e árvore de derivação) e visualização passo a passo na interface.
