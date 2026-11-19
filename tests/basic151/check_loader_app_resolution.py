#!/usr/bin/env python3
"""Exercise real loader selection for internal, named, and storage apps."""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

text = (Path(sys.argv[1]) / 'components/loader/loader.c').read_text()


def extract(name, return_type):
    match = re.search(r'(?m)^static\s+' + return_type + r'\s+' + name + r'\s*\([^)]*\)\s*\{', text)
    assert match, name
    pos, depth = match.end(), 1
    while depth:
        depth += (text[pos] == '{') - (text[pos] == '}')
        pos += 1
    return text[match.start():pos]


stub = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define furi_check(x) assert(x)
#define esp_rom_printf(...) ((void)0)
#define FURI_LOG_E(...) ((void)0)
#define RECORD_STORAGE "storage"
#define LOADER_APPLICATIONS_NAME "Apps"
#define LOADER_MAGIC_THREAD_VALUE 0xDEADBEEF
typedef struct {char text[256];} FuriString;
typedef struct {int unused;} Storage;
typedef struct {int unused;} FuriThread;
typedef struct {int unused;} FuriPubSub;
typedef enum {LoaderStatusOk, LoaderStatusErrorAppStarted, LoaderStatusErrorUnknownApp, LoaderStatusErrorInternal} LoaderStatus;
typedef enum {LoaderStatusErrorUnknown} LoaderStatusError;
typedef struct {LoaderStatus value; LoaderStatusError error;} LoaderMessageLoaderStatusResult;
typedef struct {const char* name; const char* appid; size_t stack_size;} FlipperInternalApplication;
typedef struct {const char* name; const void* icon; const char* path;} FlipperExternalApplication;
typedef enum {LoaderEventTypeApplicationBeforeLoad, LoaderEventTypeApplicationLoadFailed,
              LoaderEventTypeNoMoreAppsInQueue} LoaderEventType;
typedef struct {LoaderEventType type;} LoaderEvent;
typedef struct {
    struct {FuriThread* thread; FuriString* launch_path;} app;
    const char* pending_name;
    struct {int item_cnt;} launch_queue;
    FuriPubSub* pubsub;
} Loader;
static const FlipperExternalApplication FLIPPER_EXTERNAL_APPS[] = {
    {"Notes", NULL, "/ext/apps/notes.fap"}, {"Other", NULL, "/ext/apps/other.fap"}
};
static const size_t FLIPPER_EXTERNAL_APPS_COUNT = 2;
static Storage storage;
static FuriThread thread;
static FuriPubSub pubsub;
static FlipperInternalApplication internal = {"Internal", "internal", 4096};
static int opens, closes, internal_starts, external_starts, app_views, before, failed, empty;
static bool exists;
static LoaderStatus external_result = LoaderStatusOk;
static char seen_path[256];
static void* furi_record_open(const char* name) {assert(!strcmp(name, RECORD_STORAGE)); opens++; return &storage;}
static void furi_record_close(const char* name) {assert(!strcmp(name, RECORD_STORAGE)); closes++;}
static bool storage_file_exists(Storage* s, const char* path) {assert(s == &storage && path); return exists;}
static bool loader_do_is_locked(Loader* l) {return l->app.thread != NULL;}
static void loader_do_applications_show(Loader* l) {assert(l); app_views++;}
static void furi_pubsub_publish(FuriPubSub* p, const LoaderEvent* e) {
    assert(p == &pubsub);
    if(e->type == LoaderEventTypeApplicationBeforeLoad) before++;
    else if(e->type == LoaderEventTypeApplicationLoadFailed) failed++;
    else if(e->type == LoaderEventTypeNoMoreAppsInQueue) empty++;
}
static const FlipperInternalApplication* loader_find_application_by_name(const char* name) {
    return !strcmp(name, "Internal") ? &internal : NULL;
}
static void loader_start_internal_app(Loader* l, const FlipperInternalApplication* app, const char* args) {
    assert(app == &internal); (void)args; internal_starts++; l->app.thread = &thread;
}
static LoaderMessageLoaderStatusResult loader_start_external_fap(Loader* l, const char* path, const char* args, FuriString* error) {
    (void)args; (void)error; external_starts++; snprintf(seen_path, sizeof(seen_path), "%s", path);
    if(external_result == LoaderStatusOk) l->app.thread = &thread;
    return (LoaderMessageLoaderStatusResult){.value = external_result, .error = LoaderStatusErrorUnknown};
}
static FuriString* furi_string_alloc_set_str(const char* s) {
    FuriString* p = calloc(1, sizeof(FuriString)); assert(p); snprintf(p->text, sizeof(p->text), "%s", s); return p;
}
static void furi_string_set(FuriString* p, const char* s) {snprintf(p->text, sizeof(p->text), "%s", s);}
static void furi_string_printf(FuriString* p, const char* fmt, ...) {
    va_list ap; va_start(ap, fmt); vsnprintf(p->text, sizeof(p->text), fmt, ap); va_end(ap);
}
'''

tests = r'''
static void clear(Loader* l) {free(l->app.launch_path); l->app.launch_path = NULL; l->app.thread = NULL;}
int main(void) {
    Loader l = {.pubsub = &pubsub}; FuriString error = {0};
    assert(loader_do_start_by_name(&l, "Internal", NULL, &error).value == LoaderStatusOk);
    assert(internal_starts == 1 && opens == 0 && !strcmp(l.app.launch_path->text, "Internal")); clear(&l);
    assert(loader_do_start_by_name(&l, "Apps", NULL, &error).value == LoaderStatusOk);
    assert(app_views == 1 && opens == 0); clear(&l);
    exists = true;
    assert(loader_do_start_by_name(&l, "Notes", NULL, &error).value == LoaderStatusOk);
    assert(external_starts == 1 && !strcmp(seen_path, "/ext/apps/notes.fap"));
    assert(!strcmp(l.app.launch_path->text, "/ext/apps/notes.fap")); clear(&l);
    assert(loader_do_start_by_name(&l, "/ext/app-without-extension", NULL, &error).value == LoaderStatusOk);
    assert(external_starts == 2 && !strcmp(seen_path, "/ext/app-without-extension")); clear(&l);
    exists = false;
    assert(loader_do_start_by_name(&l, "Other", NULL, &error).value == LoaderStatusErrorUnknownApp);
    assert(external_starts == 2 && failed == 1 && empty == 1);
    exists = true; external_result = LoaderStatusErrorInternal;
    assert(loader_do_start_by_name(&l, "Notes", NULL, &error).value == LoaderStatusErrorInternal);
    assert(failed == 2 && empty == 2 && !l.app.launch_path);
    l.app.thread = &thread;
    assert(loader_do_start_by_name(&l, "Notes", NULL, &error).value == LoaderStatusErrorAppStarted);
    assert(failed == 2 && opens == closes);
    puts("Internal, named external and direct-file launches follow the 1.5.1 loader path.");
}
'''

with tempfile.TemporaryDirectory(prefix='esp-loader-resolve-') as directory:
    temp = Path(directory)
    functions = '\n'.join((extract('loader_find_external_application_by_name', r'const char\*'),
                           extract('loader_find_existing_external_path', r'const char\*'),
                           extract('loader_do_start_by_name', 'LoaderMessageLoaderStatusResult')))
    (temp / 'test.c').write_text(stub + functions + tests)
    subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
                    '-fno-omit-frame-pointer', str(temp / 'test.c'), '-o', str(temp / 'test')], check=True)
    subprocess.run([str(temp / 'test')], env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'}, check=True)
