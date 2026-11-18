#!/usr/bin/env python3
"""Exercise the real ESP API resolver with the updated 1.5.1 SDK entries."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
api = root / 'components/flipper_application/flipper_application/firmware_api.c'
text = api.read_text()
start = text.index('static const struct sym_entry firmware_api_table[] = {')
end = text.index('\n};', start)
entries = re.findall(
    r'\.hash = 0x([0-9a-fA-F]+),\s*\.address = \(uint32_t\).*?/\* ([a-zA-Z0-9_]+) \*/',
    text[start:end],
)
assert entries, 'empty resolver table'
hashes = [int(value, 16) for value, _ in entries]
assert hashes == sorted(hashes), 'resolver table must be sorted'
assert len(hashes) == len(set(hashes)), 'hash collision'

def elf_hash(name):
    value = 0x1505
    for byte in name.encode():
        value = (value * 33 + byte) & 0xffffffff
    return value

table = {name: int(value, 16) for value, name in entries}
expected = json.loads((Path(__file__).parent / 'expected_core_api.json').read_text())
for row in expected:
    name = row['name']
    assert name in table and table[name] == elf_hash(name), name
    params = row['params'] or 'void'
    signature = (
        f'_Static_assert(__builtin_types_compatible_p(__typeof__(&{name}), '
        f'{row["type"]} (*)({params})), "1.5.1 SDK signature: {name}");'
    )
    assert signature in text, f'missing target ABI assertion for {name}'

with tempfile.TemporaryDirectory(prefix='esp-api-resolver-') as temp:
    temp = Path(temp)
    (temp / 'furi.h').write_text(
        '#pragma once\n#include <assert.h>\n#include <stddef.h>\n'
        '#define furi_check(x) assert(x)\n'
        '#define FURI_LOG_I(...) ((void)0)\n'
        '#define FURI_LOG_E(...) ((void)0)\n'
        '#define FURI_LOG_W(...) ((void)0)\n'
    )
    values = ',\n'.join(f'    {{{h}u, {index + 1}u}}' for index, h in enumerate(hashes))
    expected_names = ',\n'.join(
        f'    {{"{row["name"]}", {elf_hash(row["name"])}u}}' for row in expected
    )
    harness = r'''
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <flipper_application/api_hashtable/api_hashtable.h>
static const struct sym_entry entries[] = {
VALUES
};
struct NameHash { const char* name; uint32_t hash; };
static const struct NameHash names[] = {
NAMES
};
int main(void) {
    const size_t count = sizeof(entries) / sizeof(entries[0]);
    HashtableApiInterface api = {.table_begin = entries, .table_end = entries + count};
    for(size_t i = 0; i < count; ++i) {
        Elf32_Addr address = 0;
        assert(elf_resolve_from_hashtable(&api.base, entries[i].hash, &address));
        assert(address == i + 1);
    }
    for(size_t i = 0; i < sizeof(names) / sizeof(names[0]); ++i) {
        Elf32_Addr address = 0;
        assert(elf_symbolname_hash(names[i].name) == names[i].hash);
        assert(elf_resolve_from_hashtable(&api.base, names[i].hash, &address));
    }
    Elf32_Addr address = 0;
    assert(!elf_resolve_from_hashtable(&api.base, 0, &address));
    return 0;
}
'''.replace('VALUES', values).replace('NAMES', expected_names)
    (temp / 'test.c').write_text(harness)
    subprocess.run([
        'gcc', '-std=c11', '-Wall', '-Wextra', '-Wno-unused-variable',
        '-I', str(temp), '-I', str(root / 'components/flipper_application'),
        str(temp / 'test.c'),
        str(root / 'components/flipper_application/flipper_application/api_hashtable/api_hashtable.c'),
        '-o', str(temp / 'test'),
    ], check=True)
    subprocess.run([str(temp / 'test')], check=True)
print(f'Resolver passed: {len(entries)} entries; {len(expected)} SDK functions have ABI checks.')
