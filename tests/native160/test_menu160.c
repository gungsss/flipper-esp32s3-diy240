#include "menu160.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char* labels[] = {
    "Browser", "Applications", "Bluetooth", "Settings", "Wi-Fi", "Storage", "Tools", "Info",
};

static const char* get_label(void* context, size_t index) {
    (void)context;
    return index < sizeof(labels) / sizeof(labels[0]) ? labels[index] : NULL;
}

static const char* unsupported_label(void* context, size_t index) {
    (void)context; (void)index;
    return "Caf\xc3\xa9";
}

static void write_ppm(const char* path, const uint16_t* pixels) {
    FILE* file = fopen(path, "wb");
    assert(file);
    assert(fprintf(file, "P6\n%u %u\n255\n", MENU160_WIDTH, MENU160_HEIGHT) > 0);
    for(size_t i = 0; i < MENU160_WIDTH * MENU160_HEIGHT; i++) {
        const uint16_t p = pixels[i];
        const unsigned char rgb[3] = {
            (unsigned char)(((p >> 11) & 31) * 255 / 31),
            (unsigned char)(((p >> 5) & 63) * 255 / 63),
            (unsigned char)((p & 31) * 255 / 31),
        };
        assert(fwrite(rgb, 1, sizeof(rgb), file) == sizeof(rgb));
    }
    assert(fclose(file) == 0);
}

int main(int argc, char** argv) {
    const size_t size = MENU160_WIDTH * MENU160_HEIGHT;
    uint16_t* full = calloc(size, sizeof(*full));
    uint16_t* stripes = calloc(size, sizeof(*stripes));
    assert(full && stripes);
    Menu160Model model = {
        .title = "MENU",
        .count = sizeof(labels) / sizeof(labels[0]),
        .selected = 1,
        .label = get_label,
    };

    for(size_t selected = 0; selected < model.count; selected++) {
        model.selected = selected;
        assert(menu160_render_strip(full, size, 0, MENU160_HEIGHT, &model));
        for(unsigned y = 0; y < MENU160_HEIGHT; y += 10) {
            unsigned rows = MENU160_HEIGHT - y < 10 ? MENU160_HEIGHT - y : 10;
            assert(menu160_render_strip(
                stripes + (size_t)y * MENU160_WIDTH,
                size - (size_t)y * MENU160_WIDTH,
                y,
                rows,
                &model));
        }
        assert(memcmp(full, stripes, size * sizeof(*full)) == 0);
    }

    model.selected = 0;
    assert(menu160_render_strip(full, size, 0, MENU160_HEIGHT, &model));
    model.selected = 1;
    assert(menu160_render_strip(stripes, size, 0, MENU160_HEIGHT, &model));
    assert(memcmp(full, stripes, size * sizeof(*full)) != 0);
    uint16_t guarded[MENU160_WIDTH * 10 + 2];
    guarded[0] = guarded[MENU160_WIDTH * 10 + 1] = 0xa55a;
    assert(menu160_render_strip(guarded + 1, MENU160_WIDTH * 10, 30, 10, &model));
    assert(guarded[0] == 0xa55a && guarded[MENU160_WIDTH * 10 + 1] == 0xa55a);

    model.selected = 9999;
    assert(menu160_render_strip(full, size, 0, MENU160_HEIGHT, &model));
    model.count = 0;
    model.label = NULL;
    assert(menu160_render_strip(full, size, 0, MENU160_HEIGHT, &model));
    assert(!menu160_render_strip(NULL, size, 0, MENU160_HEIGHT, &model));
    assert(!menu160_render_strip(full, size, 128, 1, &model));
    assert(!menu160_render_strip(full, size, 127, 2, &model));
    assert(!menu160_render_strip(full, MENU160_WIDTH - 1, 0, 1, &model));
    assert(!menu160_render_strip(full, size, 0, 0, &model));
    model.count = 1;
    assert(!menu160_render_strip(full, size, 0, MENU160_HEIGHT, &model));
    model.label = unsupported_label;
    assert(!menu160_supported(&model));
    assert(!menu160_render_strip(full, size, 0, MENU160_HEIGHT, &model));

    model.count = sizeof(labels) / sizeof(labels[0]);
    model.selected = 1;
    model.label = get_label;
    assert(menu160_render_strip(full, size, 0, MENU160_HEIGHT, &model));
    if(argc > 1) write_ppm(argv[1], full);
    free(stripes);
    free(full);
    puts("PASS: native 160x128 menu, selection, bounds and 10-line rendering");
    return 0;
}
