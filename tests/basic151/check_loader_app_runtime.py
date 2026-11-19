#!/usr/bin/env python3
"""Exercise the loader's actual native-app path and app power lifetime."""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

source = (Path(sys.argv[1]) / 'components/loader/loader.c').read_text()


def extract(name, return_type):
    match = re.search(r'(?m)^static\s+' + return_type + r'\s+' + name + r'\s*\([^)]*\)\s*\{', source)
    assert match, name
    index, depth = match.end(), 1
    while depth:
        depth += (source[index] == '{') - (source[index] == '}')
        index += 1
    return source[match.start():index]


scaffold = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define FURI_LOG_I(...) ((void)0)
#define FURI_LOG_E(...) ((void)0)
#define RECORD_STORAGE "storage"
typedef struct {char value[256];} FuriString;
typedef struct {int unused;} FuriThread;
typedef struct {int unused;} Storage;
typedef struct {char name[32];} FlipperApplicationManifest;
typedef struct {int plugin; FlipperApplicationManifest manifest;} FlipperApplication;
typedef struct {struct {FuriThread* thread; FlipperApplication* fap; bool insomniac;} app;} Loader;
typedef enum {LoaderStatusOk, LoaderStatusErrorInternal} LoaderStatus;
typedef enum {LoaderStatusErrorUnknown, LoaderStatusErrorInvalidFile, LoaderStatusErrorInvalidManifest,
              LoaderStatusErrorMissingImports, LoaderStatusErrorHWMismatch, LoaderStatusErrorOutdatedApp,
              LoaderStatusErrorOutOfMemory, LoaderStatusErrorOutdatedFirmware} LoaderStatusError;
typedef struct {LoaderStatus value; LoaderStatusError error;} LoaderMessageLoaderStatusResult;
typedef enum {FlipperInternalApplicationFlagDefault = 0, FlipperInternalApplicationFlagInsomniaSafe = 1} FlipperInternalApplicationFlag;
typedef enum {FuriHalRtcHeapTrackModeNone = 0, TraceOn = 1} FuriHalRtcHeapTrackMode;
typedef enum {FlipperApplicationPreloadStatusSuccess, FlipperApplicationPreloadStatusInvalidFile,
              FlipperApplicationPreloadStatusNotEnoughMemory, FlipperApplicationPreloadStatusInvalidManifest,
              FlipperApplicationPreloadStatusApiTooOld, FlipperApplicationPreloadStatusApiTooNew,
              FlipperApplicationPreloadStatusTargetMismatch} FlipperApplicationPreloadStatus;
typedef enum {FlipperApplicationLoadStatusSuccess, FlipperApplicationLoadStatusMissingImports} FlipperApplicationLoadStatus;
static Storage storage;
static FuriThread thread;
static FlipperApplication application;
static int trace, held, enters, exits, starts, frees, opens, closes, thread_allocs, trace_on, trace_off;
static int fail_alloc, fail_thread;
static FlipperApplicationPreloadStatus preload;
static FlipperApplicationLoadStatus load_status;
static const void* firmware_api_interface;
static FuriHalRtcHeapTrackMode furi_hal_rtc_get_heap_track_mode(void) {return trace ? TraceOn : FuriHalRtcHeapTrackModeNone;}
static void furi_thread_enable_heap_trace(FuriThread* p) {assert(p == &thread); trace_on++;}
static void furi_thread_disable_heap_trace(FuriThread* p) {assert(p == &thread); trace_off++;}
static void furi_hal_power_insomnia_enter(void) {held++; enters++;}
static void furi_hal_power_insomnia_exit(void) {assert(held > 0); held--; exits++;}
static void loader_thread_state_callback(void) {}
static void furi_thread_set_state_context(FuriThread* p, void* c) {assert(p == &thread && c);}
static void furi_thread_set_state_callback(FuriThread* p, void (*cb)(void)) {assert(p == &thread && cb);}
static void furi_thread_start(FuriThread* p) {assert(p == &thread); starts++;}
static void* furi_record_open(const char* name) {assert(!strcmp(name, RECORD_STORAGE)); opens++; return &storage;}
static void furi_record_close(const char* name) {assert(!strcmp(name, RECORD_STORAGE)); closes++;}
static FlipperApplication* flipper_application_alloc(Storage* p, const void* api) {
    assert(p == &storage && api == firmware_api_interface); return fail_alloc ? NULL : &application;
}
static void flipper_application_free(FlipperApplication* p) {assert(p == &application); frees++;}
static FlipperApplicationPreloadStatus flipper_application_preload(FlipperApplication* p, const char* path) {
    assert(p == &application && path); return preload;
}
static const FlipperApplicationManifest* flipper_application_get_manifest(FlipperApplication* p) {return &p->manifest;}
static const char* flipper_application_preload_status_to_string(FlipperApplicationPreloadStatus s) {(void)s; return "preload";}
static FlipperApplicationLoadStatus flipper_application_map_to_memory(FlipperApplication* p) {assert(p == &application); return load_status;}
static const char* flipper_application_load_status_to_string(FlipperApplicationLoadStatus s) {(void)s; return "mapping";}
static bool flipper_application_is_plugin(FlipperApplication* p) {return p->plugin;}
static FuriThread* flipper_application_alloc_thread(FlipperApplication* p, const char* args) {
    assert(p == &application); (void)args; thread_allocs++; return fail_thread ? NULL : &thread;
}
static void furi_thread_set_appid(FuriThread* p, const char* id) {assert(p == &thread && id);}
static FuriString* furi_string_alloc(void) {return calloc(1, sizeof(FuriString));}
static void furi_string_free(FuriString* s) {free(s);}
static const char* furi_string_get_cstr(FuriString* s) {return s->value;}
static void furi_string_set(FuriString* s, const char* v) {snprintf(s->value, sizeof(s->value), "%s", v);}
static void furi_string_printf(FuriString* s, const char* fmt, ...) {
    va_list ap; va_start(ap, fmt); vsnprintf(s->value, sizeof(s->value), fmt, ap); va_end(ap);
}
static void path_extract_filename_no_ext(const char* path, FuriString* out) {furi_string_set(out, path);}
'''

tests = r'''
int main(void) {
    Loader loader = {0}; FuriString error = {0};
    LoaderMessageLoaderStatusResult result;
    fail_alloc = 1;
    result = loader_start_external_fap(&loader, "/ext/app.fap", NULL, &error);
    assert(result.value == LoaderStatusErrorInternal && result.error == LoaderStatusErrorOutOfMemory);
    assert(!loader.app.fap && frees == 0 && enters == 0 && starts == 0);
    fail_alloc = 0; preload = FlipperApplicationPreloadStatusInvalidFile;
    result = loader_start_external_fap(&loader, "/ext/app.fap", NULL, &error);
    assert(result.value == LoaderStatusErrorInternal && result.error == LoaderStatusErrorInvalidFile);
    assert(frees == 1 && enters == 0 && starts == 0);
    preload = FlipperApplicationPreloadStatusSuccess; load_status = FlipperApplicationLoadStatusMissingImports;
    result = loader_start_external_fap(&loader, "/ext/app.fap", NULL, &error);
    assert(result.value == LoaderStatusErrorInternal && result.error == LoaderStatusErrorMissingImports);
    assert(frees == 2 && thread_allocs == 0);
    load_status = FlipperApplicationLoadStatusSuccess; application.plugin = 1;
    result = loader_start_external_fap(&loader, "/ext/plugin.fap", NULL, &error);
    assert(result.value == LoaderStatusErrorInternal);
    assert(strstr(error.value, "not runnable") && frees == 3 && thread_allocs == 0 && starts == 0);
    application.plugin = 0; fail_thread = 1;
    result = loader_start_external_fap(&loader, "/ext/app.fap", NULL, &error);
    assert(result.value == LoaderStatusErrorInternal && result.error == LoaderStatusErrorOutOfMemory);
    assert(!loader.app.fap && frees == 4 && starts == 0 && held == 0);
    fail_thread = 0;
    result = loader_start_external_fap(&loader, "/ext/app.fap", NULL, &error);
    assert(result.value == LoaderStatusOk);
    assert(loader.app.fap == &application && starts == 1 && enters == 1 && held == 1 && trace_off == 1);
    loader_finish_app_thread(&loader); assert(held == 0 && exits == 1 && !loader.app.insomniac);
    loader_finish_app_thread(&loader); assert(exits == 1);
    loader.app.thread = &thread; trace = 1;
    loader_start_app_thread(&loader, FlipperInternalApplicationFlagInsomniaSafe);
    assert(starts == 2 && held == 0 && enters == 1 && trace_on == 1);
    loader_finish_app_thread(&loader); assert(exits == 1);
    assert(opens == closes);
    puts("FAP errors and plugins fail safely; app sleep and heap-trace behavior follows the 1.5.1 loader.");
}
'''

with tempfile.TemporaryDirectory(prefix='esp-loader-app-') as directory:
    temp = Path(directory)
    functions = '\n'.join((
        extract('loader_start_app_thread', 'void'),
        extract('loader_finish_app_thread', 'void'),
        extract('loader_status_error_from_preload_status', 'LoaderStatusError'),
        extract('loader_status_error_from_load_status', 'LoaderStatusError'),
        extract('loader_start_external_fap', 'LoaderMessageLoaderStatusResult'),
    ))
    (temp / 'test.c').write_text(scaffold + functions + tests)
    subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    str(temp / 'test.c'), '-o', str(temp / 'test')], check=True)
    subprocess.run([str(temp / 'test')], env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'}, check=True)
