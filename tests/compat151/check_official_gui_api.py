#!/usr/bin/env python3
"""Check 1.5.1 GUI SDK exports and compile-time C signature guards."""
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
assert version == '9e810dc399e027e48ce07751df72168abbb19065', 'unexpected official commit'
csv_data = subprocess.check_output(
    ['git', '-C', str(official), 'show', '1.5.1:targets/f7/api_symbols.csv'], text=True)
prefixes = ('canvas_', 'gui_', 'view_', 'widget_', 'scene_manager_', 'date_time_input_')
rows = [r for r in csv.DictReader(io.StringIO(csv_data))
        if r['entry'] == 'Function' and r['status'] == '+' and r['name'].startswith(prefixes)]
table = (port / 'components/flipper_application/flipper_application/firmware_api.c').read_text()
names = re.findall(r'\.hash = 0x[0-9a-fA-F]+,\s*\.address = \(uint32_t\).*?/\* (.*?) \*/', table)
header = (port / 'components/flipper_application/flipper_application/official_gui_151_abi_checks.h').read_text()
for row in rows:
    name, result, params = row['name'], row['type'], row['params'] or 'void'
    assert names.count(name) == 1, f'{name} not exported exactly once'
    check = f'_Static_assert(__builtin_types_compatible_p(__typeof__(&{name}), {result} (*)({params})), "official 1.5.1 signature: {name}");'
    assert header.count(check) == 1, f'{name} lacks the exact official type assertion'
assert header.count('_Static_assert(') == len(rows), 'unexpected signature checks'
assert '#include "official_gui_151_abi_checks.h"' in table, 'signature checks not compiled'
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp / 'core').mkdir()
    # Only these platform definitions are needed to parse the real GUI headers.
    (tmp / 'core/common_defines.h').write_text('#pragma once\n#define FURI_DEPRECATED\n')
    (tmp / 'input.h').write_text(
        '#pragma once\n#include <stdbool.h>\n'
        'typedef struct InputEvent InputEvent;\n'
        'typedef enum { InputTypeShort } InputType;\n')
    source = tmp / 'gui_types.c'
    source.write_text('''#include <stdbool.h>
#include <gui/gui.h>
#include <gui/view.h>
#include <gui/view_dispatcher.h>
#include <gui/view_holder.h>
#include <gui/view_stack.h>
#include <gui/scene_manager.h>
#include <gui/modules/widget.h>
#include <gui/modules/date_time_input.h>
#include "official_gui_151_abi_checks.h"
''')
    subprocess.run([
        'gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-fsyntax-only',
        '-I', str(tmp), '-I', str(port / 'components'), '-I', str(port / 'components/datetime'),
        '-I', str(port / 'components/flipper_application/flipper_application'), str(source),
    ], check=True)
print(f'All {len(rows)} official GUI function names exported with release-signature checks.')
print('Host C type checks passed; Xtensa versus ARM ABI and runtime behavior remain unverified.')
