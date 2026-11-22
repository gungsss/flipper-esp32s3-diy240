#!/usr/bin/env python3
"""Regression tests for the exact M4145 ESP32-S3 N16R8 pinout."""
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_m4145_pinout import validate

PINOUT = ROOT / "patch/Pinout_ESP32S3_ST7735S_160.txt"

class TestM4145Pinout(unittest.TestCase):
    def test_actual_hardware_profile(self):
        self.assertEqual(validate(PINOUT), [])

    def mutate(self, old, new):
        original = PINOUT.read_text(encoding="utf-8")
        self.assertIn(old, original)
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "pinout.txt"
            file.write_text(original.replace(old, new), encoding="utf-8")
            return validate(file)

    def test_cc1101_cs_must_not_use_strapping_gpio46(self):
        errors = self.mutate("CC1101_CS=43", "CC1101_CS=46")
        self.assertTrue(any("GPIO46" in error for error in errors), errors)

    def test_nrf24_chip_select_conflict_detected(self):
        errors = self.mutate("NRF24_CS=1", "NRF24_CS=43")
        self.assertTrue(any("GPIO43 assigned" in error for error in errors), errors)

    def test_spi_miso_and_cc1101_gdo0_alias_is_documented(self):
        self.assertEqual(validate(PINOUT), [])

    def test_required_nrf_ce_cannot_be_disabled(self):
        errors = self.mutate("NRF24_CE=2", "NRF24_CE=-1")
        self.assertTrue(any("NRF24_CE" in error for error in errors), errors)

    def test_lcd_cs_tied_low(self):
        errors = self.mutate("LCD_CS=-1", "LCD_CS=22")
        self.assertTrue(any("LCD_CS=-1" in error for error in errors), errors)

if __name__ == "__main__":
    unittest.main()
