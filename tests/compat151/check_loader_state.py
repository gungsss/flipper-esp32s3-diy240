#!/usr/bin/env python3
"""Exercise the actual ESP32 loader status helpers against 1.5.1 API types."""
import csv
import io
import re
import subprocess
import sys
import tempfile
from pathlib import Path

official, source = map(Path, sys.argv[1:3])
commit = subprocess.check_output(
    ['git', '-C', str(official), 'rev-parse', '1.5.1^{commit}'], text=True).strip()
assert commit == '9e810dc399e027e48ce07751df72168abbb19065'
csv_text = subprocess.check_output(
    ['git', '-C', str(official), 'show', '1.5.1:targets/f7/api_symbols.csv'], text=True)
official_exports = {row['name']: row for row in csv.DictReader(io.StringIO(csv_text))
                    if row['entry'] == 'Function' and row['status'] == '+'}
expected = {
    'loader_start': ('LoaderStatus', 'Loader*, const char*, const char*, FuriString*'),
    'loader_signal': ('_Bool', 'Loader*, uint32_t, void*'),
    'loader_get_application_name': ('_Bool', 'Loader*, FuriString*'),
    'loader_get_application_launch_path': ('_Bool', 'Loader*, FuriString*'),
    'loader_get_pubsub': ('FuriPubSub*', 'Loader*'),
    'loader_is_locked': ('_Bool', 'Loader*'),
    'loader_lock': ('_Bool', 'Loader*'),
    'loader_unlock': ('void', 'Loader*'),
    'loader_show_menu': ('void', 'Loader*'),
}
table = (source / 'components/flipper_application/flipper_application/firmware_api.c').read_text()
official_loader_header = subprocess.check_output(
    ['git', '-C', str(official), 'show', '1.5.1:applications/services/loader/loader.h'], text=True)
port_loader_header = (source / 'components/loader/loader.h').read_text()
for expression in ('LoaderDeferredLaunchFlagNone = 0', 'LoaderDeferredLaunchFlagGui = (1 << 1)'):
    assert expression in official_loader_header and expression in port_loader_header, expression
for name, (ret, args) in expected.items():
    row = official_exports[name]
    assert (row['type'], row['params']) == (ret, args), name
    assert table.count(f'/* {name} */') == 1, name
    assert f'official 1.5.1 signature: {name}' in table, name

actual = (source / 'components/loader/loader.c').read_text()
functions = []
def extract_function(name, return_type):
    match = re.search(r'(?m)^static ' + return_type + ' ' + name + r'\([^)]*\) \{', actual)
    assert match, name
    depth, i = 1, match.end()
    while depth and i < len(actual):
        if actual[i] == '{': depth += 1
        if actual[i] == '}': depth -= 1
        i += 1
    assert depth == 0, name
    return actual[match.start():i]

for name in ('loader_is_application_running', 'loader_do_signal',
             'loader_do_get_application_name', 'loader_do_get_application_launch_path'):
    functions.append(extract_function(name, 'bool'))

harness = r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef struct { char data[128]; } FuriString;
typedef struct { const char* name; bool consume; uint32_t last_signal; void* last_arg; } FuriThread;
typedef struct { struct { FuriThread* thread; FuriString* launch_path; } app; } Loader;
#define LOADER_MAGIC_THREAD_VALUE 0xDEADBEEF
static bool furi_thread_signal(FuriThread* thread, uint32_t signal, void* arg) {
    thread->last_signal = signal; thread->last_arg = arg; return thread->consume;
}
static FuriThread* furi_thread_get_id(FuriThread* thread) { return thread; }
static const char* furi_thread_get_name(FuriThread* thread) { return thread->name; }
static void furi_string_set_cstr(FuriString* dst, const char* s) {
    snprintf(dst->data, sizeof(dst->data), "%s", s);
}
static void furi_string_set_string(FuriString* dst, FuriString* s) {
    furi_string_set_cstr(dst, s->data);
}
#define furi_string_set(a, b) _Generic((b), const char*: furi_string_set_cstr, \
                                      FuriString*: furi_string_set_string)(a, b)
""" + '\n'.join(functions) + r"""
int main(void) {
    Loader l = {0}; FuriString out = {0}, path = {"/ext/apps/example.fap"};
    FuriThread app = {.name="Demo", .consume=true};
    int payload = 42;
    assert(!loader_do_signal(&l, 1, &payload));
    assert(!loader_do_get_application_name(&l, &out));
    assert(!loader_do_get_application_launch_path(&l, &out));
    l.app.thread = (FuriThread*)LOADER_MAGIC_THREAD_VALUE;
    assert(!loader_do_signal(&l, 1, &payload));
    assert(!loader_do_get_application_name(&l, &out));
    assert(!loader_do_get_application_launch_path(&l, &out));
    l.app.thread = &app; l.app.launch_path = &path;
    assert(loader_do_signal(&l, 17, &payload));
    assert(app.last_signal == 17 && app.last_arg == &payload);
    app.consume = false;
    assert(!loader_do_signal(&l, 18, NULL));
    assert(loader_do_get_application_name(&l, &out) && !strcmp(out.data, "Demo"));
    assert(loader_do_get_application_launch_path(&l, &out));
    assert(!strcmp(out.data, "/ext/apps/example.fap"));
    l.app.launch_path = NULL;
    assert(!loader_do_get_application_launch_path(&l, &out));
    return 0;
}
"""
with tempfile.TemporaryDirectory() as d:
    c, exe = Path(d, 'loader.c'), Path(d, 'loader')
    c.write_text(harness)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
    close_harness = r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef struct { char data[128]; } FuriString;
typedef struct { int value; } FuriThread;
typedef struct { int value; } FlipperApplication;
typedef struct {
    struct { FuriString* launch_path; char* args; FuriThread* thread; FlipperApplication* fap; } app;
    char* pending_name; char* pending_args; void* pubsub;
} Loader;
typedef struct { int value; } LoaderMessageLoaderStatusResult;
enum { LoaderStatusOk, LoaderStatusErrorInternal };
enum { LoaderEventTypeApplicationStopped, LoaderEventTypeNoMoreAppsInQueue };
typedef struct { int type; } LoaderEvent;
static int event_count, events[3], started, freed_threads;
static char started_name[128], started_args[128];
#define furi_assert(x) assert(x)
#define FURI_LOG_I(...) ((void)0)
#define FURI_LOG_E(...) ((void)0)
static void furi_thread_join(FuriThread* t) { assert(t); }
static void furi_thread_free(FuriThread* t) { assert(t); freed_threads++; }
static void flipper_application_free(FlipperApplication* p) { assert(p); }
static void furi_string_free(FuriString* s) { free(s); }
static FuriString* furi_string_alloc(void) { return calloc(1, sizeof(FuriString)); }
static void furi_pubsub_publish(void* ps, LoaderEvent* e) {
    (void)ps; assert(event_count < 3); events[event_count++] = e->type;
}
static LoaderMessageLoaderStatusResult loader_do_start_by_name(
    Loader* l, const char* name, const char* args, FuriString* error) {
    assert(!l->app.thread && !l->app.launch_path && !l->pending_name && !l->pending_args);
    assert(error && name && args);
    strncpy(started_name, name, sizeof(started_name) - 1);
    strncpy(started_args, args, sizeof(started_args) - 1);
    started++;
    return (LoaderMessageLoaderStatusResult){.value = LoaderStatusOk};
}
static char* copy_text(const char* s) { size_t n = strlen(s) + 1; char* p = malloc(n); memcpy(p,s,n); return p; }
""" + extract_function('loader_do_app_closed', 'void') + r"""
int main(void) {
    FuriThread current = {0}; Loader l = {0};
    l.app.thread = &current; l.app.args = copy_text("old args");
    l.app.launch_path = furi_string_alloc();
    l.pending_name = copy_text("/ext/apps/next.fap");
    l.pending_args = copy_text("next args");
    loader_do_app_closed(&l);
    assert(started == 1 && !strcmp(started_name, "/ext/apps/next.fap"));
    assert(!strcmp(started_args, "next args") && freed_threads == 1);
    assert(!l.pending_name && !l.pending_args && !l.app.thread);
    assert(event_count == 1 && events[0] == LoaderEventTypeApplicationStopped);
    event_count = 0; l.app.thread = &current; loader_do_app_closed(&l);
    assert(event_count == 2 && events[0] == LoaderEventTypeApplicationStopped);
    assert(events[1] == LoaderEventTypeNoMoreAppsInQueue);
    return 0;
}
"""
    c.write_text(close_harness)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('Loader active, idle, locked, signal, name and launch-path host tests passed.')
print('App close starts pending app directly and handles an empty queue.')
