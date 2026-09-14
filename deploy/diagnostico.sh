#!/usr/bin/env bash
# Fase 1 — Engenharia reversa da comunicação: descobre EXATAMENTE onde a
# corrente IA ↔ APIs ↔ Sirius está quebrando, testando um elo por vez.
#
# Uso: preencha brain/config.env (copie de brain/config.example.env) e rode
#   ./deploy/diagnostico.sh
#
# Rode do SEU computador, na mesma rede do cachorro. Requer curl e ssh.
# O script NÃO instala nada, NÃO altera nada no robô e só envia a sua chave
# para a própria API do ModelArk/Anthropic — nunca para outro lugar.
#
# Ele para no primeiro elo quebrado e diz o que fazer. Corrigiu? Rode de novo.

set -uo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$RAIZ/brain/config.env"

verde()    { printf '\033[32m%s\033[0m\n' "$*"; }
vermelho() { printf '\033[31m%s\033[0m\n' "$*"; }
titulo()   { printf '\n\033[1m%s\033[0m\n' "$*"; }

falha() {
    # falha "<resumo>" "<o que fazer>"
    vermelho ""
    vermelho "❌ PONTO DE FALHA ENCONTRADO: $1"
    echo ""
    echo "O que fazer:"
    echo "$2"
    echo ""
    echo "Depois de corrigir, rode ./deploy/diagnostico.sh de novo."
    exit 1
}

titulo "Diagnóstico Sirius — um elo por vez"

# ---------------------------------------------------------------- elo 0
titulo "[0/6] Configuração local (brain/config.env)"
if [[ ! -f "$CONFIG" ]]; then
    falha "brain/config.env não existe" \
"  cp brain/config.example.env brain/config.env
  e preencha as chaves (ARK_API_KEY, ARK_ENDPOINT_ID, SIRIUS_HOST...)."
fi
# shellcheck disable=SC1090
source "$CONFIG"

ARK_BASE_URL="${ARK_BASE_URL:-https://ark.ap-southeast.bytepluses.com/api/v3}"
ARK_HOST="$(printf '%s' "$ARK_BASE_URL" | sed -E 's|^https?://([^/]+).*|\1|')"

[[ -n "${ARK_API_KEY:-}" ]]     || falha "ARK_API_KEY vazio no config.env" \
"  Pegue a chave em console.byteplus.com → ModelArk → API keys e preencha
  ARK_API_KEY no brain/config.env."
[[ -n "${ARK_ENDPOINT_ID:-}" ]] || falha "ARK_ENDPOINT_ID vazio no config.env" \
"  Pegue o ID (começa com ep-) em ModelArk → Online inference e preencha
  ARK_ENDPOINT_ID no brain/config.env. Ex.: ep-20260901203214-pbcr4"
verde "✅ Configuração encontrada (endpoint $ARK_ENDPOINT_ID)"

# ---------------------------------------------------------------- elo 1
titulo "[1/6] Seu computador → internet (DNS + HTTPS até $ARK_HOST)"
if ! curl -sS --max-time 15 -o /dev/null "https://$ARK_HOST"; then
    falha "seu computador não alcança $ARK_HOST" \
"  Problema de internet/DNS no SEU computador ou na sua rede.
  Teste: curl -v https://$ARK_HOST — e confira Wi-Fi, VPN e firewall."
fi
verde "✅ Internet OK a partir do seu computador"

# ---------------------------------------------------------------- elo 2
titulo "[2/6] Seu computador → API do modelo (chave + endpoint de verdade)"
RESP="$(curl -sS --max-time 60 -w '\n%{http_code}' "$ARK_BASE_URL/chat/completions" \
    -H "Authorization: Bearer $ARK_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$ARK_ENDPOINT_ID\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":8}")"
HTTP="$(printf '%s' "$RESP" | tail -n1)"
CORPO="$(printf '%s' "$RESP" | sed '$d')"
case "$HTTP" in
    200) verde "✅ API respondeu (HTTP 200) — chave e endpoint válidos" ;;
    401|403) falha "a API recusou a chave (HTTP $HTTP)" \
"  A ARK_API_KEY está errada, incompleta ou revogada.
  Pegue a chave COMPLETA em ModelArk → API keys e atualize o config.env." ;;
    404) falha "a API não achou o endpoint (HTTP 404)" \
"  O ARK_ENDPOINT_ID está errado ou é de outra região.
  Confira o ID (ep-...) em ModelArk → Online inference, região Johor." ;;
    *) falha "a API devolveu HTTP $HTTP" \
"  Resposta da API: $CORPO
  Confira saldo/ativação do modelo no console do ModelArk." ;;
esac

# ---------------------------------------------------------------- elo 3
titulo "[3/6] Seu computador → cachorro (SSH em ${SIRIUS_HOST:-?})"
[[ -n "${SIRIUS_HOST:-}" ]] || falha "SIRIUS_HOST vazio no config.env" \
"  Preencha SIRIUS_HOST com o IP do cachorro na SUA rede (pasta SSH do
  Desktop, ou o app da Hengbot mostra o IP). Este passo e os seguintes
  precisam do robô ligado e no mesmo Wi-Fi que você."
DESTINO="${SIRIUS_SSH_USER:-root}@$SIRIUS_HOST"
if ! ssh -o ConnectTimeout=10 -o BatchMode=no "$DESTINO" true; then
    falha "não consegui entrar por SSH em $DESTINO" \
"  1. O cachorro está ligado e no mesmo Wi-Fi que o seu computador?
  2. O IP mudou? (roteadores trocam IP; confira no app/roteador)
  3. Usuário/senha corretos? Teste manualmente: ssh $DESTINO"
fi
verde "✅ SSH no cachorro OK"

# Bônus: o Core API oficial do robô (porta 8088) está de pé?
if curl -sS --max-time 10 -o /dev/null "http://$SIRIUS_HOST:8088/api/v1/system/ping"; then
    verde "✅ Sirius Core API respondendo em $SIRIUS_HOST:8088 (docs/API-SIRIUS-CORE.md)"

    # Para onde a IA NATIVA do robô aponta hoje? (endpoint achado pela
    # comunidade — pode não existir em todo firmware; leitura apenas)
    CRED="$(curl -sS --max-time 10 "http://$SIRIUS_HOST:8088/api/v1/ai/credentials/status" 2>/dev/null)"
    if [[ -n "$CRED" ]]; then
        echo "ℹ️  Configuração atual da IA de fábrica (ai/credentials/status):"
        echo "$CRED"
        echo "   → se llm.base_url apontar para um host inacessível, ESTE é o"
        echo "     motivo do 网络异常 no painel. Ver a hipótese de correção em"
        echo "     docs/PESQUISA-HENGBOT-SIRIUS.md (apontar para o ModelArk)."
    else
        echo "ℹ️  /api/v1/ai/credentials/status não existe neste firmware (ok, siga)."
    fi
else
    vermelho "⚠️  Core API (porta 8088) não respondeu — o cérebro próprio vai
    precisar dele para falar/mover/ver. Siga o diagnóstico; se o resto
    passar, confira se o serviço core_api_node está rodando no robô."
fi

# ---------------------------------------------------------------- elo 4
titulo "[4/6] Cachorro → internet (DNS + HTTPS até $ARK_HOST, de DENTRO dele)"
if ! ssh "$DESTINO" "curl -sS --max-time 20 -o /dev/null https://$ARK_HOST 2>&1 || wget -q --timeout=20 -O /dev/null https://$ARK_HOST 2>&1"; then
    falha "o CACHORRO não alcança $ARK_HOST (é aqui que o 网络异常 nasce)" \
"  O robô está sem saída para a internet ou sem DNS:
  1. Confira o Wi-Fi do robô (pode estar numa rede sem internet/cativa).
  2. Dentro dele (ssh $DESTINO): ping -c2 8.8.8.8   → falhou? é rede/roteador.
     nslookup $ARK_HOST                             → falhou? é DNS.
  3. Roteador com bloqueio de sites/regiões? Libere $ARK_HOST."
fi
verde "✅ O cachorro alcança a internet e o host da API"

# Bônus: e o host de FALA da IA de fábrica (ASR Volcano/ByteDance)?
if ssh "$DESTINO" "curl -sS --max-time 15 -o /dev/null https://openspeech.bytedance.com 2>/dev/null || wget -q --timeout=15 -O /dev/null https://openspeech.bytedance.com 2>/dev/null"; then
    verde "✅ openspeech.bytedance.com alcançável — o OUVIR de fábrica tem rede"
else
    vermelho "⚠️  openspeech.bytedance.com INACESSÍVEL de dentro do robô — é o
    ASR (fala→texto) da IA de fábrica. Se o painel reclama de rede ao
    falar com o cachorro, é provável que seja isto. Saídas mapeadas em
    docs/PESQUISA-HENGBOT-SIRIUS.md (shim Whisper local ou cérebro próprio)."
fi

# ---------------------------------------------------------------- elo 5
titulo "[5/6] Cachorro → API do modelo (a mesma chamada, de DENTRO dele)"
HTTP_ROBO="$(ssh "$DESTINO" "curl -sS --max-time 60 -o /dev/null -w '%{http_code}' '$ARK_BASE_URL/chat/completions' \
    -H 'Authorization: Bearer $ARK_API_KEY' \
    -H 'Content-Type: application/json' \
    -d '{\"model\":\"$ARK_ENDPOINT_ID\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":8}'" 2>/dev/null)"
if [[ "$HTTP_ROBO" != "200" ]]; then
    falha "de dentro do cachorro a API devolveu HTTP ${HTTP_ROBO:-nada}" \
"  A internet do robô funciona, mas a chamada à API falha lá dentro.
  Como o mesmo trio funcionou do seu computador (elo 2), suspeite de:
  1. Relógio do robô atrasado (TLS falha): ssh $DESTINO date
  2. Certificados TLS antigos no robô (atualize ca-certificates).
  3. O painel do robô configurado com URL/ID/chave diferentes destes."
fi
verde "✅ O cachorro fala com a API do modelo — corrente de rede INTEIRA OK"

# ---------------------------------------------------------------- elo 6
titulo "[6/6] Veredito"
verde "✅ Todos os elos de rede funcionam."
echo ""
echo "Se o painel (Mundo Interior) AINDA mostrar 网络异常/erro de modelo, o"
echo "problema não é rede: é o serviço de IA de fábrica do robô com URL,"
echo "endpoint ou chave diferentes dos testados aqui. Próximo passo da fase 1:"
echo "  ssh $DESTINO"
echo "  grep -ril --include='*.json' --include='*.yaml' --include='*.conf' \\"
echo "      -e api_key -e base_url -e 'ark\\.' -e volc -e bytedance \\"
echo "      /etc /opt /userdata /app 2>/dev/null"
echo "para achar onde o software de fábrica guarda essa configuração."
echo ""
echo "Contexto (docs/PESQUISA-HENGBOT-SIRIUS.md): a comunidade descobriu que"
echo "o firmware chama APIs Volcano/ByteDance fixas — se esses hosts forem"
echo "inacessíveis daqui, o painel falha mesmo com a internet do robô OK."
