#!/usr/bin/env python3
"""Verify the actual DIY compile database contains the intended components."""
import json
import sys
from pathlib import Path

database = Path(sys.argv[1])
entries = json.loads(database.read_text())
sources = [entry['file'].replace('\\', '/') for entry in entries]
required = (
    '/main/app_main.c',
    '/components/furi_hal/furi_hal_display.c',
    '/components/ble_serial/ble_serial.c',
    '/components/toolbox/crc32_calc.c',
    '/components/toolbox/bit_buffer.c',
)
for suffix in required:
    assert any(name.endswith(suffix) for name in sources), f'missing compiled input: {suffix}'
assert not any('/applications/main/nfc/plugins/supported_cards/' in name for name in sources), (
    'Unexpected NFC card parser in the DIY build')
print(f'Checked {len(sources)} actual compiled source paths for the DIY target.')
