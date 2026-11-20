#!/usr/bin/env python3
"""Rotate the already-applied ST7735S profile to 160x128 landscape.

Apply the existing DIY and ST7735S patches first, on a fresh pinned upstream
checkout. This enables a native 160x128 canvas and adapts the home screen,
launcher, file browser, settings lists, editors, and common submenus; it does
not flash.
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


def patch_canvas_internal_header(s):
    s = replace_once(
        s,
        "    size_t height;\n    CompressIcon* compress_icon;",
        "    size_t height;\n    bool legacy_scale_active;\n    CompressIcon* compress_icon;",
        "track legacy-layout scaling state",
    )
    return replace_once(
        s,
        "void canvas_frame_set(\n",
        "void canvas_set_legacy_scale(Canvas* canvas, bool enabled);\nbool canvas_get_legacy_scale(const Canvas* canvas);\n\n"
        "void canvas_frame_set(\n",
        "legacy-layout scaling API",
    )


def patch_canvas_header(s):
    if "#include <stdbool.h>" not in s:
        s = replace_once(
            s,
            "#include <stdint.h>\n",
            "#include <stdint.h>\n#include <stdbool.h>\n",
            "bool type for native view layout",
        )
    return s


def patch_canvas(s):
    s = replace_once(
        s,
        "#include <u8g2_glue.h>\n",
        "#include <u8g2_glue.h>\n#include <boards/board.h>\n",
        "board geometry for legacy layout scaling",
    )
    s = replace_once(
        s,
        "    canvas->orientation = CanvasOrientationHorizontal;\n",
        "    canvas->orientation = CanvasOrientationHorizontal;\n"
        "    canvas->legacy_scale_active = false;\n",
        "initialize native canvas layout state",
    )
    s = replace_once(
        s,
        "size_t canvas_width(const Canvas* canvas) {\n    furi_check(canvas);\n    return canvas->width;\n}\n\nsize_t canvas_height(const Canvas* canvas) {\n    furi_check(canvas);\n    return canvas->height;\n}",
        """static size_t canvas_legacy_logical_width(const Canvas* canvas) {
    return (canvas->orientation == CanvasOrientationVertical ||
            canvas->orientation == CanvasOrientationVerticalFlip) ?
               64 :
               128;
}

static size_t canvas_legacy_logical_height(const Canvas* canvas) {
    return (canvas->orientation == CanvasOrientationVertical ||
            canvas->orientation == CanvasOrientationVerticalFlip) ?
               128 :
               64;
}

void canvas_set_legacy_scale(Canvas* canvas, bool enabled) {
    furi_check(canvas);
#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD
    /* Small status-bar viewports keep their native geometry. Full application
     * views that still use Flipper's 128x64 coordinates are scaled across the
     * entire ST7735S canvas, including portrait-oriented viewports. */
    canvas->legacy_scale_active = enabled && canvas->width >= 96 && canvas->height >= 64;
#else
    UNUSED(enabled);
    canvas->legacy_scale_active = false;
#endif
}

bool canvas_get_legacy_scale(const Canvas* canvas) {
    furi_check(canvas);
    return canvas->legacy_scale_active;
}

static int32_t canvas_scale_x(const Canvas* canvas, int32_t value) {
    if(!canvas->legacy_scale_active) return value;
    return (int32_t)(((int64_t)value * (int64_t)canvas->width) /
                     (int64_t)canvas_legacy_logical_width(canvas));
}

static int32_t canvas_scale_y(const Canvas* canvas, int32_t value) {
    if(!canvas->legacy_scale_active) return value;
    return (int32_t)(((int64_t)value * (int64_t)canvas->height) /
                     (int64_t)canvas_legacy_logical_height(canvas));
}

static size_t canvas_scale_width(const Canvas* canvas, size_t value) {
    if(!canvas->legacy_scale_active) return value;
    return (size_t)(((uint64_t)value * (uint64_t)canvas->width +
                     canvas_legacy_logical_width(canvas) - 1) /
                    canvas_legacy_logical_width(canvas));
}

static size_t canvas_scale_height(const Canvas* canvas, size_t value) {
    if(!canvas->legacy_scale_active) return value;
    return (size_t)(((uint64_t)value * (uint64_t)canvas->height +
                     canvas_legacy_logical_height(canvas) - 1) /
                    canvas_legacy_logical_height(canvas));
}

size_t canvas_width(const Canvas* canvas) {
    furi_check(canvas);
    if(canvas->legacy_scale_active) return canvas_legacy_logical_width(canvas);
    return canvas->width;
}

size_t canvas_height(const Canvas* canvas) {
    furi_check(canvas);
    if(canvas->legacy_scale_active) return canvas_legacy_logical_height(canvas);
    return canvas->height;
}""",
        "legacy app canvases use full-screen geometry",
    )
    s = replace_once(
        s,
        "size_t canvas_current_font_height(const Canvas* canvas) {",
        """static void canvas_draw_legacy_bitmap(
    Canvas* canvas,
    int32_t x,
    int32_t y,
    size_t width,
    size_t height,
    const uint8_t* bitmap,
    IconRotation rotation) {
    if(!width || !height || !bitmap) return;
    x = canvas_scale_x(canvas, x) + canvas->offset_x;
    y = canvas_scale_y(canvas, y) + canvas->offset_y;
    if(!canvas->legacy_scale_active || (width < 48 && height < 32)) {
        canvas_draw_u8g2_bitmap(&canvas->fb, x, y, width, height, bitmap, rotation);
        return;
    }
#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD
    size_t scaled_width = MIN(canvas_scale_width(canvas, width), canvas->width);
    size_t scaled_height = MIN(canvas_scale_height(canvas, height), canvas->height);
    const size_t scaled_stride = (scaled_width + 7) / 8;
    const size_t source_stride = (width + 7) / 8;
    uint8_t scaled_bitmap[(BOARD_LCD_H_RES * BOARD_LCD_V_RES + 7) / 8] = {0};
    for(size_t target_y = 0; target_y < scaled_height; target_y++) {
        const size_t source_y = target_y * height / scaled_height;
        for(size_t target_x = 0; target_x < scaled_width; target_x++) {
            const size_t source_x = target_x * width / scaled_width;
            const uint8_t source_byte =
                u8x8_pgm_read(bitmap + source_y * source_stride + source_x / 8);
            if(source_byte & (1u << (source_x & 7))) {
                scaled_bitmap[target_y * scaled_stride + target_x / 8] |=
                    (uint8_t)(1u << (target_x & 7));
            }
        }
    }
    canvas_draw_u8g2_bitmap(
        &canvas->fb, x, y, scaled_width, scaled_height, scaled_bitmap, rotation);
#else
    canvas_draw_u8g2_bitmap(&canvas->fb, x, y, width, height, bitmap, rotation);
#endif
}

size_t canvas_current_font_height(const Canvas* canvas) {""",
        "native scaling for large legacy bitmap screens",
    )
    # Map primitive coordinates and dimensions at the Canvas boundary. This
    # covers built-in apps and third-party screens without editing each page.
    pairs = (
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    u8g2_DrawUTF8(&canvas->fb, x, y, str);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    u8g2_DrawUTF8(&canvas->fb, x, y, str);", "scale legacy strings"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n\n    switch(horizontal) {",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n\n    switch(horizontal) {", "scale aligned legacy strings"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    uint8_t* bitmap_data = NULL;\n    compress_icon_decode(canvas->compress_icon, compressed_bitmap_data, &bitmap_data);\n    canvas_draw_u8g2_bitmap(&canvas->fb, x, y, width, height, bitmap_data, IconRotation0);",
         "    uint8_t* bitmap_data = NULL;\n    compress_icon_decode(canvas->compress_icon, compressed_bitmap_data, &bitmap_data);\n    canvas_draw_legacy_bitmap(canvas, x, y, width, height, bitmap_data, IconRotation0);", "scale legacy bitmap positions"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    uint8_t* icon_data = NULL;\n    compress_icon_decode(\n        canvas->compress_icon, icon_animation_get_data(icon_animation), &icon_data);\n    const int32_t width = (icon_animation_get_width(icon_animation) * width_scale) / 100;\n    const int32_t height = (icon_animation_get_height(icon_animation) * height_scale) / 100;\n    canvas_draw_u8g2_bitmap(\n        &canvas->fb, x, y, width, height, icon_data, IconRotation0);",
         "    uint8_t* icon_data = NULL;\n    compress_icon_decode(\n        canvas->compress_icon, icon_animation_get_data(icon_animation), &icon_data);\n    const int32_t width = (icon_animation_get_width(icon_animation) * width_scale) / 100;\n    const int32_t height = (icon_animation_get_height(icon_animation) * height_scale) / 100;\n    canvas_draw_legacy_bitmap(canvas, x, y, width, height, icon_data, IconRotation0);", "scale legacy animation images"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    uint8_t* icon_data = NULL;\n    compress_icon_decode(canvas->compress_icon, icon_get_frame_data(icon, 0), &icon_data);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    uint8_t* icon_data = NULL;\n    compress_icon_decode(canvas->compress_icon, icon_get_frame_data(icon, 0), &icon_data);", "scale legacy icon positions"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    u8g2_DrawPixel(&canvas->fb, x, y);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    u8g2_DrawPixel(&canvas->fb, x, y);", "scale legacy dots"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    u8g2_DrawBox(&canvas->fb, x, y, width, height);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    width = canvas_scale_width(canvas, width);\n    height = canvas_scale_height(canvas, height);\n    u8g2_DrawBox(&canvas->fb, x, y, width, height);", "scale legacy boxes"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    u8g2_DrawRBox(&canvas->fb, x, y, width, height, radius);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    width = canvas_scale_width(canvas, width);\n    height = canvas_scale_height(canvas, height);\n    if(canvas->legacy_scale_active) radius = canvas_scale_width(canvas, radius);\n    u8g2_DrawRBox(&canvas->fb, x, y, width, height, radius);", "scale legacy rounded boxes"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    u8g2_DrawFrame(&canvas->fb, x, y, width, height);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    width = canvas_scale_width(canvas, width);\n    height = canvas_scale_height(canvas, height);\n    u8g2_DrawFrame(&canvas->fb, x, y, width, height);", "scale legacy frames"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    u8g2_DrawRFrame(&canvas->fb, x, y, width, height, radius);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    width = canvas_scale_width(canvas, width);\n    height = canvas_scale_height(canvas, height);\n    if(canvas->legacy_scale_active) radius = canvas_scale_width(canvas, radius);\n    u8g2_DrawRFrame(&canvas->fb, x, y, width, height, radius);", "scale legacy rounded frames"),
        ("    x1 += canvas->offset_x;\n    y1 += canvas->offset_y;\n    x2 += canvas->offset_x;\n    y2 += canvas->offset_y;",
         "    x1 = canvas_scale_x(canvas, x1) + canvas->offset_x;\n    y1 = canvas_scale_y(canvas, y1) + canvas->offset_y;\n    x2 = canvas_scale_x(canvas, x2) + canvas->offset_x;\n    y2 = canvas_scale_y(canvas, y2) + canvas->offset_y;", "scale legacy lines"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    u8g2_DrawCircle(&canvas->fb, x, y, radius, U8G2_DRAW_ALL);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    if(canvas->legacy_scale_active) radius = canvas_scale_width(canvas, radius);\n    u8g2_DrawCircle(&canvas->fb, x, y, radius, U8G2_DRAW_ALL);", "scale legacy circles"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    u8g2_DrawDisc(&canvas->fb, x, y, radius, U8G2_DRAW_ALL);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    if(canvas->legacy_scale_active) radius = canvas_scale_width(canvas, radius);\n    u8g2_DrawDisc(&canvas->fb, x, y, radius, U8G2_DRAW_ALL);", "scale legacy discs"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    canvas_draw_u8g2_bitmap(&canvas->fb, x, y, width, height, bitmap_data, rotation);",
         "    canvas_draw_legacy_bitmap(canvas, x, y, width, height, bitmap_data, rotation);", "scale legacy xbm images"),
        ("    x += canvas->offset_x;\n    y += canvas->offset_y;\n    u8g2_DrawGlyph(&canvas->fb, x, y, ch);",
         "    x = canvas_scale_x(canvas, x) + canvas->offset_x;\n    y = canvas_scale_y(canvas, y) + canvas->offset_y;\n    u8g2_DrawGlyph(&canvas->fb, x, y, ch);", "scale legacy glyph positions"),
    )
    for before, after, label in pairs:
        if label == "scale legacy icon positions":
            if after in s:
                continue
            if s.count(before) != 3:
                raise ValueError(f"{label}: expected 3 source anchors, found {s.count(before)}")
            s = s.replace(before, after)
        else:
            s = replace_once(s, before, after, label)
    return s


def patch_view_header(s):
    s = replace_once(
        s,
        "void view_set_orientation(View* view, ViewOrientation orientation);",
        "void view_set_orientation(View* view, ViewOrientation orientation);\n\n"
        "/* Native-layout GUI modules opt out of legacy 128x64 canvas scaling. */\n"
        "void view_set_native_layout(View* view, bool native_layout);",
        "select native full-screen layouts",
    )
    return s


def patch_view_internal_header(s):
    return replace_once(
        s,
        "    ViewOrientation orientation;\n    ViewInputMode input_mode;",
        "    ViewOrientation orientation;\n    ViewInputMode input_mode;\n    bool native_layout;",
        "store native-layout module preference",
    )


def patch_view(s):
    s = replace_once(
        s,
        '#include "view_i.h"\n',
        '#include "view_i.h"\n#include "canvas_i.h"\n',
        "canvas scaling for legacy application views",
    )
    s = replace_once(
        s,
        "void view_set_orientation(View* view, ViewOrientation orientation) {\n    furi_check(view);\n    view->orientation = orientation;\n}\n",
        "void view_set_orientation(View* view, ViewOrientation orientation) {\n    furi_check(view);\n    view->orientation = orientation;\n}\n\n"
        "void view_set_native_layout(View* view, bool native_layout) {\n"
        "    furi_check(view);\n    view->native_layout = native_layout;\n}\n",
        "native view layout opt-out",
    )
    return replace_once(
        s,
        "void view_draw(View* view, Canvas* canvas) {\n    furi_check(view);\n    if(view->draw_callback) {\n        void* data = view_get_model(view);\n        view->draw_callback(canvas, data);\n        view_unlock_model(view);\n    }\n}",
        """void view_draw(View* view, Canvas* canvas) {
    furi_check(view);
    if(view->draw_callback) {
        const bool legacy_scale = canvas_get_legacy_scale(canvas);
        canvas_set_legacy_scale(canvas, !view->native_layout);
        void* data = view_get_model(view);
        view->draw_callback(canvas, data);
        view_unlock_model(view);
        canvas_set_legacy_scale(canvas, legacy_scale);
    }
}""",
        "scale every legacy app view to native screen",
    )


def patch_view_port(s):
    s = replace_once(
        s,
        '#include "gui_i.h"\n',
        '#include "gui_i.h"\n#include "canvas_i.h"\n',
        "canvas scaling for full-screen viewport apps",
    )
    return replace_once(
        s,
        "    if(view_port->draw_callback) {\n        view_port_setup_canvas_orientation(view_port, canvas);\n        view_port->draw_callback(canvas, view_port->draw_callback_context);\n    }",
        "    if(view_port->draw_callback) {\n"
        "        view_port_setup_canvas_orientation(view_port, canvas);\n"
        "        const bool legacy_scale = canvas_get_legacy_scale(canvas);\n"
        "        canvas_set_legacy_scale(canvas, true);\n"
        "        view_port->draw_callback(canvas, view_port->draw_callback_context);\n"
        "        canvas_set_legacy_scale(canvas, legacy_scale);\n"
        "    }",
        "scale full-screen custom viewport apps",
    )


def patch_mark_native_layout(s, view_expr, draw_callback):
    return replace_once(
        s,
        f"    view_set_draw_callback({view_expr}, {draw_callback});",
        f"    view_set_draw_callback({view_expr}, {draw_callback});\n"
        f"    view_set_native_layout({view_expr}, true);",
        f"native 160x128 view layout: {draw_callback}",
    )


def patch_multiline_elements(s):
    return replace_once(
        s,
        "    } while(end && y < 64);",
        "    } while(end && y < canvas_height(canvas));",
        "multiline text follows active full-screen canvas",
    )


def patch_interface_menu_style(s):
    s = replace_once(
        s,
        "#include <power/power_service/power.h>\n",
        "#include <power/power_service/power.h>\n#include <boards/board.h>\n",
        "board-aware menu style options",
    )
    s = replace_once(
        s,
        "static const char* const menu_style_text[MenuStyleCount] = {\n"
        '    "List",\n    "Wii",\n    "DSi",\n    "PS4",\n    "Vertical",\n    "C64",\n'
        '    "Compact",\n    "MNTM",\n    "CoverFlow",\n};',
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        'static const char* const menu_style_text[] = {"Fullscreen list"};\n'
        "#define MENU_STYLE_COUNT 1\n#else\n"
        "static const char* const menu_style_text[MenuStyleCount] = {\n"
        '    "List",\n    "Wii",\n    "DSi",\n    "PS4",\n    "Vertical",\n    "C64",\n'
        '    "Compact",\n    "MNTM",\n    "CoverFlow",\n};\n#define MENU_STYLE_COUNT MenuStyleCount\n#endif',
        "hide unsupported 64px launcher layouts on native LCD",
    )
    s = replace_once(
        s,
        "    VariableItem* item = variable_item_list_add(\n        app->variable_item_list, \"Menu style\", MenuStyleCount, menu_style_changed, app);\n    uint8_t value_index = (uint8_t)menu_get_style();",
        "    VariableItem* item = variable_item_list_add(\n"
        "        app->variable_item_list, \"Menu style\", MENU_STYLE_COUNT, menu_style_changed, app);\n"
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    uint8_t value_index = 0;\n#else\n    uint8_t value_index = (uint8_t)menu_get_style();\n#endif",
        "native LCD interface menu style selector",
    )
    return s


def patch_menu(s):
    s = replace_once(
        s,
        "#include <furi_hal.h>\n",
        "#include <furi_hal.h>\n#include <boards/board.h>\n",
        "board geometry include for responsive app menu",
    )
    s = replace_once(
        s,
        "    FURI_CRITICAL_ENTER();\n    if(!g_menu_style_loaded && valid) g_menu_style = loaded;\n    g_menu_style_loaded = true;",
        "    FURI_CRITICAL_ENTER();\n"
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    UNUSED(valid);\n"
        "    if(!g_menu_style_loaded) g_menu_style = MenuStyleList;\n"
        "#else\n    if(!g_menu_style_loaded && valid) g_menu_style = loaded;\n#endif\n"
        "    g_menu_style_loaded = true;",
        "force native launcher style on 160x128 profile",
    )
    s = replace_once(
        s,
        "void menu_set_style(MenuStyle style) {\n    if(((int)style < 0) || ((int)style >= (int)MenuStyleCount)) {",
        "void menu_set_style(MenuStyle style) {\n"
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    UNUSED(style);\n    style = MenuStyleList;\n#endif\n"
        "    if(((int)style < 0) || ((int)style >= (int)MenuStyleCount)) {",
        "keep launcher and interface setting in sync",
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
            /* Five generous rows fill the native 160x128 panel. The selected row
             * stays centered, matching the Flipper list while using the extra
             * height for more apps and a wider text area. */
            const size_t row_count = MIN((size_t)5, items_count);
            if(row_count == 0) break;
            const size_t row_height = MIN((size_t)25, canvas_height(canvas) / row_count);
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
                menu_centered_icon(canvas, item, left + 3, row_y + 5, 15, 15);
                menu_get_name(item, name, false);
                const size_t scroll_counter = menu_scroll_counter(model, selected);
                elements_scrollable_text_line(
                    canvas,
                    left + 23,
                    row_y + 17,
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
    if "const size_t row_height = 25;" in s:
        s = replace_once(
            s,
            "const size_t row_height = 25;",
            "const size_t row_height = MIN((size_t)25, canvas_height(canvas) / row_count);",
            "fit native launcher rows to available height",
        )
    if "const size_t row_height = MIN((size_t)25, canvas_height(canvas) / row_count);" in s:
        return s
    return replace_once(s, old, new, "native full-height app menu")


def patch_file_browser(s):
    s = replace_once(
        s,
        "#define LIST_ITEMS   5u\n#define MAX_LEN_PX   110\n#define FRAME_HEIGHT 12\n#define Y_OFFSET     3",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "#define LIST_ITEMS   9u\n#define MAX_LEN_PX   142\n#define FRAME_HEIGHT 12\n#define Y_OFFSET     3\n"
        "#else\n#define LIST_ITEMS   5u\n#define MAX_LEN_PX   110\n#define FRAME_HEIGHT 12\n#define Y_OFFSET     3\n#endif",
        "full-height native file browser rows",
    )
    s = replace_once(
        s,
        "#include <furi.h>\n",
        "#include <furi.h>\n#include <boards/board.h>\n",
        "board geometry include for native file browser",
    )
    s = replace_once(
        s,
        "    canvas_draw_box(\n        canvas, 0, Y_OFFSET + idx * FRAME_HEIGHT, (scrollbar ? 122 : 127), FRAME_HEIGHT);",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    const uint16_t frame_right_edge = canvas_width(canvas) - (scrollbar ? 6 : 1);\n"
        "    canvas_draw_box(canvas, 0, Y_OFFSET + idx * FRAME_HEIGHT, frame_right_edge, FRAME_HEIGHT);\n"
        "#else\n"
        "    canvas_draw_box(\n        canvas, 0, Y_OFFSET + idx * FRAME_HEIGHT, (scrollbar ? 122 : 127), FRAME_HEIGHT);\n"
        "#endif",
        "native file browser row width",
    )
    s = replace_once(
        s,
        "    canvas_draw_dot(canvas, scrollbar ? 121 : 126, Y_OFFSET + idx * FRAME_HEIGHT);\n"
        "    canvas_draw_dot(\n        canvas, scrollbar ? 121 : 126, (Y_OFFSET + idx * FRAME_HEIGHT) + (FRAME_HEIGHT - 1));",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    const uint16_t outline_right_edge = canvas_width(canvas) - (scrollbar ? 7 : 2);\n"
        "#else\n"
        "    const uint16_t outline_right_edge = scrollbar ? 121 : 126;\n"
        "#endif\n"
        "    canvas_draw_dot(canvas, outline_right_edge, Y_OFFSET + idx * FRAME_HEIGHT);\n"
        "    canvas_draw_dot(\n        canvas, outline_right_edge, (Y_OFFSET + idx * FRAME_HEIGHT) + (FRAME_HEIGHT - 1));",
        "native file browser selection frame width",
    )
    s = replace_once(
        s,
        "    uint8_t x = 128 / 2 - 24 / 2;\n    uint8_t y = 64 / 2 - 24 / 2;",
        "    uint8_t x = canvas_width(canvas) / 2 - 24 / 2;\n"
        "    uint8_t y = canvas_height(canvas) / 2 - 24 / 2;",
        "center native file browser loading icon",
    )
    s = replace_once(
        s,
        "            126,\n            Y_OFFSET,\n            canvas_height(canvas) - Y_OFFSET,",
        "            canvas_width(canvas) - 2,\n            Y_OFFSET,\n            canvas_height(canvas) - Y_OFFSET,",
        "native file browser scrollbar position",
    )
    return s


def patch_text_box(s):
    s = replace_once(
        s,
        "#include <stdint.h>\n",
        "#include <stdint.h>\n#include <boards/board.h>\n",
        "board geometry include for native text box",
    )
    first_define = s.index("#define TEXT_BOX_TEXT_WIDTH")
    previous_if = s.rfind("#if defined(BOARD_GUI_NATIVE_LCD)", 0, first_define)
    line_start = s.rfind("\n", 0, first_define) + 1
    if previous_if >= 0 and not s[line_start:first_define].strip():
        line_start = previous_if
    layout_end = s.index("#define TEXT_BOX_LINES_SCROLL_SPEED_MEDIUM", first_define)
    layout = (
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "#define TEXT_BOX_TEXT_WIDTH           (BOARD_LCD_H_RES - 16)\n"
        "#define TEXT_BOX_TEXT_HEIGHT          (BOARD_LCD_V_RES - 24)\n"
        "#define TEXT_BOX_MAX_LINES_PER_SCREEN 20\n"
        "#else\n"
        "#define TEXT_BOX_TEXT_WIDTH           (120)\n"
        "#define TEXT_BOX_TEXT_HEIGHT          (56)\n"
        "#define TEXT_BOX_MAX_LINES_PER_SCREEN (10)\n"
        "#endif\n\n"
    )
    s = s[:line_start] + layout + s[layout_end:]
    s = replace_once(
        s,
        "    elements_slightly_rounded_frame(canvas, 0, 0, 124, 64);\n    elements_scrollbar(canvas, model->scroll_pos, model->scroll_num);",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    elements_slightly_rounded_frame(\n"
        "        canvas, 1, 1, canvas_width(canvas) - 5, canvas_height(canvas) - 2);\n"
        "#else\n"
        "    elements_slightly_rounded_frame(canvas, 0, 0, 124, 64);\n"
        "#endif\n    elements_scrollbar(canvas, model->scroll_pos, model->scroll_num);",
        "fullscreen native text box frame",
    )
    s = replace_once(
        s,
        "    elements_multiline_text(canvas, 3, 11, furi_string_get_cstr(model->text_on_screen));",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    elements_multiline_text(canvas, 4, 11, furi_string_get_cstr(model->text_on_screen));\n"
        "#else\n"
        "    elements_multiline_text(canvas, 3, 11, furi_string_get_cstr(model->text_on_screen));\n"
        "#endif",
        "native text box content margin",
    )
    return s


def patch_text_input(s):
    start = s.index("static void text_input_view_draw_callback(Canvas* canvas, void* _model) {")
    end = s.index("\nstatic void text_input_handle_up(", start)
    chunk = s[start:end]
    chunk = replace_once(
        chunk,
        "    canvas_draw_str(canvas, 2, 8, model->header);\n    elements_slightly_rounded_frame(canvas, 1, 12, 126, 15);",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    canvas_draw_str(canvas, 5, 8, model->header);\n"
        "    elements_slightly_rounded_frame(canvas, 2, 12, canvas_width(canvas) - 4, 18);\n"
        "#else\n"
        "    canvas_draw_str(canvas, 2, 8, model->header);\n"
        "    elements_slightly_rounded_frame(canvas, 1, 12, 126, 15);\n"
        "#endif",
        "native text input header and field",
    )
    chunk = replace_once(
        chunk,
        "    uint8_t needed_string_width = canvas_width(canvas) - 8;\n    uint8_t start_pos = 4;",
        "    uint8_t needed_string_width = canvas_width(canvas) - 10;\n    uint8_t start_pos = 5;",
        "native text input field width",
    )
    key_anchor = "            bool selected = !model->cursor_select && model->selected_row == row &&\n                            model->selected_column == column;\n"
    key_geometry = key_anchor + "            int32_t key_x = keyboard_origin_x + keys[column].x;\n"
    key_geometry += "            int32_t key_y = keyboard_origin_y + keys[column].y;\n"
    key_geometry += "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
    key_geometry += "            key_x = 7 + (keys[column].x * 9) / 8;\n"
    key_geometry += "            key_y = row == 0 ? 50 : (row == 1 ? 78 : 106);\n"
    key_geometry += "            if(keys[column].text == ENTER_KEY || keys[column].text == SWITCH_KEYBOARD_KEY) key_y -= 11;\n"
    key_geometry += "            if(keys[column].text == BACKSPACE_KEY) key_y -= 9;\n"
    key_geometry += "#endif\n"
    if "key_y = row == 0 ? 50 : (row == 1 ? 78 : 106);" not in chunk:
        chunk = replace_once(chunk, key_anchor, key_geometry, "native text input keyboard geometry")
    chunk = chunk.replace("keyboard_origin_x + keys[column].x", "key_x")
    chunk = chunk.replace("keyboard_origin_y + keys[column].y", "key_y")
    chunk = chunk.replace("int32_t key_x = key_x;", "int32_t key_x = keyboard_origin_x + keys[column].x;")
    chunk = chunk.replace("int32_t key_y = key_y;", "int32_t key_y = keyboard_origin_y + keys[column].y;")
    chunk = replace_once(
        chunk,
        "        canvas_set_color(canvas, ColorWhite);\n        canvas_draw_box(canvas, 8, 10, 110, 48);\n        canvas_set_color(canvas, ColorBlack);\n        canvas_draw_icon(canvas, 10, 14, &I_WarningDolphin_45x42);\n        canvas_draw_rframe(canvas, 8, 8, 112, 50, 3);\n        canvas_draw_rframe(canvas, 9, 9, 110, 48, 2);",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "        const int32_t dialog_x = 8;\n        const int32_t dialog_y = (canvas_height(canvas) - 54) / 2;\n"
        "        const int32_t dialog_w = canvas_width(canvas) - 16;\n"
        "        canvas_set_color(canvas, ColorWhite);\n"
        "        canvas_draw_box(canvas, dialog_x + 2, dialog_y + 2, dialog_w - 4, 50);\n"
        "        canvas_set_color(canvas, ColorBlack);\n"
        "        canvas_draw_icon(canvas, dialog_x + 4, dialog_y + 5, &I_WarningDolphin_45x42);\n"
        "        canvas_draw_rframe(canvas, dialog_x, dialog_y, dialog_w, 54, 3);\n"
        "        canvas_draw_rframe(canvas, dialog_x + 1, dialog_y + 1, dialog_w - 2, 52, 2);\n"
        "#else\n"
        "        canvas_set_color(canvas, ColorWhite);\n"
        "        canvas_draw_box(canvas, 8, 10, 110, 48);\n"
        "        canvas_set_color(canvas, ColorBlack);\n"
        "        canvas_draw_icon(canvas, 10, 14, &I_WarningDolphin_45x42);\n"
        "        canvas_draw_rframe(canvas, 8, 8, 112, 50, 3);\n"
        "        canvas_draw_rframe(canvas, 9, 9, 110, 48, 2);\n"
        "#endif",
        "center native text input validation dialog",
    )
    chunk = replace_once(
        chunk,
        "        elements_multiline_text(canvas, 62, 20, furi_string_get_cstr(model->validator_text));",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "        elements_multiline_text(\n"
        "            canvas, 63, canvas_height(canvas) / 2 - 20, furi_string_get_cstr(model->validator_text));\n"
        "#else\n"
        "        elements_multiline_text(canvas, 62, 20, furi_string_get_cstr(model->validator_text));\n"
        "#endif",
        "native text input validation message position",
    )
    return s[:start] + chunk + s[end:]


def patch_variable_item_list(s):
    s = replace_once(
        s,
        "static uint8_t variable_item_list_items_on_screen(const VariableItemListModel* model) {\n    size_t res = 4;",
        "static uint8_t variable_item_list_items_on_screen(const VariableItemListModel* model) {\n"
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n    size_t res = 7;\n"
        "#else\n    size_t res = 4;\n#endif",
        "native settings list row count",
    )
    native_row_height = (
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    const uint8_t item_height = 16;\n"
        "#else\n    const uint8_t item_height = 16;\n#endif"
    )
    if native_row_height not in s:
        s = replace_once(
            s,
            "    const uint8_t item_height = 16;",
            native_row_height,
            "native settings list row height",
        )
    s = replace_once(
        s,
        "            uint8_t temp_x_default = 73;\n            uint8_t temp_w_default = 66;",
        "            uint8_t temp_x_default = 73;\n            uint8_t temp_w_default = 66;\n"
        "            uint8_t value_marker_x = 115;\n            uint8_t value_text_width = 37;\n"
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "            temp_x_default = 90;\n            temp_w_default = canvas_width(canvas) - 115;\n"
        "            value_marker_x = canvas_width(canvas) - 20;\n#endif",
        "native settings list value column",
    )
    s = replace_once(
        s,
        "                    temp_x_default = 80;\n                    temp_w_default = 71;",
        "                    temp_x_default = 80;\n                    temp_w_default = 71;\n"
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "                    temp_x_default = 98;\n                    temp_w_default = canvas_width(canvas) - 123;\n#endif",
        "native settings list short-value spacing",
    )
    s = s.replace("canvas_draw_icon(canvas, 110, item_text_y - 8, &I_Lock_7x8);",
                  "canvas_draw_icon(\n"
                  "                canvas,\n#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
                  "                canvas_width(canvas) - 17,\n#else\n                110,\n#endif\n"
                  "                item_text_y - 8,\n                &I_Lock_7x8);")
    s = replace_once(
        s,
        "                if(item->current_value_index > 0) {\n                    canvas_draw_str(canvas, temp_x_default, item_text_y, is_editing ? \"[\" : \"<\");\n                }\n\n                elements_scrollable_text_line_str(\n                    canvas,\n                    (115 + temp_x_default) / 2 + 1,\n                    item_text_y,\n                    37,",
        "                if(item->current_value_index > 0) {\n"
        "                    canvas_draw_str(canvas, temp_x_default, item_text_y, is_editing ? \"[\" : \"<\");\n"
        "                }\n\n                elements_scrollable_text_line_str(\n"
        "                    canvas,\n                    (value_marker_x + temp_x_default) / 2 + 1,\n"
        "                    item_text_y,\n                    value_text_width,",
        "native settings list right-aligned values",
    )
    s = s.replace(
        "canvas_draw_str(canvas, 115, item_text_y, is_editing ? \"]\" : \">\");",
        "canvas_draw_str(canvas, value_marker_x, item_text_y, is_editing ? \"]\" : \">\");",
    )
    return s


def patch_number_input(s):
    s = replace_once(
        s,
        "#include <assets_icons.h>\n",
        "#include <assets_icons.h>\n#include <boards/board.h>\n",
        "board geometry include for native number input",
    )
    s = replace_once(
        s,
        "static void number_input_draw_input(Canvas* canvas, NumberInputModel* model) {\n"
        "    const size_t text_x = 8;\n    const size_t text_y = 25;\n\n"
        "    elements_slightly_rounded_frame(canvas, 4, 14, 120, 15);\n\n"
        "    canvas_draw_str(canvas, text_x, text_y, furi_string_get_cstr(model->text_buffer));\n}",
        "static void number_input_draw_input(Canvas* canvas, NumberInputModel* model) {\n"
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    const size_t text_x = 10;\n    const size_t text_y = 51;\n"
        "    elements_slightly_rounded_frame(canvas, 4, 35, canvas_width(canvas) - 8, 22);\n"
        "#else\n    const size_t text_x = 8;\n    const size_t text_y = 25;\n"
        "    elements_slightly_rounded_frame(canvas, 4, 14, 120, 15);\n#endif\n\n"
        "    canvas_draw_str(canvas, text_x, text_y, furi_string_get_cstr(model->text_buffer));\n}",
        "native number input value field",
    )
    start = s.index("static void number_input_view_draw_callback(Canvas* canvas, void* _model) {")
    end = s.index("\nstatic bool number_input_view_input_callback(", start)
    chunk = s[start:end]
    anchor = "        for(size_t column = 0; column < column_count; column++) {\n"
    coords = anchor + "            int32_t key_x = keyboard_origin_x + keys[column].x;\n"
    coords += "            int32_t key_y = keyboard_origin_y + keys[column].y;\n"
    coords += "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
    coords += "            if(keys[column].text == backspace_symbol) {\n"
    coords += "                key_x = canvas_width(canvas) - 27;\n                key_y = 66;\n"
    coords += "            } else if(keys[column].text == sign_symbol) {\n"
    coords += "                key_x = canvas_width(canvas) - 44;\n                key_y = 99;\n"
    coords += "            } else if(keys[column].text == enter_symbol) {\n"
    coords += "                key_x = canvas_width(canvas) - 26;\n                key_y = 99;\n"
    coords += "            } else {\n"
    coords += "                key_x = 15 + (keys[column].x * 18) / 10;\n"
    coords += "                key_y = row == 0 ? 72 : 104;\n            }\n#endif\n"
    if "key_y = row == 0 ? 72 : 104;" not in chunk:
        chunk = replace_once(chunk, anchor, coords, "native number keyboard geometry")
    chunk = chunk.replace("keyboard_origin_x + keys[column].x", "key_x")
    chunk = chunk.replace("keyboard_origin_y + keys[column].y", "key_y")
    chunk = chunk.replace("int32_t key_x = key_x;", "int32_t key_x = keyboard_origin_x + keys[column].x;")
    chunk = chunk.replace("int32_t key_y = key_y;", "int32_t key_y = keyboard_origin_y + keys[column].y;")
    return s[:start] + chunk + s[end:]


def patch_byte_input(s):
    s = replace_once(
        s,
        "static const uint8_t max_drawable_bytes = 8;",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "static const uint8_t max_drawable_bytes = 10;\n"
        "#else\nstatic const uint8_t max_drawable_bytes = 8;\n#endif",
        "native byte editor display capacity",
    )
    s = replace_once(
        s,
        "    const uint8_t text_x = 8;\n    const uint8_t text_y = 25;\n    const uint8_t text_y2 = 40;",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    const uint8_t text_x = 10;\n    const uint8_t text_y = 49;\n    const uint8_t text_y2 = 66;\n"
        "#else\n    const uint8_t text_x = 8;\n    const uint8_t text_y = 25;\n    const uint8_t text_y2 = 40;\n#endif",
        "native byte editor input coordinates",
    )
    s = replace_once(
        s,
        "    elements_slightly_rounded_frame(canvas, 6, 14, 116, 15);\n\n"
        "    canvas_draw_icon(canvas, 2, 19, &I_ButtonLeftSmall_3x5);\n"
        "    canvas_draw_icon(canvas, 123, 19, &I_ButtonRightSmall_3x5);",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    elements_slightly_rounded_frame(canvas, 3, 35, canvas_width(canvas) - 6, 22);\n"
        "    canvas_draw_icon(canvas, 0, 43, &I_ButtonLeftSmall_3x5);\n"
        "    canvas_draw_icon(canvas, canvas_width(canvas) - 5, 43, &I_ButtonRightSmall_3x5);\n"
        "#else\n"
        "    elements_slightly_rounded_frame(canvas, 6, 14, 116, 15);\n"
        "    canvas_draw_icon(canvas, 2, 19, &I_ButtonLeftSmall_3x5);\n"
        "    canvas_draw_icon(canvas, 123, 19, &I_ButtonRightSmall_3x5);\n#endif",
        "native byte editor value frame",
    )
    s = replace_once(
        s,
        "    const uint8_t text_x = 7;\n    const uint8_t text_y = 25;\n\n    canvas_draw_box(canvas, 0, 12, 127, 19);\n    canvas_invert_color(canvas);\n\n"
        "    elements_slightly_rounded_frame(canvas, 6, 14, 115, 15);\n"
        "    canvas_draw_icon(canvas, 2, 19, &I_ButtonLeftSmall_3x5);\n"
        "    canvas_draw_icon(canvas, 122, 19, &I_ButtonRightSmall_3x5);",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "    const uint8_t text_x = 9;\n    const uint8_t text_y = 49;\n\n"
        "    canvas_draw_box(canvas, 0, 33, canvas_width(canvas), 26);\n"
        "    canvas_invert_color(canvas);\n"
        "    elements_slightly_rounded_frame(canvas, 3, 35, canvas_width(canvas) - 6, 22);\n"
        "    canvas_draw_icon(canvas, 0, 43, &I_ButtonLeftSmall_3x5);\n"
        "    canvas_draw_icon(canvas, canvas_width(canvas) - 5, 43, &I_ButtonRightSmall_3x5);\n"
        "#else\n"
        "    const uint8_t text_x = 7;\n    const uint8_t text_y = 25;\n\n"
        "    canvas_draw_box(canvas, 0, 12, 127, 19);\n    canvas_invert_color(canvas);\n"
        "    elements_slightly_rounded_frame(canvas, 6, 14, 115, 15);\n"
        "    canvas_draw_icon(canvas, 2, 19, &I_ButtonLeftSmall_3x5);\n"
        "    canvas_draw_icon(canvas, 122, 19, &I_ButtonRightSmall_3x5);\n#endif",
        "native byte editor selected value frame",
    )
    start = s.index("static void byte_input_view_draw_callback(Canvas* canvas, void* _model) {")
    end = s.index("\nstatic bool byte_input_view_input_callback(", start)
    chunk = s[start:end]
    anchor = "            const ByteInputKey* keys = byte_input_get_row(row);\n\n            for(uint8_t column = 0; column < column_count; column++) {\n"
    coords = anchor + "                int32_t key_x = keyboard_origin_x + keys[column].x;\n"
    coords += "                int32_t key_y = keyboard_origin_y + keys[column].y;\n"
    coords += "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
    coords += "                if(keys[column].value == backspace_symbol) {\n"
    coords += "                    key_x = canvas_width(canvas) - 26;\n                    key_y = 74;\n"
    coords += "                } else if(keys[column].value == enter_symbol) {\n"
    coords += "                    key_x = canvas_width(canvas) - 27;\n                    key_y = 100;\n"
    coords += "                } else {\n"
    coords += "                    key_x = 16 + (keys[column].x * 14) / 10;\n"
    coords += "                    key_y = row == 0 ? 82 : 106;\n                }\n#endif\n"
    if "key_y = row == 0 ? 82 : 106;" not in chunk:
        chunk = replace_once(chunk, anchor, coords, "native byte editor keyboard geometry")
    chunk = chunk.replace("keyboard_origin_x + keys[column].x", "key_x")
    chunk = chunk.replace("keyboard_origin_y + keys[column].y", "key_y")
    chunk = chunk.replace("int32_t key_x = key_x;", "int32_t key_x = keyboard_origin_x + keys[column].x;")
    chunk = chunk.replace("int32_t key_y = key_y;", "int32_t key_y = keyboard_origin_y + keys[column].y;")
    return s[:start] + chunk + s[end:]


def patch_date_time_input(s):
    s = replace_once(
        s,
        "#include <assets_icons.h>\n",
        "#include <assets_icons.h>\n#include <boards/board.h>\n",
        "board geometry include for native date and time input",
    )
    previous_native_layout = (
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "#define ROW_0_Y (34)\n#define ROW_0_H (23)\n"
        "#define ROW_1_Y (82)\n#define ROW_1_H (23)\n"
        "#define DATE_TIME_X(x) ((x) + ((BOARD_LCD_H_RES - 128) / 2))\n"
        "#define DATE_TIME_LABEL_Y(y) ((y) - 14)\n"
    )
    updated_native_layout = (
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "#define ROW_0_Y (33)\n#define ROW_0_H (22)\n"
        "#define ROW_1_Y (78)\n#define ROW_1_H (22)\n"
        "#define DATE_TIME_X(x) ((x) + ((BOARD_LCD_H_RES - 128) / 2))\n"
        "#define DATE_TIME_LABEL_Y(y) ((y) - 14)\n"
    )
    if previous_native_layout in s:
        s = s.replace(previous_native_layout, updated_native_layout, 1)
    s = replace_once(
        s,
        "#define ROW_0_Y (9)\n#define ROW_0_H (20)\n\n#define ROW_1_Y (40)\n#define ROW_1_H (20)",
        "#if defined(BOARD_GUI_NATIVE_LCD) && BOARD_GUI_NATIVE_LCD\n"
        "#define ROW_0_Y (33)\n#define ROW_0_H (22)\n"
        "#define ROW_1_Y (78)\n#define ROW_1_H (22)\n"
        "#define DATE_TIME_X(x) ((x) + ((BOARD_LCD_H_RES - 128) / 2))\n"
        "#define DATE_TIME_LABEL_Y(y) ((y) - 14)\n"
        "#else\n"
        "#define ROW_0_Y (9)\n#define ROW_0_H (20)\n"
        "#define ROW_1_Y (40)\n#define ROW_1_H (20)\n"
        "#define DATE_TIME_X(x) (x)\n#define DATE_TIME_LABEL_Y(y) ((y) - 2)\n#endif",
        "native date and time editor layout",
    )
    block_start = s.index("static inline void date_time_input_draw_block(")
    block_end = s.index("\nstatic inline void date_time_input_draw_text(", block_start)
    block_fn = s[block_start:block_end]
    block_fn = replace_once(
        block_fn,
        "    furi_assert(canvas);\n    furi_assert(text);\n\n    canvas_set_color(canvas, ColorBlack);",
        "    furi_assert(canvas);\n    furi_assert(text);\n\n"
        "    x = DATE_TIME_X(x);\n    canvas_set_color(canvas, ColorBlack);",
        "center native date and time fields",
    )
    s = s[:block_start] + block_fn + s[block_end:]
    text_fn_start = s.index("static inline void date_time_input_draw_text(")
    text_fn_end = s.index("\nstatic void date_time_input_draw_hour_24hr_callback(", text_fn_start)
    text_fn = s[text_fn_start:text_fn_end]
    text_fn = replace_once(
        text_fn,
        "    furi_assert(canvas);\n    furi_assert(text);\n\n    canvas_set_color(canvas, ColorBlack);",
        "    furi_assert(canvas);\n    furi_assert(text);\n\n"
        "    x = DATE_TIME_X(x);\n    canvas_set_color(canvas, ColorBlack);",
        "center native date and time labels",
    )
    s = s[:text_fn_start] + text_fn + s[text_fn_end:]
    for old, new in (
        ("canvas_draw_str(canvas, 0, ROW_1_Y - 2,", "canvas_draw_str(canvas, DATE_TIME_X(0), DATE_TIME_LABEL_Y(ROW_1_Y),"),
        ("canvas_draw_str(canvas, 0, ROW_0_Y - 2,", "canvas_draw_str(canvas, DATE_TIME_X(0), DATE_TIME_LABEL_Y(ROW_0_Y),"),
        ("canvas_draw_box(canvas, 60,", "canvas_draw_box(canvas, DATE_TIME_X(60),"),
        ("canvas_draw_box(canvas, 94,", "canvas_draw_box(canvas, DATE_TIME_X(94),"),
        ("canvas_draw_box(canvas, 64 - 5,", "canvas_draw_box(canvas, DATE_TIME_X(64 - 5),"),
        ("canvas_draw_box(canvas, 98 - 5,", "canvas_draw_box(canvas, DATE_TIME_X(98 - 5),"),
    ):
        s = s.replace(old, new)
    return s


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
    size_t res = (model->is_vertical) ? 9 : 7;
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
        "components/gui/canvas.h": patch_canvas_header,
        "components/gui/canvas_i.h": patch_canvas_internal_header,
        "components/gui/canvas.c": patch_canvas,
        "components/furi_hal/furi_hal_display.c": patch_display_hal,
        "components/u8g2/u8g2_glue.c": patch_u8g2,
        "components/u8g2/CMakeLists.txt": patch_u8g2_cmake,
        "components/gui/view.h": patch_view_header,
        "components/gui/view_i.h": patch_view_internal_header,
        "components/gui/view.c": patch_view,
        "components/gui/view_port.c": patch_view_port,
        "components/gui/gui_i.h": patch_gui_header,
        "components/gui/elements.c": patch_multiline_elements,
        "components/gui/modules/menu.c": patch_menu,
        "components/gui/modules/file_browser.c": patch_file_browser,
        "components/gui/modules/text_box.c": patch_text_box,
        "components/gui/modules/text_input.c": patch_text_input,
        "components/gui/modules/variable_item_list.c": patch_variable_item_list,
        "components/gui/modules/number_input.c": patch_number_input,
        "components/gui/modules/byte_input.c": patch_byte_input,
        "components/gui/modules/date_time_input.c": patch_date_time_input,
        "components/gui/modules/submenu.c": patch_submenu,
        "applications/services/desktop/animations/views/bubble_animation_view.c": patch_bubble_home,
        "applications/settings/interface_settings/interface_settings_app.c": patch_interface_menu_style,
    }
    for relative_path, transform in paths.items():
        path = root / relative_path
        path.write_text(transform(path.read_text(encoding="utf-8")), encoding="utf-8")
    native_views = {
        "components/gui/modules/menu.c": ("menu->view", "menu_draw_callback"),
        "components/gui/modules/file_browser.c": ("browser->view", "file_browser_view_draw_callback"),
        "components/gui/modules/text_box.c": ("text_box->view", "text_box_view_draw_callback"),
        "components/gui/modules/text_input.c": ("text_input->view", "text_input_view_draw_callback"),
        "components/gui/modules/variable_item_list.c": ("variable_item_list->view", "variable_item_list_draw_callback"),
        "components/gui/modules/number_input.c": ("number_input->view", "number_input_view_draw_callback"),
        "components/gui/modules/byte_input.c": ("byte_input->view", "byte_input_view_draw_callback"),
        "components/gui/modules/date_time_input.c": ("date_time_input->view", "date_time_input_view_draw_callback"),
        "components/gui/modules/submenu.c": ("submenu->view", "submenu_view_draw_callback"),
        "applications/services/desktop/animations/views/bubble_animation_view.c": (
            "view->view",
            "bubble_animation_draw_callback",
        ),
    }
    for relative_path, (view_expr, callback) in native_views.items():
        path = root / relative_path
        path.write_text(
            patch_mark_native_layout(path.read_text(encoding="utf-8"), view_expr, callback),
            encoding="utf-8",
        )


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
