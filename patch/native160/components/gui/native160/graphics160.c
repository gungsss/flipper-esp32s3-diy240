#include "graphics160.h"
#include <stdbool.h>

/* Hand-drawn 5x7 glyphs, one row per byte, most significant pixel at bit 4. */
typedef struct {
    char character;
    uint8_t row[7];
} Glyph;

static const Glyph glyphs[] = {
    {' ', {0, 0, 0, 0, 0, 0, 0}},
    {'A', {14, 17, 17, 31, 17, 17, 17}}, {'B', {30, 17, 17, 30, 17, 17, 30}},
    {'C', {14, 17, 16, 16, 16, 17, 14}}, {'D', {30, 17, 17, 17, 17, 17, 30}},
    {'E', {31, 16, 16, 30, 16, 16, 31}}, {'F', {31, 16, 16, 30, 16, 16, 16}},
    {'G', {14, 17, 16, 23, 17, 17, 15}}, {'H', {17, 17, 17, 31, 17, 17, 17}},
    {'I', {31, 4, 4, 4, 4, 4, 31}}, {'J', {7, 2, 2, 2, 2, 18, 12}},
    {'K', {17, 18, 20, 24, 20, 18, 17}}, {'L', {16, 16, 16, 16, 16, 16, 31}},
    {'M', {17, 27, 21, 21, 17, 17, 17}}, {'N', {17, 25, 21, 19, 17, 17, 17}},
    {'O', {14, 17, 17, 17, 17, 17, 14}}, {'P', {30, 17, 17, 30, 16, 16, 16}},
    {'Q', {14, 17, 17, 17, 21, 18, 13}}, {'R', {30, 17, 17, 30, 20, 18, 17}},
    {'S', {15, 16, 16, 14, 1, 1, 30}}, {'T', {31, 4, 4, 4, 4, 4, 4}},
    {'U', {17, 17, 17, 17, 17, 17, 14}}, {'V', {17, 17, 17, 17, 17, 10, 4}},
    {'W', {17, 17, 17, 21, 21, 21, 10}}, {'X', {17, 17, 10, 4, 10, 17, 17}},
    {'Y', {17, 17, 10, 4, 4, 4, 4}}, {'Z', {31, 1, 2, 4, 8, 16, 31}},
    {'a', {0, 0, 14, 1, 15, 17, 15}}, {'b', {16, 16, 22, 25, 17, 17, 30}},
    {'c', {0, 0, 14, 17, 16, 17, 14}}, {'d', {1, 1, 13, 19, 17, 17, 15}},
    {'e', {0, 0, 14, 17, 31, 16, 14}}, {'f', {6, 9, 8, 28, 8, 8, 8}},
    {'g', {0, 15, 17, 17, 15, 1, 14}}, {'h', {16, 16, 22, 25, 17, 17, 17}},
    {'i', {4, 0, 12, 4, 4, 4, 14}}, {'j', {2, 0, 6, 2, 2, 18, 12}},
    {'k', {16, 16, 18, 20, 24, 20, 18}}, {'l', {12, 4, 4, 4, 4, 4, 14}},
    {'m', {0, 0, 26, 21, 21, 21, 21}}, {'n', {0, 0, 22, 25, 17, 17, 17}},
    {'o', {0, 0, 14, 17, 17, 17, 14}}, {'p', {0, 0, 30, 17, 30, 16, 16}},
    {'q', {0, 0, 13, 19, 15, 1, 1}}, {'r', {0, 0, 22, 25, 16, 16, 16}},
    {'s', {0, 0, 15, 16, 14, 1, 30}}, {'t', {8, 8, 28, 8, 8, 9, 6}},
    {'u', {0, 0, 17, 17, 17, 19, 13}}, {'v', {0, 0, 17, 17, 17, 10, 4}},
    {'w', {0, 0, 17, 17, 21, 21, 10}}, {'x', {0, 0, 17, 10, 4, 10, 17}},
    {'y', {0, 0, 17, 17, 15, 1, 14}}, {'z', {0, 0, 31, 2, 4, 8, 31}},
    {'0', {14, 17, 19, 21, 25, 17, 14}}, {'1', {4, 12, 4, 4, 4, 4, 14}},
    {'2', {14, 17, 1, 2, 4, 8, 31}}, {'3', {30, 1, 1, 14, 1, 1, 30}},
    {'4', {2, 6, 10, 18, 31, 2, 2}}, {'5', {31, 16, 16, 30, 1, 1, 30}},
    {'6', {14, 16, 16, 30, 17, 17, 14}}, {'7', {31, 1, 2, 4, 8, 8, 8}},
    {'8', {14, 17, 17, 14, 17, 17, 14}}, {'9', {14, 17, 17, 15, 1, 1, 14}},
    {'.', {0, 0, 0, 0, 0, 6, 6}}, {':', {0, 6, 6, 0, 6, 6, 0}},
    {'-', {0, 0, 0, 31, 0, 0, 0}}, {'_', {0, 0, 0, 0, 0, 0, 31}},
    {'/', {1, 1, 2, 4, 8, 16, 16}}, {'+', {0, 4, 4, 31, 4, 4, 0}},
    {'?', {14, 17, 1, 2, 4, 0, 4}}, {'(', {2, 4, 8, 8, 8, 4, 2}},
    {')', {8, 4, 2, 2, 2, 4, 8}}, {'!', {4, 4, 4, 4, 4, 0, 4}},
    {'[', {14, 8, 8, 8, 8, 8, 14}}, {']', {14, 2, 2, 2, 2, 2, 14}},
    {'<', {1, 2, 4, 8, 4, 2, 1}}, {'>', {16, 8, 4, 2, 4, 8, 16}},
    {'%', {17, 2, 4, 4, 8, 17, 0}}, {'=', {0, 0, 31, 0, 31, 0, 0}},
};

void ui160_pixel(Ui160Surface* s, int x, int y, uint16_t color) {
    if(x < 0 || x >= (int)UI160_WIDTH || y < (int)s->first_y ||
       y >= (int)(s->first_y + s->rows)) {
        return;
    }
    s->pixels[(size_t)(y - (int)s->first_y) * UI160_WIDTH + (unsigned)x] = color;
}

void ui160_rect(Ui160Surface* s, int x, int y, int width, int height, uint16_t color) {
    if(width <= 0 || height <= 0) return;
    const int x_begin = x > 0 ? x : 0;
    const int x_end = x + width < (int)UI160_WIDTH ? x + width : (int)UI160_WIDTH;
    const int y_begin = y > (int)s->first_y ? y : (int)s->first_y;
    const int stripe_end = (int)(s->first_y + s->rows);
    const int y_end = y + height < stripe_end ? y + height : stripe_end;
    for(int row = y_begin; row < y_end; row++) {
        for(int col = x_begin; col < x_end; col++) {
            s->pixels[(size_t)(row - (int)s->first_y) * UI160_WIDTH + (unsigned)col] = color;
        }
    }
}

static const uint8_t* glyph_for(char ch) {
    for(size_t i = 0; i < sizeof(glyphs) / sizeof(glyphs[0]); i++) {
        if(glyphs[i].character == ch) return glyphs[i].row;
    }
    /* '?' is always present and is the fallback for unsupported bytes. */
    for(size_t i = 0; i < sizeof(glyphs) / sizeof(glyphs[0]); i++) {
        if(glyphs[i].character == '?') return glyphs[i].row;
    }
    return glyphs[0].row;
}

int ui160_text_supported(const char* text) {
    if(!text) return 0;
    while(*text) {
        char ch = *text++;
        bool found = false;
        for(size_t i = 0; i < sizeof(glyphs) / sizeof(glyphs[0]); i++) {
            if(glyphs[i].character == ch) {
                found = true;
                break;
            }
        }
        if(!found) return 0;
    }
    return 1;
}

void ui160_glyph(Ui160Surface* s, int x, int y, char ch, uint16_t color) {
    const uint8_t* rows = glyph_for(ch);
    for(int row = 0; row < 7; row++) {
        for(int col = 0; col < 5; col++) {
            if(rows[row] & (1u << (4 - col))) ui160_pixel(s, x + col, y + row, color);
        }
    }
}

void ui160_text(Ui160Surface* s, int x, int y, const char* str, size_t limit, uint16_t color) {
    if(!str) return;
    size_t length = 0;
    while(length <= limit && str[length]) length++;
    const bool truncated = length > limit;
    const size_t text_length = truncated && limit > 3 ? limit - 3 : length;
    for(size_t i = 0; i < text_length && i < limit; i++) {
        ui160_glyph(s, x + (int)i * 6, y, str[i], color);
    }
    if(truncated && limit >= 3) {
        for(size_t i = 0; i < 3; i++) {
            ui160_glyph(s, x + (int)(limit - 3 + i) * 6, y, '.', color);
        }
    }
}

