#!/usr/bin/env python3
"""Verify the loader reports the real reason an ESP app cannot start."""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

source = (Path(sys.argv[1]) / 'components/loader/loader.c').read_text()
match = re.search(r'(?m)^static void loader_show_gui_error\s*\([^)]*\)\s*\{', source)
assert match
pos, depth = match.end(), 1
while depth:
    depth += (source[pos] == '{') - (source[pos] == '}')
    pos += 1
function = source[match.start():pos]

stub = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
typedef enum {LoaderStatusOk, LoaderStatusErrorAppStarted, LoaderStatusErrorUnknownApp, LoaderStatusErrorInternal} LoaderStatus;
typedef enum {LoaderStatusErrorUnknown, LoaderStatusErrorInvalidFile, LoaderStatusErrorInvalidManifest,
    LoaderStatusErrorMissingImports, LoaderStatusErrorHWMismatch, LoaderStatusErrorOutdatedApp,
    LoaderStatusErrorOutOfMemory, LoaderStatusErrorOutdatedFirmware} LoaderStatusError;
typedef struct {LoaderStatus value; LoaderStatusError error;} LoaderMessageLoaderStatusResult;
typedef struct {const char* text;} FuriString;
typedef struct {int unused;} Storage;
typedef struct {int unused;} DialogsApp;
typedef struct {int unused;} DialogMessage;
typedef struct {int id;} Icon;
enum {AlignCenter, AlignTop, AlignLeft, FSE_OK};
#define RECORD_DIALOGS "dialogs"
#define RECORD_STORAGE "storage"
static const Icon I_WarningDolphinFlip_45x42 = {1}, I_err_02 = {2}, I_err_03 = {3},
                  I_err_04 = {4}, I_err_05 = {5}, I_err_06 = {6};
static Storage storage;
static DialogsApp dialogs;
static DialogMessage message;
static int shown, open_count, close_count, storage_status;
static char title[100], detail[256];
static const Icon* observed_icon;
static const char* loader_find_external_application_by_name(const char* name) {
    return !strcmp(name, "Notes") ? "/ext/notes.fap" : NULL;
}
static void* furi_record_open(const char* name) {
    open_count++; return !strcmp(name, RECORD_STORAGE) ? (void*)&storage : (void*)&dialogs;
}
static void furi_record_close(const char* name) {(void)name; close_count++;}
static bool furi_string_empty(const FuriString* p) {return !p->text || !p->text[0];}
static const char* furi_string_get_cstr(const FuriString* p) {return p->text;}
static int storage_sd_status(Storage* p) {assert(p == &storage); return storage_status;}
static DialogMessage* dialog_message_alloc(void) {return &message;}
static void dialog_message_free(DialogMessage* p) {assert(p == &message);}
static void dialog_message_set_header(DialogMessage* p, const char* s, int x, int y, int h, int v) {
    assert(p == &message); (void)x; (void)y; (void)h; (void)v; snprintf(title, sizeof(title), "%s", s);
}
static void dialog_message_set_text(DialogMessage* p, const char* s, int x, int y, int h, int v) {
    assert(p == &message); (void)x; (void)y; (void)h; (void)v; snprintf(detail, sizeof(detail), "%s", s);
}
static void dialog_message_set_icon(DialogMessage* p, const Icon* icon, int x, int y) {
    assert(p == &message); (void)x; (void)y; observed_icon = icon;
}
static void dialog_message_set_buttons(DialogMessage* p, const char* l, const char* c, const char* r) {
    assert(p == &message && !l && !c && !strcmp(r, "OK"));
}
static void dialog_message_show(DialogsApp* d, DialogMessage* p) {assert(d == &dialogs && p == &message); shown++;}
'''

tests = r'''
int main(void) {
    FuriString error = {.text = "Application not found"};
    LoaderMessageLoaderStatusResult status = {.value = LoaderStatusOk};
    loader_show_gui_error(status, "Notes", &error); assert(shown == 0);
    status.value = LoaderStatusErrorAppStarted;
    loader_show_gui_error(status, "Notes", &error); assert(shown == 0);
    status.value = LoaderStatusErrorUnknownApp; storage_status = 1;
    loader_show_gui_error(status, "Notes", &error);
    assert(shown == 1 && !strcmp(title, "SD card needed") && observed_icon == &I_WarningDolphinFlip_45x42);
    storage_status = FSE_OK;
    loader_show_gui_error(status, "Notes", &error); assert(shown == 2 && !strcmp(title, "App not found"));
    status.value = LoaderStatusErrorInternal; status.error = LoaderStatusErrorHWMismatch;
    loader_show_gui_error(status, "test.fap", &error);
    assert(shown == 3 && !strcmp(title, "Target mismatch") && strstr(detail, "ESP32"));
    status.error = LoaderStatusErrorMissingImports;
    loader_show_gui_error(status, "test.fap", &error);
    assert(shown == 4 && !strcmp(title, "Missing imports") && observed_icon == &I_err_04);
    status.error = LoaderStatusErrorOutOfMemory;
    loader_show_gui_error(status, "test.fap", &error); assert(shown == 5 && !strcmp(title, "Out of memory"));
    assert(open_count == close_count);
    puts("Loader dialogs distinguish missing SD, incompatible apps, missing imports and memory failures.");
}
'''

with tempfile.TemporaryDirectory(prefix='esp-loader-dialog-') as directory:
    temp = Path(directory)
    (temp / 'test.c').write_text(stub + function + tests)
    subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
                    '-fno-omit-frame-pointer', str(temp / 'test.c'), '-o', str(temp / 'test')], check=True)
    subprocess.run([str(temp / 'test')], env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'}, check=True)
