#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* One already-decoded, row-major 1-bit frame from the firmware animation.
 * The animation manager, not this renderer, controls timing and interaction. */
typedef struct {
    const uint8_t* bits;
    size_t size_bytes;
    unsigned width;
    unsigned height;
} Home160Frame;

typedef enum {
    /* The caller has not verified the current scene or button mapping. */
    HOME160_HINTS_NONE = 0,
    /* Normal, unlocked home: OK opens menu, down opens archive, up locks. */
    HOME160_HINTS_MAIN,
} Home160Hints;

typedef struct {
    Home160Frame frame;
    /* Optional time supplied by the caller; NULL omits it. */
    const char* time_label;
    /* Optional current animation bubble supplied by its existing manager. */
    const char* bubble_text;
    Home160Hints hints;
} Home160Model;

/* Render one 160-pixel-wide RGB565 strip, without scaling or cropping the
 * provided animation frame. Returns false if it cannot fit or is truncated. */
bool home160_render_strip(
    uint16_t* pixels,
    size_t pixel_count,
    unsigned first_y,
    unsigned rows,
    const Home160Model* model);
