#!/usr/bin/env python3
"""Adapt the pinned DIY240 source to the verified ST7735S test wiring.

Run after patch_flipper.py in a fresh upstream checkout. Does not flash a device.
The SPI driver and panel startup match diagnostics/st7735-test, which was
confirmed by the user on their physical module.
"""
from pathlib import Path
import argparse
import subprocess
import sys

PROFILE = Path(__file__).resolve().parents[2] / "patch" / "Pinout_ESP32S3_ST7735S_160.txt"


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old in text:
        if text.count(old) != 1:
            raise ValueError(f"{label}: expected exactly one source anchor")
        return text.replace(old, new, 1)
    raise ValueError(f"{label}: expected source anchor missing: {old[:100]!r}")


def patch_generator(s):
    is_landscape = (
        "#define BOARD_OTA_PROFILE_ST7735 1\n#define BOARD_LCD_H_RES 160\n#define BOARD_LCD_V_RES 128"
        in s
    )
    legacy_req = ('       "CC1101_CS","CC1101_SCK","CC1101_MOSI","CC1101_MISO","CC1101_GDO0","CC1101_GDO2",\n'
                  '       "NRF24_SCK","NRF24_MOSI","NRF24_MISO","NRF24_CS","NRF24_CE",\n'
                  '       "NFC_SDA","NFC_SCL","NFC_IRQ","NFC_RST",\n'
                  '       "IR_TX","IR_RX","RFID_TX","RFID_RX","IBUTTON_PIN",\n'
                  '       "BTN_UP","BTN_DOWN","BTN_LEFT","BTN_RIGHT","BTN_OK","BTN_BACK"]')
    canonical_req = legacy_req.replace('"RFID_TX","RFID_RX","IBUTTON_PIN"', '"RFID_TX","RFID_RX"')
    if legacy_req in s:
        s = s.replace(legacy_req, canonical_req, 1)
    for old, new in (
        ("/* Buttons (active low, wired to GND) */\n",
         "/* Buttons (active low, wired to GND) */\n"
         "#define BOARD_INPUT_DPAD 1 /* six physical buttons, not a rotary encoder */\n"),
        ('       "CC1101_CS","CC1101_GDO0","CC1101_GDO2","NRF24_CS","NRF24_CE","NFC_SDA","NFC_SCL",\n'
         '       "NFC_IRQ","NFC_RST","IR_TX","IR_RX","BTN_UP","BTN_DOWN","BTN_LEFT","BTN_RIGHT",\n'
         '       "BTN_OK","BTN_BACK"]',
         '       "CC1101_CS","CC1101_SCK","CC1101_MOSI","CC1101_MISO","CC1101_GDO0","CC1101_GDO2",\n'
         '       "NRF24_SCK","NRF24_MOSI","NRF24_MISO","NRF24_CS","NRF24_CE",\n'
         '       "NFC_SDA","NFC_SCL","NFC_IRQ","NFC_RST",\n'
         '       "IR_TX","IR_RX","RFID_TX","RFID_RX",\n'
         '       "BTN_UP","BTN_DOWN","BTN_LEFT","BTN_RIGHT","BTN_OK","BTN_BACK"]'),
        ('nrf = p["NRF24_CS"] >= 0 and p["NRF24_CE"] >= 0',
         'nrf = (p["NRF24_SCK"] >= 0 and p["NRF24_MOSI"] >= 0 and p["NRF24_MISO"] >= 0 and\n'
         '       p["NRF24_CS"] >= 0 and p["NRF24_CE"] >= 0)\n'
         'nfc_irq_macro = f\'#define BOARD_PIN_NFC_IRQ {g("NFC_IRQ")}\\n\' if p["NFC_IRQ"] >= 0 else ""\n'
         'nfc_rst_macro = f\'#define BOARD_PIN_NFC_RST {g("NFC_RST")}\\n\' if p["NFC_RST"] >= 0 else ""'),
        ("#define BOARD_OTA_PROFILE_ST7789 1\n#define BOARD_LCD_H_RES 240\n#define BOARD_LCD_V_RES 240",
         "#define BOARD_OTA_PROFILE_ST7735 1\n#define BOARD_LCD_H_RES 128\n#define BOARD_LCD_V_RES 160\n"
         "#define BOARD_LCD_SIDE_MARGIN 0\n#define BOARD_LCD_FILL_SCREEN 1"),
        ("/* LCD ST7789 */", "/* LCD ST7735S */"),
        ("#define BOARD_LCD_SPI_FREQ_HZ (10 * 1000 * 1000)",
         "#define BOARD_LCD_SPI_FREQ_HZ (5 * 1000 * 1000)"),
        ('#define BOARD_PIN_CC1101_SCK  {g("SPI_SCK")}\n#define BOARD_PIN_CC1101_CSN  {g("CC1101_CS")}\n'
         '#define BOARD_PIN_CC1101_MISO {g("SPI_MISO")}\n#define BOARD_PIN_CC1101_MOSI {g("SPI_MOSI")}',
         '#define BOARD_PIN_CC1101_SCK  {g("CC1101_SCK")}\n#define BOARD_PIN_CC1101_CSN  {g("CC1101_CS")}\n'
         '#define BOARD_PIN_CC1101_MISO {g("CC1101_MISO")}\n#define BOARD_PIN_CC1101_MOSI {g("CC1101_MOSI")}'),
        ('#define BOARD_CC1101_SPI_SHARED 1',
         '#define BOARD_CC1101_SPI_SHARED 0 /* dedicated bitbang bus; never shares the CS-less LCD */'),
        ('#define BOARD_PIN_NRF24_SCK  {g("SPI_SCK")}\n#define BOARD_PIN_NRF24_MISO {g("SPI_MISO")}\n'
         '#define BOARD_PIN_NRF24_MOSI {g("SPI_MOSI")}',
         '#define BOARD_PIN_NRF24_SCK  {g("NRF24_SCK")}\n#define BOARD_PIN_NRF24_MISO {g("NRF24_MISO")}\n'
         '#define BOARD_PIN_NRF24_MOSI {g("NRF24_MOSI")}\n#define BOARD_NRF24_SPI_SEPARATE 1'),
        ('    if p[k] in seen: sys.exit(f"Conflict: {k} and {seen[p[k]]} both use GPIO{p[k]}")\n'
         '    if p[k] in spi_seen: sys.exit(f"Conflict: {k} and {spi_seen[p[k]]} both use GPIO{p[k]}")',
         '    # ST7735S is write-only; GPIO13 can also serve as the CC1101 GDO0 input.\n'
         '    # It is an intentional input/input alias; the LCD never samples MISO.\n'
         '    shared_lcd_miso_gdo = (k == "SPI_MISO" and p[k] == p.get("CC1101_GDO0", -1))\n'
         '    if p[k] in seen and not (shared_lcd_miso_gdo and seen[p[k]] == "CC1101_GDO0"):\n'
         '        sys.exit(f"Conflict: {k} and {seen[p[k]]} both use GPIO{p[k]}")\n'
         '    if p[k] in spi_seen: sys.exit(f"Conflict: {k} and {spi_seen[p[k]]} both use GPIO{p[k]}")'),
        ('#define BOARD_PIN_NFC_IRQ {g("NFC_IRQ")}\n#define BOARD_PIN_NFC_RST {g("NFC_RST")}',
         '{nfc_irq_macro}{nfc_rst_macro}'),
        ('#define BOARD_HAS_IR {1 if p["IR_TX"] >= 0 else 0}\n#define BOARD_HAS_IBUTTON 0\n'
         '#define BOARD_HAS_RFID 0\n#define BOARD_HAS_NFC 0\n#define BOARD_HAS_SUBGHZ 0',
         '#define BOARD_HAS_IR {1 if p["IR_TX"] >= 0 and p["IR_RX"] >= 0 else 0}\n'
         '#define BOARD_HAS_IBUTTON 0 /* upstream ESP32 iButton HAL is not implemented */\n'
         '#define BOARD_HAS_RFID {1 if p["RFID_TX"] >= 0 and p["RFID_RX"] >= 0 else 0}\n'
         '#define BOARD_HAS_NFC {1 if p["NFC_SDA"] >= 0 and p["NFC_SCL"] >= 0 else 0}\n'
         '#define BOARD_HAS_SUBGHZ {1 if p["CC1101_SCK"] >= 0 and p["CC1101_MOSI"] >= 0 and '
         'p["CC1101_MISO"] >= 0 and p["CC1101_CS"] >= 0 and p["CC1101_GDO0"] >= 0 else 0}'),
        ('#define BOARD_PIN_RFID_RX UINT16_MAX\n#define BOARD_PIN_RFID_TX UINT16_MAX',
         '#define BOARD_PIN_RFID_RX {g("RFID_RX")}\n#define BOARD_PIN_RFID_TX {g("RFID_TX")}'),
        ("#define BOARD_LCD_MIRROR_Y false", "#define BOARD_LCD_MIRROR_Y true"),
        ("#define BOARD_LCD_INVERT_COLOR true", "#define BOARD_LCD_INVERT_COLOR false"),
    ):
        if is_landscape and old.startswith("#define BOARD_OTA_PROFILE_ST7789"):
            continue
        s = replace_once(s, old, new, "board generator")
    if not is_landscape:
        s = replace_once(s, "#define BOARD_LCD_MIRROR_X false",
                         "#define BOARD_LCD_MIRROR_X true", "board generator")
    return s


def patch_fam_config(s):
    marker = "# DIY_ST7735_PIN_CAPABILITY_FILTERS"
    if marker in s:
        s = s.replace(
            'os.path.join(os.path.dirname(__file__), "Pinout.txt")',
            'os.path.join(os.environ.get("FLIPPER_FAM_CONFIG_DIR", os.getcwd()), "Pinout.txt")',
        )
        nfc_activation = '    if _diy_has("NFC_SDA", "NFC_SCL") and "nfc" not in APPS:\n'
        if nfc_activation not in s:
            anchor = '    (_boards_without_nfc.discard if _diy_has("NFC_SDA", "NFC_SCL") else _boards_without_nfc.add)("DIY")\n'
            s = replace_once(s, anchor, anchor +
                             '    if _diy_has("NFC_SDA", "NFC_SCL") and "nfc" not in APPS:\n'
                             '        APPS.append("nfc")\n', "activate NFC app for DIY module profile")
        return s
    anchor = next((candidate for candidate in (
        '_boards_without_nrf24 = {"waveshare_c6", "waveshare_c6_1.9", "waveshare_c6_1.47", "DIY"}\n',
        '_boards_without_nrf24 = {"waveshare_c6", "waveshare_c6_1.9", "waveshare_c6_1.47"}\n',
    ) if candidate in s), None)
    if anchor is None:
        raise ValueError("DIY feature app selection: NRF24 board filter anchor missing")
    helper = '''

# DIY_ST7735_PIN_CAPABILITY_FILTERS
# The DIY app list follows the active generated Pinout.txt. Hardware-specific
# apps stay out of the menu until their required module pins are assigned.
_diy_pinout = {}
if _board == "DIY":
    try:
        with open(os.path.join(os.environ.get("FLIPPER_FAM_CONFIG_DIR", os.getcwd()), "Pinout.txt"), encoding="utf-8") as _pinout_file:
            for _line in _pinout_file:
                _line = _line.split("#", 1)[0].strip()
                if "=" in _line:
                    _key, _value = _line.split("=", 1)
                    _diy_pinout[_key.strip()] = int(_value.strip())
    except (OSError, ValueError):
        _diy_pinout = {}

def _diy_has(*pins):
    return all(_diy_pinout.get(pin, -1) >= 0 for pin in pins)

if _board == "DIY":
    (_boards_without_nfc.discard if _diy_has("NFC_SDA", "NFC_SCL") else _boards_without_nfc.add)("DIY")
    (_boards_without_ir.discard if _diy_has("IR_TX", "IR_RX") else _boards_without_ir.add)("DIY")
    (_boards_without_subghz.discard if _diy_has("CC1101_SCK", "CC1101_MOSI", "CC1101_MISO", "CC1101_CS", "CC1101_GDO0") else _boards_without_subghz.add)("DIY")
    (_boards_without_nrf24.discard if _diy_has("NRF24_SCK", "NRF24_MOSI", "NRF24_MISO", "NRF24_CS", "NRF24_CE") else _boards_without_nrf24.add)("DIY")
    if _diy_has("NFC_SDA", "NFC_SCL") and "nfc" not in APPS:
        APPS.append("nfc")  # The earlier generic board filter ran before pin capabilities were loaded.
    if _diy_has("RFID_TX", "RFID_RX") and "lfrfid" not in APPS:
        APPS.append("lfrfid")  # Current ESP32 HAL supports RDM6300 read-only.
'''
    return replace_once(s, anchor, anchor + helper, "DIY feature app selection")


def patch_display(s):
    s = replace_once(s, "#include <esp_lcd_panel_vendor.h>",
                     "#include <esp_lcd_panel_vendor.h>\n#include <esp_lcd_st7735.h>",
                     "ST7735S driver include")
    s = replace_once(
        s,
        "/* Scale the 128x64 framebuffer to the largest centered size that keeps aspect ratio. */\n"
        "#if (USABLE_H_RES * FB_HEIGHT) <= (LCD_V_RES * FB_WIDTH)\n"
        "#define SCALED_WIDTH  USABLE_H_RES\n"
        "#define SCALED_HEIGHT ((USABLE_H_RES * FB_HEIGHT) / FB_WIDTH)\n"
        "#else\n"
        "#define SCALED_HEIGHT LCD_V_RES\n"
        "#define SCALED_WIDTH  ((LCD_V_RES * FB_WIDTH) / FB_HEIGHT)\n"
        "#endif",
        "/* The ST7735S profile fills its entire 160x128 panel. The stock Flipper\n"
        " * 128x64 canvas is scaled independently on each axis, so there are no\n"
        " * unused top/bottom bands. Other boards retain aspect-fit rendering. */\n"
        "#if defined(BOARD_LCD_FILL_SCREEN) && BOARD_LCD_FILL_SCREEN\n"
        "#define SCALED_WIDTH LCD_H_RES\n"
        "#define SCALED_HEIGHT LCD_V_RES\n"
        "#else\n"
        "#if (USABLE_H_RES * FB_HEIGHT) <= (LCD_V_RES * FB_WIDTH)\n"
        "#define SCALED_WIDTH  USABLE_H_RES\n"
        "#define SCALED_HEIGHT ((USABLE_H_RES * FB_HEIGHT) / FB_WIDTH)\n"
        "#else\n"
        "#define SCALED_HEIGHT LCD_V_RES\n"
        "#define SCALED_WIDTH  ((LCD_V_RES * FB_WIDTH) / FB_HEIGHT)\n"
        "#endif\n"
        "#endif",
        "full-panel ST7735S scaling")
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


def patch_spi_types(s):
    return replace_once(
        s,
        "extern FuriHalSpiBus furi_hal_spi_bus_subghz;\n",
        "extern FuriHalSpiBus furi_hal_spi_bus_subghz;\n"
        "extern FuriHalSpiBus furi_hal_spi_bus_nrf24;\n",
        "independent nRF24 SPI bus declaration",
    )


def patch_resources_h(s):
    return replace_once(
        s,
        "extern const GpioPin gpio_nrf24_cs; /* NRF24 CSN -- T-Embed: GPIO44 */\n",
        "extern const GpioPin gpio_nrf24_cs; /* nRF24 CSN */\n"
        "extern const GpioPin gpio_nrf24_sck;\n"
        "extern const GpioPin gpio_nrf24_mosi;\n"
        "extern const GpioPin gpio_nrf24_miso;\n",
        "independent nRF24 GPIO declarations",
    )


def patch_resources_c(s):
    anchor = (
        "#else\n"
        "const GpioPin gpio_nrf24_cs = {.port = NULL, .pin = UINT16_MAX};\n"
        "#endif\n"
    )
    replacement = anchor + (
        "#ifdef BOARD_PIN_NRF24_SCK\n"
        "const GpioPin gpio_nrf24_sck = {.port = NULL, .pin = BOARD_PIN_NRF24_SCK};\n"
        "const GpioPin gpio_nrf24_mosi = {.port = NULL, .pin = BOARD_PIN_NRF24_MOSI};\n"
        "const GpioPin gpio_nrf24_miso = {.port = NULL, .pin = BOARD_PIN_NRF24_MISO};\n"
        "#else\n"
        "const GpioPin gpio_nrf24_sck = {.port = NULL, .pin = UINT16_MAX};\n"
        "const GpioPin gpio_nrf24_mosi = {.port = NULL, .pin = UINT16_MAX};\n"
        "const GpioPin gpio_nrf24_miso = {.port = NULL, .pin = UINT16_MAX};\n"
        "#endif\n"
    )
    return replace_once(s, anchor, replacement, "independent nRF24 GPIO resources")


def patch_spi(s):
    s = replace_once(
        s,
        "FuriHalSpiBusHandle furi_hal_spi_bus_handle_external = {\n",
        "FuriHalSpiBus furi_hal_spi_bus_nrf24 = {\n"
        "    .host_id = -1,\n"
        "    .bitbang = true,\n"
        "    .initialized = false,\n"
        "    .mutex = NULL,\n"
        "    .current_handle = NULL,\n"
        "    .mosi_pin = FURI_HAL_SPI_PIN_UNMAPPED,\n"
        "    .miso_pin = FURI_HAL_SPI_PIN_UNMAPPED,\n"
        "    .sck_pin = FURI_HAL_SPI_PIN_UNMAPPED,\n"
        "};\n\n"
        "FuriHalSpiBusHandle furi_hal_spi_bus_handle_external = {\n",
        "separate software SPI bus for nRF24",
    )
    old = (
        "/* NRF24 sits on the same SPI bus as the SubGhz / CC1101 (T-Embed) but uses its\n"
        " * own CS pin -- both devices can be parallel-attached and CS-muxed on the bus. */\n"
        "FuriHalSpiBusHandle furi_hal_spi_bus_handle_nrf24 = {\n"
        "    .bus = &furi_hal_spi_bus_subghz,\n"
        "    .miso = &gpio_ext_pa6,\n"
        "    .mosi = &gpio_ext_pa7,\n"
        "    .sck = &gpio_ext_pb3,\n"
        "    .cs = &gpio_nrf24_cs,\n"
        "    .device = NULL,\n"
        "    .initialized = false,\n"
        "    .frequency_hz = 4 * 1000 * 1000,\n"
        "    .mode = 0,\n"
        "};\n"
    )
    new = (
        "/* Most boards share the CC1101 bus. DIY ST7735S has separate wiring for\n"
        " * nRF24, so it gets an independent bit-banged bus and GPIO set. */\n"
        "#if defined(BOARD_NRF24_SPI_SEPARATE) && BOARD_NRF24_SPI_SEPARATE\n"
        "FuriHalSpiBusHandle furi_hal_spi_bus_handle_nrf24 = {\n"
        "    .bus = &furi_hal_spi_bus_nrf24,\n"
        "    .miso = &gpio_nrf24_miso,\n"
        "    .mosi = &gpio_nrf24_mosi,\n"
        "    .sck = &gpio_nrf24_sck,\n"
        "    .cs = &gpio_nrf24_cs,\n"
        "    .device = NULL,\n"
        "    .initialized = false,\n"
        "    .frequency_hz = 1 * 1000 * 1000,\n"
        "    .mode = 0,\n"
        "};\n"
        "#else\n"
        "FuriHalSpiBusHandle furi_hal_spi_bus_handle_nrf24 = {\n"
        "    .bus = &furi_hal_spi_bus_subghz,\n"
        "    .miso = &gpio_ext_pa6,\n"
        "    .mosi = &gpio_ext_pa7,\n"
        "    .sck = &gpio_ext_pb3,\n"
        "    .cs = &gpio_nrf24_cs,\n"
        "    .device = NULL,\n"
        "    .initialized = false,\n"
        "    .frequency_hz = 4 * 1000 * 1000,\n"
        "    .mode = 0,\n"
        "};\n"
        "#endif\n"
    )
    return replace_once(s, old, new, "independent nRF24 SPI handle")


def patch_build(s):
    export_line = 'export FLIPPER_FAM_CONFIG_DIR="${SCRIPT_DIR}"\n'
    generator_line = 'python3 "${SCRIPT_DIR}/tools/gen_diy_board.py" "${SCRIPT_DIR}/Pinout.txt"\n'
    if export_line not in s:
        if generator_line in s:
            s = replace_once(s, generator_line, export_line + generator_line,
                             "export source path for FAM configuration")
        else:
            s = replace_once(s, 'cd "${SCRIPT_DIR}"\n# shellcheck source=/dev/null',
                             'cd "${SCRIPT_DIR}"\n' + export_line + generator_line +
                             '# shellcheck source=/dev/null', "regenerate board profile before build")
    elif generator_line not in s:
        s = replace_once(s, export_line, export_line + generator_line,
                         "regenerate board profile before build")
    return s


def patch_sdkconfig(s):
    setting = "CONFIG_ESP_CONSOLE_NONE=y"
    if setting in s:
        return s
    return s.rstrip() + (
        "\n\n# GPIO43/TX is the CC1101 CSN pin in this board profile.\n"
        "# Keep the app UART console from taking control of the radio select line.\n"
        f"{setting}\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Apply the ST7735S landscape-capable board profile")
    parser.add_argument("root", help="patched upstream source checkout")
    parser.add_argument("--pinout", type=Path, default=PROFILE,
                        help="board pinout file (defaults to the verified ST7735S base profile)")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    profile = args.pinout.expanduser().resolve()
    changes = {
        "tools/gen_diy_board.py": patch_generator,
        "components/furi_hal/furi_hal_display.c": patch_display,
        "components/furi_hal/idf_component.yml": patch_component_manifest,
        "components/furi_hal/CMakeLists.txt": patch_component_cmake,
        "components/furi_hal/furi_hal_spi_types.h": patch_spi_types,
        "components/furi_hal/furi_hal_spi.c": patch_spi,
        "components/furi_hal/furi_hal_resources.h": patch_resources_h,
        "components/furi_hal/furi_hal_resources.c": patch_resources_c,
        "fam_config.py": patch_fam_config,
        "build_diy.sh": patch_build,
        "sdkconfig.defaults.esp32s3": patch_sdkconfig,
    }
    prepared = {p: fn((root / p).read_text(encoding="utf-8")) for p, fn in changes.items()}
    # The common DIY patch starts from ST7789. Replace that Pinout explicitly
    # so CS, SPI rate, and the generated board identity match the ST7735S.
    pinout = profile.read_text(encoding="utf-8")
    for pair in ("SPI_SCK=12", "SPI_MOSI=11", "SPI_MISO=13", "LCD_CS=-1", "LCD_DC=15", "LCD_RST=16",
                 "SD_SCK=40", "SD_MOSI=39", "SD_MISO=38", "SD_CS=14",
                 "CC1101_CS=43", "CC1101_SCK=9", "CC1101_MOSI=10", "CC1101_MISO=21",
                 "CC1101_GDO0=13", "NRF24_SCK=41", "NRF24_MOSI=42", "NRF24_MISO=47",
                 "NRF24_CS=1", "NRF24_CE=2", "NFC_SDA=-1", "NFC_SCL=-1",
                 "IR_TX=-1", "IR_RX=-1", "RFID_TX=-1", "RFID_RX=-1"):
        if pair not in pinout.splitlines():
            raise ValueError(f"Expected tested pin setting {pair}")
    for p, content in prepared.items():
        (root / p).write_text(content, encoding="utf-8")
        print("patched:", p)
    (root / "Pinout.txt").write_text(pinout, encoding="utf-8")
    subprocess.run([sys.executable, str(root / "tools/gen_diy_board.py"), str(root / "Pinout.txt")],
                   cwd=root, check=True)
    board = (root / "components/furi_hal/boards/board_DIY.h").read_text(encoding="utf-8")
    required = (
        "#define BOARD_OTA_PROFILE_ST7735 1",
        "#define BOARD_INPUT_DPAD 1",
        "#define BOARD_LCD_SIDE_MARGIN 0", "#define BOARD_LCD_FILL_SCREEN 1",
        "#define BOARD_LCD_SPI_FREQ_HZ (5 * 1000 * 1000)",
        "#define BOARD_LCD_MIRROR_Y true",
        "#define BOARD_LCD_INVERT_COLOR false", "#define BOARD_LCD_GAP_X 0", "#define BOARD_LCD_GAP_Y 0",
        "#define BOARD_PIN_LCD_CS   UINT16_MAX", "#define BOARD_PIN_BTN_OK     8",
        "#define BOARD_SD_SPI_HOST SPI3_HOST", "#define BOARD_PIN_SD_MISO2 38",
        "#define BOARD_PIN_SD_MOSI  39", "#define BOARD_PIN_SD_SCK   40", "#define BOARD_PIN_SD_CS    14",
        "#define BOARD_PIN_CC1101_CSN  43", "#define BOARD_PIN_CC1101_GDO0 13",
        "#define BOARD_PIN_NRF24_SCK  41", "#define BOARD_PIN_NRF24_MISO 47",
        "#define BOARD_PIN_NRF24_MOSI 42", "#define BOARD_NRF24_SPI_SEPARATE 1",
        "#define BOARD_PIN_NRF24_CSN  1", "#define BOARD_PIN_NRF24_CE   2",
    )
    missing = [item for item in required if item not in board]
    geometries = (
        ("#define BOARD_LCD_H_RES 128", "#define BOARD_LCD_V_RES 160", "#define BOARD_LCD_MIRROR_X true"),
        ("#define BOARD_LCD_H_RES 160", "#define BOARD_LCD_V_RES 128", "#define BOARD_LCD_MIRROR_X false"),
    )
    if not any(all(item in board for item in geometry) for geometry in geometries):
        missing.append("ST7735S portrait or landscape geometry/orientation")
    if missing:
        raise SystemExit(f"Generated board settings differ from expected: {missing}")
    print("PASSED: ST7735S 160x128 landscape or portrait profile / CS grounded / 5 MHz / SD on SPI3")


if __name__ == "__main__":
    main()
