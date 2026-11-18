#!/usr/bin/env python3
"""Run the actual date/time drawing paths with both RTC locale formats."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

source = (Path(sys.argv[1]) / 'components/gui/modules/date_time_input.c').read_text()
assert '#include <furi_hal_rtc.h>' in source
assert not re.search(r'static\s+inline\s+FuriHalRtcLocaleTimeFormat\s+furi_hal_rtc_get_locale_timeformat', source)


def function(name):
    start = source.index('static void ' + name + '(')
    brace = source.index('{', start)
    level = 0
    for end in range(brace, len(source)):
        if source[end] == '{':
            level += 1
        elif source[end] == '}':
            level -= 1
            if level == 0:
                return source[start:end + 1]
    raise AssertionError('Unclosed function: ' + name)


code = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define ROW_1_Y 40
#define ROW_1_H 20
#define get_state(...) 0
#define furi_check(x) assert(x)
typedef struct { int unused; } Canvas;
typedef struct { uint8_t hour, minute, second; } DateTime;
typedef struct { DateTime* datetime; } DateTimeInputModel;
enum { FontSecondary, FontPrimary, FontBigNumbers };
enum { FuriHalRtcLocaleTimeFormat24h, FuriHalRtcLocaleTimeFormat12h };
static int selected_format;
static char blocks[4][16], texts[4][16];
static int block_count, text_count;
static int furi_hal_rtc_get_locale_timeformat(void) { return selected_format; }
static void canvas_set_font(Canvas* c, int f) { (void)c; (void)f; }
static void canvas_draw_str(Canvas* c, int x, int y, const char* s) { (void)c; (void)x; (void)y; (void)s; }
static void canvas_draw_box(Canvas* c, int x, int y, int w, int h) { (void)c; (void)x; (void)y; (void)w; (void)h; }
static void date_time_input_draw_block(Canvas* c, int x, int y, int w, int h, int f, int state, const char* s) {
    (void)c; (void)x; (void)y; (void)w; (void)h; (void)f; (void)state;
    assert(block_count < 4); snprintf(blocks[block_count++], sizeof(blocks[0]), "%s", s);
}
static void date_time_input_draw_text(Canvas* c, int x, int y, int w, int h, int f, int state, const char* s) {
    (void)c; (void)x; (void)y; (void)w; (void)h; (void)f; (void)state;
    assert(text_count < 4); snprintf(texts[text_count++], sizeof(texts[0]), "%s", s);
}
FUNCTIONS
static void check(int format, int hour, const char* expected_hour, const char* expected_suffix) {
    Canvas canvas = {0}; DateTime date = {hour, 4, 5}; DateTimeInputModel model = {&date};
    selected_format = format; block_count = text_count = 0;
    date_time_input_draw_time_callback(&canvas, &model);
    assert(block_count == 3);
    assert(strcmp(blocks[1], "04") == 0 && strcmp(blocks[2], "05") == 0);
    if(format == FuriHalRtcLocaleTimeFormat12h) {
        assert(strcmp(blocks[0], "  ") == 0);
        assert(text_count == 2 && strcmp(texts[0], expected_hour) == 0);
        assert(strcmp(texts[1], expected_suffix) == 0);
    } else {
        assert(text_count == 0 && strcmp(blocks[0], expected_hour) == 0);
    }
}
int main(void) {
    check(FuriHalRtcLocaleTimeFormat12h, 0, "12", "AM");
    check(FuriHalRtcLocaleTimeFormat12h, 12, "12", "PM");
    check(FuriHalRtcLocaleTimeFormat12h, 23, "11", "PM");
    check(FuriHalRtcLocaleTimeFormat24h, 23, "23", "");
    return 0;
}
'''
names = ('date_time_input_draw_hour_24hr_callback', 'date_time_input_draw_hour_12hr_callback',
         'date_time_input_draw_time_callback')
code = code.replace('FUNCTIONS', '\n'.join(function(n) for n in names))
with tempfile.TemporaryDirectory(prefix='esp-datetime-') as directory:
    root = Path(directory)
    (root / 'test.c').write_text(code)
    subprocess.run(['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                    str(root / 'test.c'), '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True)
print('Date/time input honors RTC format and renders 12h/24h correctly.')
