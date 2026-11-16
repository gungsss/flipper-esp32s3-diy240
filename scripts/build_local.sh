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
python3 "$ROOT/patch/patch_flipper.py" "$SOURCE"
cd "$SOURCE"
./build_diy.sh --build-only "${@}"
if [[ ! -f build_diy/furi_esp32.bin ]]; then echo 'BUILD output missing: build_diy/furi_esp32.bin' >&2; exit 1; fi
echo "Build ready at: $SOURCE/build_diy"
