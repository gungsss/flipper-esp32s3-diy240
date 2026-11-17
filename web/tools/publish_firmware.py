#!/usr/bin/env python3
"""Create a verified ESP Web Tools merged image from the successful DIY240 artifact.

Only publish build 43889135916 for the fixed ESP32-S3 N16R8 board. The script
does not download firmware. It receives the already extracted GitHub Actions
artifact, rechecks SHA256 and offsets, invokes esptool's official merger, then
writes the same-origin web manifest and metadata.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

OUTPUT_NAME = "flipper-esp32s3-diy240-20261116-merged.bin"
SOURCE_RUN = 43889135916
MAX_FLASH = 16 * 1024 * 1024
IMAGES = [
    ("bootloader/bootloader.bin", 0x0),
    ("partition_table/partition-table.bin", 0x8000),
    ("furi_esp32.bin", 0x10000),
    ("ota_data_initial.bin", 0xBF0000),
]


def validate_inputs(source: Path) -> dict:
    metadata = json.loads((source / "BUILD_INFO.json").read_text())
    if metadata.get("board") != "DIY ESP32-S3 N16R8":
        raise ValueError("Wrong board in firmware bundle")
    if metadata.get("upstream_commit") != "e6ec11972a8e025d7ab686a6ef3016cf52360834":
        raise ValueError("Unexpected upstream commit")
    records = {item["file"]: item for item in metadata["images"]}
    if set(records) != {name for name, _ in IMAGES}:
        raise ValueError("Expected exactly four firmware images")
    args = shlex.split((source / "flash_project_args").read_text())
    pairs = {}
    for index, token in enumerate(args[:-1]):
        if token.lower().startswith("0x") and args[index + 1].endswith(".bin"):
            pairs[args[index + 1]] = int(token, 16)
    if pairs != dict(IMAGES):
        raise ValueError(f"Flash argument mapping mismatch: {pairs}")
    for name, offset in IMAGES:
        path = source / name
        if not path.is_file():
            raise ValueError(f"Missing image: {name}")
        data = path.read_bytes()
        record = records[name]
        if record["offset"].lower() != hex(offset) or record["size_bytes"] != len(data):
            raise ValueError(f"Invalid size or offset for {name}")
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError(f"Invalid SHA256 for {name}")
        if offset + len(data) > MAX_FLASH:
            raise ValueError(f"Image outside 16MB flash: {name}")
    for name in ("bootloader/bootloader.bin", "furi_esp32.bin"):
        header = (source / name).read_bytes()[:16]
        if header[0] != 0xE9 or header[12:14] != b"\x09\x00":
            raise ValueError(f"Image is not ESP32-S3: {name}")
    return metadata


def merge_firmware(source: Path, target: Path) -> None:
    cmd = [
        sys.executable, "-m", "esptool",
        "--chip", "esp32s3", "merge_bin",
        "-o", str(target),
        "--flash_mode", "dio", "--flash_freq", "80m",
        "--flash_size", "16MB",
    ]
    for name, offset in IMAGES:
        cmd.extend((hex(offset), str(source / name)))
    subprocess.run(cmd, check=True)
    merged = target.read_bytes()
    expected_end = max(offset + (source / name).stat().st_size for name, offset in IMAGES)
    if len(merged) < expected_end or len(merged) > MAX_FLASH:
        raise ValueError("Unexpected merged image length")
    if merged[0] != 0xE9 or merged[12:14] != b"\x09\x00":
        raise ValueError("Merged image has incorrect ESP32-S3 header")
    for name, offset in IMAGES:
        original = (source / name).read_bytes()
        installed = merged[offset:offset + len(original)]
        # esptool adjusts flash mode/frequency/size fields in the bootloader
        # header; only the first 16 bytes can differ for header-bearing images.
        compare_start = 16 if name.startswith("bootloader/") else 0
        if installed[compare_start:] != original[compare_start:]:
            raise ValueError(f"Merged image does not match input at {hex(offset)}: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, output = args.input.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    validate_inputs(source)
    target = output / OUTPUT_NAME
    merge_firmware(source, target)
    result = {
        "name": "Flipper ESP32-S3 DIY240",
        "version": "2.0.0-diy240.2026-11-16",
        "new_install_prompt_erase": True,
        "builds": [{
            "chipFamily": "ESP32-S3",
            "improv": False,
            "parts": [{"path": OUTPUT_NAME, "offset": 0}],
        }],
    }
    (output / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    web_release = {
        "version": "2.0.0-diy240.2026-11-16",
        "filename": OUTPUT_NAME,
        "chip": "ESP32-S3",
        "board": "DIY ESP32-S3 N16R8",
        "source_actions_run": SOURCE_RUN,
        "source_artifact": "flipper-diy-s3-n16r8-st7789-240",
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "size_bytes": target.stat().st_size,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    (output / "release.json").write_text(json.dumps(web_release, indent=2) + "\n")
    print("Web firmware published:", target, "SHA256:", web_release["sha256"])
    print("Bytes:", web_release["size_bytes"])


if __name__ == "__main__":
    main()
