"""Unit tests for deterministic source anchors and per-board configuration.

These tests do not replace the actual ESP-IDF compile or on-device test.
"""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('patch_flipper', ROOT / 'patch' / 'patch_flipper.py')
PATCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PATCH)
LANDSCAPE_SPEC = importlib.util.spec_from_file_location(
    'patch_landscape', ROOT / 'variants' / 'st7735' / 'patch_landscape.py')
LANDSCAPE = importlib.util.module_from_spec(LANDSCAPE_SPEC)
LANDSCAPE_SPEC.loader.exec_module(LANDSCAPE)


class PatchContractTest(unittest.TestCase):
    def test_pinout_isolates_buses_and_avoids_strapping(self):
        content = (ROOT / 'patch' / 'Pinout_ESP32S3_ST7735S_160.txt').read_text()
        cfg = {}
        for line in content.splitlines():
            line = line.split('#', 1)[0].strip()
            if line:
                key, value = [v.strip() for v in line.split('=', 1)]
                cfg[key] = int(value)
        required = {
            'SPI_SCK':12, 'SPI_MOSI':11, 'SPI_MISO':13,
            'SD_SCK':40, 'SD_MOSI':39, 'SD_MISO':38, 'SD_CS':14,
            'LCD_CS':-1, 'LCD_DC':15, 'LCD_RST':16, 'LCD_BL':7,
            'BTN_UP':4, 'BTN_DOWN':5, 'BTN_LEFT':6,
            'BTN_RIGHT':17, 'BTN_OK':8, 'BTN_BACK':18,
        }
        self.assertEqual({key:cfg[key] for key in required}, required)
        module_pins = {
            'CC1101_CS':22, 'CC1101_SCK':9, 'CC1101_MOSI':10,
            'CC1101_MISO':21, 'CC1101_GDO0':23,
            'NRF24_CS':24, 'NRF24_CE':25,
            'NFC_SDA':41, 'NFC_SCL':42,
            'IR_TX':1, 'IR_RX':2, 'RFID_TX':47, 'RFID_RX':48,
        }
        self.assertEqual({key:cfg[key] for key in module_pins}, module_pins)
        assigned = [val for val in cfg.values() if val >= 0]
        self.assertEqual(len(assigned), len(set(assigned)))
        self.assertFalse(set(assigned) & {0, 3, 19, 20, *range(26, 38), 43, 44, 45, 46})

    def test_display_patch_converts_absent_cs_to_minus_one(self):
        base = '.cs_gpio_num = gpio_lcd_cs.pin,'
        edited = PATCH.patch_display(base)
        self.assertIn('gpio_lcd_cs.pin == UINT16_MAX', edited)
        self.assertIn('? -1 :', edited)
        self.assertEqual(edited, PATCH.patch_display(edited))

    def test_generator_includes_240_panel_and_separate_sd(self):
        source = '''REQ = ["SPI_SCK","SPI_MOSI","SPI_MISO","LCD_CS",\n\nspi = {"SPI_SCK","SPI_MOSI","SPI_MISO"}\nfor k in spi:
    if p[k] in seen: sys.exit(f"Conflict: {k} and {seen[p[k]]} both use GPIO{p[k]}")
#define BOARD_LCD_H_RES 320
#define BOARD_LCD_V_RES 172
#define BOARD_LCD_SPI_FREQ_HZ (40 * 1000 * 1000)
#define BOARD_LCD_SWAP_XY true
#define BOARD_LCD_MIRROR_X true
#define BOARD_LCD_GAP_Y 35
#define BOARD_PIN_SD_CS   {g("SD_CS")}
#define BOARD_PIN_SD_MISO {g("SPI_MISO")}
#define BOARD_HAS_NFC 1
#define BOARD_HAS_SUBGHZ 1
'''
        modified = PATCH.patch_generator(source)
        for piece in ('SD_SCK', 'SD_MOSI', 'SD_MISO',
                      '#define BOARD_LCD_H_RES 240',
                      '#define BOARD_LCD_V_RES 240',
                      '#define BOARD_SD_BUS_NOT_SHARED 1',
                      '#define BOARD_SD_SPI_HOST SPI3_HOST',
                      '#define BOARD_HAS_NFC 0',
                      '#define BOARD_HAS_SUBGHZ 0',
                      'spi_seen[p[k]] = k'):
            self.assertIn(piece, modified)
        self.assertEqual(modified, PATCH.patch_generator(modified))

    def test_fam_disables_unavailable_hardware(self):
        original = ('_boards_without_nfc = {"a"}\n'
                    '_boards_without_ir = {"b"}\n'
                    '_boards_without_subghz = {"c"}\n'
                    '_boards_without_nrf24 = {"d"}\n')
        edited = PATCH.patch_fam(original)
        for line in edited.splitlines():
            self.assertIn('"DIY"', line)
        self.assertEqual(edited, PATCH.patch_fam(edited))

    def test_build_script_uses_s3_defaults(self):
        original = ('SDK_OPTS=("-DSDKCONFIG=${BUILD_DIR}/sdkconfig")\n'
                    'idf.py -B "${BUILD_DIR}" "${SDK_OPTS[@]}" set-target "${IDF_TARGET}"\n')
        edited = PATCH.patch_build(original)
        self.assertIn('sdkconfig.defaults.esp32s3', edited)
        self.assertIn('-DFLIPPER_BOARD="${BOARD}"', edited)
        self.assertEqual(edited, PATCH.patch_build(edited))

    def test_firmware_identity_is_m4145_and_idempotent(self):
        source = (
            '#define FURI_ESP32_PROJECT_NAME   "Flipper-Zero-ESP32-Port"\n'
            '#define FURI_ESP32_PROJECT_AUTHOR "by Sor3nt"\n'
            '#define FURI_ESP32_VERSION      "2.0.0"\n'
            '#define FURI_ESP32_VERSION_NAME "Sor3nt Stuff"\n'
        )
        modified = LANDSCAPE.patch_firmware_identity(source)
        self.assertIn('"M4145 Flipper Firmware"', modified)
        self.assertIn('"by m4145"', modified)
        self.assertIn('"1.5.1"', modified)
        self.assertIn('"m4145 ESP32-S3"', modified)
        self.assertNotIn('"Sor3nt Stuff"', modified)
        self.assertEqual(modified, LANDSCAPE.patch_firmware_identity(modified))

    def test_home_title_patch_moves_text_below_top_header(self):
        source = (
            '#include <momentum_settings.h>\n'
            '/* Give the extra panel height a purpose */\n'
            'canvas_width(canvas) / 2, 21, AlignCenter, AlignBottom, "FLIPPER ZERO"\n'
            'canvas_draw_line(canvas, 24, 27, canvas_width(canvas) - 25, 27)\n'
        )
        moved = LANDSCAPE.patch_bubble_home(source)
        self.assertIn('canvas_width(canvas) / 2, 25, AlignCenter, AlignBottom, "FLIPPER ZERO"', moved)
        self.assertIn('canvas_draw_line(canvas, 24, 31, canvas_width(canvas) - 25, 31)', moved)
        self.assertEqual(moved, LANDSCAPE.patch_bubble_home(moved))

    def test_text_input_render_buffer_reserves_cursor_and_ellipsis(self):
        source = '    char buf[text_length + 1];\n'
        fixed = LANDSCAPE.patch_text_input_render_buffer(source)
        self.assertIn('char buf[text_length + 5];', fixed)
        self.assertNotIn('char buf[text_length + 1];', fixed)
        self.assertEqual(fixed, LANDSCAPE.patch_text_input_render_buffer(fixed))


if __name__ == '__main__':
    unittest.main()
