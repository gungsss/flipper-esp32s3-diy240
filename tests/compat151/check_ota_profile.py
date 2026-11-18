#!/usr/bin/env python3
"""Exercise the actual board-profile comparator with target pin settings."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

port = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='esp151-ota-profile-') as directory:
    temp = Path(directory)
    (temp / 'board.h').write_text('''#pragma once
#define BOARD_OTA_PROFILE_ST7735 1
#define BOARD_PIN_LCD_MOSI 11
#define BOARD_PIN_LCD_SCLK 12
#define BOARD_PIN_LCD_DC 15
#define BOARD_PIN_LCD_RST 16
#define BOARD_PIN_LCD_CS UINT16_MAX
#define BOARD_PIN_LCD_BL 7
#define BOARD_PIN_SD_SCK 40
#define BOARD_PIN_SD_MOSI 39
#define BOARD_PIN_SD_MISO2 38
#define BOARD_PIN_SD_CS 14
#define BOARD_PIN_BTN_UP 4
#define BOARD_PIN_BTN_DOWN 5
#define BOARD_PIN_BTN_LEFT 6
#define BOARD_PIN_BTN_RIGHT 17
#define BOARD_PIN_BTN_OK 8
#define BOARD_PIN_BTN_BACK 18
''')
    root = port / 'components/fw_ota'
    exe = temp / 'profile-test'
    subprocess.run([
        'gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
        '-I', str(temp), '-I', str(root),
        str(Path(__file__).with_name('ota_profile_regression.c')),
        str(root / 'fw_ota_profile.c'), '-o', str(exe),
    ], check=True)
    subprocess.run([str(exe)], env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'}, check=True)
print('OTA board profile matches correct wiring and rejects altered/truncated profiles.')
