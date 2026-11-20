#!/usr/bin/env python3
"""Check that the complete Flipper UI render path targets ST7735S 160x128.

This is a source/layout contract audit. It complements ESP-IDF compilation; it
cannot replace visual inspection on the actual board.
"""
import re
import sys
from pathlib import Path


REQUIRED_NATIVE_VIEWS = {
    "components/gui/modules/menu.c": "menu_draw_callback",
    "components/gui/modules/file_browser.c": "file_browser_view_draw_callback",
    "components/gui/modules/text_box.c": "text_box_view_draw_callback",
    "components/gui/modules/text_input.c": "text_input_view_draw_callback",
    "components/gui/modules/variable_item_list.c": "variable_item_list_draw_callback",
    "components/gui/modules/number_input.c": "number_input_view_draw_callback",
    "components/gui/modules/byte_input.c": "byte_input_view_draw_callback",
    "components/gui/modules/date_time_input.c": "date_time_input_view_draw_callback",
    "components/gui/modules/submenu.c": "submenu_view_draw_callback",
    "applications/services/desktop/animations/views/bubble_animation_view.c": "bubble_animation_draw_callback",
}


# Each public Canvas drawing API must transform legacy coordinates before it
# reaches U8g2. Geometry primitives also scale their dimensions; bitmap APIs use
# the bounded bitmap resampler for larger images.
CANVAS_REQUIREMENTS = {
    "canvas_draw_str": ("canvas_scale_x(canvas, x)", "canvas_scale_y(canvas, y)"),
    "canvas_draw_str_aligned": ("canvas_scale_x(canvas, x)", "canvas_scale_y(canvas, y)"),
    "canvas_draw_bitmap": ("canvas_draw_legacy_bitmap(canvas",),
    "canvas_draw_icon_ex": ("canvas_scale_x(canvas, x)", "canvas_scale_y(canvas, y)"),
    "canvas_draw_icon": ("canvas_scale_x(canvas, x)", "canvas_scale_y(canvas, y)"),
    "canvas_draw_dot": ("canvas_scale_x(canvas, x)", "canvas_scale_y(canvas, y)"),
    "canvas_draw_box": ("canvas_scale_width(canvas, width)", "canvas_scale_height(canvas, height)"),
    "canvas_draw_rbox": ("canvas_scale_width(canvas, width)", "canvas_scale_height(canvas, height)"),
    "canvas_draw_frame": ("canvas_scale_width(canvas, width)", "canvas_scale_height(canvas, height)"),
    "canvas_draw_rframe": ("canvas_scale_width(canvas, width)", "canvas_scale_height(canvas, height)"),
    "canvas_draw_line": ("canvas_scale_x(canvas, x1)", "canvas_scale_y(canvas, y1)",
                         "canvas_scale_x(canvas, x2)", "canvas_scale_y(canvas, y2)"),
    "canvas_draw_circle": ("canvas_scale_x(canvas, x)", "canvas_scale_y(canvas, y)"),
    "canvas_draw_disc": ("canvas_scale_x(canvas, x)", "canvas_scale_y(canvas, y)"),
    "canvas_draw_triangle": ("canvas_draw_line(canvas",),
    "canvas_draw_xbm_ex": ("canvas_draw_legacy_bitmap(canvas",),
    "canvas_draw_glyph": ("canvas_scale_x(canvas, x)", "canvas_scale_y(canvas, y)"),
    "canvas_draw_icon_bitmap": ("canvas_scale_x(canvas, x)", "canvas_scale_y(canvas, y)"),
}


def require(condition, message):
    if not condition:
        raise SystemExit(f"UI audit failed: {message}")


def function_body(source, name):
    match = re.search(rf"\b{re.escape(name)}\s*\([^;]*?\)\s*\{{", source, re.S)
    require(match is not None, f"Canvas function {name} is missing")
    opening = source.find("{", match.start())
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening:index + 1]
    raise SystemExit(f"UI audit failed: unterminated Canvas function {name}")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: audit_st7735_ui.py /path/to/patched/upstream")
    root = Path(sys.argv[1]).resolve()

    def read(relative):
        path = root / relative
        require(path.is_file(), f"missing source file: {relative}")
        return path.read_text(encoding="utf-8")

    board = read("components/furi_hal/boards/board_DIY.h")
    for macro in (
        "#define BOARD_LCD_H_RES 160",
        "#define BOARD_LCD_V_RES 128",
        "#define BOARD_GUI_NATIVE_LCD 1",
        "#define BOARD_LCD_FILL_SCREEN 1",
        "#define BOARD_LCD_SIDE_MARGIN 0",
    ):
        require(macro in board, f"panel geometry does not include {macro}")

    display = read("components/furi_hal/furi_hal_display.c")
    require("#define FB_WIDTH  LCD_H_RES" in display, "framebuffer width is not native panel width")
    require("#define FB_HEIGHT LCD_V_RES" in display, "framebuffer height is not native panel height")
    require("#define SCALED_WIDTH  FB_WIDTH" in display, "display path is not full-screen")
    require("#define SCALED_HEIGHT FB_HEIGHT" in display, "display path is not full-screen")

    u8g2 = read("components/u8g2/u8g2_glue.c")
    require(".pixel_width = 160" in u8g2 and ".pixel_height = 128" in u8g2,
            "U8g2 canvas is not 160x128")
    require("u8g2_m_20_16_f" in u8g2, "U8g2 framebuffer is not allocated for 160x128")

    canvas = read("components/gui/canvas.c")
    for name, required_tokens in CANVAS_REQUIREMENTS.items():
        body = function_body(canvas, name)
        for token in required_tokens:
            require(token in body, f"{name} bypasses full-screen transform ({token})")
    require("canvas_legacy_logical_width" in canvas and "canvas_legacy_logical_height" in canvas,
            "legacy 128x64 coordinate map is missing")
    require("scaled_bitmap[(BOARD_LCD_H_RES * BOARD_LCD_V_RES + 7) / 8]" in canvas,
            "large legacy images are not resampled for the full panel")

    view = read("components/gui/view.c")
    require("canvas_set_legacy_scale(canvas, !view->native_layout)" in view,
            "View draw callbacks are not routed through native or legacy layout")
    viewport = read("components/gui/view_port.c")
    require("canvas_set_legacy_scale(canvas, true)" in viewport,
            "custom ViewPort draw callbacks are not adapted to the full panel")

    for relative, callback in REQUIRED_NATIVE_VIEWS.items():
        source = read(relative)
        require(f"view_set_draw_callback" in source and callback in source,
                f"native layout callback is missing in {relative}")
        require("view_set_native_layout" in source,
                f"native layout opt-out is missing in {relative}")

    menu = read("components/gui/modules/menu.c")
    require("const size_t row_count = MIN((size_t)5, items_count);" in menu,
            "launcher does not use the five-row full-height layout")
    file_browser = read("components/gui/modules/file_browser.c")
    require("#define LIST_ITEMS   9u" in file_browser,
            "file browser does not use the expanded screen height")
    elements = read("components/gui/elements.c")
    require("y < canvas_height(canvas)" in elements,
            "multiline text still stops at the old 64-pixel boundary")

    app_sources = list((root / "applications").rglob("*.c"))
    app_view_callbacks = sum(
        len(re.findall(r"\bview_set_draw_callback\s*\(", path.read_text(encoding="utf-8")))
        for path in app_sources
    )
    app_viewports = sum(
        len(re.findall(r"\bview_port_set_draw_callback\s*\(", path.read_text(encoding="utf-8")))
        for path in app_sources
    )
    print(
        "PASSED: 160x128 full-panel path; "
        f"{len(CANVAS_REQUIREMENTS)} Canvas APIs audited; "
        f"{len(REQUIRED_NATIVE_VIEWS)} native screen modules; "
        f"{app_view_callbacks} application View callbacks and {app_viewports} ViewPort callbacks "
        "flow through the shared GUI adapters."
    )


if __name__ == "__main__":
    main()
