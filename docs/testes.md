# Registro de testes: Etapa 3 (análise léxica)

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
| **Scanner**: palavras reservadas, identificadores, literais (válidos e malformados), operadores, delimitadores, comentários, espaços, posição, erros, INDENT/DEDENT, bordas, aleatório | Unitário | `test_scanner.py` | 125 | 0 |
| Endpoint `/api/analisar` com tokens/erros (contrato da Etapa 3) + regressão das Etapas 1 e 2 | Endpoints / regressão | `test_api.py` | 40 | 0 |
| Regras de validação | Unitário / regressão | `test_validacao.py` | 22 | 0 |
| Fixtures do frontend iguais à resposta real do backend | Contrato | `test_fixtures.py` | 1 | 0 |
| **Total backend** | | `python -m pytest -q` | **188** | **0** |
| Catálogo de tokens, explicações, segmentação do realce | Unitário | `tokens.test.js` | 22 | 0 |
| Tabela, código colorido, erros, passo a passo, segurança (XSS), responsividade | Interface (jsdom) | `lexico-ui.test.js` | 33 | 0 |
| Tela, exemplos, edição, envio, mensagens de erro (Etapa 2, adaptado) | Interface / regressão | `ui.test.js` | 35 | 0 |
| Validação, exemplos, módulo de API | Unitário / regressão | `validacao.test.js`, `exemplos.test.js`, `api.test.js` | 34 | 0 |
| **Total frontend (sem backend)** | | `npm test` | **124** (7 ignorados) | **0** |
| Frontend ↔ backend real (inclui todos os 9 exemplos da tela) | Integração | `BACKEND_URL=http://127.0.0.1:5000 npm test` | **131** | **0** |
| Implantação e contrato HTTP via proxy | Smoke test | `./scripts/smoke_test.sh` | 24 | 0 |

### O que os testes cobrem (checklist do enunciado, seção 6)

- **6.1 Scanner:** cada palavra reservada, identificadores válidos e inválidos, inteiros, decimais e literais malformados (`007`, `3.`, `.5`, `1.2.3`, `12abc`, `1e5`), todos os operadores (inclusive `==`, `!=`, `<=`, `>=`), delimitadores, comentários, espaços e quebras (`\n`, `\r\n`, `\r`), linha/coluna em várias linhas, caracteres inválidos com localização, strings, tabulação e indentação inconsistente, e bordas: código vazio, só espaços, só comentários, token no fim do arquivo sem quebra de linha. Há ainda um teste com 600 entradas aleatórias (semente fixa) que exige: nunca lançar exceção, `FIM_DE_ARQUIVO` sempre por último e todo lexema estar exatamente na linha/coluna informada.
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
