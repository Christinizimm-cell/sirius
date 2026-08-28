#!/usr/bin/env bash
# Instala o cérebro do Sirius no cachorro via SSH, com um único comando.
#
# Uso: preencha brain/config.env (copie de brain/config.example.env) e rode
#   ./deploy/deploy.sh
#
# Rode do SEU computador, na mesma rede do cachorro. Requer ssh e scp.

set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$RAIZ/brain/config.env"

if [[ ! -f "$CONFIG" ]]; then
    echo "ERRO: $CONFIG não existe."
    echo "Copie brain/config.example.env para brain/config.env e preencha."
    exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG"

: "${SIRIUS_HOST:?Preencha SIRIUS_HOST no config.env (IP do cachorro)}"
: "${SIRIUS_SSH_USER:?Preencha SIRIUS_SSH_USER no config.env}"
: "${ANTHROPIC_API_KEY:?Preencha ANTHROPIC_API_KEY no config.env}"

DESTINO="$SIRIUS_SSH_USER@$SIRIUS_HOST"
PASTA=/opt/sirius-brain

echo "==> Conectando em $DESTINO ..."
ssh "$DESTINO" "mkdir -p $PASTA"

echo "==> Copiando o cérebro ..."
scp "$RAIZ/brain/sirius_brain.py" "$RAIZ/brain/memory.py" \
    "$RAIZ/brain/requirements.txt" "$CONFIG" "$DESTINO:$PASTA/"
scp "$RAIZ/deploy/sirius-brain.service" "$DESTINO:/tmp/sirius-brain.service"

echo "==> Instalando dependências e registrando o serviço ..."
ssh "$DESTINO" bash -s <<'REMOTO'
set -euo pipefail
python3 -m pip install -r /opt/sirius-brain/requirements.txt
chmod 600 /opt/sirius-brain/config.env
if command -v sudo >/dev/null && [ "$(id -u)" != 0 ]; then SUDO=sudo; else SUDO=; fi
$SUDO mv /tmp/sirius-brain.service /etc/systemd/system/sirius-brain.service
$SUDO systemctl daemon-reload
$SUDO systemctl enable --now sirius-brain
$SUDO systemctl status sirius-brain --no-pager || true
REMOTO

echo
echo "✅ Pronto! O cérebro do Sirius está instalado e rodando."
echo "   Memória persistente: $PASTA/memoria.json (dentro do cachorro)"
echo "   Logs ao vivo:        ssh $DESTINO journalctl -u sirius-brain -f"
