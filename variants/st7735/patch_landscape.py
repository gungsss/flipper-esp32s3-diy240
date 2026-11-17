#!/usr/bin/env python3
"""Rotate the already-applied ST7735S profile to 160x128 landscape.

Apply the existing DIY and ST7735S patches first, on a fresh pinned upstream
checkout. This changes display geometry/orientation only; it does not flash.
"""
from pathlib import Path
import subprocess
import sys


def replace_once(text, before, after, label):
    if after in text:
        return text
    if text.count(before) != 1:
        raise ValueError(f"{label}: missing or ambiguous source anchor: {before!r}")
    return text.replace(before, after, 1)


def patch_generator(s):
    for old, new in (
        ("#define BOARD_LCD_H_RES 128\n#define BOARD_LCD_V_RES 160\n#define BOARD_LCD_SIDE_MARGIN 0",
         "#define BOARD_LCD_H_RES 160\n#define BOARD_LCD_V_RES 128\n#define BOARD_LCD_SIDE_MARGIN 0"),
        ("#define BOARD_LCD_SWAP_XY false", "#define BOARD_LCD_SWAP_XY true"),
        ("#define BOARD_LCD_MIRROR_X true", "#define BOARD_LCD_MIRROR_X false"),
    ):
        s = replace_once(s, old, new, "ST7735S landscape generator")
    return s


def patch_display(s):
    if "esp_lcd_new_panel_st7735(" not in s:
        raise ValueError("ST7735S driver profile has not been applied")
    anchor = "    ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel_handle, BOARD_LCD_INVERT_COLOR));\n"
    rotated = anchor + "    ESP_ERROR_CHECK(esp_lcd_panel_swap_xy(panel_handle, BOARD_LCD_SWAP_XY));\n"
    return replace_once(s, anchor, rotated, "ST7735S axis swap")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_landscape.py /path/to/patched/upstream")
    root = Path(sys.argv[1]).resolve()
    updates = {
        "tools/gen_diy_board.py": patch_generator,
        "components/furi_hal/furi_hal_display.c": patch_display,
    }
    prepared = {p: fn((root / p).read_text(encoding="utf-8")) for p, fn in updates.items()}
    pinout = (root / "Pinout.txt").read_text(encoding="utf-8").splitlines()
    for setting in ("SPI_SCK=12", "SPI_MOSI=11", "LCD_CS=-1", "LCD_DC=15", "LCD_RST=16",
                    "SD_SCK=40", "SD_MOSI=39", "SD_MISO=38", "SD_CS=14",
                    "BTN_UP=4", "BTN_DOWN=5", "BTN_LEFT=6", "BTN_RIGHT=17", "BTN_OK=8", "BTN_BACK=18"):
        if setting not in pinout:
            raise ValueError(f"Pinout differs from the tested profile: {setting}")
    for path, data in prepared.items():
        (root / path).write_text(data, encoding="utf-8")
    subprocess.run([sys.executable, str(root / "tools/gen_diy_board.py"), str(root / "Pinout.txt")],
                   cwd=root, check=True)
    board = (root / "components/furi_hal/boards/board_DIY.h").read_text(encoding="utf-8")
    required = (
        "#define BOARD_LCD_H_RES 160", "#define BOARD_LCD_V_RES 128",
        "#define BOARD_LCD_SIDE_MARGIN 0", "#define BOARD_LCD_SPI_FREQ_HZ (5 * 1000 * 1000)",
        "#define BOARD_LCD_SWAP_XY true", "#define BOARD_LCD_MIRROR_X false",
        "#define BOARD_LCD_MIRROR_Y true", "#define BOARD_LCD_INVERT_COLOR false",
        "#define BOARD_LCD_GAP_X 0", "#define BOARD_LCD_GAP_Y 0", "#define BOARD_PIN_LCD_CS   UINT16_MAX",
        "#define BOARD_SD_SPI_HOST SPI3_HOST", "#define BOARD_PIN_SD_MISO2 38",
        "#define BOARD_PIN_SD_MOSI  39", "#define BOARD_PIN_SD_SCK   40", "#define BOARD_PIN_SD_CS    14",
        "#define BOARD_PIN_BTN_OK     8", "#define BOARD_PIN_BTN_BACK   18",
    )
    missing = [item for item in required if item not in board]
    if missing:
        raise SystemExit(f"Generated landscape board configuration mismatch: {missing}")
    print("PASSED: ST7735S landscape 160x128, 5 MHz, same wiring and SD SPI3")


if __name__ == "__main__":
    main()
