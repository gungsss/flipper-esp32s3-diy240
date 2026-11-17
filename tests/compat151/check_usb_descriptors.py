#!/usr/bin/env python3
"""Compile and inspect the actual ESP32 USB configuration descriptors.

The descriptor macros come from TinyUSB itself. Pass the patched ESP32 port
root and the TinyUSB 0.21 source root; no USB device is needed for this test.
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: check_usb_descriptors.py PORT_ROOT TINYUSB_ROOT')

root, tinyusb = map(Path, sys.argv[1:])
tests = Path(__file__).resolve().parent
hal = root / 'components/furi_hal'
single = (hal / 'furi_hal_usb_hid_tinyusb.c').read_text()
composite = (hal / 'furi_hal_usb_tinyusb_composite.c').read_text()

def definitions(text, prefixes):
    # Join continuation lines before extracting the actual build definitions.
    text = re.sub(r'\\\n\s*', ' ', text)
    return '\n'.join(
        line for line in text.splitlines()
        if line.startswith('#define ') and line.split()[1].startswith(prefixes)
    )

def array(text, name):
    m = re.search(r'static const uint8_t ' + name + r'\[\] = \{.*?\n\};', text, re.S)
    if not m:
        raise AssertionError(f'missing array {name}')
    return m.group(0)

def compile_descriptor(text, names, array_name):
    c = '\n'.join([
        '#include <stdio.h>',
        '#include <tusb.h>',
        '#include "furi_hal_usb_hid_output_report.h"',
        definitions(text, names),
        array(single, 'hid_report_descriptor'),
        array(text, array_name),
        'int main(void) {',
        f'for(size_t i=0;i<sizeof({array_name});i++) printf("%02x", {array_name}[i]);',
        'puts("");',
        'for(size_t i=0;i<sizeof(hid_report_descriptor);i++) printf("%02x", hid_report_descriptor[i]);',
        'puts(""); return 0;}',
    ])
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / 'descriptor.c'
        exe = Path(tmp) / 'descriptor'
        src.write_text(c)
        subprocess.run([
            'gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
            '-I', str(tests), '-I', str(hal), '-I', str(tinyusb / 'src'),
            str(src), '-o', str(exe),
        ], check=True)
        lines = subprocess.check_output([str(exe)], text=True).splitlines()
    return tuple(bytes.fromhex(x) for x in lines)

def inspect_config(data, expected, composite_mode):
    if data[0] != 9 or data[1] != 2 or int.from_bytes(data[2:4], 'little') != len(data):
        raise AssertionError('invalid configuration header or total length')
    endpoints = []
    interfaces = []
    classes = []
    pos = 0
    while pos < len(data):
        length, kind = data[pos:pos+2]
        if length < 2 or pos + length > len(data):
            raise AssertionError(f'invalid descriptor at {pos}')
        item = data[pos:pos+length]
        if kind == 4:
            interfaces.append((item[2], item[4], item[5]))
        elif kind == 5:
            endpoints.append(item[2])
        elif kind == 0x21:
            classes.append((pos, item))
        pos += length
    if endpoints != expected:
        raise AssertionError(f'wrong endpoint layout: {endpoints!r}')
    if not interfaces or interfaces[0][1:] != (2, 3):
        raise AssertionError(f'HID interface does not expose two endpoints: {interfaces!r}')
    if len(endpoints) != len(set(endpoints)):
        raise AssertionError('duplicate endpoints')
    # The composite installer patches report length at bytes 25 and 26.
    if composite_mode and (len(classes) != 1 or classes[0][0] + 7 != 25):
        raise AssertionError('composite HID report-length patch offset drifted')

for source, names, arr, endpoints, comp in (
    (single, ('HID_', 'REPORT_ID_'), 'hid_configuration_descriptor', [0x01, 0x81], False),
    (composite, ('HID_', 'REPORT_ID_', 'CDC_', 'MSC_', 'ITF_', 'COMP_CONFIG_'),
     's_composite_config_desc', [0x01, 0x81, 0x82, 0x03, 0x83, 0x04, 0x84], True),
):
    config, report = compile_descriptor(source, names, arr)
    inspect_config(config, endpoints, comp)
    if bytes([0x2a, 0xff, 0x00]) not in report or bytes([0x26, 0xff, 0x00]) not in report:
        raise AssertionError('keyboard report does not support usages through 255')
    print(f'{arr}: {len(config)} bytes, endpoints {endpoints}, keyboard range 0..255')

with tempfile.TemporaryDirectory() as tmp:
    exe = Path(tmp) / 'usb-led-test'
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
        '-I', str(hal), str(tests / 'usb_led_reports.c'), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'})
print('keyboard LED control and interrupt report handling passed')
