#!/usr/bin/env bash
# TOM'u başlatır (masaüstü simgesi bunu bir terminal penceresinde çalıştırır).
#   scripts/tom-baslat.sh [--llm gemma4:e2b] [--no-wake] …   (ek argümanlar tom'a geçer)
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1

if pgrep -f "\.venv/bin/python -m tom(\.gui)?( |$)" >/dev/null; then
  notify-send -a TOM -i audio-input-microphone "TOM zaten açık" "İkinci kez başlatılmadı." 2>/dev/null
  echo "TOM zaten açık."
  sleep 3
  exit 0
fi

export PYTHONPATH=. CUDA_HOME=/usr/local/cuda-12.4 PATH="/usr/local/cuda-12.4/bin:$PATH"
.venv/bin/python -m tom --deepspeed "$@"
code=$?
if [ $code -ne 0 ]; then  # hata olduysa pencere hemen kapanmasın, mesaj okunabilsin
  echo; echo "TOM hatayla kapandı (kod $code). Kapatmak için Enter'a bas."; read -r
fi
