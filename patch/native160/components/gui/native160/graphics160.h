#pragma once

#include <stddef.h>
#include <stdint.h>

#define UI160_WIDTH 160u
#define UI160_HEIGHT 128u

typedef struct {
    uint16_t* pixels;
    unsigned first_y;
    unsigned rows;
} Ui160Surface;

enum {
    UI160_COLOR_BG = 0x0843,
    UI160_COLOR_PANEL = 0x10a6,
    UI160_COLOR_LINE = 0x31a9,
    UI160_COLOR_TEXT = 0xf7be,
    UI160_COLOR_MUTED = 0x9cf3,
    UI160_COLOR_ACCENT = 0xfd26,
    UI160_COLOR_INK = 0x0823,
    UI160_COLOR_PAPER = 0xf75a,
};

void ui160_pixel(Ui160Surface* s, int x, int y, uint16_t color);
void ui160_rect(Ui160Surface* s, int x, int y, int width, int height, uint16_t color);
void ui160_glyph(Ui160Surface* s, int x, int y, char ch, uint16_t color);
void ui160_text(Ui160Surface* s, int x, int y, const char* text, size_t limit, uint16_t color);
/* A view may use its legacy renderer if this small font cannot represent a
 * string without substituting a character. */
int ui160_text_supported(const char* text);
