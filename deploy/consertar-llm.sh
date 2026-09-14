#!/usr/bin/env bash
# Correção pontual nº 1: troca a chave do LLM do robô pela que está viva.
#
# Uso:  ./deploy/consertar-llm.sh
#
# Lê a configuração atual da IA de fábrica, mostra, pede confirmação e grava
# a chave do brain/config.env (ARK_API_KEY) no lugar da atual. Preserva
# base_url e model. NÃO mexe em ASR nem TTS.
#
# ATENÇÃO: a chave antiga do robô vem mascarada pela API — ao trocar, ela se
# perde. Isso é reversível criando/colando outra chave no console ModelArk.

set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
source "$RAIZ/brain/config.env" 2>/dev/null || { echo "Falta brain/config.env"; exit 1; }
IP="${SIRIUS_HOST:?preencha SIRIUS_HOST no config.env}"
: "${ARK_API_KEY:?preencha ARK_API_KEY no config.env}"
BASE="http://$IP:8088/api/v1/ai/credentials"

echo "=== Antes ==="
ANTES="$(curl -sS --max-time 10 "$BASE/status")" || { echo "robô não respondeu"; exit 1; }
echo "$ANTES"

URL_ATUAL="$(printf '%s' "$ANTES" | sed -n 's/.*"base_url":"\([^"]*\)".*/\1/p')"
MOD_ATUAL="$(printf '%s' "$ANTES" | sed -n 's/.*"model":"\([^"]*\)".*/\1/p')"
URL="${URL_ATUAL:-${ARK_BASE_URL:-https://ark.ap-southeast.bytepluses.com/api/v3}}"
MOD="${MOD_ATUAL:-${ARK_ENDPOINT_ID:-dola-seed-2-1-turbo-260628}}"

echo
echo "Vou gravar no robô:"
echo "  base_url : $URL   (mantida)"
echo "  model    : $MOD   (mantido)"
echo "  api_key  : ${ARK_API_KEY:0:12}…${ARK_API_KEY: -5}   (a do seu config.env)"
echo
read -r -p "Confirma? (s/N) " R
[[ "$R" == "s" || "$R" == "S" ]] || { echo "Cancelado, nada foi alterado."; exit 0; }

echo
echo "=== Gravando ==="
curl -sS --max-time 15 -X POST "$BASE" -H 'Content-Type: application/json' \
  -d "{\"llm\":{\"api_key\":\"$ARK_API_KEY\",\"base_url\":\"$URL\",\"model\":\"$MOD\",\"provider\":\"openai\"}}"
echo

echo
echo "=== Depois ==="
curl -sS --max-time 10 "$BASE/status"; echo

echo
echo "Agora teste a conversa no painel/no robô. Se ainda falhar, o problema"
echo "não é a chave: é o Safe Experience Mode pausando o modelo para a conta"
echo "inteira — console.byteplus.com → ModelArk → Model activation."
