#!/usr/bin/env python3
"""Exercise both DIY display-board profiles with the real OTA comparator."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

port = Path(sys.argv[1]).resolve()
pins = '''#pragma once
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
'''
profiles = (('BOARD_OTA_PROFILE_ST7735', 7735), ('BOARD_OTA_PROFILE_ST7789', 7789))
with tempfile.TemporaryDirectory(prefix='esp151-ota-profile-') as directory:
    temp = Path(directory)
    root = port / 'components/fw_ota'
    for macro, controller in profiles:
        board_text = pins.replace('#pragma once', f'#pragma once\n#define {macro} 1', 1)
        (temp / 'board.h').write_text(board_text)
        exe = temp / f'profile-test-{controller}'
        subprocess.run([
            'gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
            f'-D{macro}=1',
            '-I', str(temp), '-I', str(root),
            str(Path(__file__).with_name('ota_profile_regression.c')),
            str(root / 'fw_ota_profile.c'), '-o', str(exe),
        ], check=True)
        subprocess.run([str(exe)], env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'}, check=True)
        print(f'OTA profile {controller} matches its wiring and rejects altered/truncated profiles.')
