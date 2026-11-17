#!/usr/bin/env python3
"""Check added storage/locale functions against the 1.5.1 SDK declarations."""
import csv
import io
import re
import subprocess
import sys
import tempfile
from pathlib import Path

official, port = map(Path, sys.argv[1:3])
sha = subprocess.check_output(
    ['git', '-C', str(official), 'rev-parse', '1.5.1^{commit}'], text=True).strip()
assert sha == '9e810dc399e027e48ce07751df72168abbb19065', 'unexpected official commit'
raw = subprocess.check_output(
    ['git', '-C', str(official), 'show', '1.5.1:targets/f7/api_symbols.csv'], text=True)
official_api = {r['name']: r for r in csv.DictReader(io.StringIO(raw))
                if r['entry'] == 'Function' and r['status'] == '+'}
root = port / 'components/flipper_application/flipper_application'
table = (root / 'firmware_api.c').read_text()
header = (root / 'official_storage_151_abi_checks.h').read_text()
names = re.findall(r'official 1\.5\.1 signature: ((?:storage|locale|datetime)_\w+)', header)
expected_names = {name for name in official_api if name.startswith(('storage_', 'locale_', 'datetime_'))}
assert set(names) == expected_names and len(set(names)) == len(names), 'incomplete or duplicate function set'
table_names = re.findall(r'\.hash = 0x[0-9a-fA-F]+,\s*\.address = \(uint32_t\).*?/\* (.*?) \*/', table)
for name in names:
    row = official_api[name]
    expected = (f'_Static_assert(__builtin_types_compatible_p(__typeof__(&{name}), '
                f'{row["type"]} (*)({row["params"] or "void"})), '
                f'"official 1.5.1 signature: {name}");')
    assert header.count(expected) == 1, f'{name}: type guard differs from official SDK'
    assert table_names.count(name) == 1, f'{name}: missing or duplicate symbol table entry'
assert '#include "official_storage_151_abi_checks.h"' in table, 'type guards not compiled'

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp / 'freertos').mkdir()
    (tmp / 'freertos/FreeRTOS.h').write_text(
        '#pragma once\ntypedef int BaseType_t;\n#define portNUM_PROCESSORS 2\n')
    (tmp / 'freertos/task.h').write_text('#pragma once\n')
    (tmp / 'furi_hal.h').write_text('#pragma once\n#include <furi_hal_rtc.h>\n')
    source = tmp / 'storage_types.c'
    source.write_text('#include <stdint.h>\n#define _ATTRIBUTE(x) __attribute__(x)\n'
                      '#include <furi.h>\n#include <furi_hal_rtc.h>\n'
                      '#include <storage/storage.h>\n#include <locale/locale.h>\n'
                      '#include <datetime.h>\n#include "official_storage_151_abi_checks.h"\n')
    include_dirs = (tmp, port / 'components', port / 'components/furi_hal',
                    port / 'components/furi', port / 'components/furi/core',
                    port / 'components/mlib', port / 'components/datetime', root)
    flags = [arg for folder in include_dirs for arg in ('-I', str(folder))]
    subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                    '-fsyntax-only', *flags, str(source)], check=True)
print(f'{len(names)} storage/locale exports match the official 1.5.1 SDK C signatures on host.')
print('SD, internal storage, and application behavior have not been validated on the device.')
