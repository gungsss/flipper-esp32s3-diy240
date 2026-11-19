#!/usr/bin/env python3
"""Stage a verified Native160 firmware package for Vercel static publishing."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

EXPECTED_PORT_COMMIT = "e6ec11972a8e025d7ab686a6ef3016cf52360834"
EXPECTED_OFFICIAL_151 = "9e810dc399e027e48ce07751df72168abbb19065"
ARCHIVE_NAME = "ESP32S3_ST7735S_Native160_151_Compatibility_Preview_FLASH_READY.zip"
IMAGES = {
    "bootloader/bootloader.bin": 0x0,
    "partition_table/partition-table.bin": 0x8000,
    "furi_esp32.bin": 0x10000,
    "ota_data_initial.bin": 0xBF0000,
}
WEB_NAMES = {
    "bootloader/bootloader.bin": "bootloader.bin",
    "partition_table/partition-table.bin": "partition-table.bin",
    "furi_esp32.bin": "furi_esp32.bin",
    "ota_data_initial.bin": "ota_data_initial.bin",
}


def validate(source: Path) -> dict:
    info = json.loads((source / "BUILD_INFO.json").read_text())
    if info.get("board") != "DIY ESP32-S3 N16R8":
        raise ValueError("Wrong board target")
    if info.get("upstream_commit") != EXPECTED_PORT_COMMIT:
        raise ValueError("Unexpected ESP32 source port commit")
    expected_ref = (
        "flipperdevices/flipperzero-firmware@1.5.1 ("
        + EXPECTED_OFFICIAL_151
        + ")"
    )
    if info.get("official_flipper_151_source") != expected_ref:
        raise ValueError("Official Flipper 1.5.1 source reference mismatch")
    if info.get("reported_flipper_version") != "1.5.1-ESP32-preview":
        raise ValueError("Build does not identify the intended 1.5.1 ESP32 port")
    if info.get("port_author") != "m4145":
        raise ValueError("Missing m4145 port credit")
    if not info.get("upstream_credit", "").startswith("Sor3nt/"):
        raise ValueError("Missing upstream Sor3nt credit")
    if "ST7735S landscape 160x128" not in info.get("lcd", ""):
        raise ValueError("Wrong display target")

    records = {row["file"]: row for row in info["images"]}
    if set(records) != set(IMAGES) or len(records) != len(IMAGES):
        raise ValueError("Expected exactly four flash images")

    spans = []
    for name, expected_offset in IMAGES.items():
        image = (source / name).read_bytes()
        record = records[name]
        if int(record["offset"], 16) != expected_offset:
            raise ValueError(f"Wrong flash offset: {name}")
        if record["size_bytes"] != len(image):
            raise ValueError(f"Wrong image length: {name}")
        if hashlib.sha256(image).hexdigest() != record["sha256"]:
            raise ValueError(f"SHA256 mismatch: {name}")
        if expected_offset + len(image) > 16 * 1024 * 1024:
            raise ValueError(f"Image exceeds ESP32-S3 flash: {name}")
        if name in ("bootloader/bootloader.bin", "furi_esp32.bin"):
            if len(image) < 16 or image[0] != 0xE9 or image[12:14] != b"\x09\x00":
                raise ValueError(f"Invalid ESP32-S3 image header: {name}")
        spans.append((expected_offset, expected_offset + len(image)))

    spans.sort()
    if any(end > next_start for (_, end), (next_start, _) in zip(spans, spans[1:])):
        raise ValueError("Flash images overlap")
    app = (source / "furi_esp32.bin").read_bytes()
    if b"1.5.1-ESP32-preview" not in app or b"DIY240 by m4145" not in app:
        raise ValueError("Firmware binary is missing its version or author label")
    return info


def stage(source: Path, output: Path, index_html: Path) -> None:
    info = validate(source)
    if output.exists():
        shutil.rmtree(output)
    firmware_dir = output / "firmware"
    firmware_dir.mkdir(parents=True)
    rows = []
    for original, offset in IMAGES.items():
        name = WEB_NAMES[original]
        target = firmware_dir / name
        shutil.copyfile(source / original, target)
        rows.append({
            "file": f"firmware/{name}",
            "offset": offset,
            "size_bytes": target.stat().st_size,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        })

    shutil.copyfile(index_html, output / "index.html")
    shutil.copyfile(source / "BUILD_INFO.json", output / "build-info.json")
    archive_path = output / ARCHIVE_NAME
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())
    with zipfile.ZipFile(archive_path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"Download ZIP failed CRC validation: {bad}")

    manifest = {
        "name": "Flipper 1.5.1 ESP32-S3 Native160 port by m4145",
        "version": info["reported_flipper_version"],
        "new_install_prompt_erase": False,
        "builds": [{
            "chipFamily": "ESP32-S3",
            "parts": [{"path": row["file"], "offset": row["offset"]} for row in rows],
        }],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    release = {
        "version": info["reported_flipper_version"],
        "port_author": info["port_author"],
        "port_credit": info["port_credit"],
        "upstream_credit": info["upstream_credit"],
        "upstream_commit": info["upstream_commit"],
        "official_flipper_151_source": info["official_flipper_151_source"],
        "board": info["board"],
        "lcd": info["lcd"],
        "images": rows,
        "scope": info["scope"],
        "hardware_validation": info["hardware_validation"],
    }
    (output / "release.json").write_text(json.dumps(release, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--index-html", type=Path, required=True)
    args = parser.parse_args()
    try:
        stage(args.input.resolve(), args.output.resolve(), args.index_html.resolve())
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as error:
        raise SystemExit(f"Cannot stage Vercel firmware release: {error}") from error


if __name__ == "__main__":
    main()
