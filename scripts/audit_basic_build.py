#!/usr/bin/env python3
"""Check the selected DIY target and exclude unused NFC application sources."""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
header = (root / 'components/furi_hal/boards/board_DIY.h').read_text()
for expected in (
    '#define BOARD_HAS_NFC 0',
    '#define BOARD_LCD_H_RES 160',
    '#define BOARD_LCD_V_RES 128',
    '#define BOARD_PIN_LCD_DC   15',
    '#define BOARD_PIN_LCD_RST  16',
    '#define BOARD_PIN_SD_CS    14',
    '#define BOARD_PIN_SD_MISO2 38',
    '#define BOARD_PIN_SD_MOSI  39',
    '#define BOARD_PIN_SD_SCK   40',
):
    if expected not in header:
        raise SystemExit(f'Board mismatch: {expected}')

if (root / 'applications/main/nfc/plugins/supported_cards/hotels.c').exists():
    raise SystemExit('Unexpected parser source in build checkout')

db = json.loads((root / 'build_diy/compile_commands.json').read_text())
sources = [str(x['file']).replace('\\', '/').lower() for x in db]
blocked = [x for x in sources if '/applications/main/nfc/' in x or '/supported_cards/' in x]
if blocked:
    raise SystemExit('Unexpected NFC app or card parser in compile inputs')
print(f'OK: ST7735 landscape, SD SPI3, and {len(sources)} compile inputs checked.')
