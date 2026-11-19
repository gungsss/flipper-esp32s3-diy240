#include "canvas_i.h"
#include "native160/native160_canvas.h"
#include "native160/graphics160.h"
#include "native160/present160.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned width = 160, height = 128, calls, fail_at, alloc_count, legacy_commits;
static bool sleeping, allocation_fails;
static uint16_t framebuffer[160 * 128];

uint16_t furi_hal_display_get_h_res(void) { return (uint16_t)width; }
uint16_t furi_hal_display_get_v_res(void) { return (uint16_t)height; }
bool furi_hal_display_is_asleep(void) { return sleeping; }
void furi_hal_display_commit(const uint8_t* pixels, uint32_t size) {
    assert(pixels != NULL && size == 1024);
    legacy_commits++;
}
void* heap_caps_malloc(size_t size, unsigned caps) {
    assert(caps == 3);
    alloc_count++;
    return allocation_fails ? NULL : malloc(size);
}
bool furi_hal_display_draw_rgb565(
    uint16_t x, uint16_t y, uint16_t w, uint16_t h, const uint16_t* pixels) {
    assert(x == 0 && w == 160 && y + h <= 128);
    calls++;
    if(calls == fail_at) return false;
    memcpy(&framebuffer[(size_t)y * 160], pixels, (size_t)w * h * sizeof(*pixels));
    return true;
}
CanvasOrientation canvas_get_orientation(const Canvas* canvas) { return canvas->orientation; }
uint8_t* canvas_get_buffer(Canvas* canvas) { return canvas->fb.bytes; }
size_t canvas_get_buffer_size(const Canvas* canvas) { return sizeof(canvas->fb.bytes); }

static const char* label(void* context, size_t index) {
    const char* const* labels = context;
    return labels[index];
}
static bool list_item(void* context, size_t index, List160Item* item) {
    const char* const* labels = context;
    if(index >= 3) return false;
    *item = (List160Item){.label=labels[index]};
    return true;
}
static uint16_t swap(uint16_t pixel) { return (uint16_t)((pixel << 8) | (pixel >> 8)); }

int main(void) {
    Canvas canvas = {.width = 128, .height = 64, .orientation = CanvasOrientationHorizontal};
    const char* labels[] = {"Applications", "Settings", "Archive"};
    Menu160Model model = {.title = "MENU", .count = 3, .selected = 1,
                          .label = label, .context = labels};
    assert(native160_panel_supported());
    native160_canvas_mark_home(&canvas);
    assert(canvas.native160_home_pending);
    canvas.offset_x = 17; /* A status-bar viewport can change the canvas frame after home draw. */
    canvas.width = 10;
    canvas.height = 13;
    canvas.fb.bytes[0] = 1;
    assert(native160_canvas_present_home(&canvas));
    assert(calls == 13 && alloc_count == 1);
    assert(framebuffer[31 * 160 + 16] == swap(UI160_COLOR_INK));
    assert(framebuffer[31 * 160 + 17] == swap(UI160_COLOR_PAPER));

    canvas.offset_x = 0; canvas.width = 128; canvas.height = 64;
    calls = 0;
    assert(native160_canvas_present_menu(&canvas, &model));
    assert(canvas.native160_menu_presented && calls == 13 && alloc_count == 1);
    uint16_t expected[160 * 128];
    assert(menu160_render_strip(expected, 160 * 128, 0, 128, &model));
    for(size_t i = 0; i < 160u * 128u; i++) assert(framebuffer[i] == swap(expected[i]));
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(!canvas.native160_menu_presented && !canvas.native160_home_pending && legacy_commits == 0);

    /* If a later layer changes the framebuffer, the completed frame wins. */
    calls = 0;
    assert(native160_canvas_present_menu(&canvas, &model));
    canvas.fb.bytes[0] = 0;
    canvas.fb.bytes[1] = 1;
    calls = 0;
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(calls == 13 && legacy_commits == 0);
    assert(framebuffer[31 * 160 + 16] == swap(UI160_COLOR_PAPER));
    assert(framebuffer[31 * 160 + 17] == swap(UI160_COLOR_INK));
    canvas.fb.bytes[0] = 1;
    canvas.fb.bytes[1] = 0;

    List160Model list = {.title="SETTINGS", .count=3, .selected=2,
                         .get_item=list_item, .context=labels};
    calls = 0;
    assert(native160_canvas_present_list(&canvas, &list));
    assert(calls == 13 && canvas.native160_menu_presented);
    uint16_t expected_list[160 * 128];
    assert(list160_render_strip(expected_list, 160 * 128, 0, 128, &list));
    for(size_t i=0; i<160u*128u; i++) assert(framebuffer[i] == swap(expected_list[i]));
    calls = 0;
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(calls == 0 && legacy_commits == 0);

    canvas.native160_menu_presented = false;
    calls = 0; fail_at = 3;
    assert(!native160_canvas_present_menu(&canvas, &model));
    assert(!canvas.native160_menu_presented && calls == 3);
    calls = 0; fail_at = 0;
    assert(native160_canvas_present_menu(&canvas, &model) && calls == 13);
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(legacy_commits == 0);

    native160_canvas_mark_home(&canvas);
    calls = 0; fail_at = 3;
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    /* A single failed native transfer retries as a 1:1 compatibility view. */
    assert(legacy_commits == 0 && calls == 16 && !canvas.native160_home_pending);
    calls = 0; fail_at = 0;
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(legacy_commits == 0 && calls == 13);
    assert(framebuffer[31 * 160 + 16] == swap(UI160_COLOR_INK));
    assert(framebuffer[31 * 160 + 17] == swap(UI160_COLOR_PAPER));

    /* On a further SPI error, the board-specific HAL path repaints 1:1. */
    calls = 0; fail_at = 3;
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(legacy_commits == 1 && calls == 3);
    fail_at = 0;

    canvas.native160_home_pending = false;
    canvas.orientation = CanvasOrientationHorizontalFlip;
    native160_canvas_mark_home(&canvas);
    assert(!canvas.native160_home_pending && !native160_canvas_present_menu(&canvas, &model));
    calls = 0;
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(calls == 13 && legacy_commits == 1);
    canvas.orientation = CanvasOrientationHorizontal;
    width = 240;
    assert(!native160_panel_supported() && !native160_canvas_present_home(&canvas));
    calls = 0;
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(calls == 0 && legacy_commits == 2);
    width = 160;
    sleeping = true;
    assert(!native160_canvas_present_home(&canvas));
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(calls == 0 && legacy_commits == 2);
    sleeping = false;
    free(canvas.native160_dma);
    canvas.native160_dma = NULL;
    allocation_fails = true;
    assert(!native160_canvas_present_home(&canvas));
    assert(canvas.native160_dma == NULL);
    native160_canvas_commit(&canvas, canvas.fb.bytes, sizeof(canvas.fb.bytes));
    assert(calls == 0 && legacy_commits == 3);
    puts("PASS: firmware canvas adapter, panel bounds, DMA failure and native transition");
}
