#pragma once
#include <stdbool.h>
#include <stdint.h>
uint16_t furi_hal_display_get_h_res(void);
uint16_t furi_hal_display_get_v_res(void);
bool furi_hal_display_is_asleep(void);
void furi_hal_display_commit(const uint8_t* data, uint32_t size);
bool furi_hal_display_draw_rgb565(
    uint16_t x, uint16_t y, uint16_t width, uint16_t height, const uint16_t* pixels);
