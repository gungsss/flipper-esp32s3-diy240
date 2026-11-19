#include "list160.h"
#include "graphics160.h"

#include <stdio.h>
#include <string.h>

enum { VISIBLE_ITEMS = 4, LABEL_LIMIT = 21, SPLIT_LABEL_LIMIT = 13, VALUE_LIMIT = 7 };

static size_t selected_index(const List160Model* model) {
    return model->count && model->selected >= model->count ? model->count - 1 : model->selected;
}

static size_t first_index(const List160Model* model) {
    size_t selected = selected_index(model);
    size_t first = selected >= VISIBLE_ITEMS ? selected - VISIBLE_ITEMS + 1 : 0;
    if(model->count > VISIBLE_ITEMS && first > model->count - VISIBLE_ITEMS) {
        first = model->count - VISIBLE_ITEMS;
    }
    return first;
}

bool list160_supported(const List160Model* model) {
    if(!model || (model->count && !model->get_item)) return false;
    if(model->title && (!ui160_text_supported(model->title) || strlen(model->title) > 15)) {
        return false;
    }
    size_t first = first_index(model);
    for(size_t row = 0; row < VISIBLE_ITEMS && first + row < model->count; row++) {
        List160Item item = {0};
        if(!model->get_item(model->context, first + row, &item)) return false;
        if(item.separator) continue;
        size_t label_limit = item.has_value || item.locked ? SPLIT_LABEL_LIMIT : LABEL_LIMIT;
        if(!item.label || !ui160_text_supported(item.label) || strlen(item.label) > label_limit) {
            return false;
        }
        if(item.has_value && !item.locked &&
           (!item.value || !ui160_text_supported(item.value) || strlen(item.value) > VALUE_LIMIT)) {
            return false;
        }
    }
    return true;
}

bool list160_render_strip(uint16_t* pixels, size_t pixel_count, unsigned first_y,
                          unsigned rows, const List160Model* model) {
    if(!pixels || !rows || first_y >= UI160_HEIGHT || rows > UI160_HEIGHT - first_y ||
       pixel_count < (size_t)UI160_WIDTH * rows || !list160_supported(model)) return false;

    Ui160Surface s = {.pixels = pixels, .first_y = first_y, .rows = rows};
    for(size_t i = 0; i < (size_t)UI160_WIDTH * rows; i++) pixels[i] = UI160_COLOR_BG;
    ui160_rect(&s, 0, 0, 160, 22, UI160_COLOR_PANEL);
    ui160_rect(&s, 0, 21, 160, 1, UI160_COLOR_LINE);
    ui160_rect(&s, 7, 7, 3, 8, UI160_COLOR_ACCENT);
    ui160_text(&s, 15, 8, model->title ? model->title : "MENU", 15, UI160_COLOR_TEXT);

    size_t selected = selected_index(model);
    char position[16];
    unsigned current = model->count ? (unsigned)(selected < 999 ? selected + 1 : 999) : 0;
    unsigned count = (unsigned)(model->count < 999 ? model->count : 999);
    (void)snprintf(position, sizeof(position), "%u/%u", current, count);
    ui160_text(&s, 153 - (int)strlen(position) * 6, 8, position, 7, UI160_COLOR_MUTED);

    size_t first = first_index(model);
    if(!model->count) ui160_text(&s, 14, 55, "EMPTY", 5, UI160_COLOR_MUTED);
    for(size_t row = 0; row < VISIBLE_ITEMS && first + row < model->count; row++) {
        size_t index = first + row;
        List160Item item = {0};
        if(!model->get_item(model->context, index, &item)) return false;
        int y = 25 + (int)row * 19;
        if(item.separator) {
            ui160_rect(&s, 12, y + 8, 136, 1, UI160_COLOR_LINE);
            continue;
        }
        bool active = index == selected;
        uint16_t ink = active ? UI160_COLOR_INK : UI160_COLOR_TEXT;
        if(active) ui160_rect(&s, 5, y, 150, 17, UI160_COLOR_ACCENT);
        int x = 12;
        if(item.centered && !item.has_value && !item.locked) {
            x = (int)(UI160_WIDTH - strlen(item.label) * 6) / 2;
        }
        ui160_text(&s, x, y + 5, item.label,
                   item.has_value || item.locked ? SPLIT_LABEL_LIMIT : LABEL_LIMIT, ink);
        if(item.locked) {
            ui160_text(&s, 120, y + 5, "LOCK", 4, ink);
        } else if(item.has_value) {
            if(item.can_decrease) ui160_glyph(&s, 94, y + 5, active && model->editing ? '[' : '<', ink);
            ui160_text(&s, 101, y + 5, item.value, VALUE_LIMIT, ink);
            if(item.can_increase) ui160_glyph(&s, 146, y + 5, active && model->editing ? ']' : '>', ink);
        }
    }

    ui160_rect(&s, 0, 107, 160, 21, UI160_COLOR_PANEL);
    ui160_rect(&s, 0, 107, 160, 1, UI160_COLOR_LINE);
    ui160_text(&s, 8, 114, "UP/DN", 5, UI160_COLOR_MUTED);
    ui160_text(&s, 66, 114, "OK", 2, UI160_COLOR_ACCENT);
    ui160_text(&s, 116, 114, "BACK", 4, UI160_COLOR_TEXT);
    return true;
}
