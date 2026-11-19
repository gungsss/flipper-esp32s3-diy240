#include "present160.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint16_t* received;
    unsigned calls;
    unsigned fail_at;
} Transport;

static bool fake_flush(void* context, unsigned y, unsigned rows, const uint16_t* pixels) {
    Transport* t = context;
    t->calls++;
    assert(y == (t->calls - 1) * UI160_STRIP_ROWS);
    assert(rows == (y == 120 ? 8u : 10u));
    if(t->calls == t->fail_at) return false;
    memcpy(t->received + (size_t)y * MENU160_WIDTH, pixels,
           (size_t)rows * MENU160_WIDTH * sizeof(*pixels));
    return true;
}

static const char* get_label(void* context, size_t index) {
    (void)context;
    const char* labels[] = {"Browser", "Applications", "Settings"};
    return index < 3 ? labels[index] : NULL;
}

static uint16_t swap(uint16_t pixel) {
    return (uint16_t)((pixel << 8) | (pixel >> 8));
}

int main(int argc, char** argv) {
    assert(argc == 2);
    uint8_t frame[16 * 47];
    FILE* f = fopen(argv[1], "rb");
    assert(f && fread(frame, 1, sizeof(frame), f) == sizeof(frame));
    assert(fclose(f) == 0);
    const size_t count = MENU160_WIDTH * MENU160_HEIGHT;
    uint16_t* expected = calloc(count, sizeof(*expected));
    uint16_t* output = calloc(count, sizeof(*output));
    uint16_t* dma = calloc(UI160_DMA_PIXELS, sizeof(*dma));
    assert(expected && output && dma);
    Transport transport = {.received = output};
    Ui160Display display = {.dma_pixels = dma,
                            .capacity_pixels = UI160_DMA_PIXELS,
                            .flush = fake_flush,
                            .context = &transport,
                            .swap_rgb565_bytes = true};
    Menu160Model menu = {.title = "MENU", .count = 3, .selected = 1, .label = get_label};

    assert(menu160_render_strip(expected, count, 0, MENU160_HEIGHT, &menu));
    assert(ui160_present_menu(&display, &menu) == UI160_PRESENT_OK);
    assert(transport.calls == 13);
    for(size_t i = 0; i < count; i++) assert(output[i] == swap(expected[i]));

    Home160Model home = {.frame = {.bits = frame, .size_bytes = sizeof(frame),
                                    .width = 128, .height = 47},
                         .hints = HOME160_HINTS_MAIN};
    transport.calls = 0;
    display.swap_rgb565_bytes = false;
    assert(home160_render_strip(expected, count, 0, MENU160_HEIGHT, &home));
    assert(ui160_present_home(&display, &home) == UI160_PRESENT_OK);
    assert(transport.calls == 13);
    assert(memcmp(output, expected, count * sizeof(*output)) == 0);

    transport.calls = 0;
    transport.fail_at = 3;
    assert(ui160_present_home(&display, &home) == UI160_PRESENT_TRANSPORT_ERROR);
    assert(transport.calls == 3);
    transport.calls = 0;
    transport.fail_at = 0;
    assert(ui160_present_home(&display, &home) == UI160_PRESENT_OK);
    assert(memcmp(output, expected, count * sizeof(*output)) == 0);

    transport.calls = 0;
    display.capacity_pixels--;
    assert(ui160_present_home(&display, &home) == UI160_PRESENT_INVALID);
    assert(transport.calls == 0);
    display.capacity_pixels++;
    home.frame.size_bytes--;
    assert(ui160_present_home(&display, &home) == UI160_PRESENT_INVALID);
    assert(transport.calls == 0);
    assert(ui160_present_home(NULL, &home) == UI160_PRESENT_INVALID);
    free(dma);
    free(output);
    free(expected);
    puts("PASS: native strips, RGB565 byte order and failed-transfer retry");
    return 0;
}
