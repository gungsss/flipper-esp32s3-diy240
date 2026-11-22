#!/usr/bin/env python3
"""Package checked ESP-IDF build output for esptool first-flash.

This script does not build the firmware. It refuses incomplete builds and verifies
that the expected image names and offsets are in IDF's generated flash args.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shlex
import shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True, help='Upstream checkout with build_diy/')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--profile-name', default='m4145-unified', help='Build profile label for BUILD_INFO.json')
    ns = ap.parse_args()
    build = ns.source / 'build_diy'
    images = {
        'bootloader/bootloader.bin': '0x0',
        'partition_table/partition-table.bin': '0x8000',
        'furi_esp32.bin': '0x10000',
        'ota_data_initial.bin': '0xbf0000',
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
            elif relative.lower().endswith('.bin'):
                raise SystemExit(f'Unknown binary in ESP-IDF flash_project_args: {relative} ({token}). Package all referenced images before distribution.')
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
    windows_flash_tool = Path(__file__).with_name('flash_windows.ps1')
    if not windows_flash_tool.is_file():
        raise SystemExit(f'Missing Windows flasher: {windows_flash_tool}')
    shutil.copy2(windows_flash_tool, out / 'flash_windows.ps1')
    docs_root = Path(__file__).resolve().parents[1] / 'docs'
    for document in ('FLASH.md', 'HARDWARE.md', 'INSTALL_WINDOWS.md'):
        shutil.copy2(docs_root / document, out / document)
    board_header = ns.source / 'components/furi_hal/boards/board_DIY.h'
    if not board_header.is_file():
        raise SystemExit(f'Missing generated board profile: {board_header}')
    header = board_header.read_text(encoding='utf-8')
    pinout = ns.source / 'Pinout.txt'
    if not pinout.is_file():
        raise SystemExit(f'Missing selected board pinout: {pinout}')
    pinout_sha256 = hashlib.sha256(pinout.read_bytes()).hexdigest()
    shutil.copy2(pinout, out / 'Pinout.txt')

    def board_flag(name):
        match = re.search(rf'^#define\s+{re.escape(name)}\s+(\d+)', header, re.MULTILINE)
        return bool(match and int(match.group(1)))

    enabled_modules = [name for name, flag in (
        ('CC1101 Sub-GHz', 'BOARD_HAS_SUBGHZ'),
        ('nRF24L01+', 'BOARD_HAS_NRF24'),
        ('PN532 NFC', 'BOARD_HAS_NFC'),
        ('Infrared', 'BOARD_HAS_IR'),
        ('LF RFID read-only', 'BOARD_HAS_RFID'),
    ) if board_flag(flag)]
    manifest = {
        'name': 'M4145 Flipper 1.5.1 ESP32-S3 ST7735S radio bring-up',
        'version': '1.5.1-m4145-esp32s3-st7735s-unified',
        'new_install_prompt_erase': False,
        'builds': [{
            'chipFamily': 'ESP32-S3',
            'parts': [
                {'path': relative, 'offset': int(offset, 16)}
                for relative, offset in images.items()
            ],
        }],
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (out / 'BUILD_INFO.json').write_text(json.dumps({
        'project_name':'M4145 Flipper ESP32-S3',
        'firmware_author':'m4145',
        'source_base_repository':'Sor3nt/Flipper-Zero-ESP32-Port',
        'source_base_commit':'e6ec11972a8e025d7ab686a6ef3016cf52360834',
        'official_flipper_tag':'1.5.1',
        'official_flipper_commit':'9e810dc399e027e48ce07751df72168abbb19065',
        'reported_flipper_version':'1.5.1-ESP32-preview',
        'reported_ble_software_revision':'1.5.1-ESP32-preview',
        'firmware_build_date':'Compiler-generated from __DATE__ at build time',
        'scope':'Selected portable Flipper 1.5.1 changes adapted to the ESP32 port; not full official source, SDK, runtime, or hardware parity.',
        'build_profile':ns.profile_name,
        'pinout_sha256':pinout_sha256,
        'board':'DIY ESP32-S3 N16R8',
        'lcd':'ST7735S landscape 160x128, CS tied to GND, 5 MHz SPI',
        'ui_rendering':'Full-panel 160x128 native GUI canvas; all legacy Canvas views use the shared 128x64-to-160x128 adapter, while core screen modules use native layouts. Static source audit covers all Canvas draw APIs and GUI callback paths; physical display validation remains separate.',
        'display_driver':'waveshare/esp_lcd_st7735==2.0.0',
        'sd':'SPI3_HOST',
        'enabled_optional_modules':enabled_modules,
        'module_behavior':'This single image uses the current wiring profile: CC1101 and nRF24L01+ detection are enabled. The nRF24 app exposes passive channel survey only. Wi-Fi deauthentication/raw-TX support, the WPS PIN adapter, Bluetooth spam, and external attack FAPs are excluded from this bring-up build. Other module GPIOs remain disabled until assigned and built.',
        'unsupported_or_limited_features':[
            'iButton HAL is not implemented for this ESP32 port.',
            'LF RFID through RDM6300 is read-only; writing and emulation need another compatible frontend and firmware support.',
            'ARM-targeted FAP files are not binary-compatible with ESP32-S3 and must be ported and rebuilt.',
        ],
        'hardware_validation':'Build packaging does not verify physical LCD, buttons, SD, or optional modules.',
        'images':records
    },indent=2)+'\n')
    print('Packaged images:')
    for row in records:
        print(row['offset'], row['file'], f"{row['size_bytes']} B", row['sha256'])


if __name__ == '__main__':
    main()
