#!/usr/bin/env python3
"""Stage a real 1.5.1-based DIY ST7735 image for the web flasher.

This script consumes an extracted, verified build bundle; it never downloads
or flashes firmware. It refuses compatibility previews still based on 1.4.3.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

FLIPPER_151_COMMIT = '9e810dc399e027e48ce07751df72168abbb19065'
MAX_FLASH = 16 * 1024 * 1024
IMAGES = {
    'bootloader/bootloader.bin': 0,
    'partition_table/partition-table.bin': 0x8000,
    'furi_esp32.bin': 0x10000,
    'ota_data_initial.bin': 0xBF0000,
}
WEB_NAMES = {
    'bootloader/bootloader.bin': 'bootloader.bin',
    'partition_table/partition-table.bin': 'partition-table.bin',
    'furi_esp32.bin': 'furi_esp32.bin',
    'ota_data_initial.bin': 'ota_data_initial.bin',
}


def validate(source: Path) -> dict:
    metadata = json.loads((source / 'BUILD_INFO.json').read_text())
    if metadata.get('board') != 'DIY ESP32-S3 N16R8':
        raise ValueError('Firmware is not for the DIY ESP32-S3 N16R8 board')
    if 'ST7735S landscape 160x128' not in metadata.get('lcd', ''):
        raise ValueError('Firmware is not configured for the ST7735S landscape display')
    if metadata.get('flipper_source_commit') != FLIPPER_151_COMMIT:
        raise ValueError('The build has no verified Flipper 1.5.1 source-base identity')
    if metadata.get('flipper_source_version') != '1.5.1':
        raise ValueError('The build source version is not Flipper 1.5.1')
    if metadata.get('flipper_151_core_ported') is not True:
        raise ValueError('The Flipper 1.5.1 core is not marked as ported')
    version = metadata.get('reported_flipper_version', '')
    if version != '1.5.1' and not version.startswith('1.5.1-'):
        raise ValueError('The firmware still reports another Flipper version')
    records = {row['file']: row for row in metadata['images']}
    if len(metadata['images']) != len(IMAGES) or set(records) != set(IMAGES):
        raise ValueError('Expected exactly the four ESP32 flash images')
    intervals = []
    source = source.resolve()
    for name, offset in IMAGES.items():
        path = (source / name).resolve()
        if not path.is_relative_to(source):
            raise ValueError('Image path escapes the firmware directory')
        data = path.read_bytes()
        row = records[name]
        if int(row['offset'], 16) != offset or row['size_bytes'] != len(data):
            raise ValueError(f'Incorrect offset or length: {name}')
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError(f'Checksum mismatch: {name}')
        if not data or offset + len(data) > MAX_FLASH:
            raise ValueError(f'Image exceeds 16 MB flash: {name}')
        if name in ('bootloader/bootloader.bin', 'furi_esp32.bin'):
            if len(data) < 16 or data[0] != 0xE9 or data[12:14] != b'\x09\x00':
                raise ValueError(f'Incorrect ESP32-S3 image header: {name}')
        intervals.append((offset, offset + len(data)))
    intervals.sort()
    if any(end > next_start for (_, end), (next_start, _) in zip(intervals, intervals[1:])):
        raise ValueError('Overlapping flash images')
    return metadata


def prepare(source: Path, target: Path) -> None:
    info = validate(source)
    target.mkdir(parents=True, exist_ok=True)
    images = []
    for name, offset in IMAGES.items():
        output = target / WEB_NAMES[name]
        shutil.copyfile(source / name, output)
        data = output.read_bytes()
        original = next(row for row in info['images'] if row['file'] == name)
        if hashlib.sha256(data).hexdigest() != original['sha256']:
            raise ValueError(f'Staged image checksum mismatch: {name}')
        images.append({'file': output.name, 'offset': offset, 'size_bytes': len(data),
                       'sha256': original['sha256']})
    release = {
        'source_version': '1.5.1',
        'reported_flipper_version': info['reported_flipper_version'],
        'source_commit': FLIPPER_151_COMMIT,
        'board': info['board'],
        'lcd': info['lcd'],
        'images': images,
        'hardware_validation': info.get('hardware_validation', 'not specified'),
        'disabled_features': info.get('disabled_features', []),
    }
    manifest = {
        'name': 'ESP32-S3 ST7735S - Flipper 1.5.1 port',
        'version': info['reported_flipper_version'],
        'new_install_prompt_erase': False,
        'builds': [{'chipFamily': 'ESP32-S3',
                    'parts': [{'path': row['file'], 'offset': row['offset']} for row in images]}],
    }
    (target / 'release.json').write_text(json.dumps(release, indent=2) + '\n')
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Prepared four separately addressed images for the web flasher.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare(args.input.resolve(), args.output.resolve())
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit(f'Cannot publish firmware: {error}') from error


if __name__ == '__main__':
    main()
