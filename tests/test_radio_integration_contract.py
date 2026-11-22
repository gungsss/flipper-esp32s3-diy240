#!/usr/bin/env python3
"""Guard M4145 Red Team radio wiring and feature claims at source level."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "patch/Pinout_ESP32S3_ST7735S_160.txt"
PATCH = ROOT / "variants/st7735/patch_module_detection.py"
BOARD = ROOT / "variants/st7735/patch_st7735.py"

class RadioIntegrationContract(unittest.TestCase):
    def test_cc1101_nrf24_independent_spi(self):
        profile = PROFILE.read_text()
        for assignment in (
            "CC1101_CS=43", "CC1101_SCK=9", "CC1101_MOSI=10",
            "CC1101_MISO=21", "CC1101_GDO0=13", "NRF24_SCK=41",
            "NRF24_MOSI=42", "NRF24_MISO=47", "NRF24_CS=1",
            "NRF24_CE=2",
        ):
            self.assertIn(assignment + "\n", profile)
        self.assertIn("BOARD_NRF24_SPI_SEPARATE", BOARD.read_text())

    def test_no_conflicting_accessory_wiring_hints(self):
        patch = PATCH.read_text()
        self.assertNotIn("SDA GPIO41, SCL GPIO42", patch)
        self.assertNotIn("TX GPIO1\\nand a 38kHz receiver on RX GPIO2", patch)
        self.assertIn("GPIO41/42 belong to nRF24 SPI", patch)
        self.assertIn("GPIO1/2 belong to nRF24", patch)

    def test_radio_diagnostics_are_hardware_backed(self):
        patch = PATCH.read_text()
        self.assertIn("furi_hal_subghz_refresh_connection()", patch)
        self.assertIn("nrf24_hw_probe()", patch)
        self.assertIn("nrf24_hw_acquire()", patch)
        self.assertIn("nrf24_hw_release()", patch)

    def test_disabled_actions_are_not_claimed_operational(self):
        patch = PATCH.read_text()
        self.assertIn("Jammer unavailable", patch)
        self.assertIn("MouseJacker unavailable", patch)

if __name__ == "__main__":
    unittest.main()
