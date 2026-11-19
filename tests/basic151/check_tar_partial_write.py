#!/usr/bin/env python3
"""Ensure a short SD write fails extraction instead of corrupting a restored file."""
import subprocess
import sys
import tempfile
from pathlib import Path

source = (Path(sys.argv[1]) / 'components/toolbox/tar/tar_archive.c').read_text()
start = source.index('static bool archive_extract_current_file(')
end = source.index('\n/* Archive entries must stay', start)
function = source[start:end]
test = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#define FILE_BLOCK_SIZE 512
#define FILE_OPEN_NTRIES 10
#define FILE_OPEN_RETRY_DELAY 25
#define FURI_LOG_W(...) ((void)0)
#define FSAM_WRITE 0
#define FSOM_CREATE_ALWAYS 0
typedef struct { int unused; } Storage;
typedef struct { int unused; } mtar_t;
typedef struct { int unused; } File;
typedef struct { Storage* storage; mtar_t tar; } TarArchive;
static File output;
static bool open_ok, short_write, read_fail, consumed;
static int freed;
static File* storage_file_alloc(Storage* s) { assert(s); return &output; }
static bool storage_file_open(File* f, const char* p, int a, int b) {
    assert(f == &output && p && a == 0 && b == 0); return open_ok;
}
static void storage_file_close(File* f) { assert(f == &output); }
static void furi_delay_ms(int ms) { assert(ms == FILE_OPEN_RETRY_DELAY); }
static bool storage_file_is_open(File* f) { assert(f == &output); return open_ok; }
static bool mtar_eof_data(mtar_t* t) { assert(t); return consumed; }
static int32_t mtar_read_data(mtar_t* t, void* buf, size_t size) {
    assert(t && buf && size == FILE_BLOCK_SIZE); consumed = true; return read_fail ? -1 : 3;
}
static size_t storage_file_write(File* f, void* p, size_t size) {
    assert(f == &output && p && size == 3); return short_write ? 2 : size;
}
static void storage_file_free(File* f) { assert(f == &output); freed++; }
FUNCTION
int main(void) {
    Storage s = {0}; TarArchive a = {.storage = &s};
    open_ok = true; consumed = false; assert(archive_extract_current_file(&a, "/ext/file"));
    short_write = true; consumed = false; assert(!archive_extract_current_file(&a, "/ext/file"));
    short_write = false; read_fail = true; consumed = false;
    assert(!archive_extract_current_file(&a, "/ext/file"));
    open_ok = false; consumed = false; assert(!archive_extract_current_file(&a, "/ext/file"));
    assert(freed == 4); return 0;
}
'''.replace('FUNCTION', function)
with tempfile.TemporaryDirectory(prefix='esp-tar-write-') as directory:
    root = Path(directory)
    (root / 'test.c').write_text(test)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(root / 'test.c'),
                    '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True)
print('Archive extraction detects short writes, read errors and open failures.')
