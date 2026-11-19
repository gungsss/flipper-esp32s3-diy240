#!/usr/bin/env python3
"""Check the 1.5.1 SD status initialization and mount/unmount events."""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

text = (Path(sys.argv[1]) / 'applications/services/storage/storage.c').read_text()


def extract(name, return_type):
    match = re.search(r'(?m)^' + return_type + r'\s*' + name + r'\s*\([^)]*\)\s*\{', text)
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
#include <stdio.h>
#include <stdlib.h>
#define FURI_LOG_I(...) ((void)0)
#define CONFIG_T_EMBED_PLUS_SD_RECOVERY 0
#define STORAGE_COUNT 2
#define ST_EXT 1
#define RECORD_GUI "gui"
#define GuiLayerStatusBarLeft 0
#define ViewPortStatusBarIconSdCard 0
typedef struct {int unused;} Canvas;
typedef struct {int unused;} StorageMessage;
typedef struct {bool enabled;} ViewPort;
typedef struct {int unused;} Gui;
typedef struct {int unused;} Icon;
static const Icon mounted_icon = {0};
#define ICON_SD_MOUNTED (&mounted_icon)
typedef enum {StorageStatusNotReady, StorageStatusOK, StorageStatusNotMounted,
    StorageStatusNoFS, StorageStatusNotAccessible, StorageStatusErrorInternal} StorageStatus;
typedef enum {StorageEventTypeCardUnmount, StorageEventTypeCardMount, StorageEventTypeCardMountError} StorageEventType;
typedef struct {StorageEventType type;} StorageEvent;
typedef struct StorageData StorageData;
typedef struct {void (*tick)(StorageData*);} StorageApi;
struct StorageData {StorageStatus status; StorageApi api;};
typedef struct {
    void* message_queue; void* pubsub;
    StorageData storage[STORAGE_COUNT];
    struct {bool enabled; ViewPort* view_port;} sd_gui;
} Storage;
static StorageStatus initial_status;
static StorageEventType last_event;
static int event_count, viewport_changes;
static ViewPort viewport;
static Gui gui;
static int queue, pubsub;
static void* furi_message_queue_alloc(int count, size_t size) {assert(count == 8 && size == sizeof(StorageMessage)); return &queue;}
static void* furi_pubsub_alloc(void) {return &pubsub;}
static void storage_data_init(StorageData* p) {p->status = StorageStatusNotReady; p->api.tick = NULL;}
static void storage_data_timestamp(StorageData* p) {assert(p);}
static void storage_ext_init(StorageData* p) {p->status = initial_status;}
static ViewPort* view_port_alloc(void) {viewport.enabled = false; return &viewport;}
static int icon_get_width(const Icon* p) {assert(p == ICON_SD_MOUNTED); return 11;}
static void view_port_set_width(ViewPort* p, int width) {assert(p == &viewport && width == 11);}
static void storage_app_sd_icon_draw_callback(Canvas* c, void* p) {(void)c; (void)p;}
static void view_port_draw_callback_set(ViewPort* p, void (*cb)(Canvas*, void*), void* ctx) {assert(p && cb && ctx);}
static void view_port_set_statusbar_icon(ViewPort* p, int i) {assert(p == &viewport && i == 0);}
static void view_port_enabled_set(ViewPort* p, bool enabled) {assert(p == &viewport); p->enabled = enabled; viewport_changes++;}
static void* furi_record_open(const char* name) {(void)name; return &gui;}
static void furi_record_close(const char* name) {(void)name;}
static void gui_add_view_port(Gui* g, ViewPort* p, int layer) {assert(g == &gui && p == &viewport && layer == 0);}
static void furi_pubsub_publish(void* p, const StorageEvent* event) {assert(p == &pubsub); last_event = event->type; event_count++;}
'''

tests = r'''
int main(void) {
    initial_status = StorageStatusOK;
    Storage* app = storage_app_alloc(); assert(app->sd_gui.enabled && viewport.enabled);
    storage_tick(app); assert(event_count == 0);
    app->storage[ST_EXT].status = StorageStatusNotReady;
    storage_tick(app); assert(event_count == 1 && last_event == StorageEventTypeCardUnmount && !viewport.enabled);
    storage_tick(app); assert(event_count == 1);
    app->storage[ST_EXT].status = StorageStatusOK;
    storage_tick(app); assert(event_count == 2 && last_event == StorageEventTypeCardMount && viewport.enabled);
    free(app);
    event_count = 0; initial_status = StorageStatusNotMounted;
    app = storage_app_alloc(); assert(app->sd_gui.enabled && viewport.enabled);
    storage_tick(app); assert(event_count == 0); free(app);
    initial_status = StorageStatusNotReady;
    app = storage_app_alloc(); assert(!app->sd_gui.enabled && !viewport.enabled);
    app->storage[ST_EXT].status = StorageStatusNoFS;
    storage_tick(app); assert(event_count == 1 && last_event == StorageEventTypeCardMountError);
    assert(viewport_changes > 0); free(app);
    puts("1.5.1 SD initialization avoids false mount events and reports real transitions.");
}
'''

functions = '\n'.join((extract('storage_app_alloc', r'Storage\*'), extract('storage_tick', 'void')))
with tempfile.TemporaryDirectory(prefix='esp-151-storage-') as directory:
    temp = Path(directory)
    (temp / 'test.c').write_text(stub + functions + tests)
    subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
                    '-fno-omit-frame-pointer', str(temp / 'test.c'), '-o', str(temp / 'test')], check=True)
    subprocess.run([str(temp / 'test')], env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'}, check=True)
