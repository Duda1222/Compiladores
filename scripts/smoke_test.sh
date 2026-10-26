#!/usr/bin/env bash
# Teste de implantação / ponta a ponta contra a aplicação em execução.
# Use com a aplicação de pé:  docker compose up --build -d
# Depois:                      ./scripts/smoke_test.sh
# Para outro endereço:         BASE_URL=http://localhost:8081 ./scripts/smoke_test.sh

set -u
BASE_URL="${BASE_URL:-http://localhost:8080}"
ESPERA_MAX="${ESPERA_MAX:-60}"

aprovados=0
reprovados=0

ok()   { echo "  [OK]    $1"; aprovados=$((aprovados + 1)); }
falha() { echo "  [FALHA] $1"; reprovados=$((reprovados + 1)); }

# Compara o status HTTP de uma requisição.
verificar_status() {
  local descricao="$1" esperado="$2"; shift 2
  local obtido
  obtido=$(curl -s -o /dev/null -w "%{http_code}" "$@")
  if [ "$obtido" = "$esperado" ]; then ok "$descricao (HTTP $obtido)"; else falha "$descricao (esperado $esperado, obtido $obtido)"; fi
}

# Verifica se o corpo da resposta contém um trecho.
verificar_corpo() {
  local descricao="$1" trecho="$2"; shift 2
  local corpo
  corpo=$(curl -s "$@")
  if printf '%s' "$corpo" | grep -qF -- "$trecho"; then ok "$descricao"; else falha "$descricao (trecho não encontrado: $trecho)"; fi
}

echo "Aguardando a aplicação em $BASE_URL (até ${ESPERA_MAX}s)..."
inicio=$(date +%s)
until curl -sf "$BASE_URL/api/health" > /dev/null 2>&1; do
  if [ $(( $(date +%s) - inicio )) -ge "$ESPERA_MAX" ]; then
    echo "A aplicação não respondeu a tempo. Verifique: docker compose ps / docker compose logs"
    exit 2
  fi
  sleep 2
done
echo "Aplicação disponível."

echo
echo "Frontend (servido pelo Nginx)"
verificar_status "página inicial responde" 200 "$BASE_URL/"
verificar_corpo  "página identifica o sistema" "Compilador Educacional" "$BASE_URL/"
verificar_corpo  "página identifica a linguagem Python" "Python" "$BASE_URL/"
verificar_status "css/estilo.css disponível" 200 "$BASE_URL/css/estilo.css"
verificar_status "js/app.js disponível" 200 "$BASE_URL/js/app.js"
verificar_status "js/exemplos.js disponível" 200 "$BASE_URL/js/exemplos.js"
verificar_status "js/tokens.js disponível" 200 "$BASE_URL/js/tokens.js"
verificar_status "js/resultado.js disponível" 200 "$BASE_URL/js/resultado.js"

echo
echo "Backend via proxy do Nginx (comunicação entre contêineres)"
verificar_corpo  "GET /api/health" '"status":"ok"' "$BASE_URL/api/health"
verificar_corpo  "GET /api/hello (regressão da Etapa 1)" "Hello, World!" "$BASE_URL/api/hello"

echo
echo "Contrato de POST /api/analisar"
JSON=(-H "Content-Type: application/json")
verificar_status "código válido" 200 -X POST "${JSON[@]}" -d '{"codigo":"x = 10"}' "$BASE_URL/api/analisar"
verificar_corpo  "resposta confirma recebimento" '"recebido":true' -X POST "${JSON[@]}" -d '{"codigo":"x = 10"}' "$BASE_URL/api/analisar"
verificar_corpo  "scanner: lista de tokens" '"tipo":"IDENTIFICADOR"' -X POST "${JSON[@]}" -d '{"codigo":"x = 10"}' "$BASE_URL/api/analisar"
verificar_corpo  "scanner: literal inteiro reconhecido" '"tipo":"LITERAL_INTEIRO"' -X POST "${JSON[@]}" -d '{"codigo":"x = 10"}' "$BASE_URL/api/analisar"
verificar_corpo  "scanner: sucesso true sem erros" '"sucesso":true' -X POST "${JSON[@]}" -d '{"codigo":"x = 10"}' "$BASE_URL/api/analisar"
verificar_status "scanner: código com erro léxico (HTTP 200)" 200 -X POST "${JSON[@]}" -d '{"codigo":"x = 10 @ 2"}' "$BASE_URL/api/analisar"
verificar_corpo  "scanner: erro léxico reportado" '"tipo":"ERRO_LEXICO"' -X POST "${JSON[@]}" -d '{"codigo":"x = 10 @ 2"}' "$BASE_URL/api/analisar"
verificar_corpo  "scanner: sucesso false com erro" '"sucesso":false' -X POST "${JSON[@]}" -d '{"codigo":"x = 10 @ 2"}' "$BASE_URL/api/analisar"
verificar_corpo  "scanner: INDENT/DEDENT em blocos" '"tipo":"INDENT"' -X POST "${JSON[@]}" -d '{"codigo":"if x:\n    y = 1\n"}' "$BASE_URL/api/analisar"
verificar_status "texto vazio" 422 -X POST "${JSON[@]}" -d '{"codigo":""}' "$BASE_URL/api/analisar"
verificar_status "somente espaços" 422 -X POST "${JSON[@]}" -d '{"codigo":"   \n  "}' "$BASE_URL/api/analisar"
verificar_status "campo ausente" 400 -X POST "${JSON[@]}" -d '{"outro":"x"}' "$BASE_URL/api/analisar"
verificar_status "JSON malformado" 400 -X POST "${JSON[@]}" -d '{codigo: x' "$BASE_URL/api/analisar"
verificar_status "método não permitido" 405 "$BASE_URL/api/analisar"

echo
echo "Resumo: $aprovados aprovados, $reprovados reprovados."
[ "$reprovados" -eq 0 ]
