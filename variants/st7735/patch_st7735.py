#!/usr/bin/env python3
"""Adapt the pinned DIY240 source to the verified ST7735S test wiring.

Run after patch_flipper.py in a fresh upstream checkout. Does not flash a device.
The SPI driver and panel startup match diagnostics/st7735-test, which was
confirmed by the user on their physical module.
"""
from pathlib import Path
import subprocess
import sys


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old in text:
        if text.count(old) != 1:
            raise ValueError(f"{label}: expected exactly one source anchor")
        return text.replace(old, new, 1)
    raise ValueError(f"{label}: expected source anchor missing: {old[:100]!r}")


def patch_generator(s):
    for old, new in (
        ("#define BOARD_LCD_H_RES 240\n#define BOARD_LCD_V_RES 240",
         "#define BOARD_LCD_H_RES 128\n#define BOARD_LCD_V_RES 160\n#define BOARD_LCD_SIDE_MARGIN 0\n"
         "#define BOARD_OTA_PROFILE_ST7735 1"),
        ("#define BOARD_LCD_SPI_FREQ_HZ (20 * 1000 * 1000)",
         "#define BOARD_LCD_SPI_FREQ_HZ (5 * 1000 * 1000)"),
        ("#define BOARD_LCD_MIRROR_X false", "#define BOARD_LCD_MIRROR_X true"),
        ("#define BOARD_LCD_MIRROR_Y false", "#define BOARD_LCD_MIRROR_Y true"),
        ("#define BOARD_LCD_INVERT_COLOR true", "#define BOARD_LCD_INVERT_COLOR false"),
    ):
        s = replace_once(s, old, new, "board generator")
    return s


def patch_display(s):
    s = replace_once(s, "#include <esp_lcd_panel_vendor.h>",
                     "#include <esp_lcd_panel_vendor.h>\n#include <esp_lcd_st7735.h>",
                     "ST7735S driver include")
    s = replace_once(s, "#define STRIPE_HEIGHT 32", "#define STRIPE_HEIGHT 10",
                     "DMA stripe size")
    # waveshare/esp_lcd_st7735 2.0.0 exposes DISPON/DISPOFF, but does not
    # implement esp_lcd_panel_disp_sleep. Send the ST7735 sleep commands via
    # the panel IO and wait for the controller to settle instead.
    s = replace_once(s, "    esp_lcd_panel_disp_sleep(panel_handle, true);",
                     "    esp_lcd_panel_io_tx_param(io_handle, 0x10 /* SLPIN */, NULL, 0);\n"
                     "    vTaskDelay(pdMS_TO_TICKS(120));", "panel sleep")
    s = replace_once(s, "    /* SLPOUT (driver waits ~100 ms to settle) then DISPON. */",
                     "    /* ST7735S SLPOUT needs time to settle before DISPON. */", "wake comment")
    s = replace_once(s, "    esp_lcd_panel_disp_sleep(panel_handle, false);",
                     "    esp_lcd_panel_io_tx_param(io_handle, 0x11 /* SLPOUT */, NULL, 0);\n"
                     "    vTaskDelay(pdMS_TO_TICKS(120));", "panel wake")
    marker = "    /* ST7735S startup used by the validated color diagnostic. */\n"
    if marker not in s:
        start = "    /* Create ST7789 panel */\n"
        end = "    fg_color = BOARD_LCD_FG_COLOR;"
        if s.count(start) != 1 or s.count(end) != 1:
            raise ValueError("display initialization source anchors are not unique")
        before, rest = s.split(start, 1)
        _, after = rest.split(end, 1)
        replacement = marker + """    esp_lcd_panel_dev_config_t panel_config = {
        .reset_gpio_num = gpio_lcd_rst.pin,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_st7735(io_handle, &panel_config, &panel_handle));
    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel_handle));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel_handle));
    ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel_handle, BOARD_LCD_INVERT_COLOR));
    ESP_ERROR_CHECK(esp_lcd_panel_mirror(panel_handle, BOARD_LCD_MIRROR_X, BOARD_LCD_MIRROR_Y));
    ESP_ERROR_CHECK(esp_lcd_panel_set_gap(panel_handle, BOARD_LCD_GAP_X, BOARD_LCD_GAP_Y));
    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel_handle, true));

"""
        s = before + replacement + end + after
    return s


def patch_component_manifest(s):
    dependency = '  waveshare/esp_lcd_st7735:\n    version: "==2.0.0"\n'
    if "  waveshare/esp_lcd_st7735:" in s:
        if dependency not in s:
            raise ValueError("ST7735S dependency exists with a different version")
        return s
    return replace_once(s, "dependencies:\n", "dependencies:\n" + dependency,
                        "component manifest")


def patch_component_cmake(s):
    return replace_once(s, "furi toolbox input driver esp_lcd fatfs sdmmc datetime",
                        "furi toolbox input driver esp_lcd waveshare__esp_lcd_st7735 fatfs sdmmc datetime",
                        "component requirements")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_st7735.py /path/to/patched/upstream")
    root = Path(sys.argv[1]).resolve()
    changes = {
        "tools/gen_diy_board.py": patch_generator,
        "components/furi_hal/furi_hal_display.c": patch_display,
        "components/furi_hal/idf_component.yml": patch_component_manifest,
        "components/furi_hal/CMakeLists.txt": patch_component_cmake,
    }
    prepared = {p: fn((root / p).read_text(encoding="utf-8")) for p, fn in changes.items()}
    # Refuse configuration drift before writing anything.
    pinout = (root / "Pinout.txt").read_text(encoding="utf-8")
    for pair in ("SPI_SCK=12", "SPI_MOSI=11", "LCD_CS=-1", "LCD_DC=15", "LCD_RST=16"):
        if pair not in pinout.splitlines():
            raise ValueError(f"Expected tested pin setting {pair}")
    for p, content in prepared.items():
        (root / p).write_text(content, encoding="utf-8")
        print("patched:", p)
    subprocess.run([sys.executable, str(root / "tools/gen_diy_board.py"), str(root / "Pinout.txt")],
                   cwd=root, check=True)
    board = (root / "components/furi_hal/boards/board_DIY.h").read_text(encoding="utf-8")
    required = (
        "#define BOARD_LCD_H_RES 128", "#define BOARD_LCD_V_RES 160",
        "#define BOARD_LCD_SIDE_MARGIN 0", "#define BOARD_LCD_SPI_FREQ_HZ (5 * 1000 * 1000)",
        "#define BOARD_LCD_MIRROR_X true", "#define BOARD_LCD_MIRROR_Y true",
        "#define BOARD_LCD_INVERT_COLOR false", "#define BOARD_LCD_GAP_X 0", "#define BOARD_LCD_GAP_Y 0",
        "#define BOARD_PIN_LCD_CS   UINT16_MAX", "#define BOARD_PIN_BTN_OK     8",
        "#define BOARD_SD_SPI_HOST SPI3_HOST", "#define BOARD_PIN_SD_MISO2 38",
        "#define BOARD_PIN_SD_MOSI  39", "#define BOARD_PIN_SD_SCK   40", "#define BOARD_PIN_SD_CS    14",
    )
    missing = [item for item in required if item not in board]
    if missing:
        raise SystemExit(f"Generated board settings differ from expected: {missing}")
    print("PASSED: ST7735S 128x160 / CS grounded / 5 MHz / SD on separate SPI3")


if __name__ == "__main__":
    main()
