#!/usr/bin/env python3
"""Check all newly exported 1.5.1 API names against the ESP32 symbol table.

Name coverage alone does not establish type, architecture, or ABI parity.
"""
import csv
import io
import re
import subprocess
import sys
from pathlib import Path

official, port = map(Path, sys.argv[1:3])
expected = {
    '1.4.3': '8622f1a2b83d8f4918dd5fa3f43de963f6d6f819',
    '1.5.1': '9e810dc399e027e48ce07751df72168abbb19065',
}

def exports(tag):
    git = ['git', '-C', str(official)]
    sha = subprocess.check_output([*git, 'rev-parse', tag + '^{commit}'], text=True).strip()
    if sha != expected[tag]:
        raise AssertionError(f'unexpected {tag} commit: {sha}')
    content = subprocess.check_output(
        [*git, 'show', f'{tag}:targets/f7/api_symbols.csv'], text=True)
    return {
        (row['entry'], row['name'])
        for row in csv.DictReader(io.StringIO(content))
        if row['entry'] in ('Function', 'Variable') and row['status'] == '+'
    }

new_exports = exports('1.5.1') - exports('1.4.3')
source = (port / 'components/flipper_application/flipper_application/firmware_api.c').read_text()
port_exports = set(re.findall(r'\.hash = 0x[0-9a-fA-F]+,\s*\.address = \(uint32_t\).*?/\* (.*?) \*/', source))
missing = sorted(name for _, name in new_exports if name not in port_exports)
if missing:
    raise AssertionError('missing 1.5.1 SDK delta exports: ' + ', '.join(missing))
print(f'All {len(new_exports)} newly exported 1.5.1 SDK names exist in the ESP32 table.')
print('This verifies names only; ABI, architecture, and behavior still require separate checks.')
