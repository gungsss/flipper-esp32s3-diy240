#!/usr/bin/env python3
"""Compile the official 1.5.1 date/time example on the host and check imports.

This test uses real project headers with small platform stubs. CI also tries an
Xtensa build; neither test executes the example on the device.
"""
import io
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

official, port = map(Path, sys.argv[1:3])
path = 'applications/examples/example_date_time_input'
sha = subprocess.check_output(
    ['git', '-C', str(official), 'rev-parse', '1.5.1^{commit}'], text=True).strip()
assert sha == '9e810dc399e027e48ce07751df72168abbb19065', 'unexpected official source'
archive = subprocess.check_output(['git', '-C', str(official), 'archive', '1.5.1', path])

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for entry in tar.getmembers():
            if not (entry.name == path or path.startswith(entry.name + '/') or
                    entry.name.startswith(path + '/')):
                raise ValueError('archive contains an unexpected path')
        tar.extractall(root, filter='data')
    stub = root / 'stub'
    (stub / 'freertos').mkdir(parents=True)
    (stub / 'freertos/FreeRTOS.h').write_text(
        '#pragma once\ntypedef int BaseType_t;\n#define portNUM_PROCESSORS 2\n')
    (stub / 'freertos/task.h').write_text('#pragma once\n')
    (stub / 'furi_hal.h').write_text('#pragma once\n#include <furi_hal_rtc.h>\n')
    (stub / 'prelude.h').write_text('#include <stdint.h>\n#define _ATTRIBUTE(x) __attribute__(x)\n')
    sources = sorted((root / path).rglob('*.c'))
    assert sources, 'official example is missing source files'
    objects = []
    include_dirs = (stub, port / 'components', port / 'components/furi',
                    port / 'components/furi/core', port / 'components/mlib',
                    port / 'components/input', port / 'components/gui',
                    port / 'components/datetime', port / 'components/furi_hal')
    flags = [arg for folder in include_dirs for arg in ('-I', str(folder))]
    for index, source in enumerate(sources):
        obj = root / f'app_{index}.o'
        # Host distributions may inject x86-specific stack-protector imports;
        # the independently compiled Xtensa example checks its own imports.
        subprocess.run(['gcc', '-std=gnu11', '-fno-stack-protector', '-c', '-include', str(stub / 'prelude.h'),
                        *flags, str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    combined = root / 'app.o'
    subprocess.run(['ld', '-r', *objects, '-o', str(combined)], check=True)
    unresolved = subprocess.check_output(['nm', '-u', str(combined)], text=True)
    names = sorted(set(re.findall(r'\bU\s+(\w+)', unresolved)))
    assert names, 'example unexpectedly has no imports'
    imports = root / 'imports.txt'
    imports.write_text('\n'.join(names) + '\n')
    subprocess.run(['python3', str(port / 'tools/check_fap_symbols.py'),
                    str(port / 'components/flipper_application/flipper_application/firmware_api.c'),
                    str(imports)], check=True)
print(f'Official 1.5.1 example compiled on host; {len(names)} imports checked.')
