# Compilador Educacional

Software educacional web para o ensino de **análise léxica e análise sintática** de um subconjunto da linguagem **Python**, com visualização passo a passo voltada a estudantes de graduação em Ciência da Computação.

**Autora:** Maria Eduarda Almeida Lopes
**Disciplina:** Compiladores. Trabalho 1, primeira etapa do projeto.

Nesta etapa o objetivo é preparar a base do projeto: estrutura do repositório, aplicação web mínima (frontend + backend) exibindo "Hello, World!" e ambiente Docker reproduzível.

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

## Estrutura do repositório

```
.
├── backend/              # API em Python (Flask + Gunicorn)
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # Interface web estática servida pelo Nginx
│   ├── index.html
│   ├── nginx.conf
│   └── Dockerfile
├── config/               # Arquivos de configuração (reservada para as próximas etapas)
├── docker-compose.yml
├── .gitignore
├── .dockerignore
└── README.md
```

O frontend exibe a interface e encaminha as chamadas `/api/*` ao backend por meio do Nginx. Nesta etapa não há banco de dados.

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

Depois abra no navegador: <http://localhost:8080>. A página deve exibir **Hello, World!**.

Para testar o backend diretamente pelo terminal (pelo Nginx):

```bash
curl http://localhost:8080/api/hello
# {"message":"Hello, World!"}
```

## Como encerrar

```bash
docker compose down
```

Para remover também as imagens construídas:

```bash
docker compose down --rmi local
```

## Solução de problemas

- **Porta 8080 em uso:** altere o mapeamento em `docker-compose.yml` (por exemplo `"8081:80"`) e acesse a nova porta.
- **Ver logs:** `docker compose logs -f`.
- **Reconstruir do zero:** `docker compose down --rmi local && docker compose up --build -d`.

## Próximas etapas

Análise léxica (expressões regulares e autômatos), análise sintática (gramática, FIRST/FOLLOW, tabela preditiva e árvore de derivação) e visualização passo a passo na interface.
