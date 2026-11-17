#!/usr/bin/env bash
# Open WebUI'yi (Docker) TOM API'sine ve Ollama'ya bağlı olarak kurar/başlatır: http://127.0.0.1:3000
#   scripts/openwebui.sh          # yoksa kur, varsa başlat
#   scripts/openwebui.sh yenile   # imajı güncelle ve konteyneri yeniden kur (sohbetler volume'da kalır)
#   scripts/openwebui.sh durdur
# Sohbetler, ayarlar: docker volume "open-webui". TOM API'si ayrıca çalışmalı: scripts/tom-api.sh
set -euo pipefail
IMAGE=ghcr.io/open-webui/open-webui:main-slim
NAME=open-webui

case "${1:-}" in
  durdur) docker stop "$NAME"; exit 0 ;;
  yenile) docker pull "$IMAGE"; docker rm -f "$NAME" 2>/dev/null || true ;;
esac

if docker container inspect "$NAME" >/dev/null 2>&1; then
  docker start "$NAME" >/dev/null
else
  # host ağı: konteyner 127.0.0.1'deki Ollama'ya ve TOM API'sine erişir. HOST=127.0.0.1: arayüz yalnız bu
  # bilgisayardan açılır, ağa açık değil (o yüzden girişsiz tek kullanıcı modu güvenli).
  docker run -d --name "$NAME" --network host --restart unless-stopped \
    -e HOST=127.0.0.1 -e PORT=3000 \
    -e WEBUI_AUTH=False -e WEBUI_NAME="TOM" \
    -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
    -e OPENAI_API_BASE_URL=http://127.0.0.1:8800/v1 -e OPENAI_API_KEY="${TOM_API_KEY:-tom-yerel}" \
    -e DEFAULT_MODELS=tom -e DEFAULT_LOCALE=tr-TR \
    -e ENABLE_EVALUATION_ARENA_MODELS=False -e ANONYMIZED_TELEMETRY=False -e DO_NOT_TRACK=True \
    -e SCARF_NO_ANALYTICS=True \
    -v open-webui:/app/backend/data \
    "$IMAGE" >/dev/null
fi
echo "Open WebUI: http://127.0.0.1:3000 (ilk açılış 1-2 dk sürebilir)"
