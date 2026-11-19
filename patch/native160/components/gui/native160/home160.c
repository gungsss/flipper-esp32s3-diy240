#include "home160.h"
#include "graphics160.h"

enum { ART_MAX_WIDTH = 136, ART_MAX_HEIGHT = 64 };

static void draw_bubble(Ui160Surface* surface, const char* text) {
    if(!text || !*text) return;
    char lines[2][22] = {{0}};
    size_t row = 0, col = 0;
    while(*text && row < 2) {
        if(*text == '\n') {
            row++;
            col = 0;
        } else if(col < 20) {
            lines[row][col++] = *text;
        } else {
            lines[row][17] = lines[row][18] = lines[row][19] = '.';
            while(text[1] && text[1] != '\n') text++;
        }
        text++;
    }
    const int height = lines[1][0] ? 23 : 15;
    size_t longest = 0;
    for(size_t line = 0; line < 2; line++) {
        size_t n = 0;
        while(lines[line][n]) n++;
        if(n > longest) longest = n;
    }
    const int width = (int)longest * 6 + 10;
    ui160_rect(surface, 9, 29, width, height, UI160_COLOR_INK);
    ui160_rect(surface, 10, 30, width - 2, height - 2, UI160_COLOR_PANEL);
    ui160_text(surface, 13, 33, lines[0], 20, UI160_COLOR_TEXT);
    if(lines[1][0]) ui160_text(surface, 13, 41, lines[1], 20, UI160_COLOR_TEXT);
    ui160_rect(surface, 20, 29 + height, 5, 1, UI160_COLOR_INK);
    ui160_rect(surface, 21, 30 + height, 3, 1, UI160_COLOR_INK);
    ui160_pixel(surface, 22, 31 + height, UI160_COLOR_INK);
}

bool home160_render_strip(
    uint16_t* pixels,
    size_t pixel_count,
    unsigned first_y,
    unsigned rows,
    const Home160Model* model) {
    if(!pixels || !model || !rows || first_y >= UI160_HEIGHT ||
       rows > UI160_HEIGHT - first_y || pixel_count < (size_t)UI160_WIDTH * rows) {
        return false;
    }
    const Home160Frame* frame = &model->frame;
    const bool has_frame = frame->bits != NULL;
    size_t bytes_per_row = 0;
    if(has_frame) {
        if(!frame->width || !frame->height || frame->width > ART_MAX_WIDTH ||
           frame->height > ART_MAX_HEIGHT) {
            return false;
        }
        bytes_per_row = (frame->width + 7u) / 8u;
        if(frame->size_bytes < bytes_per_row * frame->height) return false;
    } else if(frame->size_bytes || frame->width || frame->height) {
        return false;
    }
    if(model->hints != HOME160_HINTS_NONE && model->hints != HOME160_HINTS_MAIN) return false;

    Ui160Surface s = {.pixels = pixels, .first_y = first_y, .rows = rows};
    for(size_t i = 0; i < (size_t)UI160_WIDTH * rows; i++) pixels[i] = UI160_COLOR_BG;

    /* Optional status is supplied by firmware, never manufactured. */
    ui160_rect(&s, 0, 0, 160, 22, UI160_COLOR_PANEL);
    ui160_rect(&s, 0, 21, 160, 1, UI160_COLOR_LINE);
    ui160_rect(&s, 7, 7, 3, 8, UI160_COLOR_ACCENT);
    ui160_text(&s, 15, 8, "FLIPPER", 7, UI160_COLOR_TEXT);
    if(model->time_label) ui160_text(&s, 119, 8, model->time_label, 5, UI160_COLOR_MUTED);

    /* Frame artwork is exactly one display pixel per source pixel. */
    ui160_rect(&s, 5, 25, 150, 77, UI160_COLOR_LINE);
    ui160_rect(&s, 6, 26, 148, 75, UI160_COLOR_PAPER);
    if(has_frame) {
        const int x0 = ((int)UI160_WIDTH - (int)frame->width) / 2;
        const int y0 = 26 + (75 - (int)frame->height) / 2;
        int start = (int)first_y - y0;
        int end = (int)(first_y + rows) - y0;
        if(start < 0) start = 0;
        if(end > (int)frame->height) end = (int)frame->height;
        for(int y = start; y < end; y++) {
            for(unsigned x = 0; x < frame->width; x++) {
                const uint8_t byte = frame->bits[(size_t)y * bytes_per_row + x / 8u];
                if(byte & (uint8_t)(1u << (x % 8u))) {
                    ui160_pixel(&s, x0 + (int)x, y0 + y, UI160_COLOR_INK);
                }
            }
        }
    } else {
        ui160_text(&s, 49, 61, "MEMUAT...", 9, UI160_COLOR_INK);
    }
    draw_bubble(&s, model->bubble_text);

    ui160_rect(&s, 0, 107, 160, 21, UI160_COLOR_PANEL);
    ui160_rect(&s, 0, 107, 160, 1, UI160_COLOR_LINE);
    if(model->hints == HOME160_HINTS_MAIN) {
        ui160_text(&s, 6, 114, "OK", 2, UI160_COLOR_ACCENT);
        ui160_text(&s, 20, 114, "MENU", 4, UI160_COLOR_TEXT);
        ui160_text(&s, 54, 114, "DN", 2, UI160_COLOR_ACCENT);
        ui160_text(&s, 68, 114, "ARSIP", 5, UI160_COLOR_TEXT);
        ui160_text(&s, 107, 114, "UP", 2, UI160_COLOR_ACCENT);
        ui160_text(&s, 121, 114, "KUNCI", 5, UI160_COLOR_TEXT);
    }
    return true;
}
