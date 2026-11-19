#!/usr/bin/env python3
"""Verify web publication rejects mislabeled or corrupt firmware bundles."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('publish151', root / 'web/tools/prepare_st7735_151.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def rejected(source, message):
    try:
        module.validate(source)
    except ValueError:
        return
    raise AssertionError(message)


with tempfile.TemporaryDirectory(prefix='esp151-publish-') as directory:
    directory = Path(directory)
    prior = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if prior is not None:
        extracted = directory / 'preview'
        with zipfile.ZipFile(prior) as bundle:
            bundle.extractall(extracted)
        rejected(extracted, '1.4.3-based preview was accepted as 1.5.1')

    candidate = directory / 'candidate'
    candidate.mkdir()
    rows = []
    for name, offset in module.IMAGES.items():
        data = bytearray(32)
        if name in ('bootloader/bootloader.bin', 'furi_esp32.bin'):
            data[0], data[12] = 0xE9, 9
        file = candidate / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        rows.append({'file': name, 'offset': hex(offset), 'size_bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})
    metadata = {
        'board': 'DIY ESP32-S3 N16R8', 'lcd': 'ST7735S landscape 160x128',
        'flipper_source_commit': module.FLIPPER_151_COMMIT,
        'flipper_source_version': '1.5.1', 'flipper_151_core_ported': True,
        'reported_flipper_version': '1.5.1-esp', 'images': rows,
    }
    manifest = candidate / 'BUILD_INFO.json'
    manifest.write_text(json.dumps(metadata))
    assert module.validate(candidate)['flipper_source_version'] == '1.5.1'

    metadata['reported_flipper_version'] = '1.4.3'
    manifest.write_text(json.dumps(metadata))
    rejected(candidate, 'wrong reported version was accepted')
    metadata['reported_flipper_version'] = '1.5.1-esp'
    metadata['flipper_151_core_ported'] = False
    manifest.write_text(json.dumps(metadata))
    rejected(candidate, 'incomplete core was accepted')
    metadata['flipper_151_core_ported'] = True
    manifest.write_text(json.dumps(metadata))
    (candidate / 'furi_esp32.bin').write_bytes(b'corrupt')
    rejected(candidate, 'corrupted binary was accepted')
print('Web release guard rejects partial, mislabeled, and corrupt firmware.')
