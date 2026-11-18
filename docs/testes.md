# Registro de testes

Este arquivo guarda o registro de cada etapa. A Etapa 4 vem primeiro; o registro da Etapa 3 foi mantido abaixo, sem alterações de conteúdo.

# Etapa 4 (análise sintática e AST)

Os testes das Etapas 1 a 3 foram **mantidos e continuam rodando** (regressão). Nenhum teste antigo foi alterado para passar; as únicas mudanças em arquivos existentes de teste foram acrescentar dois casos (`sintatico_valido`, `sintatico_erro`) à geração de fixtures (`gerar_fixtures.py`).

## Como executar

| Camada | Comando | Pasta |
| --- | --- | --- |
| Backend completo (scanner + parser + endpoints) | `python -m pytest -q` | `backend/` |
| Só o parser e a AST | `python -m pytest -q tests/test_sintatico.py` | `backend/` |
| Só o endpoint com análise sintática | `python -m pytest -q tests/test_api_sintatico.py` | `backend/` |
| Frontend (unitários e interface) | `npm test` | `frontend/` |
| Frontend + backend real | `BACKEND_URL=http://localhost:5000 npm test` | `frontend/` com o backend em execução |
| Tudo sem Docker | `./scripts/testar_tudo.sh` | raiz |
| Implantação (inclui 8 verificações novas do parser) | `./scripts/smoke_test.sh` | raiz, com `docker compose up --build -d` |
| Regenerar respostas de exemplo do frontend | `python tests/gerar_fixtures.py` | `backend/` |

## Resultados da última execução

Executada em **cópia limpa** do repositório (sem `node_modules`, `.venv`, `__pycache__`; ambiente virtual novo com `requirements-dev.txt` e `npm install`), via `./scripts/testar_tudo.sh`. Ambiente: Linux, Python 3.12, Node (o do ambiente de desenvolvimento).

| Funcionalidade | Arquivo | Aprovados | Reprovados |
| --- | --- | --- | --- |
| **Parser e AST**: cada construção, precedência e associatividade, aninhamento, posições, casos limite, 12+ categorias de erro com linha/coluna/mensagem, recuperação sem cascata, árvore de derivação, comparação com o módulo `ast` do Python (300 programas) | `test_sintatico.py` | 398 | 0 |
| **Endpoint** com `lexico` + `sintatico`: contrato, campos da Etapa 3 preservados, erro sintático (ast nula), erro léxico (parser não executa), programa vazio, regressão das Etapas 1 e 2, falha inesperada, entradas hostis | `test_api_sintatico.py` | 21 | 0 |
| Regressão: scanner | `test_scanner.py` | 126 | 0 |
| Regressão: verificação cruzada do scanner com `tokenize` | `test_scanner_vs_tokenize.py` | 42 | 0 |
| Regressão: endpoint da Etapa 3 (contrato plano) | `test_api.py` | 40 | 0 |
| Regressão: validação de entrada | `test_validacao.py` | 22 | 0 |
| Fixtures do frontend = resposta real do backend | `test_fixtures.py` | 1 | 0 |
| **Casos de teste documentados** (CT-01 a CT-18; CT-S01 e CT-S02 ignorados até a Etapa 5) | `test_casos_etapa4.py` | 18 (2 ignorados) | 0 |
| **Total backend** | `python -m pytest -q` | **668** (2 ignorados) | **0** |
| Funções puras da tela sintática (rótulos, texto indentado, posição, realce, JSON) | `sintatico.test.js` | 9 | 0 |
| Interface sintática (árvore, expandir/recolher, realce, filtro, exportar JSON, erros, parser não executado, programa vazio, HTML hostil, consistência tokens × derivação) | `sintatico-ui.test.js` | 22 | 0 |
| Regressão do frontend (Etapas 2 e 3) | demais arquivos | 130 (7 ignorados) | 0 |
| **Total frontend sem backend** | `npm test` | **161** (20 ignorados) | **0** |
| Frontend ↔ backend **real** (inclui os 11 exemplos da tela) | `BACKEND_URL=... npm test` | **181** | **0** |

Os testes `tokens`, `ui` e `exemplos` das Etapas 2 e 3 têm casos gerados a partir das fixtures e da lista de exemplos; por isso a contagem deles subiu (24, 37 e 14) sem que nenhum teste fosse editado.

### Verificações extras

- **Smoke test completo:** executado em 18/11/2026 contra a aplicação de pé em `http://localhost:8080`, a partir de um **clone limpo** do repositório no GitHub: **33 aprovadas, 0 reprovadas** (inclui a página inicial, os arquivos estáticos `css/` e `js/`, `/api/health`, `/api/hello`, o scanner, o parser e as entradas inválidas). **Ressalva honesta:** o ambiente usado não tem acesso ao Docker Hub (o `docker build` falha ao baixar `nginx:1.27-alpine` e `python:3.12-slim`), então a aplicação foi servida por Gunicorn na porta 5000 e por um servidor estático na 8080 que reproduz o `frontend/nginx.conf` (arquivos estáticos + encaminhamento de `/api/`). O que **falta validar** é só a construção das imagens e o Nginx em si: rode `docker compose up --build -d && ./scripts/smoke_test.sh` numa máquina com Docker Hub liberado.
- **Interface em navegador real:** conferida em Chromium (Playwright) contra o backend real: exemplos 9, 10 e 11 e o 8 em largura de celular (390 px). Sem erros no console e sem rolagem horizontal. Capturas em `docs/img/`.

## O que os testes cobrem (checklist do enunciado, seção 7)

- **Parser (7.1):** válidos por construção (atribuição, `if`, `if/else`, `while`, expressões, relacionais, unário); estrutura da AST; precedência e associatividade (`10 + 5 * 2`, `20 - 5 - 3`, `(10 + 5) * 2`); aninhamento e `else` pendente; construções incompletas; construções inválidas; posições; mensagens; casos limite (código vazio, só comentários, número com 6.000 dígitos, cadeias e aninhamento acima do limite); integração com o scanner (as folhas da árvore de derivação = tokens).
- **Referência externa:** 200 programas aleatórios cuja AST é comparada, nó a nó, com a do `ast` do Python; 100 sem parênteses também com início e fim de cada nó.
- **Backend (7.2):** código válido, erro sintático (`ast` nula), erro léxico (parser não roda, decisão documentada), entrada vazia como na Etapa 2 (422), contrato mantendo os campos da Etapa 3, códigos HTTP, regressão.
- **Interface (7.3):** árvore exibida, erros com linha/coluna/esperado/encontrado, parser não executado, programa vazio, expandir/recolher, realce, filtro, JSON, acessibilidade (não depende de cor), HTML hostil não é interpretado.
- **Consistência token × árvore (7.4):** folhas da derivação = tokens; nós da tela = `total_nos` da resposta.
- **Regressão (7.5):** todos os testes das Etapas 1 a 3.

## Falhas encontradas durante o desenvolvimento e correções

| Falha | Correção |
| --- | --- |
| `test_fixtures` (Etapa 3) falhou depois de acrescentar `lexico` e `sintatico` à resposta | Esperado: o teste existe para avisar que as fixtures ficaram desatualizadas. As fixtures foram **regeneradas** com o scanner/parser reais (`gerar_fixtures.py`); o teste não foi alterado |
| Erro de "parêntese não fechado" no fim do arquivo apontava para a linha 3, que não existe (o `NEWLINE` sintético do scanner fica na linha seguinte) | Para fim de arquivo, o erro aponta o fim do último token com conteúdo; teste dedicado |
| `if = 3` dava a mensagem genérica "esperava identificador, número ou '('" | Mensagem específica de palavra reservada usada como variável; o teste (escrito primeiro) já cobrava isso |
| Teste de interface comparava `Encontrado fim da linha` mas o `textContent` do DOM junta `<dt>` e `<dd>` sem espaço | Erro do teste (a tela estava certa): regex ajustada com `\s*` |
| Primeira versão da tela deixava os rótulos da árvore quebrarem em várias linhas e o painel do nó longe do clique | Layout em coluna única, painel e código acima da árvore, rótulos sem quebra; refeitas as capturas |
| Exemplo 11 prometia "parêntese sem fechar" e "else sem if", mas o parser (corretamente) descartava o `else` do `if` com erro | Exemplo reescrito para mostrar erros que de fato aparecem; a descrição agora corresponde à saída |

## Pendências e limitações (o que **não** foi validado)

- **Docker Compose real:** o ambiente em que esta etapa foi desenvolvida **não tem Docker**. Portanto **não foram executados** `docker compose up --build`, o smoke test completo (com Nginx) nem a verificação de que a imagem do backend contém os novos arquivos. O que foi feito: `backend/Dockerfile` passou a copiar `arvore.py` e `sintatico.py` (sem isso o contêiner falharia ao importar); `docker-compose.yml`, `nginx.conf` e o Dockerfile do frontend **não mudaram** (o Nginx já serve `js/` inteiro). Rodar `docker compose up --build -d && ./scripts/smoke_test.sh` num clone limpo é a validação que falta.
- Não há teste automatizado em navegador real no repositório; a interface é testada em jsdom e verificada manualmente com Playwright (capturas).
- Não há avaliação com estudantes.
- Diferenciais **não** implementados: construção passo a passo da árvore e integração com Ollama/Llama 3.2 (ver `docs/sintatico.md`, seção 7).

## Histórico: registro da Etapa 3 (análise léxica)

Registro do que foi testado na Etapa 3. Os testes das Etapas 1 e 2 foram **mantidos** e continuam rodando (regressão).

## Como executar

| Camada | Comando | Pasta |
| --- | --- | --- |
| Backend (scanner + endpoints + validação) | `python -m pytest -q` | `backend/` (após `pip install -r requirements-dev.txt`) |
| Só o scanner | `python -m pytest -q tests/test_scanner.py` | `backend/` |
| Frontend (unitários + interface) | `npm test` | `frontend/` (após `npm install`) |
| Frontend + backend real (integração) | `BACKEND_URL=http://localhost:5000 npm test` | `frontend/` com o backend em execução |
| Implantação / ponta a ponta | `./scripts/smoke_test.sh` | raiz, com `docker compose up --build -d` |
| Backend + frontend (sem Docker) | `./scripts/testar_tudo.sh` | raiz |
| Regenerar respostas de exemplo do frontend | `python tests/gerar_fixtures.py` | `backend/` |

## Resultados da última execução

| Funcionalidade / módulo | Tipo | Arquivo | Aprovados | Reprovados |
| --- | --- | --- | --- | --- |
| **Scanner**: palavras reservadas, identificadores, literais (válidos e malformados), operadores, delimitadores, comentários, espaços, posição, erros, INDENT/DEDENT, bordas, aleatório | Unitário | `test_scanner.py` | 126 | 0 |
| Endpoint `/api/analisar` com tokens/erros (contrato da Etapa 3) + regressão das Etapas 1 e 2 | Endpoints / regressão | `test_api.py` | 40 | 0 |
| Regras de validação | Unitário / regressão | `test_validacao.py` | 22 | 0 |
| Fixtures do frontend iguais à resposta real do backend | Contrato | `test_fixtures.py` | 1 | 0 |
| **Verificação cruzada** do scanner contra o módulo `tokenize` da biblioteca padrão do Python (tipo, lexema, linha e coluna): 20 programas fixos, 300 programas aleatórios do subconjunto | Referência | `test_scanner_vs_tokenize.py` | 42 | 0 |
| **Total backend** | | `python -m pytest -q` | **231** | **0** |
| Catálogo de tokens, explicações, segmentação do realce | Unitário | `tokens.test.js` | 22 | 0 |
| Tabela, código colorido, erros, passo a passo, segurança (XSS), responsividade | Interface (jsdom) | `lexico-ui.test.js` | 33 | 0 |
| Tela, exemplos, edição, envio, mensagens de erro (Etapa 2, adaptado) | Interface / regressão | `ui.test.js` | 35 | 0 |
| Validação, exemplos, módulo de API | Unitário / regressão | `validacao.test.js`, `exemplos.test.js`, `api.test.js` | 34 | 0 |
| **Total frontend (sem backend)** | | `npm test` | **124** (7 ignorados) | **0** |
| Frontend ↔ backend real (inclui todos os 9 exemplos da tela) | Integração | `BACKEND_URL=http://127.0.0.1:5000 npm test` | **131** | **0** |
| Implantação e contrato HTTP via proxy | Smoke test | `./scripts/smoke_test.sh` | 24 | 0 |

### O que os testes cobrem (checklist do enunciado, seção 6)

- **6.1 Scanner:** cada palavra reservada, identificadores válidos e inválidos, inteiros, decimais e literais malformados (`007`, `3.`, `.5`, `1.2.3`, `12abc`, `1e5`), todos os operadores (inclusive `==`, `!=`, `<=`, `>=`), delimitadores, comentários, espaços e quebras (`\n`, `\r\n`, `\r`), linha/coluna em várias linhas, caracteres inválidos com localização, strings, tabulação e indentação inconsistente, e bordas: código vazio, só espaços, só comentários, token no fim do arquivo sem quebra de linha. Há ainda um teste com 600 entradas aleatórias (semente fixa) que exige: nunca lançar exceção, `FIM_DE_ARQUIVO` sempre por último e todo lexema estar exatamente na linha/coluna informada.
- **Referência externa:** a sequência de tokens do scanner é comparada, token a token, com a do `tokenize` do Python em programas do subconjunto. Isso não prova correção para entradas fora do subconjunto, onde o scanner é propositalmente mais restrito.
- **6.2 Endpoints:** requisição válida → `sucesso: true` e tokens; erro léxico → HTTP 200 com `sucesso: false` e `erros`; entrada vazia como na Etapa 2 (422); formato de cada token/erro; limite de 200 erros; falha inesperada no scanner → 500 genérico sem detalhes internos.
- **6.3 Interface:** tokens na tabela, erros com linha e coluna, trechos com erro marcados no código, interface estável com entradas inválidas (HTML/script no código nunca é inserido como HTML), passo a passo (Próximo, Anterior, Reproduzir, Pausar, Mostrar tudo), contagem por categoria, funcionalidades da Etapa 2 preservadas.
- **6.4 Regressão:** todos os testes das Etapas 1 e 2 executados (backend e frontend), integração com o backend real e smoke test.

## Falhas encontradas durante o desenvolvimento e correções

| Falha | Correção |
| --- | --- |
| `test_analisar_codigo_valido` (Etapa 2) falhou: a mensagem de sucesso agora é "Análise léxica concluída sem erros." | Mudança intencional do contrato; teste atualizado. Campos `recebido`, `linhas` e `caracteres` foram mantidos |
| Teste de interface "sucesso mostra a mensagem do backend" (Etapa 2) falhou pelo mesmo motivo | Teste adaptado para a nova tela de resultados |
| Mensagem de indentação inconsistente listava os níveis **depois** de desempilhar (mostrava só `0`) | Níveis capturados antes do desempilhamento |
| Depois de um erro de indentação, linhas seguintes com o mesmo recuo repetiam o erro | O novo nível é registrado na pilha para recuperação |
| Uma string como `"Ana"` gerava dois erros (as duas aspas) e `Ana` virava identificador | A string inteira passa a ser **um único** erro; string sem fechar vai até o fim da linha |
| Dois testes de interface comparavam texto sem contar os `\n` reais; um terceiro concatenava `IDENTIFICADOR` e `×4` sem espaço | Testes corrigidos (o código do produto estava certo) |
| Na verificação cruzada com o `tokenize`, `FIM_DE_ARQUIVO` e `DEDENT` ficavam na mesma linha do último token quando o arquivo não terminava em quebra de linha; o Python os coloca na linha seguinte | Scanner alinhado à convenção do Python; teste dedicado |
| O realce duplicaria o texto quando um erro de tabulação coincidia com o token `INDENT` | `montarSegmentos` trata sobreposição; teste dedicado |

## Execução com Docker real

Executado pela autora em Linux (WSL), com Docker 29.9.2 e Docker Compose v5.6.1, a partir de um clone limpo do repositório:

| Verificação em Docker real | Resultado |
| --- | --- |
| `docker compose up --build -d` | aprovado: os dois contêineres subiram e a aplicação respondeu em `http://localhost:8080` |
| `./scripts/smoke_test.sh` | **aprovado: 24 aprovados, 0 reprovados** |
| Fluxo manual em `http://localhost:8080`: escolher o exemplo 9, analisar, ver erros léxicos, código colorido, tokens e passo a passo | aprovado (capturas de tela da execução) |

Na fase de desenvolvimento, o mesmo smoke test já havia passado (24/24) contra uma emulação do Nginx, pois o ambiente de desenvolvimento não conseguia baixar as imagens do Docker Hub. A alteração feita nos arquivos do Docker foi mínima: o `backend/Dockerfile` agora copia também `scanner.py`. O `docker-compose.yml`, o `nginx.conf` e o Dockerfile do frontend não mudaram.

## Verificação manual da interface

Conferida em Chromium (Playwright) com a pilha emulada: telas inicial, com blocos aninhados no passo a passo, com erros léxicos e em largura de celular (390 px). Sem erros de JavaScript no console e sem rolagem horizontal da página no celular. As capturas estão em `docs/img/`.

## Limitações e testes que ainda faltam

- Não há teste automatizado de navegador real (Playwright/Selenium) no repositório; a interface é testada em jsdom e verificada manualmente.
- Os testes de implantação dependem de rodar o Docker manualmente (não há CI configurado).
- Não há análise sintática/semântica, então não há testes dessas fases (Etapas 4 e 5).
