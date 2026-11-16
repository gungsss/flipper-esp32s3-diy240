#!/usr/bin/env bash
# Run from extracted GitHub Actions firmware artifact.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo 'Usage: ./flash_macos_linux.sh /dev/cu.usbmodemXXXX' >&2
  exit 2
fi
PORT="$1"
[[ -e "$PORT" ]] || { echo "Port not found: $PORT" >&2; exit 1; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
for path in bootloader/bootloader.bin partition_table/partition-table.bin furi_esp32.bin flash_project_args; do
  [[ -f "$path" ]] || { echo "Missing $path" >&2; exit 1; }
done
python3 -c 'import esptool' >/dev/null 2>&1 || { echo 'esptool not installed. See docs/FLASH.md. Recommended: python3 -m venv .venv && source .venv/bin/activate && pip install "esptool>=4.8,<5"' >&2; exit 1; }
echo "Flashing from build artifact to $PORT"
echo 'WARNING: This writes bootloader, partition table and firmware to ESP32-S3.'
read -r -p 'Enter FLASH to confirm: ' confirm
[[ "$confirm" == FLASH ]] || { echo 'Cancelled'; exit 1; }
python3 -m esptool --chip esp32s3 --port "$PORT" --baud 460800 --before default_reset --after hard_reset write_flash '@flash_project_args'
echo 'Flash completed; disconnect/reconnect USB if board does not restart.'
