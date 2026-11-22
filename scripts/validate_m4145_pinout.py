#!/usr/bin/env python3
"""Validate actual M4145 ESP32-S3 ST7735S hardware pin assignments before build."""
import argparse
from pathlib import Path

REQUIRED = ("SPI_SCK", "SPI_MOSI", "LCD_DC", "LCD_RST", "SD_SCK", "SD_MOSI", "SD_MISO", "SD_CS",
            "CC1101_SCK", "CC1101_MOSI", "CC1101_MISO", "CC1101_CS", "CC1101_GDO0",
            "NRF24_SCK", "NRF24_MOSI", "NRF24_MISO", "NRF24_CS", "NRF24_CE",
            "BTN_UP", "BTN_DOWN", "BTN_LEFT", "BTN_RIGHT", "BTN_OK", "BTN_BACK")
RESERVED = {0, 3, 19, 20, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 45, 46}
# LCD SPI_MISO is an optional input and may share the CC1101 GDO0 pad
ALLOWED_ALIAS = {frozenset(("SPI_MISO", "CC1101_GDO0"))}

def validate(path):
    pins = {}
    errors = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" not in line:
            errors.append(f"line {number}: expected NAME=GPIO")
            continue
        key, value = map(str.strip, line.split("=", 1))
        if key in pins:
            errors.append(f"line {number}: duplicate {key}")
            continue
        try:
            pins[key] = int(value)
        except ValueError:
            errors.append(f"line {number}: invalid GPIO {value!r}")
    for key in REQUIRED:
        if pins.get(key, -1) == -1:
            errors.append(f"required pin missing or disabled: {key}")
    used = {}
    for key, gpio in pins.items():
        if gpio == -1:
            continue
        if gpio < 0 or gpio > 48:
            errors.append(f"{key}: GPIO{gpio} out of range")
        if gpio in RESERVED:
            errors.append(f"{key}: GPIO{gpio} reserved/strap/USB/flash")
        used.setdefault(gpio, []).append(key)
    for gpio, names in used.items():
        if len(names) > 1 and frozenset(names) not in ALLOWED_ALIAS:
            errors.append(f"GPIO{gpio} assigned to {', '.join(names)}")
    if pins.get("LCD_CS") != -1:
        errors.append("ST7735S profile requires LCD_CS=-1 (CS physically tied to GND)")
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pinout", type=Path)
    args = parser.parse_args()
    errors = validate(args.pinout)
    if errors:
        for error in errors:
            print("ERROR:", error)
        raise SystemExit(1)
    print("M4145 hardware pinout validation: PASS")

if __name__ == "__main__":
    main()
