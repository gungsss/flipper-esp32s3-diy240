#!/usr/bin/env python3
"""Exercise the real ported stream and FuriString code using memory streams."""
import subprocess
import sys
import tempfile
from pathlib import Path

port = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='esp151-stream-') as directory:
    temp = Path(directory)
    (temp / 'storage').mkdir()
    (temp / 'core').mkdir()
    (temp / 'storage/storage.h').write_text('''#pragma once
typedef struct Storage Storage;
typedef enum {FSAM_READ, FSAM_WRITE} FS_AccessMode;
typedef enum {FSOM_OPEN_EXISTING, FSOM_CREATE_ALWAYS} FS_OpenMode;
typedef enum {FSE_OK} FS_Error;
''')
    (temp / 'furi.h').write_text('''#pragma once
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define _ATTRIBUTE(x) __attribute__(x)
#include <core/furi_string.h>
#define furi_check(x) assert(x)
#define MIN(a, b) ((a) < (b) ? (a) : (b))
''')
    (temp / 'prelude.h').write_text('#define _ATTRIBUTE(x) __attribute__(x)\n')
    (temp / 'core/common_defines.h').write_text('#pragma once\n')
    sources = (Path(__file__).with_name('stream_regression.c'),
               port / 'components/toolbox/stream/stream.c',
               port / 'components/toolbox/stream/string_stream.c',
               port / 'components/furi/core/furi_string.c')
    include_dirs = (temp, port / 'components', port / 'components/furi',
                    port / 'components/furi/core', port / 'components/mlib')
    flags = [arg for folder in include_dirs for arg in ('-I', str(folder))]
    exe = temp / 'stream-regression'
    subprocess.run(['gcc', '-std=gnu11', '-O1', '-ffunction-sections', '-fdata-sections',
                    '-include', str(temp / 'prelude.h'),
                    *flags, *(str(source) for source in sources), '-Wl,--gc-sections',
                    '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('Ported string stream passed write, line reading, replacement and rewind checks.')
