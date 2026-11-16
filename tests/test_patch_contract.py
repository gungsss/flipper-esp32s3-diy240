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


class PatchContractTest(unittest.TestCase):
    def test_pinout_isolates_buses_and_avoids_strapping(self):
        content = (ROOT / 'patch' / 'Pinout_ESP32S3_ST7789_240.txt').read_text()
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


if __name__ == '__main__':
    unittest.main()
