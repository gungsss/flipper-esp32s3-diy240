#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Native-pixel renderer for the ST7735S landscape menu. */
#define MENU160_WIDTH 160u
#define MENU160_HEIGHT 128u

typedef const char* (*Menu160Label)(void* context, size_t index);

typedef struct {
    const char* title;
    size_t count;
    size_t selected;
    Menu160Label label;
    void* context;
} Menu160Model;

/* Use the compatibility path when labels cannot be represented faithfully. */
bool menu160_supported(const Menu160Model* model);

/* Render a strip in RGB565, in native 160x128 pixel coordinates. The buffer
 * must contain at least 160 * rows pixels. No allocation or scaling occurs. */
bool menu160_render_strip(
    uint16_t* pixels,
    size_t pixel_count,
    unsigned first_y,
    unsigned rows,
    const Menu160Model* model);
