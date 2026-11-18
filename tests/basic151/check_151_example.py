#!/usr/bin/env python3
"""Verify and register the upstream 1.5.1 date/time input example on ESP."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
expected = json.loads((Path(__file__).parent / 'official151_date_example_sha256.json').read_text())
for name, digest in expected.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name

with tempfile.TemporaryDirectory(prefix='esp151-example-') as directory:
    directory = Path(directory)
    registry = directory / 'registry.c'
    cmake = directory / 'ported.cmake'
    env = dict(os.environ, FLIPPER_BOARD='DIY')
    subprocess.run([sys.executable, str(root / 'tools/fam/generate.py'),
                    '--project-dir', str(root), '--config', str(root / 'fam_config.py'),
                    '--registry-out', str(registry), '--cmake-out', str(cmake)],
                   env=env, cwd=root, check=True)
    entries = registry.read_text()
    sources = cmake.read_text()
    assert '.appid = "example_date_time_input"' in entries
    assert 'esp32_fam_app_example_date_time_input' in sources
    for name in expected:
        if name.endswith('.c'):
            assert str(root / name) in sources, name
    assert 'esp32_fam_app_nfc OBJECT' not in sources
print('Original 1.5.1 date/time example is intact and registered for the DIY board.')
