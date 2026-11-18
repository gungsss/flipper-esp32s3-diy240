#!/usr/bin/env python3
"""Exercise the actual TinyUSB output-report callback for the S3 profile."""
import subprocess
import sys
import tempfile
from pathlib import Path

source = (Path(sys.argv[1]) / 'components/furi_hal/furi_hal_usb_hid_tinyusb.c').read_text()
assert '#define HID_EP_OUT      0x01' in source
assert 'TUD_HID_INOUT_DESC_LEN' in source
assert 'TUD_HID_INOUT_DESCRIPTOR(' in source
start = source.index('void tud_hid_set_report_cb(')
brace = source.index('{', start)
depth = 0
for i in range(brace, len(source)):
    if source[i] == '{':
        depth += 1
    elif source[i] == '}':
        depth -= 1
        if depth == 0:
            callback = source[start:i + 1]
            break
else:
    raise AssertionError('HID callback was not found')

test = r'''
#include <assert.h>
#include <stdint.h>
#define CONFIG_IDF_TARGET_ESP32S3 1
#define REPORT_ID_KEYBOARD 1
typedef enum { HID_REPORT_TYPE_INPUT = 1, HID_REPORT_TYPE_OUTPUT = 2 } hid_report_type_t;
static struct { uint8_t led_state; } s_state;
static int u2f_active, u2f_calls;
static uint16_t u2f_size;
static int furi_hal_usb_u2f_backend_is_active(void) { return u2f_active; }
static void furi_hal_hid_u2f_receive_report(const uint8_t* buffer, uint16_t size) {
    (void)buffer; u2f_calls++; u2f_size = size;
}
CALLBACK
int main(void) {
    uint8_t control[] = {0x02};
    uint8_t interrupt[] = {1, 0x04};
    uint8_t other[] = {2, 0x08};
    s_state.led_state = 0;
    tud_hid_set_report_cb(0, 1, HID_REPORT_TYPE_OUTPUT, control, sizeof(control));
    assert(s_state.led_state == 0x02);
    tud_hid_set_report_cb(0, 0, HID_REPORT_TYPE_OUTPUT, interrupt, sizeof(interrupt));
    assert(s_state.led_state == 0x04);
    tud_hid_set_report_cb(0, 0, HID_REPORT_TYPE_OUTPUT, other, sizeof(other));
    tud_hid_set_report_cb(0, 0, HID_REPORT_TYPE_OUTPUT, interrupt, 1);
    tud_hid_set_report_cb(0, 1, HID_REPORT_TYPE_OUTPUT, 0, 1);
    tud_hid_set_report_cb(0, 1, HID_REPORT_TYPE_INPUT, control, sizeof(control));
    assert(s_state.led_state == 0x04);
    u2f_active = 1;
    tud_hid_set_report_cb(0, 0, HID_REPORT_TYPE_OUTPUT, other, sizeof(other));
    assert(u2f_calls == 1 && u2f_size == sizeof(other));
    assert(s_state.led_state == 0x04);
    tud_hid_set_report_cb(0, 1, HID_REPORT_TYPE_OUTPUT, control, sizeof(control));
    assert(u2f_calls == 1 && s_state.led_state == 0x04);
    return 0;
}
'''.replace('CALLBACK', callback)
with tempfile.TemporaryDirectory(prefix='esp-hid-') as directory:
    root = Path(directory)
    (root / 'test.c').write_text(test)
    subprocess.run(['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                    str(root / 'test.c'), '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True)
print('USB HID control and interrupt LED reports are handled; other reports stay isolated.')
