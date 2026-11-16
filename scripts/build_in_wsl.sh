#!/usr/bin/env bash
# Windows (WSL2 Ubuntu) fallback: build without GitHub-hosted Actions.
# Needs Ubuntu WSL, working internet access, free disk space, sudo permission.
set -euo pipefail
[[ -n "${WSL_DISTRO_NAME:-}" ]] || { echo 'Run this script from an Ubuntu WSL terminal on Windows.' >&2; exit 2; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
IDF_DIR="${ESP32_IDF_DIR:-$HOME/esp-flipper/esp-idf}"
for cmd in sudo git python3; do command -v "$cmd" >/dev/null || { echo "Missing $cmd" >&2; exit 2; }; done
echo '[1/5] Installing Ubuntu host dependencies (requires sudo)'
sudo apt-get update
sudo apt-get install -y git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 libglib2.0-dev
echo '[2/5] Preparing isolated ESP-IDF v5.4.1'
if [[ ! -e "$IDF_DIR" ]]; then
  mkdir -p "$(dirname "$IDF_DIR")"
  git clone --recursive --branch v5.4.1 --depth 1 https://github.com/espressif/esp-idf.git "$IDF_DIR"
fi
[[ -f "$IDF_DIR/export.sh" ]] || { echo "Incomplete ESP-IDF installation: $IDF_DIR" >&2; exit 1; }
EXPECTED_IDF_SHA="$(git -C "$IDF_DIR" rev-parse 'refs/tags/v5.4.1^{commit}' 2>/dev/null || true)"
HEAD_IDF_SHA="$(git -C "$IDF_DIR" rev-parse HEAD 2>/dev/null || true)"
[[ -n "$EXPECTED_IDF_SHA" && "$EXPECTED_IDF_SHA" == "$HEAD_IDF_SHA" ]] || { echo "ESP-IDF must be checked out at the exact v5.4.1 tag: $IDF_DIR" >&2; exit 1; }
"$IDF_DIR/install.sh" esp32s3
export ESP_IDF_EXPORT_SCRIPT="$IDF_DIR/export.sh"
echo '[3/5] Testing repository scripts'
cd "$ROOT"
python3 -m unittest discover -s tests -v
echo '[4/5] Building firmware against the pinned upstream source'
bash "$ROOT/scripts/build_local.sh"
echo '[5/5] Validating and packaging the build for flashing'
python3 "$ROOT/scripts/package_artifacts.py" --source "$ROOT/.work/upstream" --output "$ROOT/dist/firmware"
echo 'Output: dist/firmware/'
echo 'Contains flash_windows.ps1, BUILD_INFO.json, bootloader, partition table and application.'
echo 'To open the output in Windows Explorer:'
echo "  explorer.exe \"$(wslpath -w "$ROOT/dist/firmware")\""
echo 'Windows flashing instructions: docs/INSTALL_WINDOWS.md'
