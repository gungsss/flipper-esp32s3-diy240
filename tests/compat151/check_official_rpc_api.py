#!/usr/bin/env python3
"""Check exported RPC functions against the pinned 1.5.1 SDK declarations."""

import csv
import io
import re
import subprocess
import sys
import tempfile
from pathlib import Path

official, port = map(Path, sys.argv[1:3])
version = subprocess.check_output(
    ['git', '-C', str(official), 'rev-parse', '1.5.1^{commit}'], text=True).strip()
assert version == '9e810dc399e027e48ce07751df72168abbb19065', 'unexpected official source'
raw = subprocess.check_output(
    ['git', '-C', str(official), 'show', '1.5.1:targets/f7/api_symbols.csv'], text=True)
rows = [r for r in csv.DictReader(io.StringIO(raw))
        if r['entry'] == 'Function' and r['status'] == '+' and
        r['name'].startswith(('rpc_session_', 'rpc_system_app_'))]
assert len(rows) == 18, 'unexpected official RPC function set'
root = port / 'components/flipper_application/flipper_application'
table = (root / 'firmware_api.c').read_text()
names = re.findall(r'\.hash = 0x[0-9a-fA-F]+,\s*\.address = \(uint32_t\).*?/\* (.*?) \*/', table)
checks = (root / 'official_rpc_151_abi_checks.h').read_text()
for row in rows:
    name = row['name']
    expected = (f'_Static_assert(__builtin_types_compatible_p(__typeof__(&{name}), '
                f'{row["type"]} (*)({row["params"] or "void"})), '
                f'"official 1.5.1 signature: {name}");')
    assert checks.count(expected) == 1, f'{name}: signature guard missing'
    assert names.count(name) == 1, f'{name}: export missing or duplicated'
assert checks.count('_Static_assert(') == len(rows)
assert '#include "official_rpc_151_abi_checks.h"' in table

with tempfile.TemporaryDirectory(prefix='rpc-api-') as directory:
    tmp = Path(directory)
    (tmp / 'furi.h').write_text(
        '#pragma once\n#include <stdbool.h>\n#include <stdint.h>\n#include <stddef.h>\n')
    source = tmp / 'rpc_types.c'
    source.write_text('#include <rpc/rpc.h>\n#include <rpc/rpc_app.h>\n'
                      '#include "official_rpc_151_abi_checks.h"\n')
    subprocess.run([
        'gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-fsyntax-only',
        '-I', str(tmp), '-I', str(port / 'components'), '-I', str(root), str(source),
    ], check=True)

print('All 18 official RPC function names and C signatures match on host.')
print('Device RPC behavior and Xtensa ABI still require separate verification.')
