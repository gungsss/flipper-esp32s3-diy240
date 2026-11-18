#!/usr/bin/env python3
"""Check the actual 1.5.1 CRC implementation and its ESP32 SDK exports."""
import subprocess
import sys
import tempfile
from pathlib import Path

official, port = map(Path, sys.argv[1:3])
assert subprocess.check_output(
    ['git', '-C', str(official), 'rev-parse', '1.5.1^{commit}'], text=True
).strip() == '9e810dc399e027e48ce07751df72168abbb19065'

for name in ('crc32_calc.c', 'crc32_calc.h'):
    expected = subprocess.check_output(
        ['git', '-C', str(official), 'show', f'1.5.1:lib/toolbox/{name}'])
    assert (port / 'components/toolbox' / name).read_bytes() == expected, name

api = (port / 'components/flipper_application/flipper_application/firmware_api.c').read_text()
for name in ('crc32_calc_buffer', 'crc32_calc_file'):
    assert api.count(f'/* {name} */') == 1, f'{name}: SDK export missing or duplicated'
    assert f'official 1.5.1 signature: {name}' in api, f'{name}: missing type check'
assert '"crc32_calc.c"' in (port / 'components/toolbox/CMakeLists.txt').read_text()

stub = r'''
#pragma once
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#define furi_check(cond) assert(cond)
typedef struct File {
    const uint8_t* data;
    size_t length;
    size_t offset;
} File;
bool storage_file_is_open(File* file);
bool storage_file_seek(File* file, uint32_t offset, bool from_start);
size_t storage_file_read(File* file, void* buffer, size_t count);
uint64_t storage_file_size(File* file);
'''

harness = r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <toolbox/crc32_calc.h>

bool storage_file_is_open(File* f) { return f != NULL; }
bool storage_file_seek(File* f, uint32_t off, bool start) {
    if(!start || off > f->length) return false;
    f->offset = off;
    return true;
}
size_t storage_file_read(File* f, void* dst, size_t count) {
    if(count > f->length - f->offset) count = f->length - f->offset;
    memcpy(dst, f->data + f->offset, count);
    f->offset += count;
    return count;
}
uint64_t storage_file_size(File* f) { return f->length; }

static uint32_t reference_crc(const uint8_t* data, size_t length) {
    uint32_t crc = ~0u;
    for(size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for(int j = 0; j < 8; ++j)
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}
static void progress(uint8_t value, void* ctx) {
    unsigned* calls = ctx;
    assert(value > 0 && value <= 100);
    ++*calls;
}
int main(void) {
    const char* example = "123456789";
    assert(crc32_calc_buffer(0, example, 9) == 0xcbf43926u);
    uint32_t first = crc32_calc_buffer(0, example, 4);
    assert(crc32_calc_buffer(first, example + 4, 5) == 0xcbf43926u);
    uint8_t data[4097];
    for(size_t i = 0; i < sizeof(data); ++i) data[i] = (i * 73u + 11u) & 0xffu;
    const size_t lengths[] = {0, 1, 511, 512, 513, 1300, sizeof(data)};
    for(size_t i = 0; i < sizeof(lengths)/sizeof(lengths[0]); ++i) {
        size_t n = lengths[i];
        File file = {.data = data, .length = n, .offset = n};
        unsigned calls = 0;
        assert(crc32_calc_buffer(0, data, n) == reference_crc(data, n));
        assert(crc32_calc_file(&file, progress, &calls) == reference_crc(data, n));
        assert(file.offset == n);
        assert(calls == n / 512);
    }
    return 0;
}
'''

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp / 'storage').mkdir()
    (tmp / 'storage/storage.h').write_text(stub)
    (tmp / 'harness.c').write_text(harness)
    subprocess.run([
        'gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
        '-I', str(tmp), '-I', str(port / 'components'),
        str(tmp / 'harness.c'), str(port / 'components/toolbox/crc32_calc.c'),
        '-o', str(tmp / 'crc32-test'),
    ], check=True)
    subprocess.run([str(tmp / 'crc32-test')], check=True)

print('Official CRC32 buffer and file checks pass with boundary-length samples.')
print('The actual SD card and ESP32 hardware still need separate validation.')
