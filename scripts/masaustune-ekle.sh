#!/usr/bin/env bash
# TOM'u Ubuntu uygulama menüsüne ekler (~/.local/share/applications/tom.desktop). Kaldırmak için: --kaldir
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
DESK="$HOME/.local/share/applications/tom-asistan.desktop"
if [ "$1" = "--kaldir" ]; then rm -f "$DESK"; echo "Kaldırıldı."; exit 0; fi
chmod +x "$ROOT/scripts/tom-baslat.sh" "$ROOT/scripts/tom-kapat.sh" "$ROOT/scripts/tom-pencere.sh"
mkdir -p "$(dirname "$DESK")"
cat > "$DESK" <<DESKTOP
[Desktop Entry]
Type=Application
Name=TOM
GenericName=Sesli asistan
Comment=Kişisel Türkçe sesli asistan (Hey TOM)
Exec="$ROOT/scripts/tom-pencere.sh"
StartupWMClass=tom
Icon=$ROOT/assets/tom.png
Terminal=false
Categories=Utility;
Keywords=asistan;tom;ses;jarvis;
StartupNotify=true
Actions=hizli;terminal;kapat;

[Desktop Action hizli]
Name=TOM (hızlı model, e2b)
Exec="$ROOT/scripts/tom-pencere.sh" --llm gemma4:e2b

[Desktop Action terminal]
Name=TOM (terminalde, ayrıntılı kayıt)
Exec=gnome-terminal --title=TOM --geometry=110x32 -- "$ROOT/scripts/tom-baslat.sh"

[Desktop Action kapat]
Name=TOM'u kapat
Exec=$ROOT/scripts/tom-kapat.sh
DESKTOP
chmod +x "$DESK"
update-desktop-database "$(dirname "$DESK")" 2>/dev/null || true
echo "Eklendi: $DESK"
echo "Uygulamalar menüsünde 'TOM' ara; sağ tık → 'Sık kullanılanlara ekle' ile dock'a sabitle."
