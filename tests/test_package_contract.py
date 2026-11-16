"""Minimal test for artifact packager: validates offsets, missing files and hashes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'package_artifacts.py'


class PackageContractTest(unittest.TestCase):
    def _fixture(self, td):
        source = Path(td) / 'upstream'
        build = source / 'build_diy'
        for rel in ('bootloader/bootloader.bin', 'partition_table/partition-table.bin', 'furi_esp32.bin'):
            path = build / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('firmware:' + rel).encode())
        (build / 'flash_project_args').write_text(
            '--flash_mode dio --flash_freq 80m --flash_size 16MB '
            '0x0 bootloader/bootloader.bin '
            '0x8000 partition_table/partition-table.bin '
            '0x10000 furi_esp32.bin\n'
        )
        return source, build

    def _run(self, source, dest):
        return subprocess.run(
            [sys.executable, str(SCRIPT), '--source', str(source), '--output', str(dest)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def test_build_bundle_contains_expected_artifacts_and_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            src, _ = self._fixture(td)
            dst = Path(td) / 'out'
            result = self._run(src, dst)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            manifest = json.loads((dst / 'BUILD_INFO.json').read_text())
            self.assertEqual(manifest['board'], 'DIY ESP32-S3 N16R8')
            self.assertEqual(len(manifest['images']), 3)
            for entry in manifest['images']:
                path = dst / entry['file']
                self.assertTrue(path.is_file())
                self.assertEqual(entry['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertTrue((dst / 'flash_macos_linux.sh').is_file())

    def test_rejects_wrong_flash_offset(self):
        with tempfile.TemporaryDirectory() as td:
            src, build = self._fixture(td)
            args = build / 'flash_project_args'
            args.write_text(args.read_text().replace('0x10000 furi_esp32.bin', '0x20000 furi_esp32.bin'))
            result = self._run(src, Path(td) / 'out')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('expected mapping', result.stderr + result.stdout)

    def test_rejects_missing_binary(self):
        with tempfile.TemporaryDirectory() as td:
            src, build = self._fixture(td)
            (build / 'furi_esp32.bin').unlink()
            result = self._run(src, Path(td) / 'out')
            self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
