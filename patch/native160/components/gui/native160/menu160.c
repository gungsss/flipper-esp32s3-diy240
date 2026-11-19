#include "menu160.h"
#include "graphics160.h"

#include <stdio.h>
#include <string.h>

bool menu160_supported(const Menu160Model* model) {
    if(!model || (model->count && !model->label)) return false;
    if(model->title && (!ui160_text_supported(model->title) || strlen(model->title) > 15)) return false;
    size_t selected = model->count && model->selected >= model->count ? model->count - 1 : model->selected;
    size_t first = selected >= 4 ? selected - 3 : 0;
    if(model->count > 4 && first > model->count - 4) first = model->count - 4;
    for(size_t row = 0; row < 4 && first + row < model->count; row++) {
        const char* label = model->label(model->context, first + row);
        if(!label || !ui160_text_supported(label) || strlen(label) > 19) return false;
    }
    return true;
}

bool menu160_render_strip(
    uint16_t* pixels,
    size_t pixel_count,
    unsigned first_y,
    unsigned rows,
    const Menu160Model* model) {
    if(!pixels || !model || rows == 0 || first_y >= UI160_HEIGHT ||
       rows > UI160_HEIGHT - first_y ||
       pixel_count < (size_t)UI160_WIDTH * rows ||
       !menu160_supported(model)) {
        return false;
    }

    Ui160Surface s = {.pixels = pixels, .first_y = first_y, .rows = rows};
    for(size_t i = 0; i < (size_t)UI160_WIDTH * rows; i++) pixels[i] = UI160_COLOR_BG;

    /* Header uses real menu position; no fabricated clock/battery/radio state. */
    ui160_rect(&s, 0, 0, 160, 22, UI160_COLOR_PANEL);
    ui160_rect(&s, 0, 21, 160, 1, UI160_COLOR_LINE);
    ui160_rect(&s, 7, 7, 3, 8, UI160_COLOR_ACCENT);
    ui160_text(&s, 15, 8, model->title ? model->title : "MENU", 15, UI160_COLOR_TEXT);

    const size_t selected = model->count && model->selected >= model->count ?
                                model->count - 1 : model->selected;
    char position[16];
    unsigned current = model->count ? (unsigned)(selected < 999 ? selected + 1 : 999) : 0;
    unsigned count = (unsigned)(model->count < 999 ? model->count : 999);
    (void)snprintf(position, sizeof(position), "%u/%u", current, count);
    size_t position_len = 0;
    while(position[position_len]) position_len++;
    ui160_text(&s, 153 - (int)position_len * 6, 8, position, 7, UI160_COLOR_MUTED);

    const size_t visible = 4;
    size_t first = selected >= visible ? selected - visible + 1 : 0;
    if(model->count > visible && first > model->count - visible) first = model->count - visible;
    if(!model->count) ui160_text(&s, 14, 55, "BELUM ADA APLIKASI", 22, UI160_COLOR_MUTED);

    for(size_t row = 0; row < visible && row < model->count; row++) {
        size_t index = first + row;
        if(index >= model->count) break;
        const int y = 25 + (int)row * 19;
        const bool active = index == selected;
        if(active) {
            ui160_rect(&s, 5, y, 150, 17, UI160_COLOR_ACCENT);
            ui160_rect(&s, 5, y, 2, 2, UI160_COLOR_BG);
            ui160_rect(&s, 153, y, 2, 2, UI160_COLOR_BG);
            ui160_rect(&s, 5, y + 15, 2, 2, UI160_COLOR_BG);
            ui160_rect(&s, 153, y + 15, 2, 2, UI160_COLOR_BG);
        }
        const char* label = model->label(model->context, index);
        if(!label) label = "?";
        uint16_t ink = active ? UI160_COLOR_INK : UI160_COLOR_TEXT;
        ui160_rect(&s, 11, y + 4, 9, 9, active ? UI160_COLOR_INK : UI160_COLOR_LINE);
        ui160_rect(&s, 12, y + 5, 7, 7, active ? UI160_COLOR_ACCENT : UI160_COLOR_BG);
        ui160_glyph(&s, 13, y + 5, label[0] ? label[0] : '?', ink);
        ui160_text(&s, 27, y + 5, label, 19, ink);
        if(active) {
            ui160_pixel(&s, 145, y + 6, ink);
            ui160_pixel(&s, 146, y + 7, ink);
            ui160_pixel(&s, 147, y + 8, ink);
            ui160_pixel(&s, 146, y + 9, ink);
            ui160_pixel(&s, 145, y + 10, ink);
        }
    }

    /* Footer describes only the physical navigation for this menu view. */
    ui160_rect(&s, 0, 107, 160, 21, UI160_COLOR_PANEL);
    ui160_rect(&s, 0, 107, 160, 1, UI160_COLOR_LINE);
    ui160_pixel(&s, 9, 113, UI160_COLOR_MUTED);
    ui160_rect(&s, 8, 114, 3, 1, UI160_COLOR_MUTED);
    ui160_rect(&s, 7, 115, 5, 1, UI160_COLOR_MUTED);
    ui160_rect(&s, 7, 117, 5, 1, UI160_COLOR_MUTED);
    ui160_rect(&s, 8, 118, 3, 1, UI160_COLOR_MUTED);
    ui160_pixel(&s, 9, 119, UI160_COLOR_MUTED);
    ui160_text(&s, 16, 114, "PILIH", 5, UI160_COLOR_TEXT);
    ui160_text(&s, 52, 114, "OK", 2, UI160_COLOR_ACCENT);
    ui160_text(&s, 67, 114, "BUKA", 4, UI160_COLOR_TEXT);
    ui160_text(&s, 98, 114, "SET", 3, UI160_COLOR_ACCENT);
    ui160_text(&s, 119, 114, "BACK", 4, UI160_COLOR_TEXT);
    return true;
}
