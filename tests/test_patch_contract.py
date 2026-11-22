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
ST7735_SPEC = importlib.util.spec_from_file_location(
    'patch_st7735', ROOT / 'variants' / 'st7735' / 'patch_st7735.py')
ST7735 = importlib.util.module_from_spec(ST7735_SPEC)
ST7735_SPEC.loader.exec_module(ST7735)


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
            'CC1101_CS':43, 'CC1101_SCK':9, 'CC1101_MOSI':10,
            'CC1101_MISO':21, 'CC1101_GDO0':13,
            'NRF24_SCK':41, 'NRF24_MOSI':42, 'NRF24_MISO':47,
            'NRF24_CS':1, 'NRF24_CE':2,
            'NFC_SDA':-1, 'NFC_SCL':-1,
            'IR_TX':-1, 'IR_RX':-1, 'RFID_TX':-1, 'RFID_RX':-1,
        }
        self.assertEqual({key:cfg[key] for key in module_pins}, module_pins)
        assigned = [val for val in cfg.values() if val >= 0]
        self.assertEqual({v for v in assigned if assigned.count(v) > 1}, {13})
        self.assertEqual(cfg['SPI_MISO'], cfg['CC1101_GDO0'])
        self.assertEqual(cfg['CC1101_CS'], 43)  # board silkscreen labels this pad TX
        self.assertFalse(set(assigned) & {0, 3, 19, 20, *range(26, 38), 44, 45, 46})

    def test_nrf24_uses_an_independent_spi_bus(self):
        source = '''REQ = ["SPI_SCK","SPI_MOSI","SPI_MISO","LCD_CS","LCD_DC","LCD_RST","LCD_BL","SD_CS",
       "CC1101_CS","CC1101_GDO0","CC1101_GDO2","NRF24_CS","NRF24_CE","NFC_SDA","NFC_SCL",
       "NFC_IRQ","NFC_RST","IR_TX","IR_RX","BTN_UP","BTN_DOWN","BTN_LEFT","BTN_RIGHT",
       "BTN_OK","BTN_BACK"]
spi = {"SPI_SCK","SPI_MOSI","SPI_MISO"}
spi_seen = {}
for k in sorted(spi):
    if p[k] < 0: sys.exit(f"{k}: SPI signal must have a GPIO")
    if p[k] in seen: sys.exit(f"Conflict: {k} and {seen[p[k]]} both use GPIO{p[k]}")
    if p[k] in spi_seen: sys.exit(f"Conflict: {k} and {spi_seen[p[k]]} both use GPIO{p[k]}")
    spi_seen[p[k]] = k
nrf = p["NRF24_CS"] >= 0 and p["NRF24_CE"] >= 0
nfc_irq_macro = f'#define BOARD_PIN_NFC_IRQ {g("NFC_IRQ")}\\n' if p["NFC_IRQ"] >= 0 else ""
nfc_rst_macro = f'#define BOARD_PIN_NFC_RST {g("NFC_RST")}\\n' if p["NFC_RST"] >= 0 else ""
/* Buttons (active low, wired to GND) */
#define BOARD_OTA_PROFILE_ST7735 1
#define BOARD_LCD_H_RES 160
#define BOARD_LCD_V_RES 128
/* LCD ST7789 */
#define BOARD_LCD_SPI_FREQ_HZ (10 * 1000 * 1000)
#define BOARD_OTA_PROFILE_ST7789 1
#define BOARD_LCD_H_RES 240
#define BOARD_LCD_V_RES 240
#define BOARD_PIN_CC1101_SCK  {g("SPI_SCK")}
#define BOARD_PIN_CC1101_CSN  {g("CC1101_CS")}
#define BOARD_PIN_CC1101_MISO {g("SPI_MISO")}
#define BOARD_PIN_CC1101_MOSI {g("SPI_MOSI")}
#define BOARD_CC1101_SPI_SHARED 1
#define BOARD_PIN_NRF24_SCK  {g("SPI_SCK")}
#define BOARD_PIN_NRF24_MISO {g("SPI_MISO")}
#define BOARD_PIN_NRF24_MOSI {g("SPI_MOSI")}
#define BOARD_PIN_NFC_IRQ {g("NFC_IRQ")}\n#define BOARD_PIN_NFC_RST {g("NFC_RST")}
#define BOARD_HAS_IR {1 if p["IR_TX"] >= 0 else 0}\n#define BOARD_HAS_IBUTTON 0\n#define BOARD_HAS_RFID 0\n#define BOARD_HAS_NFC 0\n#define BOARD_HAS_SUBGHZ 0
#define BOARD_PIN_RFID_RX UINT16_MAX
#define BOARD_PIN_RFID_TX UINT16_MAX
#define BOARD_LCD_MIRROR_Y false
#define BOARD_LCD_INVERT_COLOR true
#define BOARD_LCD_MIRROR_X false
'''
        patched = ST7735.patch_generator(source)
        self.assertIn('"NRF24_SCK","NRF24_MOSI","NRF24_MISO"', patched)
        self.assertIn('#define BOARD_PIN_NRF24_SCK  {g("NRF24_SCK")}', patched)
        self.assertIn('#define BOARD_NRF24_SPI_SEPARATE 1', patched)
        self.assertIn('shared_lcd_miso_gdo', patched)
        self.assertEqual(patched, ST7735.patch_generator(patched))

    def test_cc1101_tx_pad_does_not_share_app_uart_console(self):
        source = '# Target: ESP32-S3\n'
        patched = ST7735.patch_sdkconfig(source)
        self.assertIn('CONFIG_ESP_CONSOLE_NONE=y', patched)
        self.assertIn('GPIO43/TX is the CC1101 CSN pin', patched)
        self.assertEqual(patched, ST7735.patch_sdkconfig(patched))

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
