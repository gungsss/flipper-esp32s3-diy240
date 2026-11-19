#!/usr/bin/env python3
"""Run the 1.5.1 GUI entry points used by apps against representative state."""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

root = Path(sys.argv[1])


def extract(path, name, return_type):
    text = (root / path).read_text()
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
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define furi_check(x) assert(x)
#define furi_assert(x) assert(x)
typedef struct {const char* label;} VariableItem;
typedef struct {int views;} ViewDispatcher;
static int present;
static void* ViewDict_get(int occupied, uint32_t id) {return occupied && id == 42 ? &present : NULL;}
typedef struct {uint8_t data[1024];} FakeFramebuffer;
typedef struct {FakeFramebuffer fb;} Canvas;
static uint8_t* u8g2_GetBufferPtr(FakeFramebuffer* fb) {return fb->data;}
static size_t u8g2_GetBufferTileWidth(const FakeFramebuffer* fb) {(void)fb; return 16;}
static size_t u8g2_GetBufferTileHeight(const FakeFramebuffer* fb) {(void)fb; return 8;}
typedef struct {int id;} ViewPort;
typedef struct {ViewPort* items[8]; size_t count;} ViewPortArray;
typedef struct {ViewPortArray* array; size_t index;} Iter;
typedef Iter ViewPortArray_it_t[1];
typedef enum {Layer0, Layer1, GuiLayerMAX} GuiLayer;
typedef struct {ViewPortArray layers[GuiLayerMAX][1];} Gui;
static int locks, unlocks, updates;
static void gui_lock(Gui* p) {assert(p); locks++;}
static void gui_unlock(Gui* p) {assert(p); unlocks++;}
static void gui_update(Gui* p) {assert(p); updates++;}
static void ViewPortArray_it(ViewPortArray_it_t it, ViewPortArray* arr) {it->array = arr; it->index = 0;}
static bool ViewPortArray_end_p(ViewPortArray_it_t it) {return it->index >= it->array->count;}
static ViewPort** ViewPortArray_ref(ViewPortArray_it_t it) {return &it->array->items[it->index];}
static void ViewPortArray_next(ViewPortArray_it_t it) {it->index++;}
static void ViewPortArray_remove(ViewPortArray* arr, ViewPortArray_it_t it) {
    assert(arr == it->array && it->index < arr->count);
    memmove(&arr->items[it->index], &arr->items[it->index + 1],
            (arr->count - it->index - 1) * sizeof(arr->items[0])); arr->count--;
}
static void ViewPortArray_push_at(ViewPortArray* arr, size_t index, ViewPort* item) {
    assert(index <= arr->count && arr->count < 8);
    memmove(&arr->items[index + 1], &arr->items[index], (arr->count - index) * sizeof(arr->items[0]));
    arr->items[index] = item; arr->count++;
}
'''

tests = r'''
int main(void) {
    VariableItem item = {.label = "old"}; variable_item_set_item_label(&item, "new"); assert(!strcmp(item.label, "new"));
    ViewDispatcher dispatcher = {.views = 1};
    assert(!view_dispatcher_check_id(&dispatcher, 42));
    assert(view_dispatcher_check_id(&dispatcher, 43));
    Canvas canvas = {0}; assert(canvas_get_buffer(&canvas) == canvas.fb.data);
    assert(canvas_get_buffer_size(&canvas) == sizeof(canvas.fb.data));
    ViewPort a = {1}, b = {2}, c = {3}, other = {4}; Gui gui = {0};
    ViewPortArray* layer = gui.layers[Layer1];
    layer->items[0] = &a; layer->items[1] = &b; layer->items[2] = &c; layer->count = 3;
    gui.layers[Layer0]->items[0] = &other; gui.layers[Layer0]->count = 1;
    gui_view_port_send_to_back(&gui, &b);
    assert(layer->count == 3 && layer->items[0] == &b && layer->items[1] == &a && layer->items[2] == &c);
    assert(gui.layers[Layer0]->items[0] == &other && locks == 1 && unlocks == 1 && updates == 1);
    puts("1.5.1 canvas, item label, view ID and view ordering APIs pass behavior checks.");
}
'''

functions = '\n'.join((
    extract('components/gui/modules/variable_item_list.c', 'variable_item_set_item_label', 'void'),
    extract('components/gui/view_dispatcher.c', 'view_dispatcher_check_id', 'bool'),
    extract('components/gui/canvas.c', 'canvas_get_buffer', r'uint8_t\*'),
    extract('components/gui/canvas.c', 'canvas_get_buffer_size', 'size_t'),
    extract('components/gui/gui.c', 'gui_view_port_send_to_back', 'void'),
))
with tempfile.TemporaryDirectory(prefix='esp-151-gui-') as directory:
    temp = Path(directory)
    (temp / 'test.c').write_text(stub + functions + tests)
    subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
                    '-fno-omit-frame-pointer', str(temp / 'test.c'), '-o', str(temp / 'test')], check=True)
    subprocess.run([str(temp / 'test')], env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'}, check=True)
