#include "frame160.h"

#include <string.h>

bool ui160_legacy_frame_to_rows(
    const uint8_t* pages, size_t pages_size, uint8_t* rows, size_t rows_size) {
    if(!pages || !rows || pages_size < UI160_LEGACY_BYTES || rows_size < UI160_LEGACY_BYTES) {
        return false;
    }
    memset(rows, 0, UI160_LEGACY_BYTES);
    for(unsigned y = 0; y < UI160_LEGACY_HEIGHT; y++) {
        for(unsigned x = 0; x < UI160_LEGACY_WIDTH; x++) {
            const uint8_t page = pages[(y / 8u) * UI160_LEGACY_WIDTH + x];
            if(page & (uint8_t)(1u << (y % 8u))) {
                rows[y * (UI160_LEGACY_WIDTH / 8u) + x / 8u] |= (uint8_t)(1u << (x % 8u));
            }
        }
    }
    return true;
}

Ui160PresentResult ui160_present_legacy_home(
    Ui160Display* display, const uint8_t* pages, size_t pages_size) {
    uint8_t rows[UI160_LEGACY_BYTES];
    if(!ui160_legacy_frame_to_rows(pages, pages_size, rows, sizeof(rows))) {
        return UI160_PRESENT_INVALID;
    }
    const Home160Model model = {
        .frame = {
            .bits = rows,
            .size_bytes = sizeof(rows),
            .width = UI160_LEGACY_WIDTH,
            .height = UI160_LEGACY_HEIGHT,
        },
        .time_label = NULL,
        .bubble_text = NULL,
        .hints = HOME160_HINTS_NONE,
    };
    return ui160_present_home(display, &model);
}
