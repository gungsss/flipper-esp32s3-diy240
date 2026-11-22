#!/usr/bin/env python3
"""Validate configurable ESP32-S3 radio wiring; does not verify physical hardware."""
import configparser
import sys
from pathlib import Path

RESERVED = {0, 3, 19, 20, 45, 46, *range(26, 38)}
OCCUPIED = {4, 5, 6, 7, 8, 11, 12, 14, 15, 16, 17, 18, 38, 39, 40}
SIGNALS = {"cc1101": ("sck", "mosi", "miso", "cs", "gdo0", "gdo2"),
           "nrf24": ("sck", "mosi", "miso", "csn", "ce", "irq")}
OPTIONAL = {("cc1101", "gdo2"), ("nrf24", "irq")}

def validate(path):
    cfg = configparser.ConfigParser()
    if not cfg.read(path):
        raise ValueError("Cannot read pin profile")
    used = {}
    buses = []
    for device, signals in SIGNALS.items():
        if device not in cfg:
            raise ValueError(f"Missing [{device}]")
        for signal in signals:
            try:
                pin = cfg.getint(device, signal)
            except (ValueError, configparser.Error) as e:
                raise ValueError(f"Invalid {device}.{signal}") from e
            if pin == -1 and (device, signal) in OPTIONAL:
                continue
            if not 0 <= pin <= 48 or pin in RESERVED or pin in OCCUPIED:
                raise ValueError(f"{device}.{signal}: invalid/reserved GPIO {pin}")
            if pin in used and not (signal in ("sck", "mosi", "miso") and used[pin][1] == signal):
                raise ValueError(f"GPIO{pin} collision with {used[pin]}")
            used[pin] = (device, signal)
        buses.append(tuple(cfg.getint(device, signal) for signal in ("sck", "mosi", "miso")))
    overlap = set(buses[0]) & set(buses[1])
    if overlap and buses[0] != buses[1]:
        raise ValueError("SPI buses must share all SCK/MOSI/MISO or none")
    print("PASS: logical pin assignment; physical wiring not verified")

if __name__ == "__main__":
    try:
        validate(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "config/radio_pins.ini")
    except ValueError as e:
        sys.exit(f"FAIL: {e}")
