#include "frame160.h"
#include "graphics160.h"

#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

typedef struct {
    uint16_t* pixels;
    unsigned calls;
    unsigned fail_at;
} FakePanel;

static bool flush(void* context, unsigned y, unsigned rows, const uint16_t* pixels) {
    FakePanel* panel = context;
    panel->calls++;
    if(panel->calls == panel->fail_at) return false;
    memcpy(panel->pixels + y * UI160_WIDTH, pixels, rows * UI160_WIDTH * sizeof(*pixels));
    return true;
}

int main(void) {
    uint8_t pages[UI160_LEGACY_BYTES];
    uint8_t rows[UI160_LEGACY_BYTES];
    for(size_t i = 0; i < sizeof(pages); i++) pages[i] = (uint8_t)(i * 37u + i / 13u);
    memset(rows, 0xA5, sizeof(rows));
    assert(!ui160_legacy_frame_to_rows(pages, sizeof(pages) - 1, rows, sizeof(rows)));
    for(size_t i = 0; i < sizeof(rows); i++) assert(rows[i] == 0xA5);
    assert(!ui160_legacy_frame_to_rows(pages, sizeof(pages), rows, sizeof(rows) - 1));
    assert(!ui160_legacy_frame_to_rows(NULL, sizeof(pages), rows, sizeof(rows)));
    assert(!ui160_legacy_frame_to_rows(pages, sizeof(pages), NULL, sizeof(rows)));
    assert(ui160_legacy_frame_to_rows(pages, sizeof(pages), rows, sizeof(rows)));
    for(unsigned y = 0; y < UI160_LEGACY_HEIGHT; y++) {
        for(unsigned x = 0; x < UI160_LEGACY_WIDTH; x++) {
            bool source = (pages[(y / 8u) * UI160_LEGACY_WIDTH + x] >> (y % 8u)) & 1u;
            bool target = (rows[y * 16u + x / 8u] >> (x % 8u)) & 1u;
            assert(source == target);
        }
    }

    uint16_t* output = calloc(UI160_WIDTH * UI160_HEIGHT, sizeof(*output));
    uint16_t* dma = calloc(UI160_DMA_PIXELS, sizeof(*dma));
    assert(output && dma);
    FakePanel panel = {.pixels = output};
    Ui160Display display = {
        .dma_pixels = dma, .capacity_pixels = UI160_DMA_PIXELS,
        .flush = flush, .context = &panel, .swap_rgb565_bytes = false,
    };
    assert(ui160_present_legacy_home(&display, pages, sizeof(pages)) == UI160_PRESENT_OK);
    assert(panel.calls == 13);
    const unsigned x0 = (UI160_WIDTH - UI160_LEGACY_WIDTH) / 2u;
    const unsigned y0 = 26u + (75u - UI160_LEGACY_HEIGHT) / 2u;
    for(unsigned y = 0; y < UI160_LEGACY_HEIGHT; y++) {
        for(unsigned x = 0; x < UI160_LEGACY_WIDTH; x++) {
            bool source = (pages[(y / 8u) * UI160_LEGACY_WIDTH + x] >> (y % 8u)) & 1u;
            assert(output[(y0 + y) * UI160_WIDTH + x0 + x] ==
                   (source ? UI160_COLOR_INK : UI160_COLOR_PAPER));
        }
    }
    panel.calls = 0;
    panel.fail_at = 3;
    assert(ui160_present_legacy_home(&display, pages, sizeof(pages)) ==
           UI160_PRESENT_TRANSPORT_ERROR);
    assert(panel.calls == 3);
    panel.calls = 0;
    panel.fail_at = 0;
    assert(ui160_present_legacy_home(&display, pages, sizeof(pages)) == UI160_PRESENT_OK);
    assert(panel.calls == 13);
    free(dma);
    free(output);
    puts("PASS: legacy animation framebuffer conversion, native rendering and retry");
}
