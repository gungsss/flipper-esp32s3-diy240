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
    'loader_enqueue_launch': ('void', 'Loader*, const char*, const char*, LoaderDeferredLaunchFlag'),
    'loader_clear_launch_queue': ('void', 'Loader*'),
    'loader_start_with_gui_error': ('LoaderStatus', 'Loader*, const char*, const char*'),
    'loader_start_detached_with_gui_error': ('void', 'Loader*, const char*, const char*'),
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
queue_source = (source / 'components/loader/loader_queue.c').read_text()
functions = []
def extract_function(name, return_type, text=actual, static=True):
    match = re.search(r'(?m)^' + ('static ' if static else '') + return_type + ' ' +
                      name + r'\([^)]*\) \{', text)
    assert match, name
    depth, i = 1, match.end()
    while depth and i < len(text):
        if text[i] == '{': depth += 1
        if text[i] == '}': depth -= 1
        i += 1
    assert depth == 0, name
    return text[match.start():i]

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
typedef enum { LoaderDeferredLaunchFlagNone = 0, LoaderDeferredLaunchFlagGui = (1 << 1) } LoaderDeferredLaunchFlag;
typedef struct { char* name_or_path; char* args; LoaderDeferredLaunchFlag flags; } LoaderDeferredLaunchRecord;
typedef struct { LoaderDeferredLaunchRecord items[4]; size_t item_cnt; } LoaderLaunchQueue;
#define LOADER_QUEUE_MAX_SIZE 4
typedef struct {
    struct { FuriString* launch_path; char* args; FuriThread* thread; FlipperApplication* fap; } app;
    LoaderLaunchQueue launch_queue;
    char* pending_name; char* pending_args; void* pubsub;
} Loader;
typedef struct { int value; } LoaderMessageLoaderStatusResult;
enum { LoaderStatusOk, LoaderStatusErrorInternal };
enum { LoaderEventTypeApplicationStopped, LoaderEventTypeNoMoreAppsInQueue };
typedef struct { int type; } LoaderEvent;
static int event_count, events[10], started, freed_threads;
static int failed_attempts;
static int dialogs_shown;
static FuriThread started_thread;
static char started_name[128], started_args[128];
#define furi_assert(x) assert(x)
#define FURI_LOG_I(...) ((void)0)
#define FURI_LOG_E(...) ((void)0)
static void furi_thread_join(FuriThread* t) { assert(t); }
static void furi_thread_free(FuriThread* t) { assert(t); freed_threads++; }
static void flipper_application_free(FlipperApplication* p) { assert(p); }
static void furi_string_free(FuriString* s) { free(s); }
static FuriString* furi_string_alloc(void) { return calloc(1, sizeof(FuriString)); }
static void loader_show_gui_error(int status, FuriString* error) { assert(status && error); dialogs_shown++; }
static void furi_pubsub_publish(void* ps, LoaderEvent* e) {
    (void)ps; assert(event_count < 10); events[event_count++] = e->type;
}
static LoaderMessageLoaderStatusResult loader_do_start_by_name(
    Loader* l, const char* name, const char* args, FuriString* error) {
    assert(!l->app.thread && !l->app.launch_path && !l->pending_name && !l->pending_args);
    assert(error && name && args);
    if(!strcmp(name, "broken")) {
        failed_attempts++;
        return (LoaderMessageLoaderStatusResult){.value = LoaderStatusErrorInternal};
    }
    strncpy(started_name, name, sizeof(started_name) - 1);
    strncpy(started_args, args, sizeof(started_args) - 1);
    started++;
    l->app.thread = &started_thread;
    return (LoaderMessageLoaderStatusResult){.value = LoaderStatusOk};
}
static char* copy_text(const char* s) { size_t n = strlen(s) + 1; char* p = malloc(n); memcpy(p,s,n); return p; }
""" + '\n'.join(extract_function(n, ret, queue_source, False) for n, ret in (
    ('loader_queue_item_clear', 'void'), ('loader_queue_pop', 'bool'),
    ('loader_queue_push', 'bool'), ('loader_queue_clear', 'void'))) + '\n' + \
    extract_function('loader_start_deferred_item', 'bool') + '\n' + \
    extract_function('loader_do_app_closed', 'void') + r"""
int main(void) {
    FuriThread current = {0}; Loader l = {0};
    l.app.thread = &current; l.app.args = copy_text("old args");
    l.app.launch_path = furi_string_alloc();
    l.pending_name = copy_text("/ext/apps/next.fap");
    l.pending_args = copy_text("next args");
    LoaderDeferredLaunchRecord one = {copy_text("one"), copy_text("a"), 0};
    LoaderDeferredLaunchRecord two = {copy_text("two"), copy_text("b"), 0};
    assert(loader_queue_push(&l.launch_queue, &one));
    assert(loader_queue_push(&l.launch_queue, &two));
    loader_do_app_closed(&l);
    assert(started == 1 && !strcmp(started_name, "/ext/apps/next.fap"));
    assert(!strcmp(started_args, "next args") && freed_threads == 1);
    assert(!l.pending_name && !l.pending_args && l.app.thread == &started_thread);
    assert(l.launch_queue.item_cnt == 2);
    assert(event_count == 1 && events[0] == LoaderEventTypeApplicationStopped);
    loader_do_app_closed(&l);
    assert(started == 2 && !strcmp(started_name, "one") && !strcmp(started_args, "a"));
    assert(l.launch_queue.item_cnt == 1);
    loader_do_app_closed(&l);
    assert(started == 3 && !strcmp(started_name, "two") && !strcmp(started_args, "b"));
    assert(l.launch_queue.item_cnt == 0);
    event_count = 0; loader_do_app_closed(&l);
    assert(event_count == 2 && events[0] == LoaderEventTypeApplicationStopped);
    assert(events[1] == LoaderEventTypeNoMoreAppsInQueue);
    l.app.thread = &current;
    LoaderDeferredLaunchRecord bad = {copy_text("broken"), copy_text("arg"), 0};
    LoaderDeferredLaunchRecord good = {copy_text("next-good"), copy_text("arg"), 0};
    assert(loader_queue_push(&l.launch_queue, &bad));
    assert(loader_queue_push(&l.launch_queue, &good));
    loader_do_app_closed(&l);
    assert(failed_attempts == 1 && started == 4 && !strcmp(started_name, "next-good"));
    assert(dialogs_shown == 0);
    l.app.thread = &current;
    bad = (LoaderDeferredLaunchRecord){copy_text("broken"), copy_text("arg"), LoaderDeferredLaunchFlagGui};
    good = (LoaderDeferredLaunchRecord){copy_text("another"), copy_text("arg"), 0};
    assert(loader_queue_push(&l.launch_queue, &bad));
    assert(loader_queue_push(&l.launch_queue, &good));
    loader_do_app_closed(&l);
    assert(failed_attempts == 2 && started == 5 && dialogs_shown == 1);
    for(unsigned i=0; i<4; ++i) {
        LoaderDeferredLaunchRecord item = {copy_text("full"), copy_text("arg"), 0};
        assert(loader_queue_push(&l.launch_queue, &item));
    }
    LoaderDeferredLaunchRecord extra = {copy_text("extra"), copy_text("arg"), 0};
    assert(!loader_queue_push(&l.launch_queue, &extra));
    loader_queue_item_clear(&extra);
    loader_queue_clear(&l.launch_queue);
    assert(l.launch_queue.item_cnt == 0);
    return 0;
}
"""
    c.write_text(close_harness)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
    api_harness = r"""
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define furi_check(x) assert(x)
#define LOADER_QUEUE_MAX_SIZE 4
typedef enum { LoaderDeferredLaunchFlagNone = 0, LoaderDeferredLaunchFlagGui = (1 << 1) } LoaderDeferredLaunchFlag;
typedef struct { char* name_or_path; char* args; LoaderDeferredLaunchFlag flags; } LoaderDeferredLaunchRecord;
typedef struct { LoaderDeferredLaunchRecord items[4]; size_t item_cnt; } LoaderLaunchQueue;
typedef struct { LoaderLaunchQueue launch_queue; } Loader;
enum { LoaderMessageTypeEnqueueLaunch, LoaderMessageTypeClearLaunchQueue };
typedef struct { int type; LoaderDeferredLaunchRecord defer_start; } LoaderMessage;
""" + '\n'.join(extract_function(n, ret, queue_source, False) for n, ret in (
    ('loader_queue_item_clear', 'void'), ('loader_queue_pop', 'bool'),
    ('loader_queue_push', 'bool'), ('loader_queue_clear', 'void'))) + r"""
static void loader_generic_synchronous_request(Loader* loader, LoaderMessage* message) {
    assert(loader);
    if(message->type == LoaderMessageTypeEnqueueLaunch) {
        assert(loader_queue_push(&loader->launch_queue, &message->defer_start));
    } else {
        assert(message->type == LoaderMessageTypeClearLaunchQueue);
        loader_queue_clear(&loader->launch_queue);
    }
}
""" + extract_function('loader_enqueue_launch', 'void', actual, False) + '\n' + \
    extract_function('loader_clear_launch_queue', 'void', actual, False) + r"""
int main(void) {
    Loader l = {0};
    char name[] = "app-one", args[] = "argument";
    loader_enqueue_launch(&l, name, args, LoaderDeferredLaunchFlagGui);
    name[0] = 'X'; args[0] = 'Y';
    assert(l.launch_queue.item_cnt == 1);
    assert(!strcmp(l.launch_queue.items[0].name_or_path, "app-one"));
    assert(!strcmp(l.launch_queue.items[0].args, "argument"));
    assert(l.launch_queue.items[0].flags == LoaderDeferredLaunchFlagGui);
    loader_enqueue_launch(&l, "app-two", NULL, LoaderDeferredLaunchFlagNone);
    assert(l.launch_queue.item_cnt == 2 && l.launch_queue.items[1].args == NULL);
    loader_clear_launch_queue(&l);
    assert(l.launch_queue.item_cnt == 0);
    return 0;
}
"""
    c.write_text(api_harness)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
    gui_harness = r"""
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
typedef struct { const char* text; } FuriString;
typedef struct { int unused; } DialogsApp;
typedef struct { int unused; } DialogMessage;
typedef enum { LoaderStatusOk, LoaderStatusErrorAppStarted, LoaderStatusErrorUnknownApp } LoaderStatus;
enum { AlignCenter, AlignTop };
#define RECORD_DIALOGS "dialogs"
static DialogsApp app;
static DialogMessage message;
static int opens, closes, shows;
static char displayed[128];
static void* furi_record_open(const char* name) { assert(!strcmp(name, RECORD_DIALOGS)); opens++; return &app; }
static void furi_record_close(const char* name) { assert(!strcmp(name, RECORD_DIALOGS)); closes++; }
static DialogMessage* dialog_message_alloc(void) { return &message; }
static void dialog_message_free(DialogMessage* m) { assert(m == &message); }
static void dialog_message_set_header(DialogMessage* m, const char* s, int x, int y, int a, int b) {
    assert(m && s); (void)x; (void)y; (void)a; (void)b;
}
static bool furi_string_empty(const FuriString* s) { return !s->text || !s->text[0]; }
static const char* furi_string_get_cstr(const FuriString* s) { return s->text; }
static void dialog_message_set_text(DialogMessage* m, const char* s, int x, int y, int a, int b) {
    assert(m && s); snprintf(displayed, sizeof(displayed), "%s", s); (void)x; (void)y; (void)a; (void)b;
}
static void dialog_message_set_buttons(DialogMessage* m, const char* l, const char* c, const char* r) {
    assert(m && !l && !c && r);
}
static int dialog_message_show(DialogsApp* a, DialogMessage* m) { assert(a == &app && m == &message); shows++; return 0; }
""" + extract_function('loader_show_gui_error', 'void') + r"""
int main(void) {
    FuriString error = {"open failed"};
    loader_show_gui_error(LoaderStatusOk, &error);
    loader_show_gui_error(LoaderStatusErrorAppStarted, &error);
    assert(!opens && !closes && !shows);
    loader_show_gui_error(LoaderStatusErrorUnknownApp, &error);
    assert(opens == 1 && closes == 1 && shows == 1 && !strcmp(displayed, "open failed"));
    error.text = "";
    loader_show_gui_error(LoaderStatusErrorUnknownApp, &error);
    assert(opens == 2 && closes == 2 && shows == 2 && !strcmp(displayed, "Application unavailable"));
    return 0;
}
"""
    c.write_text(gui_harness)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('Loader active, idle, locked, signal, name and launch-path host tests passed.')
print('Deferred FIFO ordering, argument ownership, full/clear and app-close behavior passed.')
print('Error dialog behavior and empty-message fallback passed.')
