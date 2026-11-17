#!/usr/bin/env bash
# Açık TOM'u kapatır (Ctrl+C ile aynı: düzgün çıkar).
if pkill -TERM -f "\.venv/bin/python -m tom(\.gui)?( |$)"; then
  notify-send -a TOM -i audio-input-microphone "TOM kapatılıyor" "Görüşürüz." 2>/dev/null
else
  notify-send -a TOM -i audio-input-microphone "TOM açık değil" 2>/dev/null
fi
