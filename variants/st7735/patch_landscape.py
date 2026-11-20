#!/usr/bin/env python3
"""Rotate the already-applied ST7735S profile to 160x128 landscape.

Apply the existing DIY and ST7735S patches first, on a fresh pinned upstream
checkout. This enables a native 160x128 canvas and adapts the home screen,
launcher, and common submenus to it; it does not flash.
"""
from pathlib import Path
import subprocess
import sys


def replace_once(text, before, after, label):
    if after in text:
        return text
    if text.count(before) != 1:
        raise ValueError(f"{label}: missing or ambiguous source anchor: {before!r}")
    return text.replace(before, after, 1)


def patch_generator(s):
    if "#define BOARD_GUI_NATIVE_LCD 1" not in s:
        s = replace_once(
            s,
            "#define BOARD_LCD_H_RES 128\n#define BOARD_LCD_V_RES 160\n#define BOARD_LCD_SIDE_MARGIN 0",
            "#define BOARD_LCD_H_RES 160\n#define BOARD_LCD_V_RES 128\n"
            "#define BOARD_GUI_NATIVE_LCD 1\n#define BOARD_LCD_SIDE_MARGIN 0",
            "enable native 160x128 GUI for landscape ST7735S",
        )
    for old, new in (
        ("#define BOARD_LCD_SWAP_XY false", "#define BOARD_LCD_SWAP_XY true"),
        ("#define BOARD_LCD_MIRROR_X true", "#define BOARD_LCD_MIRROR_X false"),
    ):
        s = replace_once(s, old, new, "ST7735S landscape generator")
    return s


def patch_display(s):
    if "esp_lcd_new_panel_st7735(" not in s:
        raise ValueError("ST7735S driver profile has not been applied")
    anchor = "    ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel_handle, BOARD_LCD_INVERT_COLOR));\n"
    rotated = anchor + "    ESP_ERROR_CHECK(esp_lcd_panel_swap_xy(panel_handle, BOARD_LCD_SWAP_XY));\n"
    return replace_once(s, anchor, rotated, "ST7735S axis swap")


def patch_display_hal(s):
    old_fb = """/* Flipper framebuffer dimensions */
#define FB_WIDTH  128
#define FB_HEIGHT 64"""
    new_fb = """/* Keep legacy display profiles at 128x64. The ST7735S landscape
 * profile renders directly from a native 160x128 monochrome canvas. */
#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD
#define FB_WIDTH  LCD_H_RES
#define FB_HEIGHT LCD_V_RES
#else
#define FB_WIDTH  128
#define FB_HEIGHT 64
#endif"""
    s = replace_once(s, old_fb, new_fb, "native display framebuffer dimensions")

    old_scale = """/* The ST7735S profile fills its entire 160x128 panel. The stock Flipper
 * 128x64 canvas is scaled independently on each axis, so there are no
 * unused top/bottom bands. Other boards retain aspect-fit rendering. */
#if defined(BOARD_LCD_FILL_SCREEN) && BOARD_LCD_FILL_SCREEN
#define SCALED_WIDTH LCD_H_RES
#define SCALED_HEIGHT LCD_V_RES
#else
#if (USABLE_H_RES * FB_HEIGHT) <= (LCD_V_RES * FB_WIDTH)
#define SCALED_WIDTH  USABLE_H_RES
#define SCALED_HEIGHT ((USABLE_H_RES * FB_HEIGHT) / FB_WIDTH)
#else
#define SCALED_HEIGHT LCD_V_RES
#define SCALED_WIDTH  ((LCD_V_RES * FB_WIDTH) / FB_HEIGHT)
#endif
#endif"""
    new_scale = """/* Native ST7735S uses every pixel without stretching a 128x64 frame.
 * Other panels keep their existing aspect-fit/full-panel behavior. */
#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD
#define SCALED_WIDTH  FB_WIDTH
#define SCALED_HEIGHT FB_HEIGHT
#elif defined(BOARD_LCD_FILL_SCREEN) && BOARD_LCD_FILL_SCREEN
#define SCALED_WIDTH LCD_H_RES
#define SCALED_HEIGHT LCD_V_RES
#else
#if (USABLE_H_RES * FB_HEIGHT) <= (LCD_V_RES * FB_WIDTH)
#define SCALED_WIDTH  USABLE_H_RES
#define SCALED_HEIGHT ((USABLE_H_RES * FB_HEIGHT) / FB_WIDTH)
#else
#define SCALED_HEIGHT LCD_V_RES
#define SCALED_WIDTH  ((LCD_V_RES * FB_WIDTH) / FB_HEIGHT)
#endif
#endif"""
    s = replace_once(s, old_scale, new_scale, "native display scaling")
    s = replace_once(
        s,
        "#define STRIPE_HEIGHT 10",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "#define STRIPE_HEIGHT 16\n#else\n#define STRIPE_HEIGHT 10\n#endif",
        "native display DMA stripe size",
    )
    s = replace_once(
        s,
        "void furi_hal_display_commit(const uint8_t* data, uint32_t size) {\n    UNUSED(size);\n    if(!panel_handle || !rgb565_buf || !data) return;",
        "void furi_hal_display_commit(const uint8_t* data, uint32_t size) {\n"
        "    if(!panel_handle || !rgb565_buf || !data || size < sizeof(fb_shadow)) return;",
        "validate framebuffer size before display commit",
    )
    return s


def patch_u8g2(s):
    s = replace_once(
        s,
        '#include <furi.h>\n',
        '#include <furi.h>\n#include <boards/board.h>\n',
        "board geometry include for native U8g2 canvas",
    )
    old_info = """    .tile_width = 16, /* width of 16*8=128 pixel */
    .tile_height = 8,
    .default_x_offset = 0,
    .flipmode_x_offset = 4,
    .pixel_width = 128,
    .pixel_height = 64};"""
    new_info = """#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD
    .tile_width = 20, /* native 160-pixel canvas */
    .tile_height = 16,
    .default_x_offset = 0,
    .flipmode_x_offset = 4,
    .pixel_width = 160,
    .pixel_height = 128
#else
    .tile_width = 16,
    .tile_height = 8,
    .default_x_offset = 0,
    .flipmode_x_offset = 4,
    .pixel_width = 128,
    .pixel_height = 64
#endif
};"""
    s = replace_once(s, old_info, new_info, "native U8g2 display geometry")
    old_buf = """    buf = u8g2_m_16_8_f(&tile_buf_height);
    u8g2_SetupBuffer(u8g2, buf, tile_buf_height, u8g2_ll_hvline_vertical_top_lsb, rotation);"""
    new_buf = """#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD
    buf = u8g2_m_20_16_f(&tile_buf_height);
#else
    buf = u8g2_m_16_8_f(&tile_buf_height);
#endif
    u8g2_SetupBuffer(u8g2, buf, tile_buf_height, u8g2_ll_hvline_vertical_top_lsb, rotation);"""
    return replace_once(s, old_buf, new_buf, "native U8g2 framebuffer allocation")


def patch_u8g2_cmake(s):
    return replace_once(
        s,
        '    REQUIRES furi\n',
        '    REQUIRES furi furi_hal\n',
        "export board geometry to U8g2 component",
    )


def patch_gui_header(s):
    s = replace_once(
        s,
        "#include \"gui.h\"\n",
        "#include \"gui.h\"\n#include <boards/board.h>\n",
        "board geometry include for native GUI",
    )
    return replace_once(
        s,
        "#define GUI_DISPLAY_WIDTH  128\n#define GUI_DISPLAY_HEIGHT 64",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "#define GUI_DISPLAY_WIDTH  BOARD_LCD_H_RES\n"
        "#define GUI_DISPLAY_HEIGHT BOARD_LCD_V_RES\n"
        "#else\n"
        "#define GUI_DISPLAY_WIDTH  128\n"
        "#define GUI_DISPLAY_HEIGHT 64\n"
        "#endif",
        "native GUI logical dimensions",
    )


def patch_menu(s):
    s = replace_once(
        s,
        "#include <furi_hal.h>\n",
        "#include <furi_hal.h>\n#include <boards/board.h>\n",
        "board geometry include for responsive app menu",
    )
    old = """        case MenuStyleList: {
            for(uint8_t i = 0; i < 3; i++) {
                canvas_set_font(canvas, i == 1 ? FontPrimary : FontSecondary);
                shift_position = (position + items_count + i - 1) % items_count;
                item = MenuItemArray_get(model->items, shift_position);
                menu_centered_icon(canvas, item, 4, 3 + 22 * i, 14, 14);
                menu_get_name(item, name, false);
                size_t scroll_counter = menu_scroll_counter(model, i == 1);
                elements_scrollable_text_line(
                    canvas, 22, 14 + 22 * i, 98, name, scroll_counter, false);
            }
            elements_frame(canvas, 0, 21, 128 - 5, 21);
            elements_scrollbar(canvas, position, items_count);
            break;
        }"""
    new = """        case MenuStyleList: {
#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD
            /* Five crisp rows fill the native 160x128 panel. The selected row
             * stays centered, matching the Flipper list while using the extra
             * height for more apps and a wider text area. */
            const size_t row_height = 21;
            const size_t row_count = MIN((size_t)5, items_count);
            const size_t center_row = row_count / 2;
            const size_t top = (canvas_height(canvas) - row_count * row_height) / 2;
            const size_t left = 2;
            const size_t row_width = canvas_width(canvas) - 6;
            for(size_t i = 0; i < row_count; i++) {
                const bool selected = i == center_row;
                const int32_t delta = (int32_t)i - (int32_t)center_row;
                int32_t index = (int32_t)position + delta;
                while(index < 0) index += (int32_t)items_count;
                shift_position = (size_t)index % items_count;
                const size_t row_y = top + i * row_height;
                if(selected) {
                    elements_slightly_rounded_box(
                        canvas, left, row_y + 1, row_width, row_height - 2);
                    canvas_set_color(canvas, ColorWhite);
                }
                canvas_set_font(canvas, selected ? FontPrimary : FontSecondary);
                item = MenuItemArray_get(model->items, shift_position);
                menu_centered_icon(canvas, item, left + 3, row_y + 3, 15, 15);
                menu_get_name(item, name, false);
                const size_t scroll_counter = menu_scroll_counter(model, selected);
                elements_scrollable_text_line(
                    canvas,
                    left + 23,
                    row_y + 14,
                    row_width - 28,
                    name,
                    scroll_counter,
                    false);
                if(selected) canvas_set_color(canvas, ColorBlack);
            }
            elements_scrollbar(canvas, position, items_count);
#else
            for(uint8_t i = 0; i < 3; i++) {
                canvas_set_font(canvas, i == 1 ? FontPrimary : FontSecondary);
                shift_position = (position + items_count + i - 1) % items_count;
                item = MenuItemArray_get(model->items, shift_position);
                menu_centered_icon(canvas, item, 4, 3 + 22 * i, 14, 14);
                menu_get_name(item, name, false);
                size_t scroll_counter = menu_scroll_counter(model, i == 1);
                elements_scrollable_text_line(
                    canvas, 22, 14 + 22 * i, 98, name, scroll_counter, false);
            }
            elements_frame(canvas, 0, 21, 128 - 5, 21);
            elements_scrollbar(canvas, position, items_count);
#endif
            break;
        }"""
    return replace_once(s, old, new, "native full-height app menu")


def patch_submenu(s):
    s = replace_once(
        s,
        "#include <u8g2_glue.h>\n",
        "#include <u8g2_glue.h>\n#include <boards/board.h>\n",
        "board geometry include for responsive submenus",
    )
    return replace_once(
        s,
        """static size_t submenu_items_on_screen(SubmenuModel* model) {
    size_t res = (model->is_vertical) ? 10 : 4;
    return (furi_string_empty(model->header)) ? res : res - 1;
}""",
        """static size_t submenu_items_on_screen(SubmenuModel* model) {
#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD
    size_t res = (model->is_vertical) ? 10 : 7;
#else
    size_t res = (model->is_vertical) ? 10 : 4;
#endif
    return (furi_string_empty(model->header)) ? res : res - 1;
}""",
        "responsive 160x128 submenu row count",
    )


def patch_bubble_home(s):
    s = replace_once(
        s,
        "#include <momentum_settings.h>\n",
        "#include <momentum_settings.h>\n#include <boards/board.h>\n#include <stdio.h>\n",
        "board geometry include for home dashboard",
    )
    old = """static void bubble_animation_draw_callback(Canvas* canvas, void* model_) {
    furi_assert(model_);
    furi_assert(canvas);

    BubbleAnimationViewModel* model = model_;
    const BubbleAnimation* animation = model->current;

    if(model->freeze_frame) {
        uint8_t y_offset = canvas_height(canvas) - icon_get_height(model->freeze_frame);
        canvas_draw_icon(canvas, 0, y_offset, model->freeze_frame);
        return;
    }

    if(!animation) {
        return;
    }

    furi_assert(model->current_frame < 255);

    uint8_t index = bubble_animation_get_frame_index(model);
    uint8_t width = icon_get_width(&animation->icon_animation);
    uint8_t height = icon_get_height(&animation->icon_animation);
    uint8_t y_offset = canvas_height(canvas) - height;
    canvas_draw_bitmap(
        canvas, 0, y_offset, width, height, animation->icon_animation.frames[index]);

    const FrameBubble* bubble = model->current_bubble;
    if(bubble) {
        if((model->current_frame >= bubble->start_frame) &&
           (model->current_frame <= bubble->end_frame)) {
            const Bubble* b = &bubble->bubble;
            elements_bubble_str(canvas, b->x, b->y, b->text, b->align_h, b->align_v);
        }
    }
}"""
    new = """static void bubble_animation_draw_callback(Canvas* canvas, void* model_) {
    furi_assert(model_);
    furi_assert(canvas);

    BubbleAnimationViewModel* model = model_;
    const BubbleAnimation* animation = model->current;
#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD
    /* Give the extra panel height a purpose: a compact clock/date header above
     * the original pixel-art animation. Both remain sharp at native resolution. */
    DateTime datetime;
    char time_text[9];
    char date_text[16];
    furi_hal_rtc_get_datetime(&datetime);
    snprintf(
        time_text,
        sizeof(time_text),
        "%02u:%02u",
        (unsigned int)datetime.hour,
        (unsigned int)datetime.minute);
    snprintf(
        date_text,
        sizeof(date_text),
        "%04u-%02u-%02u",
        (unsigned int)datetime.year,
        (unsigned int)datetime.month,
        (unsigned int)datetime.day);
    canvas_set_color(canvas, ColorBlack);
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str_aligned(
        canvas, canvas_width(canvas) / 2, 16, AlignCenter, AlignBottom, "FLIPPER ZERO");
    canvas_draw_line(canvas, 24, 22, canvas_width(canvas) - 25, 22);
    canvas_set_font(canvas, FontBigNumbers);
    canvas_draw_str_aligned(
        canvas, canvas_width(canvas) / 2, 44, AlignCenter, AlignBottom, time_text);
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str_aligned(
        canvas, canvas_width(canvas) / 2, 57, AlignCenter, AlignBottom, date_text);
    const int32_t art_x = ((int32_t)canvas_width(canvas) - 128) / 2;
    const int32_t art_y = (int32_t)canvas_height(canvas) - 64;
#else
    const int32_t art_x = 0;
    const int32_t art_y = 0;
#endif

    if(model->freeze_frame) {
        const int32_t x = ((int32_t)canvas_width(canvas) - icon_get_width(model->freeze_frame)) / 2;
        const int32_t y = (int32_t)canvas_height(canvas) - icon_get_height(model->freeze_frame);
        canvas_draw_icon(canvas, x, y, model->freeze_frame);
    } else if(animation) {
        furi_assert(model->current_frame < 255);
        uint8_t index = bubble_animation_get_frame_index(model);
        uint8_t height = icon_get_height(&animation->icon_animation);
        uint8_t y_offset = canvas_height(canvas) - height;
        canvas_draw_bitmap(
            canvas,
            art_x,
            y_offset,
            icon_get_width(&animation->icon_animation),
            height,
            animation->icon_animation.frames[index]);

        const FrameBubble* bubble = model->current_bubble;
        if(bubble && (model->current_frame >= bubble->start_frame) &&
           (model->current_frame <= bubble->end_frame)) {
            const Bubble* b = &bubble->bubble;
            elements_bubble_str(
                canvas, b->x + art_x, b->y + art_y, b->text, b->align_h, b->align_v);
        }
    }
}"""
    return replace_once(s, old, new, "native full-screen home dashboard")


def patch_native_ui(root):
    paths = {
        "components/furi_hal/furi_hal_display.c": patch_display_hal,
        "components/u8g2/u8g2_glue.c": patch_u8g2,
        "components/u8g2/CMakeLists.txt": patch_u8g2_cmake,
        "components/gui/gui_i.h": patch_gui_header,
        "components/gui/modules/menu.c": patch_menu,
        "components/gui/modules/submenu.c": patch_submenu,
        "applications/services/desktop/animations/views/bubble_animation_view.c": patch_bubble_home,
    }
    for relative_path, transform in paths.items():
        path = root / relative_path
        path.write_text(transform(path.read_text(encoding="utf-8")), encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_landscape.py /path/to/patched/upstream")
    root = Path(sys.argv[1]).resolve()
    updates = {
        "tools/gen_diy_board.py": patch_generator,
        "components/furi_hal/furi_hal_display.c": patch_display,
    }
    prepared = {p: fn((root / p).read_text(encoding="utf-8")) for p, fn in updates.items()}
    pinout = (root / "Pinout.txt").read_text(encoding="utf-8").splitlines()
    for setting in ("SPI_SCK=12", "SPI_MOSI=11", "LCD_CS=-1", "LCD_DC=15", "LCD_RST=16",
                    "SD_SCK=40", "SD_MOSI=39", "SD_MISO=38", "SD_CS=14",
                    "BTN_UP=4", "BTN_DOWN=5", "BTN_LEFT=6", "BTN_RIGHT=17", "BTN_OK=8", "BTN_BACK=18"):
        if setting not in pinout:
            raise ValueError(f"Pinout differs from the tested profile: {setting}")
    for path, data in prepared.items():
        (root / path).write_text(data, encoding="utf-8")
    subprocess.run([sys.executable, str(root / "tools/gen_diy_board.py"), str(root / "Pinout.txt")],
                   cwd=root, check=True)
    patch_native_ui(root)
    board = (root / "components/furi_hal/boards/board_DIY.h").read_text(encoding="utf-8")
    required = (
        "#define BOARD_LCD_H_RES 160", "#define BOARD_LCD_V_RES 128",
        "#define BOARD_GUI_NATIVE_LCD 1",
        "#define BOARD_LCD_FILL_SCREEN 1",
        "#define BOARD_LCD_SIDE_MARGIN 0", "#define BOARD_LCD_SPI_FREQ_HZ (5 * 1000 * 1000)",
        "#define BOARD_LCD_SWAP_XY true", "#define BOARD_LCD_MIRROR_X false",
        "#define BOARD_LCD_MIRROR_Y true", "#define BOARD_LCD_INVERT_COLOR false",
        "#define BOARD_LCD_GAP_X 0", "#define BOARD_LCD_GAP_Y 0", "#define BOARD_PIN_LCD_CS   UINT16_MAX",
        "#define BOARD_SD_SPI_HOST SPI3_HOST", "#define BOARD_PIN_SD_MISO2 38",
        "#define BOARD_PIN_SD_MOSI  39", "#define BOARD_PIN_SD_SCK   40", "#define BOARD_PIN_SD_CS    14",
        "#define BOARD_PIN_BTN_OK     8", "#define BOARD_PIN_BTN_BACK   18",
    )
    missing = [item for item in required if item not in board]
    if missing:
        raise SystemExit(f"Generated landscape board configuration mismatch: {missing}")
    print("PASSED: ST7735S landscape 160x128, 5 MHz, same wiring and SD SPI3")


if __name__ == "__main__":
    main()
