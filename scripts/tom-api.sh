#!/usr/bin/env bash
# TOM'un OpenAI uyumlu API'si (Open WebUI bunu kullanır): http://127.0.0.1:8800/v1
#   scripts/tom-api.sh            # ön planda
#   scripts/tom-api.sh arkaplan   # arka planda, kayıt: logs/tom-api.log
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
if [ "${1:-}" = arkaplan ]; then
  mkdir -p logs
  nohup .venv/bin/python -m tom.api "${@:2}" >> logs/tom-api.log 2>&1 &
  echo "TOM API arka planda (pid $!), kayıt: logs/tom-api.log"
else
  exec .venv/bin/python -m tom.api "$@"
fi
