#!/usr/bin/env python3
"""Verify the actual date/time UI is the official 1.5.1 implementation."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

official, port = map(Path, sys.argv[1:3])
base = 'applications/services/gui/modules/'
for name in ('date_time_input.c', 'date_time_input.h'):
    upstream = subprocess.check_output(['git', '-C', str(official), 'show', '1.5.1:' + base + name])
    actual = (port / 'components/gui/modules' / name).read_bytes()
    if actual != upstream:
        raise AssertionError(name + ' differs from official 1.5.1')

source = (port / 'components/gui/modules/date_time_input.c').read_text()
functions = []
for name in ('date_time_input_draw_hour_24hr_callback',
             'date_time_input_draw_hour_12hr_callback',
             'date_time_input_draw_time_callback'):
    match = re.search(r'static void ' + name + r'\([^\n]*\) \{.*?\n\}', source, re.S)
    if not match:
        raise AssertionError('unable to locate ' + name)
    functions.append(match.group(0))

harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef struct { uint8_t hour, minute, second; } DateTime;
typedef struct { DateTime* datetime; } DateTimeInputModel;
typedef struct { int unused; } Canvas;
enum { FontPrimary, FontSecondary, FontBigNumbers, ROW_1_Y=15, ROW_1_H=20 };
enum { FuriHalRtcLocaleTimeFormat24h, FuriHalRtcLocaleTimeFormat12h };
static int rtc_format, nblocks, ntexts;
static char blocks[4][16], texts[4][16];
#define get_state(m,r,c,f) 0
#define furi_check(x) assert(x)
static int furi_hal_rtc_get_locale_timeformat(void) { return rtc_format; }
static void canvas_set_font(Canvas* c, int f) { (void)c; (void)f; }
static void canvas_draw_str(Canvas* c, int x, int y, const char* s) {
    (void)c; (void)x; (void)y; (void)s;
}
static void canvas_draw_box(Canvas* c, int x, int y, int w, int h) {
    (void)c; (void)x; (void)y; (void)w; (void)h;
}
static void date_time_input_draw_block(Canvas* c,int x,int y,int w,int h,int f,int s,const char* t) {
    (void)c; (void)x; (void)y; (void)w; (void)h; (void)f; (void)s;
    assert(nblocks < 4); snprintf(blocks[nblocks++], sizeof(blocks[0]), "%s", t);
}
static void date_time_input_draw_text(Canvas* c,int x,int y,int w,int h,int f,int s,const char* t) {
    (void)c; (void)x; (void)y; (void)w; (void)h; (void)f; (void)s;
    assert(ntexts < 4); snprintf(texts[ntexts++], sizeof(texts[0]), "%s", t);
}
''' + '\n'.join(functions) + r'''
int main(void) {
    Canvas c = {0}; DateTime dt = {13, 5, 9}; DateTimeInputModel m = {&dt};
    rtc_format = FuriHalRtcLocaleTimeFormat12h;
    date_time_input_draw_time_callback(&c, &m);
    assert(nblocks == 3 && ntexts == 2);
    assert(strcmp(blocks[0], "  ") == 0);
    assert(strcmp(texts[0], "01") == 0 && strcmp(texts[1], "PM") == 0);
    assert(strcmp(blocks[1], "05") == 0 && strcmp(blocks[2], "09") == 0);
    nblocks = ntexts = 0; dt.hour = 0;
    date_time_input_draw_time_callback(&c, &m);
    assert(strcmp(texts[0], "12") == 0 && strcmp(texts[1], "AM") == 0);
    nblocks = ntexts = 0; dt.hour = 13; rtc_format = FuriHalRtcLocaleTimeFormat24h;
    date_time_input_draw_time_callback(&c, &m);
    assert(nblocks == 3 && ntexts == 0 && strcmp(blocks[0], "13") == 0);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c = Path(tmp, 'date_time.c')
    exe = Path(tmp, 'date_time')
    c.write_text(harness)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('Official 1.5.1 date/time source and 12/24-hour rendering checks passed.')
