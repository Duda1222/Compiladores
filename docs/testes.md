# Registro de testes: Etapa 2

Registro do que foi testado durante a Etapa 2 (interface web e entrada de código-fonte).

## Como executar

| Camada | Comando | Pasta |
| --- | --- | --- |
| Backend (unitários + endpoints) | `python -m pytest -q` | `backend/` (após `pip install -r requirements-dev.txt`) |
| Frontend (unitários + interface) | `npm test` | `frontend/` (após `npm install`) |
| Frontend + backend real (integração) | `BACKEND_URL=http://localhost:5000 npm test` | `frontend/` com o backend em execução |
| Implantação / ponta a ponta | `./scripts/smoke_test.sh` | raiz, com `docker compose up --build -d` |
| Backend + frontend (sem Docker) | `./scripts/testar_tudo.sh` | raiz |

## Resultados da última execução

| Funcionalidade / módulo | Tipo | Comando | Aprovados | Reprovados |
| --- | --- | --- | --- | --- |
| Regras de validação (`validacao.py`) | Unitário | `pytest tests/test_validacao.py` | 22 | 0 |
| Endpoints `/api/analisar`, `/api/hello`, `/api/health`, erros 404/405/500 | Endpoints / regressão | `pytest tests/test_api.py` | 26 | 0 |
| **Total backend** | | `python -m pytest -q` | **48** | **0** |
| Validação, exemplos, módulo de API | Unitário | `npm test` | 30 | 0 |
| Tela, exemplos, edição, envio, mensagens de erro | Interface (jsdom) | `npm test` | 31 | 0 |
| **Total frontend (sem backend)** | | `npm test` | **61** (5 ignorados) | **0** |
| Frontend ↔ backend real | Integração | `BACKEND_URL=http://127.0.0.1:5000 npm test` | **66** (inclui os 5 acima) | **0** |
| Implantação e contrato HTTP via proxy | Smoke test | `./scripts/smoke_test.sh` | 15 | 0 |

### Observação importante sobre o smoke test e o Docker

O `smoke_test.sh` foi executado, e passou (15/15), contra uma **emulação** do Nginx
(servidor Python que serve o frontend e repassa `/api/*` ao backend em Gunicorn),
porque o ambiente de desenvolvimento usado nesta etapa não tinha daemon Docker.
Portanto:

- `docker compose config` foi validado (sintaxe do `docker-compose.yml` correta);
- **`docker compose up --build` ainda não foi executado neste registro.** Antes da entrega
  é necessário rodar `docker compose up --build -d` e depois `./scripts/smoke_test.sh`
  numa máquina com Docker, e anotar o resultado abaixo.

| Verificação em Docker real | Resultado |
| --- | --- |
| `docker compose up --build -d` | _pendente_ |
| `./scripts/smoke_test.sh` | _pendente_ |

## Falhas encontradas durante o desenvolvimento

- `npm test` com `node --test tests/` falhou no Node 22 (tratava a pasta como módulo).
  Corrigido usando o padrão `node --test "tests/*.test.js"`.

## Limitações e testes que ainda faltam

- Não há teste automatizado de navegador real (ponta a ponta com Playwright/Selenium);
  a interface é testada em jsdom e verificada manualmente em um navegador.
- Os testes de implantação dependem de rodar o Docker manualmente (não há CI configurado).
- O backend ainda não faz análise léxica/sintática/semântica, então não há testes dessas fases.
