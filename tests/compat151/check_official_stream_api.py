#!/usr/bin/env python3
"""Check stream SDK exports against the official Flipper 1.5.1 types."""
import csv
import io
import re
import subprocess
import sys
import tempfile
from pathlib import Path

official, port = map(Path, sys.argv[1:3])
assert subprocess.check_output(
    ['git', '-C', str(official), 'rev-parse', '1.5.1^{commit}'], text=True
).strip() == '9e810dc399e027e48ce07751df72168abbb19065'
raw = subprocess.check_output(
    ['git', '-C', str(official), 'show', '1.5.1:targets/f7/api_symbols.csv'], text=True)
prefixes = ('stream_', 'string_stream_', 'file_stream_', 'buffered_file_stream_')
rows = [r for r in csv.DictReader(io.StringIO(raw)) if r['entry'] == 'Function'
        and r['status'] == '+' and r['name'].startswith(prefixes)]
root = port / 'components/flipper_application/flipper_application'
table = (root / 'firmware_api.c').read_text()
header = (root / 'official_stream_151_abi_checks.h').read_text()
names = re.findall(r'\.hash = 0x[0-9a-fA-F]+,\s*\.address = \(uint32_t\).*?/\* (.*?) \*/', table)
for row in rows:
    name, result, params = row['name'], row['type'], row['params'] or 'void'
    check = (f'_Static_assert(__builtin_types_compatible_p(__typeof__(&{name}), '
             f'{result} (*)({params})), "official 1.5.1 signature: {name}");')
    assert names.count(name) == 1, f'{name}: missing or duplicate SDK export'
    assert header.count(check) == 1, f'{name}: signature differs from official SDK'
assert header.count('_Static_assert(') == len(rows)
assert '#include "official_stream_151_abi_checks.h"' in table

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp / 'freertos').mkdir()
    (tmp / 'freertos/FreeRTOS.h').write_text(
        '#pragma once\ntypedef int BaseType_t;\n#define portNUM_PROCESSORS 2\n')
    (tmp / 'freertos/task.h').write_text('#pragma once\n')
    source = tmp / 'stream_types.c'
    source.write_text('#include <stdint.h>\n#define _ATTRIBUTE(x) __attribute__(x)\n'
                      '#include <furi.h>\n#include <toolbox/stream/stream.h>\n'
                      '#include <toolbox/stream/file_stream.h>\n'
                      '#include <toolbox/stream/buffered_file_stream.h>\n'
                      '#include <toolbox/stream/string_stream.h>\n'
                      '#include "official_stream_151_abi_checks.h"\n')
    include_dirs = (tmp, port / 'components', port / 'components/furi_hal',
                    port / 'components/furi', port / 'components/furi/core',
                    port / 'components/mlib', port / 'components/datetime', root)
    flags = [arg for folder in include_dirs for arg in ('-I', str(folder))]
    subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                    '-fsyntax-only', *flags, str(source)], check=True)

print(f'{len(rows)} stream SDK C signatures match the official 1.5.1 list.')
print('SD behavior and the target ABI still require physical validation.')
