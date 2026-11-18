#!/usr/bin/env python3
"""Compile official 1.5.1 examples on the host and check their imports.

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
examples = ('example_date_time_input', 'example_view_dispatcher', 'example_apps_data')
paths = tuple('applications/examples/' + name for name in examples)
sha = subprocess.check_output(
    ['git', '-C', str(official), 'rev-parse', '1.5.1^{commit}'], text=True).strip()
assert sha == '9e810dc399e027e48ce07751df72168abbb19065', 'unexpected official source'
archive = subprocess.check_output(['git', '-C', str(official), 'archive', '1.5.1', *paths])

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for entry in tar.getmembers():
            if not any(entry.name == path or path.startswith(entry.name + '/') or
                       entry.name.startswith(path + '/') for path in paths):
                raise ValueError('archive contains an unexpected path')
        tar.extractall(root, filter='data')
    stub = root / 'stub'
    (stub / 'freertos').mkdir(parents=True)
    (stub / 'freertos/FreeRTOS.h').write_text(
        '#pragma once\ntypedef int BaseType_t;\n#define portNUM_PROCESSORS 2\n')
    (stub / 'freertos/task.h').write_text('#pragma once\n')
    (stub / 'furi_hal.h').write_text('#pragma once\n#include <furi_hal_rtc.h>\n')
    (stub / 'prelude.h').write_text('#include <stdint.h>\n#define _ATTRIBUTE(x) __attribute__(x)\n')
    include_dirs = (stub, port / 'components', port / 'components/furi',
                    port / 'components/furi/core', port / 'components/mlib',
                    port / 'components/input', port / 'components/gui',
                    port / 'components/datetime', port / 'components/furi_hal')
    flags = [arg for folder in include_dirs for arg in ('-I', str(folder))]
    for example, path in zip(examples, paths):
        sources = sorted((root / path).rglob('*.c'))
        assert sources, f'{example} is missing source files'
        objects = []
        for index, source in enumerate(sources):
            obj = root / f'{example}_{index}.o'
            # Host distributions may inject x86-specific stack-protector imports;
            # the independently compiled Xtensa examples check their own imports.
            subprocess.run([
                'gcc', '-std=gnu11', '-fno-stack-protector', '-c',
                '-include', str(stub / 'prelude.h'), *flags, str(source), '-o', str(obj),
            ], check=True)
            objects.append(str(obj))
        combined = root / f'{example}.o'
        subprocess.run(['ld', '-r', *objects, '-o', str(combined)], check=True)
        unresolved = subprocess.check_output(['nm', '-u', str(combined)], text=True)
        names = sorted(set(re.findall(r'\bU\s+(\w+)', unresolved)))
        assert names, f'{example} unexpectedly has no imports'
        imports = root / f'{example}_imports.txt'
        imports.write_text('\n'.join(names) + '\n')
        subprocess.run([
            'python3', str(port / 'tools/check_fap_symbols.py'),
            str(port / 'components/flipper_application/flipper_application/firmware_api.c'),
            str(imports),
        ], check=True)
        print(f'{example}: compiled on host; {len(names)} imports checked.')

    probe = Path(__file__).parent / 'sdk_probe/sdk_probe.c'
    probe_obj = root / 'sdk_probe.o'
    subprocess.run([
        'gcc', '-std=gnu11', '-fno-stack-protector', '-c',
        '-include', str(stub / 'prelude.h'), *flags, str(probe), '-o', str(probe_obj),
    ], check=True)
    unresolved = subprocess.check_output(['nm', '-u', str(probe_obj)], text=True)
    names = sorted(set(re.findall(r'\bU\s+(\w+)', unresolved)))
    required = {'file_browser_alloc', 'bit_buffer_append_bit',
                'flipper_format_update_string_cstr', 'crc32_calc_buffer',
                'string_stream_alloc', 'stream_write_cstring'}
    assert required <= set(names), 'SDK probe failed to exercise newly exported functions'
    imports = root / 'sdk_probe_imports.txt'
    imports.write_text('\n'.join(names) + '\n')
    subprocess.run([
        'python3', str(port / 'tools/check_fap_symbols.py'),
        str(port / 'components/flipper_application/flipper_application/firmware_api.c'),
        str(imports),
    ], check=True)
    print(f'SDK probe: compiled on host; {len(names)} imports checked.')
