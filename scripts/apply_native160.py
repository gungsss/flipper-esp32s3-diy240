#!/usr/bin/env python3
"""Verify and apply the Native160 landscape UI integration to a prepared source tree."""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OVERLAY = REPO / "patch" / "native160"

def verify_hashes(root: Path, manifest_path: Path) -> None:
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = document.get("sha256")
    if not isinstance(entries, dict) or not entries:
        raise SystemExit(f"Invalid checksum manifest: {manifest_path}")
    mismatches = []
    for relative, expected in entries.items():
        path = root / relative
        if not path.is_file():
            mismatches.append(f"missing: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            mismatches.append(f"hash mismatch: {relative} expected {expected} got {actual}")
    if mismatches:
        raise SystemExit("Native160 source baseline check failed:\n  " + "\n  ".join(mismatches))

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply_native160.py /path/to/prepared-upstream")
    root = Path(sys.argv[1]).expanduser().resolve()
    verify_hashes(root, OVERLAY / "integration" / "baseline-sha256.json")
    verify_hashes(root, OVERLAY / "integration" / "source-requirements.json")
    board = root / "components/furi_hal/boards/board_DIY.h"
    display = root / "components/furi_hal/furi_hal_display.c"
    if not board.is_file() or not display.is_file():
        raise SystemExit("Prepared DIY board/display source is incomplete")
    board_text = board.read_text(encoding="utf-8")
    display_text = display.read_text(encoding="utf-8")
    for required in (
        "#define BOARD_LCD_H_RES 160", "#define BOARD_LCD_V_RES 128",
        "#define BOARD_LCD_SWAP_XY true", "#define BOARD_PIN_LCD_CS   UINT16_MAX",
        "#define BOARD_SD_SPI_HOST SPI3_HOST",
    ):
        if required not in board_text:
            raise SystemExit(f"Wrong board profile; expected {required}")
    if "esp_lcd_new_panel_st7735(" not in display_text:
        raise SystemExit("Expected ST7735S driver initialization in prepared display source")
    source_components = OVERLAY / "components"
    gui_destination = root / "components/gui/native160"
    gui_destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_components / "gui/native160", gui_destination, dirs_exist_ok=True)
    shutil.copy2(source_components / "furi_hal/display_geometry.h",
                 root / "components/furi_hal/display_geometry.h")
    patch = OVERLAY / "integration/native160_integration_only.patch"
    subprocess.run(["git", "-C", str(root), "apply", "--check", str(patch)], check=True)
    subprocess.run(["git", "-C", str(root), "apply", str(patch)], check=True)
    print("Native160 160x128 UI patch applied after strict baseline/profile checks.")

if __name__ == "__main__":
    main()
