#!/usr/bin/env bash
# TOM'u küçük pencereyle başlatır (terminalsiz). Ek argümanlar TOM'a geçer (ör. --llm gemma4:e2b).
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
if pgrep -f "\.venv/bin/python -m tom(\.gui)?( |$)" >/dev/null; then
  notify-send -a TOM -i audio-input-microphone "TOM zaten açık" "İkinci kez başlatılmadı." 2>/dev/null
  exit 0
fi
export PYTHONPATH=. CUDA_HOME=/usr/local/cuda-12.4 PATH="/usr/local/cuda-12.4/bin:$PATH"
mkdir -p logs
exec .venv/bin/python -m tom.gui --deepspeed "$@" >>logs/tom-pencere.log 2>&1
