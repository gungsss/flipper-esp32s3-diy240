#include <assert.h>
#include <stdio.h>
#include "display_geometry.h"

int main(void) {
#if BOARD_LCD_H_RES == 160 && BOARD_LCD_V_RES == 128
    assert(SCALED_WIDTH == 128 && SCALED_HEIGHT == 64);
    assert(MARGIN_X == 16 && MARGIN_Y == 32);
    /* The HAL lookup maps every physical output pixel to exactly the source
     * pixel at the same relative coordinate. */
    for(unsigned x = 0; x < SCALED_WIDTH; x++) {
        assert((x * FB_WIDTH) / SCALED_WIDTH == x);
    }
    for(unsigned y = 0; y < SCALED_HEIGHT; y++) {
        assert((y * FB_HEIGHT) / SCALED_HEIGHT == y);
    }
    puts("PASS: 160x128 fallback geometry is centered at 1:1");
#elif BOARD_LCD_H_RES == 240 && BOARD_LCD_V_RES == 240
    assert(SCALED_WIDTH == 232 && SCALED_HEIGHT == 116);
    assert(MARGIN_X == 4 && MARGIN_Y == 62);
    puts("PASS: 240x240 geometry retains its existing aspect-fit size");
#else
#error "Define a supported test configuration"
#endif
}
