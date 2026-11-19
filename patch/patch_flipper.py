#!/usr/bin/env python3
"""Apply targeted DIY-240 patch to a local clone of Sor3nt Flipper ESP32 port.

Target: commit e6ec11972a8e025d7ab686a6ef3016cf52360834 (2026-11-14).
No third-party dependencies. Strict text anchors fail closed on source drift.
Backups saved in .flipper-diy240-backups before writing. Idempotent.
"""
from pathlib import Path
import re
import sys
import shutil
import subprocess

THIS = Path(__file__).resolve().parent
PROFILE = THIS / 'Pinout_ESP32S3_ST7789_240.txt'
EXPECTED = 'e6ec11972a8e025d7ab686a6ef3016cf52360834'


def replace_one(s: str, before: str, after: str, name: str) -> str:
    if before in s:
        hits = s.count(before)
        if hits != 1:
            raise ValueError(f'{name}: expected 1 occurrence, found {hits}: {before[:70]!r}')
        return s.replace(before, after, 1)
    if after in s:
        return s
    raise ValueError(f'{name}: source anchor no longer matches: {before[:95]!r}')


def patch_generator(s: str) -> str:
    tag = 'tools/gen_diy_board.py'
    s = replace_one(s,
        'REQ = ["SPI_SCK","SPI_MOSI","SPI_MISO","LCD_CS",',
        'REQ = ["SPI_SCK","SPI_MOSI","SPI_MISO","SD_SCK","SD_MOSI","SD_MISO","LCD_CS",', tag)
    s = replace_one(s,
        'spi = {"SPI_SCK","SPI_MOSI","SPI_MISO"}',
        'spi = {"SPI_SCK","SPI_MOSI","SPI_MISO","SD_SCK","SD_MOSI","SD_MISO"}', tag)
    # Check for collisions among BOTH buses, not only with non-SPI pins.
    s = replace_one(s,
        'for k in spi:\n    if p[k] in seen: sys.exit(f"Conflict: {k} and {seen[p[k]]} both use GPIO{p[k]}")',
        'spi_seen = {}\nfor k in sorted(spi):\n    if p[k] < 0: sys.exit(f"{k}: SPI signal must have a GPIO")\n    if p[k] in seen: sys.exit(f"Conflict: {k} and {seen[p[k]]} both use GPIO{p[k]}")\n    if p[k] in spi_seen: sys.exit(f"Conflict: {k} and {spi_seen[p[k]]} both use GPIO{p[k]}")\n    spi_seen[p[k]] = k', tag)
    s = replace_one(s, '#define BOARD_LCD_H_RES 320\n#define BOARD_LCD_V_RES 172',
        '#define BOARD_LCD_H_RES 240\n#define BOARD_LCD_V_RES 240', tag)
    s = replace_one(s, '#define BOARD_LCD_SPI_FREQ_HZ (40 * 1000 * 1000)',
        '#define BOARD_LCD_SPI_FREQ_HZ (20 * 1000 * 1000)', tag)
    s = replace_one(s, '#define BOARD_LCD_SWAP_XY true', '#define BOARD_LCD_SWAP_XY false', tag)
    s = replace_one(s, '#define BOARD_LCD_MIRROR_X true', '#define BOARD_LCD_MIRROR_X false', tag)
    s = replace_one(s, '#define BOARD_LCD_GAP_Y 35', '#define BOARD_LCD_GAP_Y 0', tag)
    s = replace_one(s,
        '#define BOARD_PIN_SD_CS   {g("SD_CS")}\n#define BOARD_PIN_SD_MISO {g("SPI_MISO")}',
        '#define BOARD_SD_BUS_NOT_SHARED 1\n#define BOARD_SD_SPI_HOST SPI3_HOST\n'
        '#define BOARD_SD_SPI_FREQ_KHZ 10000 /* conservative starting point */\n'
        '#define BOARD_PIN_SD_CS    {g("SD_CS")}\n'
        '#define BOARD_PIN_SD_MISO  {g("SPI_MISO")} /* LCD SPI2 MISO, unused by LCD */\n'
        '#define BOARD_PIN_SD_MISO2 {g("SD_MISO")} /* SD SPI3 */\n'
        '#define BOARD_PIN_SD_MOSI  {g("SD_MOSI")}\n'
        '#define BOARD_PIN_SD_SCK   {g("SD_SCK")}', tag)
    s = replace_one(s, '#define BOARD_HAS_NFC 1', '#define BOARD_HAS_NFC 0', tag)
    s = replace_one(s, '#define BOARD_HAS_SUBGHZ 1', '#define BOARD_HAS_SUBGHZ 0', tag)
    # Add compile-time guard to avoid accidentally using CS-less LCD on SPI2
    # with an enabled second SPI2 device. Radio modules can be added later with
    # a different topology and an explicit CS pin.
    return s


def patch_display(s: str) -> str:
    tag = 'components/furi_hal/furi_hal_display.c'
    return replace_one(s,
        '.cs_gpio_num = gpio_lcd_cs.pin,',
        '.cs_gpio_num = (gpio_lcd_cs.pin == UINT16_MAX) ? -1 : (int)gpio_lcd_cs.pin,', tag)


def patch_fam(s: str) -> str:
    tag = 'fam_config.py'
    for name in ('_boards_without_nfc', '_boards_without_ir',
                 '_boards_without_subghz', '_boards_without_nrf24'):
        pat = re.compile(r'(?m)^(' + re.escape(name) + r'\s*=\s*\{)([^\n]*)(\})$')
        m = pat.search(s)
        if not m:
            raise ValueError(f'{tag}: missing {name} declaration')
        old = m.group(0)
        if '"DIY"' not in old:
            fresh = m.group(1) + m.group(2).rstrip() + ', "DIY"' + m.group(3)
            s = s[:m.start()] + fresh + s[m.end():]
    # In the base firmware the list for subghz is checked only AFTER the NFC etc,
    # but all corresponding filters still work in this order.
    return s


def patch_build(s: str) -> str:
    tag = 'build_diy.sh'
    s = replace_one(s,
        'SDK_OPTS=("-DSDKCONFIG=${BUILD_DIR}/sdkconfig")',
        'SDK_OPTS=("-DSDKCONFIG=${BUILD_DIR}/sdkconfig" "-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.defaults.esp32s3")', tag)
    s = replace_one(s,
        'idf.py -B "${BUILD_DIR}" "${SDK_OPTS[@]}" set-target "${IDF_TARGET}"',
        'idf.py -B "${BUILD_DIR}" -DFLIPPER_BOARD="${BOARD}" "${SDK_OPTS[@]}" set-target "${IDF_TARGET}"', tag)
    return s


def write_with_backup(root: Path, rel: str, data: str) -> None:
    dest = root / rel
    if not dest.exists():
        raise FileNotFoundError(f'Cannot find expected upstream file: {dest}')
    old = dest.read_text(encoding='utf-8')
    if data == old:
        print('unchanged:', rel)
        return
    backup = root / '.flipper-diy240-backups' / rel
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest, backup)
    dest.write_text(data, encoding='utf-8')
    print('patched:', rel)


def main():
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 patch_flipper.py /path/to/Flipper-Zero-ESP32-Port')
    root = Path(sys.argv[1]).expanduser().resolve()
    if not (root / 'tools/gen_diy_board.py').is_file():
        sys.exit('ERROR: provide root directory of Sor3nt source clone')
    if not PROFILE.is_file():
        sys.exit('ERROR: Pinout_ESP32S3_ST7789_240.txt missing next to script')
    result = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True, capture_output=True)
    if result.returncode == 0 and result.stdout.strip() != EXPECTED:
        sys.exit(f'ERROR: clone is {result.stdout.strip()}. Expected {EXPECTED}.\n'
                 'Run `git checkout ' + EXPECTED + '` before applying this patch.')
    updates = {
        'tools/gen_diy_board.py': patch_generator,
        'components/furi_hal/furi_hal_display.c': patch_display,
        'fam_config.py': patch_fam,
        'build_diy.sh': patch_build,
    }
    # Prepare all updates before altering anything.
    prepared = {}
    for rel, patcher in updates.items():
        content = (root / rel).read_text(encoding='utf-8')
        prepared[rel] = patcher(content)
    new_pinout = PROFILE.read_text(encoding='utf-8')
    for rel, data in prepared.items():
        write_with_backup(root, rel, data)
    write_with_backup(root, 'Pinout.txt', new_pinout)
    print('Running upstream DIY board generator...')
    subprocess.run([sys.executable, str(root/'tools/gen_diy_board.py'), str(root/'Pinout.txt')],
                   cwd=root, check=True)
    header_path = root/'components/furi_hal/boards/board_DIY.h'
    hdr = header_path.read_text(encoding='utf-8')
    ota_profile = '#define BOARD_OTA_PROFILE_ST7789 1'
    if ota_profile not in hdr:
        anchor = '#define BOARD_LCD_H_RES 240'
        if hdr.count(anchor) != 1:
            sys.exit('ERROR: could not select the ST7789 OTA profile in board_DIY.h')
        hdr = hdr.replace(anchor, ota_profile + '\n' + anchor, 1)
        header_path.write_text(hdr, encoding='utf-8')
    expected = {
        '#define BOARD_LCD_H_RES 240', '#define BOARD_LCD_V_RES 240',
        '#define BOARD_OTA_PROFILE_ST7789 1',
        '#define BOARD_PIN_LCD_CS   UINT16_MAX',
        '#define BOARD_SD_BUS_NOT_SHARED 1', '#define BOARD_SD_SPI_HOST SPI3_HOST',
        '#define BOARD_PIN_SD_MISO2 38', '#define BOARD_PIN_SD_MOSI  39',
        '#define BOARD_PIN_SD_SCK   40', '#define BOARD_PIN_SD_CS    14',
        '#define BOARD_PIN_BTN_OK     8',
        '#define BOARD_HAS_NFC 0', '#define BOARD_HAS_SUBGHZ 0',
    }
    missing = [s for s in sorted(expected) if s not in hdr]
    if missing:
        sys.exit('ERROR: generated board header mismatch: ' + repr(missing))
    print('PASSED: generated header has ST7789 OTA identity, no-CS 240x240 LCD + independent SPI3 microSD.')
    print('Next: ./build_diy.sh --clean --build-only (requires ESP-IDF 5.4.1)')


if __name__ == '__main__':
    main()
