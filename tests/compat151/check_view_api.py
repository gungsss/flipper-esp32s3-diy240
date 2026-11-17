#!/usr/bin/env python3
"""Run the public view-ID contract against the actual ported function body."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1], 'components/gui/view_dispatcher.c').read_text()
matches = re.findall(r'bool view_dispatcher_check_id\([^\n]*\) \{\n.*?\n\}', source, re.S)
assert len(matches) == 1, 'expected one view_dispatcher_check_id implementation'
harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
typedef struct { uint32_t id; int value; } ViewMap;
typedef struct { ViewMap* views; } ViewDispatcher;
#define furi_check(x) assert(x)
static int* ViewDict_get(ViewMap* map, uint32_t id) {
    return map->id == id ? &map->value : NULL;
}
''' + matches[0] + r'''
int main(void) {
    ViewMap map = {.id = 42, .value = 7};
    ViewDispatcher dispatcher = {.views = &map};
    assert(view_dispatcher_check_id(&dispatcher, 42));
    assert(!view_dispatcher_check_id(&dispatcher, 43));
    return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp, 'test.c')
    path.write_text(harness)
    exe = Path(tmp, 'test')
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Werror', str(path), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('View-ID lookup passed for both present and absent IDs.')
