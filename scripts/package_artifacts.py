#!/usr/bin/env python3
"""Package checked ESP-IDF build output for esptool first-flash.

This script does not build the firmware. It refuses incomplete builds and verifies
that the expected image names and offsets are in IDF's generated flash args.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shlex
import shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True, help='Upstream checkout with build_diy/')
    ap.add_argument('--output', type=Path, required=True)
    ns = ap.parse_args()
    build = ns.source / 'build_diy'
    images = {
        'bootloader/bootloader.bin': '0x0',
        'partition_table/partition-table.bin': '0x8000',
        'furi_esp32.bin': '0x10000',
    }
    argfile = build / 'flash_project_args'
    if not argfile.is_file():
        raise SystemExit('Missing ESP-IDF flash_project_args; cannot verify flash offsets')
    # Split the generated argument file like a shell, supporting quoted paths.
    tokens = shlex.split(argfile.read_text())
    found = {}
    for idx, token in enumerate(tokens[:-1]):
        if token.lower().startswith('0x'):
            try:
                value = int(token, 16)
            except ValueError:
                continue
            relative = tokens[idx + 1]
            if relative in images:
                found[relative] = value
    for relative, offset in images.items():
        if not (build / relative).is_file():
            raise SystemExit(f'Missing expected image: {build / relative}')
        if found.get(relative) != int(offset, 16):
            raise SystemExit(f'Flash args do not contain expected mapping {offset} {relative}. Inspect manually: {argfile}')
    out = ns.output
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for relative, offset in images.items():
        source_file = build / relative
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
        data = target.read_bytes()
        records.append({'file':relative,'offset':offset,'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    shutil.copy2(argfile, out / 'flash_project_args')
    flash_tool = Path(__file__).with_name('flash_package.sh')
    shutil.copy2(flash_tool, out / 'flash_macos_linux.sh')
    docs_root = Path(__file__).resolve().parents[1] / 'docs'
    for document in ('FLASH.md', 'HARDWARE.md'):
        shutil.copy2(docs_root / document, out / document)
    (out / 'BUILD_INFO.json').write_text(json.dumps({
        'upstream_repository':'Sor3nt/Flipper-Zero-ESP32-Port',
        'upstream_commit':'e6ec11972a8e025d7ab686a6ef3016cf52360834',
        'board':'DIY ESP32-S3 N16R8', 'lcd':'ST7789 240x240 7-pin no CS',
        'sd':'SPI3_HOST', 'images':records
    },indent=2)+'\n')
    print('Packaged images:')
    for row in records:
        print(row['offset'], row['file'], f"{row['size_bytes']} B", row['sha256'])


if __name__ == '__main__':
    main()
