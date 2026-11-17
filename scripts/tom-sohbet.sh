#!/usr/bin/env bash
# Yazılı TOM: API'yi (yoksa) arka planda başlatır, Open WebUI'yi açar ve tarayıcıda gösterir.
set -uo pipefail
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd "$ROOT"
if ! curl -s -o /dev/null --max-time 2 http://127.0.0.1:8800/health; then
  "$ROOT/scripts/tom-api.sh" arkaplan
fi
"$ROOT/scripts/openwebui.sh" >/dev/null
for _ in $(seq 1 60); do
  curl -s -o /dev/null --max-time 2 http://127.0.0.1:3000/health && break
  sleep 2
done
xdg-open http://127.0.0.1:3000 >/dev/null 2>&1 &
