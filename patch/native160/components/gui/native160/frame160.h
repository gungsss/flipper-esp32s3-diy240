#pragma once

#include "present160.h"

#include <stddef.h>
#include <stdint.h>

/* The legacy canvas uses vertical, eight-pixel u8g2 pages. */
#define UI160_LEGACY_WIDTH 128u
#define UI160_LEGACY_HEIGHT 64u
#define UI160_LEGACY_BYTES (UI160_LEGACY_WIDTH * UI160_LEGACY_HEIGHT / 8u)

/* Convert to row-major, LSB-first pixels consumed by home160.  Buffers must
 * not overlap. Invalid lengths leave the destination untouched. */
bool ui160_legacy_frame_to_rows(
    const uint8_t* pages, size_t pages_size, uint8_t* rows, size_t rows_size);

/* The caller owns a synchronous display/strip buffer. The complete composed
 * framebuffer includes the real animation, bubbles and any status overlays. */
Ui160PresentResult ui160_present_legacy_home(
    Ui160Display* display, const uint8_t* pages, size_t pages_size);
