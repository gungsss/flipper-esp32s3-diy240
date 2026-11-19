#pragma once

/* BOARD_LCD_* must be provided by the selected board configuration. */
#define LCD_H_RES BOARD_LCD_H_RES
#define LCD_V_RES BOARD_LCD_V_RES
#define FB_WIDTH 128
#define FB_HEIGHT 64

#ifndef BOARD_LCD_SIDE_MARGIN
#define BOARD_LCD_SIDE_MARGIN 4
#endif
#define DISPLAY_SIDE_MARGIN BOARD_LCD_SIDE_MARGIN
#define USABLE_H_RES (LCD_H_RES - 2 * DISPLAY_SIDE_MARGIN)

/* Never enlarge legacy pixels on the target 160x128 display. */
#if LCD_H_RES == 160 && LCD_V_RES == 128
#define SCALED_WIDTH FB_WIDTH
#define SCALED_HEIGHT FB_HEIGHT
#elif (USABLE_H_RES * FB_HEIGHT) <= (LCD_V_RES * FB_WIDTH)
#define SCALED_WIDTH USABLE_H_RES
#define SCALED_HEIGHT ((USABLE_H_RES * FB_HEIGHT) / FB_WIDTH)
#else
#define SCALED_HEIGHT LCD_V_RES
#define SCALED_WIDTH ((LCD_V_RES * FB_WIDTH) / FB_HEIGHT)
#endif

#define MARGIN_X ((LCD_H_RES - SCALED_WIDTH) / 2)
#define MARGIN_Y ((LCD_V_RES - SCALED_HEIGHT) / 2)
