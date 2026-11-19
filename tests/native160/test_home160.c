#include "graphics160.h"
#include "home160.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void write_ppm(const char* path, const uint16_t* pixels) {
    FILE* file = fopen(path, "wb");
    assert(file);
    assert(fprintf(file, "P6\n%u %u\n255\n", UI160_WIDTH, UI160_HEIGHT) > 0);
    for(size_t i = 0; i < UI160_WIDTH * UI160_HEIGHT; i++) {
        uint16_t p = pixels[i];
        unsigned char rgb[3] = {
            (unsigned char)(((p >> 11) & 31) * 255 / 31),
            (unsigned char)(((p >> 5) & 63) * 255 / 63),
            (unsigned char)((p & 31) * 255 / 31),
        };
        assert(fwrite(rgb, 1, sizeof(rgb), file) == sizeof(rgb));
    }
    assert(fclose(file) == 0);
}

int main(int argc, char** argv) {
    assert(argc == 3 || argc == 4);
    uint8_t frame[16 * 47];
    FILE* input = fopen(argv[1], "rb");
    assert(input);
    assert(fread(frame, 1, sizeof(frame), input) == sizeof(frame));
    assert(fgetc(input) == EOF);
    assert(fclose(input) == 0);

    const size_t count = UI160_WIDTH * UI160_HEIGHT;
    uint16_t* full = calloc(count, sizeof(*full));
    uint16_t* strips = calloc(count, sizeof(*strips));
    assert(full && strips);
    Home160Model model = {
        .frame = {.bits = frame, .size_bytes = sizeof(frame), .width = 128, .height = 47},
        .time_label = NULL,
        .hints = HOME160_HINTS_MAIN,
    };

    assert(home160_render_strip(full, count, 0, UI160_HEIGHT, &model));
    for(unsigned y = 0; y < UI160_HEIGHT; y += 10) {
        unsigned rows = UI160_HEIGHT - y < 10 ? UI160_HEIGHT - y : 10;
        assert(home160_render_strip(strips + (size_t)y * UI160_WIDTH,
                                    count - (size_t)y * UI160_WIDTH, y, rows, &model));
    }
    assert(memcmp(full, strips, count * sizeof(*full)) == 0);

    /* Every original bit is present exactly once, with no stretching or crop. */
    const unsigned x0 = (UI160_WIDTH - 128) / 2;
    const unsigned y0 = 26 + (75 - 47) / 2;
    for(unsigned y = 0; y < 47; y++) {
        for(unsigned x = 0; x < 128; x++) {
            bool set = (frame[y * 16 + x / 8] & (1u << (x % 8))) != 0;
            uint16_t actual = full[(size_t)(y0 + y) * UI160_WIDTH + x0 + x];
            assert(actual == (set ? UI160_COLOR_INK : UI160_COLOR_PAPER));
        }
    }

    Home160Model bubble = model;
    bubble.bubble_text = "A VERY LONG ORIGINAL ANIMATION BUBBLE\nSECOND LINE\nIGNORED";
    assert(home160_render_strip(strips, count, 0, UI160_HEIGHT, &bubble));
    assert(memcmp(full, strips, count * sizeof(*full)) != 0);
    Home160Model no_hints = model;
    no_hints.hints = HOME160_HINTS_NONE;
    assert(home160_render_strip(strips, count, 0, UI160_HEIGHT, &no_hints));
    assert(memcmp(full, strips, count * sizeof(*full)) != 0);
    assert(memcmp(full, strips, (size_t)107 * UI160_WIDTH * sizeof(*full)) == 0);

    Home160Model invalid = model;
    invalid.frame.size_bytes--;
    assert(!home160_render_strip(strips, count, 0, UI160_HEIGHT, &invalid));
    invalid = model;
    invalid.frame.width = 137;
    assert(!home160_render_strip(strips, count, 0, UI160_HEIGHT, &invalid));
    invalid = model;
    invalid.frame.height = 65;
    assert(!home160_render_strip(strips, count, 0, UI160_HEIGHT, &invalid));
    invalid = model;
    invalid.hints = (Home160Hints)99;
    assert(!home160_render_strip(strips, count, 0, UI160_HEIGHT, &invalid));
    assert(!home160_render_strip(NULL, count, 0, 1, &model));
    assert(!home160_render_strip(strips, UI160_WIDTH - 1, 0, 1, &model));
    assert(!home160_render_strip(strips, count, 127, 2, &model));
    assert(!home160_render_strip(strips, count, 0, 0, &model));

    Home160Model empty = {0};
    assert(home160_render_strip(strips, count, 0, UI160_HEIGHT, &empty));
    if(argc == 4) {
        model.bubble_text = argv[3];
        assert(home160_render_strip(full, count, 0, UI160_HEIGHT, &model));
    }
    write_ppm(argv[2], full);
    free(strips);
    free(full);
    puts("PASS: original animation pixels 1:1, strip output and bounds");
    return 0;
}
