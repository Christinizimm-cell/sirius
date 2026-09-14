#!/usr/bin/env bash
# Vistoria rápida do cachorro — SÓ HTTP, sem SSH e sem senha.
# Descobre o que já responde no robô, mesmo sem credencial de login.
#
# Uso:  ./deploy/vistoria-rapida.sh [IP-do-cachorro]
#       (sem IP, usa o SIRIUS_HOST do brain/config.env, ou 192.168.0.48)

set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
[[ -f "$RAIZ/brain/config.env" ]] && source "$RAIZ/brain/config.env" 2>/dev/null
IP="${1:-${SIRIUS_HOST:-192.168.0.48}}"

ok()   { printf '\033[32m✅ %s\033[0m\n' "$*"; }
nao()  { printf '\033[31m❌ %s\033[0m\n' "$*"; }
tit()  { printf '\n\033[1m%s\033[0m\n' "$*"; }

testar() { # testar "<nome>" "<caminho>"
    local nome="$1" caminho="$2" resp cod
    resp="$(curl -sS --max-time 8 -w '\n%{http_code}' "http://$IP:8088$caminho" 2>&1)"
    cod="$(printf '%s' "$resp" | tail -n1)"
    if [[ "$cod" == "200" ]]; then
        ok "$nome"
        printf '%s' "$resp" | sed '$d' | head -c 600; echo
    else
        nao "$nome (HTTP ${cod:-sem resposta})"
    fi
}

tit "Vistoria rápida do Sirius em $IP (só HTTP, sem SSH)"

tit "1. O robô está na rede?"
if ping -c 2 -t 3 "$IP" >/dev/null 2>&1; then
    ok "responde ping — está ligado e no mesmo Wi-Fi"
else
    nao "não responde ping — confira se está ligado, acordado e no Wi-Fi de casa"
    echo "   (alguns robôs bloqueiam ping mas respondem HTTP; seguindo mesmo assim)"
fi

tit "2. Core API (porta 8088) — a espinha dorsal"
testar "ping do sistema"            "/api/v1/system/ping"
testar "bateria"                    "/api/v1/battery/status"
testar "configuração da IA nativa"  "/api/v1/ai/credentials/status"
testar "rostos vistos pela câmera"  "/api/v1/vision/faces"
testar "gestos vistos pela câmera"  "/api/v1/vision/gestures"

tit "3. Outras portas"
for porta in 8765 8080 8082; do
    if nc -z -G 3 "$IP" "$porta" 2>/dev/null; then
        case $porta in
            8765) ok "8765 aberta — WebSocket (eventos em tempo real)" ;;
            8080) ok "8080 aberta — vídeo: abra http://$IP:8080/video_stream no Safari" ;;
            8082) ok "8082 aberta — painel AI Studio: http://$IP:8082/ai-studio" ;;
        esac
    else
        nao "$porta fechada ou sem resposta"
    fi
done

tit "Resumo"
echo "Se o 'ping do sistema' deu ✅, o cachorro aceita comandos por HTTP —"
echo "dá para fazer ele se mexer sem SSH nenhum. Mande esta saída inteira."
