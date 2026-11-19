#!/usr/bin/env python3
"""Ensure the source provenance check rejects altered or unsafe records."""
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

project = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('official151', project / 'scripts/check_official151_core.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
source = Path(sys.argv[1]).resolve()
original = json.loads((project / 'tests/basic151/official151_core_manifest.json').read_text())


def must_reject(data):
    with tempfile.TemporaryDirectory(prefix='esp-provenance-') as directory:
        path = Path(directory) / 'manifest.json'
        path.write_text(json.dumps(data))
        try:
            check.verify_manifest(source, path)
        except (ValueError, OSError):
            return
        raise AssertionError('Invalid provenance manifest was accepted')


wrong_commit = copy.deepcopy(original)
wrong_commit['official_commit'] = '0' * 40
must_reject(wrong_commit)
wrong_hash = copy.deepcopy(original)
wrong_hash['files'][0]['blob'] = '0' * 40
must_reject(wrong_hash)
wrong_path = copy.deepcopy(original)
wrong_path['files'][0]['source'] = '../../outside.c'
must_reject(wrong_path)
duplicate = copy.deepcopy(original)
duplicate['files'].append(copy.deepcopy(duplicate['files'][0]))
must_reject(duplicate)
print('Provenance check rejects altered commits, hashes, paths, and duplicate records.')
