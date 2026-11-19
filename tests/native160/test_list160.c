#include "list160.h"
#include "graphics160.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { List160Item* items; size_t count; } Fixture;

static bool item_at(void* context, size_t index, List160Item* item) {
    Fixture* f = context;
    if(index >= f->count) return false;
    *item = f->items[index];
    return true;
}

int main(void) {
    List160Item items[] = {
        {.label="Display", .value="ON", .has_value=true, .can_increase=true},
        {.label="Brightness", .value="75%", .has_value=true, .can_increase=true, .can_decrease=true},
        {.separator=true},
        {.label="Password", .locked=true},
        {.label="Centered", .centered=true},
        {.label="About"},
    };
    Fixture fixture = {.items=items, .count=sizeof(items)/sizeof(items[0])};
    List160Model model = {.title="SETTINGS", .count=fixture.count, .selected=1,
                          .get_item=item_at, .context=&fixture};
    size_t count = UI160_WIDTH * UI160_HEIGHT;
    uint16_t* full = calloc(count, sizeof(*full));
    uint16_t* stripes = calloc(count, sizeof(*stripes));
    assert(full && stripes && list160_supported(&model));
    uint16_t glyph_a[160 * 10] = {0}, glyph_A[160 * 10] = {0};
    Ui160Surface a = {.pixels=glyph_a, .first_y=0, .rows=10};
    Ui160Surface A = {.pixels=glyph_A, .first_y=0, .rows=10};
    ui160_glyph(&a, 0, 0, 'a', UI160_COLOR_TEXT);
    ui160_glyph(&A, 0, 0, 'A', UI160_COLOR_TEXT);
    assert(memcmp(glyph_a, glyph_A, sizeof(glyph_a)) != 0);
    assert(list160_render_strip(full, count, 0, UI160_HEIGHT, &model));
    for(unsigned y=0; y<UI160_HEIGHT; y+=10) {
        unsigned rows = UI160_HEIGHT-y < 10 ? UI160_HEIGHT-y : 10;
        assert(list160_render_strip(stripes + (size_t)y*UI160_WIDTH,
                                    count-(size_t)y*UI160_WIDTH, y, rows, &model));
    }
    assert(memcmp(full, stripes, count * sizeof(*full)) == 0);
    /* Selected row, separator, and lock are encoded distinctly. */
    assert(full[44 * UI160_WIDTH + 5] == UI160_COLOR_ACCENT);
    assert(full[71 * UI160_WIDTH + 13] == UI160_COLOR_LINE);
    model.selected = 0;
    assert(list160_render_strip(stripes, count, 0, UI160_HEIGHT, &model));
    assert(memcmp(full, stripes, count * sizeof(*full)) != 0);
    model.selected = 1;
    model.editing = true;
    assert(list160_render_strip(stripes, count, 0, UI160_HEIGHT, &model));
    assert(memcmp(full, stripes, count * sizeof(*full)) != 0);

    /* Unsupported or clipped text must use the original view. */
    items[0].label = "This setting is far too long";
    assert(!list160_supported(&model));
    items[0].label = "Display";
    items[0].value = "ENABLED NOW";
    assert(!list160_supported(&model));
    items[0].value = "ON";
    items[0].label = "Caf\xc3\xa9";
    assert(!list160_supported(&model));
    items[0].label = "Display";
    assert(!list160_render_strip(full, count, 127, 2, &model));
    assert(!list160_render_strip(full, UI160_WIDTH-1, 0, 1, &model));
    assert(!list160_render_strip(NULL, count, 0, 1, &model));
    model.count = 0;
    model.get_item = NULL;
    assert(list160_render_strip(full, count, 0, UI160_HEIGHT, &model));
    free(stripes);
    free(full);
    puts("PASS: native list layout, values, locks, bounds and faithful-text fallback");
}
