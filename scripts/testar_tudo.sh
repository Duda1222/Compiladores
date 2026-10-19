#!/usr/bin/env bash
# Executa a bateria de testes que não depende do Docker:
#   1. testes do backend (pytest)
#   2. testes do frontend (node:test + jsdom)
# Para incluir o teste de implantação, suba o Compose e rode também
# ./scripts/smoke_test.sh

set -euo pipefail
raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== Backend (pytest) =="
cd "$raiz/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements-dev.txt
fi
.venv/bin/python -m pytest -q

echo
echo "== Frontend (node:test + jsdom) =="
cd "$raiz/frontend"
[ -d node_modules ] || npm install --no-audit --no-fund --silent
npm test
