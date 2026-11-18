#!/usr/bin/env python3
"""Test official and indexed ESP browser callbacks without SD hardware."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
directory = root / 'components/gui/modules'
header = (directory / 'file_browser_worker.h').read_text()
source = (directory / 'file_browser_worker.c').read_text()

def callback_type(name):
    match = re.search(r'typedef void \(\*' + name + r'\)\([^;]+;', header, re.S)
    assert match, name
    return match.group(0)

def function(name, static=False):
    prefix = 'static ' if static else ''
    match = re.search(r'(?m)^' + prefix + r'void ' + name + r'\([^)]*\) \{', source)
    assert match, name
    index, depth = match.end(), 1
    while depth:
        if source[index] == '{':
            depth += 1
        elif source[index] == '}':
            depth -= 1
        index += 1
    return source[match.start():index]

for path in (
    directory / 'file_browser.c',
    root / 'components/archive/archive/helpers/archive_browser.c',
    root / 'applications/main/archive/helpers/archive_browser.c',
):
    assert 'file_browser_worker_set_indexed_item_callback(' in path.read_text(), path

prelude = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#define furi_check(x) assert(x)
typedef struct FuriString { int unused; } FuriString;
typedef struct BrowserWorker BrowserWorker;
'''
typedefs = '\n'.join(callback_type(name) for name in (
    'BrowserWorkerListItemCallback', 'BrowserWorkerIndexedListItemCallback'))
worker = r'''
_Static_assert(__builtin_types_compatible_p(
    BrowserWorkerListItemCallback, void (*)(void*, FuriString*, bool, bool)), "official ABI");
_Static_assert(__builtin_types_compatible_p(
    BrowserWorkerIndexedListItemCallback, void (*)(void*, FuriString*, uint32_t, bool, bool)), "ESP ABI");
struct BrowserWorker {
    void* cb_ctx;
    BrowserWorkerListItemCallback list_item_cb;
    BrowserWorkerIndexedListItemCallback list_item_indexed_cb;
};
'''
functions = '\n'.join((
    function('browser_worker_emit_item', static=True),
    function('file_browser_worker_set_item_callback'),
    function('file_browser_worker_set_indexed_item_callback'),
))
tests = r'''
typedef struct { int normal, indexed; uint32_t index; bool folder, last; FuriString* path; } State;
static void ordinary(void* ctx, FuriString* path, bool folder, bool last) {
    State* s = ctx; ++s->normal; s->path = path; s->folder = folder; s->last = last;
}
static void indexed(void* ctx, FuriString* path, uint32_t index, bool folder, bool last) {
    State* s = ctx; ++s->indexed; s->path = path; s->index = index; s->folder = folder; s->last = last;
}
int main(void) {
    State state = {0}; FuriString name = {0}; BrowserWorker browser = {.cb_ctx = &state};
    browser_worker_emit_item(&browser, &name, 5, true, false);
    assert(state.normal == 0 && state.indexed == 0);
    file_browser_worker_set_item_callback(&browser, ordinary);
    browser_worker_emit_item(&browser, &name, 5, true, false);
    assert(state.normal == 1 && state.indexed == 0 && state.path == &name && state.folder && !state.last);
    file_browser_worker_set_indexed_item_callback(&browser, indexed);
    browser_worker_emit_item(&browser, &name, 17, false, false);
    assert(state.normal == 1 && state.indexed == 1 && state.index == 17 && !state.folder);
    browser_worker_emit_item(&browser, NULL, 0, false, true);
    assert(state.indexed == 2 && state.path == NULL && state.last);
    file_browser_worker_set_item_callback(&browser, ordinary);
    browser_worker_emit_item(&browser, NULL, 0, false, true);
    assert(state.normal == 2 && state.indexed == 2 && state.path == NULL && state.last);
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='esp-browser-callback-') as temp:
    temp = Path(temp)
    (temp / 'test.c').write_text(prelude + typedefs + worker + functions + tests)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    str(temp / 'test.c'), '-o', str(temp / 'test')], check=True)
    subprocess.run([str(temp / 'test')], check=True)
print('File browser supports the official callback and ESP indexed callback.')
