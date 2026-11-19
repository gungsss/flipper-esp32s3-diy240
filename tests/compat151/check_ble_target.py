#!/usr/bin/env python3
"""Check ESP BLE hardware identity and reported preview revision."""
import subprocess
import sys
import tempfile
from pathlib import Path

port = Path(sys.argv[1]).resolve()
ble = port / 'components/ble_serial'
source = (ble / 'ble_serial.c').read_text()
assert '#include "ble_serial_device_info.h"' in source
assert 'dis_hw_revision[] = BLE_SERIAL_HW_REVISION' in source
assert 'dis_sw_revision[] = "1.5.1-ESP32-preview"' in source, 'BLE must report the ESP32 preview build, not the old 1.4.3 base'
cases = {'ESP32S3': 'ESP32-S3', 'ESP32C6': 'ESP32-C6', 'ESP32S2': 'ESP32-S2'}
with tempfile.TemporaryDirectory(prefix='esp151-ble-') as directory:
    tmp = Path(directory)
    main = tmp / 'main.c'
    main.write_text('#include <string.h>\n#include "ble_serial_device_info.h"\n'
                    'int main(int argc, char** argv) {\n'
                    'return argc != 2 || strcmp(BLE_SERIAL_HW_REVISION, argv[1]);\n}\n')
    for target, expected in cases.items():
        (tmp / 'sdkconfig.h').write_text(f'#define CONFIG_IDF_TARGET_{target} 1\n')
        out = tmp / 'ble-target-check'
        subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                        '-I', str(tmp), '-I', str(ble), str(main), '-o', str(out)], check=True)
        subprocess.run([str(out), expected], check=True)
print('BLE hardware identity matches ESP32-S3, C6 and S2 target configurations.')
print('BLE software revision reports 1.5.1-ESP32-preview.')
print('BLE behavior still needs testing on the physical board and phone.')
