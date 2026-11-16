#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo 'Usage: ./scripts/flash_local.sh /dev/cu.usbmodemXXXX [--monitor]' >&2
  exit 2
fi
PORT="$1"; MONITOR="${2:-}"
[[ "$MONITOR" == '' || "$MONITOR" == '--monitor' ]] || { echo 'Only optional --monitor flag is accepted' >&2; exit 2; }
[[ -e "$PORT" ]] || { echo "Serial port not found: $PORT" >&2; exit 2; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/common.sh"
[[ -f "$SOURCE/build_diy/furi_esp32.bin" ]] || { echo 'Build first: ./scripts/build_local.sh' >&2; exit 1; }
[[ -f "$SOURCE/build_diy/bootloader/bootloader.bin" ]] || { echo 'Bootloader missing; rebuild first' >&2; exit 1; }
[[ -f "$SOURCE/build_diy/partition_table/partition-table.bin" ]] || { echo 'Partition table missing; rebuild first' >&2; exit 1; }
IDF_EXPORT="${ESP_IDF_EXPORT_SCRIPT:-$HOME/esp/esp-idf/export.sh}"
[[ -f "$IDF_EXPORT" ]] || { echo "ESP-IDF missing: $IDF_EXPORT" >&2; exit 1; }
# shellcheck source=/dev/null
source "$IDF_EXPORT"
echo 'TARGET ESP32-S3 N16R8 / ST7789 240x240 / microSD on SPI3'
echo "PORT: $PORT"
echo 'First flash may overwrite the existing firmware and on-device settings.'
read -r -p 'Have you verified wiring and backed up important data? Type FLASH: ' CONFIRM
[[ "$CONFIRM" == FLASH ]] || { echo 'Cancelled'; exit 1; }
cd "$SOURCE"
ARGS=(--port "$PORT")
[[ "$MONITOR" == '--monitor' ]] && ARGS+=(--monitor)
./build_diy.sh "${ARGS[@]}"
