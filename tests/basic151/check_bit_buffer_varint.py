#!/usr/bin/env python3
"""Exercise the actual generic data APIs exposed to native ESP applications."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1]).resolve()
test = r'''
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>
#include <toolbox/bit_buffer.h>
#include "varint.h"
int main(void) {
    uint8_t one[] = {0xA5};
    BitBuffer* a = bit_buffer_alloc(1);
    bit_buffer_copy_bytes(a, one, sizeof(one));
    assert(bit_buffer_get_byte_from_bit(a, 0) == 0xA5);
    assert(bit_buffer_get_byte_from_bit(a, 1) == 0x52);
    assert(bit_buffer_get_byte_from_bit(a, 7) == 0x01);
    uint8_t pair[] = {0xA5, 0x3C};
    BitBuffer* b = bit_buffer_alloc(3);
    bit_buffer_copy_bytes(b, pair, sizeof(pair));
    assert(bit_buffer_get_byte_from_bit(b, 4) == 0xCA);
    assert(bit_buffer_get_byte_from_bit(b, 8) == 0x3C);
    bit_buffer_append(b, a);
    assert(bit_buffer_get_size_bytes(b) == 3 && bit_buffer_get_byte(b, 2) == 0xA5);
    assert(bit_buffer_get_byte_from_bit(b, 16) == 0xA5);
    assert(bit_buffer_get_byte_from_bit(b, 23) == 0x01);
    bit_buffer_free(a); bit_buffer_free(b);
    const uint32_t unsigned_values[] = {0, 1, 127, 128, 16383, 16384, 0x7fffffff, UINT32_MAX};
    for(size_t i = 0; i < sizeof(unsigned_values)/sizeof(unsigned_values[0]); ++i) {
        uint8_t encoded[5] = {0}; uint32_t decoded = 0;
        size_t n = varint_uint32_pack(unsigned_values[i], encoded);
        assert(n == varint_uint32_length(unsigned_values[i]));
        assert(varint_uint32_unpack(&decoded, encoded, n) == n && decoded == unsigned_values[i]);
    }
    const int32_t signed_values[] = {INT32_MIN, -100000, -1, 0, 1, 100000, INT32_MAX};
    for(size_t i = 0; i < sizeof(signed_values)/sizeof(signed_values[0]); ++i) {
        uint8_t encoded[5] = {0}; int32_t decoded = 0;
        size_t n = varint_int32_pack(signed_values[i], encoded);
        assert(n == varint_int32_length(signed_values[i]));
        assert(varint_int32_unpack(&decoded, encoded, n) == n && decoded == signed_values[i]);
    }
    uint8_t truncated[] = {0x80};
    uint8_t overflow[] = {0xff, 0xff, 0xff, 0xff, 0x10};
    uint8_t continued[] = {0xff, 0xff, 0xff, 0xff, 0x80, 0x00};
    uint32_t u = 9; int32_t s = 9;
    assert(varint_uint32_unpack(&u, NULL, 0) == 0 && u == 0);
    assert(varint_uint32_unpack(&u, truncated, sizeof(truncated)) == 0 && u == 0);
    assert(varint_uint32_unpack(&u, overflow, sizeof(overflow)) == 0 && u == 0);
    assert(varint_int32_unpack(&s, continued, sizeof(continued)) == 0 && s == 0);
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='esp-generic-api-') as directory:
    root = Path(directory)
    (root / 'furi.h').write_text(r'''
#pragma once
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#define furi_check(x) assert(x)
#define FURI_BIT(x, n) (((x) >> (n)) & 1)
#define malloc(size) calloc(1, (size))
''')
    (root / 'test.c').write_text(test)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-g',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    '-I', str(root), '-I', str(source / 'components'),
                    '-I', str(source / 'lib/toolbox'), str(root / 'test.c'),
                    str(source / 'components/toolbox/bit_buffer.c'),
                    str(source / 'lib/toolbox/varint.c'), '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True,
                   env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'})
print('Bit-buffer boundary reads and varint round trips pass sanitizers.')
