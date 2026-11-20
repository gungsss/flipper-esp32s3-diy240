#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
IDF_EXPORT="${ESP_IDF_EXPORT_SCRIPT:-$HOME/esp/esp-idf/export.sh}"
[[ -f "$IDF_EXPORT" ]] || { echo "ESP-IDF export.sh not found: $IDF_EXPORT" >&2; echo "Install v5.4.1; see docs/INSTALL_MAC.md" >&2; exit 1; }
# shellcheck source=/dev/null
source "$IDF_EXPORT"
command -v idf.py >/dev/null || { echo 'idf.py not found after exporting IDF environment' >&2; exit 1; }
source "$ROOT/scripts/common.sh"
bash "$ROOT/scripts/fetch_upstream.sh"
for PORT_PATCH in \
  "$ROOT/patch/flipper_1_5_1_port.patch" \
  "$ROOT/patch/loader_151_port.patch" \
  "$ROOT/patch/loader_cli_151_port.patch"; do
  if git -C "$SOURCE" apply --reverse --check "$PORT_PATCH" >/dev/null 2>&1; then
    echo "Already applied: $(basename "$PORT_PATCH")"
  else
    git -C "$SOURCE" apply --check "$PORT_PATCH"
    git -C "$SOURCE" apply "$PORT_PATCH"
  fi
done
python3 "$ROOT/patch/patch_flipper.py" "$SOURCE"
python3 "$ROOT/patch/patch_hotels_151.py" "$SOURCE"
ST7735_PINOUT="${ST7735_PINOUT:-$ROOT/patch/Pinout_ESP32S3_ST7735S_160.txt}"
python3 "$ROOT/variants/st7735/patch_st7735.py" "$SOURCE" --pinout "$ST7735_PINOUT"
python3 "$ROOT/variants/st7735/patch_landscape.py" "$SOURCE"
python3 "$ROOT/scripts/audit_st7735_ui.py" "$SOURCE"
cd "$SOURCE"
./build_diy.sh --build-only "${@}"
if [[ ! -f build_diy/furi_esp32.bin ]]; then echo 'BUILD output missing: build_diy/furi_esp32.bin' >&2; exit 1; fi
echo "Build ready at: $SOURCE/build_diy"
