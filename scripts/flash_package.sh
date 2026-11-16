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
for path in bootloader/bootloader.bin partition_table/partition-table.bin furi_esp32.bin ota_data_initial.bin flash_project_args BUILD_INFO.json; do
  [[ -f "$path" ]] || { echo "Missing $path" >&2; exit 1; }
done
python3 -c 'import esptool' >/dev/null 2>&1 || { echo 'esptool not installed. See docs/FLASH.md. Recommended: python3 -m venv .venv && source .venv/bin/activate && pip install "esptool>=4.8,<5"' >&2; exit 1; }
python3 - <<'PY'
import hashlib
import json
from pathlib import Path
import shlex

root = Path.cwd()
info = json.loads((root / 'BUILD_INFO.json').read_text())
assert info.get('board') == 'DIY ESP32-S3 N16R8', 'Wrong board profile'
expected = {
    'bootloader/bootloader.bin': 0x0,
    'partition_table/partition-table.bin': 0x8000,
    'furi_esp32.bin': 0x10000,
    'ota_data_initial.bin': 0xBF0000,
}
records = {x['file']: x for x in info['images']}
assert set(records) == set(expected), 'Missing/extra images in manifest'
for name, offset in expected.items():
    record = records[name]
    assert int(record['offset'], 16) == offset, f'Invalid manifest offset: {name}'
    data = (root / name).read_bytes()
    assert len(data) == record['size_bytes'], f'Invalid image size: {name}'
    assert hashlib.sha256(data).hexdigest() == record['sha256'], f'Checksum mismatch: {name}'
tokens = shlex.split((root / 'flash_project_args').read_text())
pairs = {}
for index, word in enumerate(tokens[:-1]):
    if word.lower().startswith('0x') and tokens[index + 1].lower().endswith('.bin'):
        pairs[tokens[index + 1]] = int(word, 16)
assert pairs == expected, f'Unexpected flash arguments: {pairs}'
print('Verified 4 firmware images, offsets and SHA256 hashes.')
PY
echo "Flashing from build artifact to $PORT"
echo 'WARNING: This writes bootloader, partition table and firmware to ESP32-S3.'
read -r -p 'Enter FLASH to confirm: ' confirm
[[ "$confirm" == FLASH ]] || { echo 'Cancelled'; exit 1; }
python3 -m esptool --chip esp32s3 --port "$PORT" --baud 460800 --before default_reset --after hard_reset write_flash '@flash_project_args'
echo 'Flash completed; disconnect/reconnect USB if board does not restart.'
