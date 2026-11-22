#!/usr/bin/env python3
"""Tests for the physical-radio diagnostic log exporter."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("radio_probe_report", ROOT / "tools/radio_probe_report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

class RadioProbeReportTest(unittest.TestCase):
    def test_parse_realistic_esp_idf_logs(self):
        lines = [
            "I (1234) m4145: nRF24 initial SPI probe: detected\n",
            "I (1300) m4145: nRF24 manual SPI probe: missing\n",
            "[05:12:13.012] CC1101 detected\n",
            "I (1400) unrelated status\n",
        ]
        rows = list(report.parse(lines))
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["module"] for r in rows], ["nRF24L01+", "nRF24L01+", "CC1101"])
        self.assertEqual([r["state"] for r in rows], ["detected", "missing", "detected"])
        self.assertEqual(rows[0]["timestamp"], "1234")
        self.assertEqual(rows[2]["timestamp"], "05:12:13.012")
        self.assertEqual(rows[1]["line"], 2)

    def test_empty_input_never_fabricates_radio_data(self):
        self.assertEqual(list(report.parse(["no hardware probes here\n"])), [])

    def test_csv_export_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "serial.log"
            csv_file = Path(directory) / "report.csv"
            log.write_text("I (55) m4145: nRF24 manual SPI probe: detected\n")
            report.main([str(log), "-o", str(csv_file)])
            with csv_file.open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["module"], "nRF24L01+")
            self.assertEqual(rows[0]["phase"], "manual")

if __name__ == "__main__":
    unittest.main()
