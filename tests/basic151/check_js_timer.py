#!/usr/bin/env python3
"""Exercise the real JS timer handler with zero, negative and positive intervals."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

source = (Path(sys.argv[1]) / 'applications/system/js_app/modules/js_event_loop/js_event_loop.c').read_text()
match = re.search(r'(?m)^static void js_event_loop_timer\(struct mjs\* mjs\) \{', source)
assert match
index, depth = match.end(), 1
while depth:
    if source[index] == '{':
        depth += 1
    elif source[index] == '}':
        depth -= 1
    index += 1
handler = source[match.start():index]
prelude = r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef enum { FuriEventLoopTimerTypePeriodic, FuriEventLoopTimerTypeOnce } FuriEventLoopTimerType;
typedef struct { const char* name; int value; } JsValueEnumVariant;
typedef struct { int unused; } JsValueDeclaration;
typedef struct { int unused; } JsValueArguments;
typedef struct JsEventLoopContract {
    int magic, object_type;
    void* object;
    struct { uint32_t interval_ticks; FuriEventLoopTimerType type; } timer;
} JsEventLoopContract;
typedef struct { JsEventLoopContract* owned_contracts; } JsEventLoop;
struct mjs { int32_t interval; int errors; JsEventLoop loop; void* result; };
enum { JsValueTypeInt32, MJS_BAD_ARGS_ERROR, JsForeignMagic_JsEventLoopContract, JsEventLoopObjectTypeTimer };
#define JS_VALUE_ENUM(type, variants) {0}
#define JS_VALUE_SIMPLE(type) {0}
#define JS_VALUE_ARGS(list) {0}
#define JS_VALUE_PARSE_ARGS_OR_RETURN(m, args, mptr, iptr) do { \
    (void)(args); *(mptr) = FuriEventLoopTimerTypePeriodic; *(iptr) = (m)->interval; \
} while(0)
#define JS_GET_CONTEXT(m) (&(m)->loop)
static void mjs_prepend_errorf(struct mjs* m, int code, const char* text) {
    assert(code == MJS_BAD_ARGS_ERROR && strstr(text, "positive")); ++m->errors;
}
static uint32_t furi_ms_to_ticks(uint32_t n) { return n; }
static void push(JsEventLoopContract** target, JsEventLoopContract* value) { *target = value; }
#define ContractArray_push_back(array, value) push(&(array), (value))
static void* mjs_mk_foreign(struct mjs* m, void* ptr) { (void)m; return ptr; }
static void mjs_return(struct mjs* m, void* ptr) { m->result = ptr; }
'''
tests = r'''
int main(void) {
    struct mjs value = {.interval = 0};
    js_event_loop_timer(&value);
    assert(value.errors == 1 && !value.result && !value.loop.owned_contracts);
    value.interval = -42;
    js_event_loop_timer(&value);
    assert(value.errors == 2 && !value.result && !value.loop.owned_contracts);
    value.interval = 100;
    js_event_loop_timer(&value);
    assert(value.errors == 2 && value.result == value.loop.owned_contracts);
    assert(value.loop.owned_contracts->timer.interval_ticks == 100);
    free(value.loop.owned_contracts);
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='esp-js-timer-') as temp:
    temp = Path(temp)
    (temp / 'test.c').write_text(prelude + '\n' + handler + '\n' + tests)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Wno-unused-variable',
                    str(temp / 'test.c'), '-o', str(temp / 'test')], check=True)
    subprocess.run([str(temp / 'test')], check=True)
print('JS timer rejects invalid intervals and accepts a positive interval.')
