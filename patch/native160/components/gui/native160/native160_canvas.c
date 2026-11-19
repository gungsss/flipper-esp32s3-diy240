#include "native160_canvas.h"

#include "../canvas_i.h"
#include "frame160.h"

#include <esp_heap_caps.h>
#include <furi_hal.h>
#include <string.h>

bool native160_panel_supported(void) {
    return furi_hal_display_get_h_res() == MENU160_WIDTH &&
           furi_hal_display_get_v_res() == MENU160_HEIGHT;
}

static bool native160_canvas_supported(const Canvas* canvas) {
    return canvas && native160_panel_supported() &&
           canvas_get_orientation(canvas) == CanvasOrientationHorizontal;
}

static bool native160_full_frame(const Canvas* canvas) {
    return native160_canvas_supported(canvas) &&
           canvas->offset_x == 0 && canvas->offset_y == 0 &&
           canvas->width == UI160_LEGACY_WIDTH && canvas->height == UI160_LEGACY_HEIGHT;
}

static bool native160_flush(void* context, unsigned y, unsigned rows, const uint16_t* pixels) {
    (void)context;
    return furi_hal_display_draw_rgb565(0, (uint16_t)y, MENU160_WIDTH, (uint16_t)rows, pixels);
}

static bool native160_display(Canvas* canvas, Ui160Display* out) {
    /* The completed u8g2 framebuffer already contains any orientation
     * transform. Legacy views can therefore use the native-pixel presenter
     * even when the current logical view is flipped or rotated. */
    if(!canvas || !native160_panel_supported() || furi_hal_display_is_asleep()) return false;
    if(!canvas->native160_dma) {
        canvas->native160_dma = heap_caps_malloc(
            UI160_DMA_PIXELS * sizeof(uint16_t), MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
    }
    if(!canvas->native160_dma) return false;
    *out = (Ui160Display){
        .dma_pixels = canvas->native160_dma,
        .capacity_pixels = UI160_DMA_PIXELS,
        .flush = native160_flush,
        .context = NULL,
        .swap_rgb565_bytes = true,
    };
    return true;
}

void native160_canvas_mark_home(Canvas* canvas) {
    if(native160_full_frame(canvas)) canvas->native160_home_pending = true;
}

bool native160_canvas_present_menu(Canvas* canvas, const Menu160Model* model) {
    Ui160Display display;
    if(!native160_full_frame(canvas) || !menu160_supported(model)) return false;
    if(canvas_get_buffer_size(canvas) != UI160_LEGACY_BYTES || !canvas_get_buffer(canvas)) return false;
    if(!native160_display(canvas, &display)) return false;
    if(ui160_present_menu(&display, model) != UI160_PRESENT_OK) return false;
    memcpy(canvas->native160_view_snapshot, canvas_get_buffer(canvas), UI160_LEGACY_BYTES);
    canvas->native160_snapshot_valid = true;
    canvas->native160_menu_presented = true;
    return true;
}

bool native160_canvas_present_list(Canvas* canvas, const List160Model* model) {
    Ui160Display display;
    if(!native160_full_frame(canvas) || !list160_supported(model)) return false;
    if(canvas_get_buffer_size(canvas) != UI160_LEGACY_BYTES || !canvas_get_buffer(canvas)) return false;
    if(!native160_display(canvas, &display)) return false;
    if(ui160_present_list(&display, model) != UI160_PRESENT_OK) return false;
    memcpy(canvas->native160_view_snapshot, canvas_get_buffer(canvas), UI160_LEGACY_BYTES);
    canvas->native160_snapshot_valid = true;
    canvas->native160_menu_presented = true;
    return true;
}

bool native160_canvas_present_home(Canvas* canvas) {
    Ui160Display display;
    if(!native160_canvas_supported(canvas)) return false;
    if(!native160_display(canvas, &display)) return false;
    return ui160_present_legacy_home(
               &display, canvas_get_buffer(canvas), canvas_get_buffer_size(canvas)) ==
           UI160_PRESENT_OK;
}

void native160_canvas_commit(Canvas* canvas, const uint8_t* pixels, size_t size) {
    /* A later legacy layer may have drawn on top of the view after the native
     * transfer. In that case repaint the completed framebuffer instead of
     * hiding the overlay. */
    bool presented = canvas->native160_menu_presented && canvas->native160_snapshot_valid &&
                     pixels && size == UI160_LEGACY_BYTES &&
                     memcmp(canvas->native160_view_snapshot, pixels, UI160_LEGACY_BYTES) == 0;
    if(!presented && canvas->native160_home_pending) {
        presented = native160_canvas_present_home(canvas);
    }
    /* Legacy views are composed within a 160x128 frame at exactly one panel
     * pixel per framebuffer pixel. This is a compatibility layout, not a
     * claim that every application's own layout has been reflowed. */
    if(!presented && native160_panel_supported()) {
        Ui160Display display;
        if(native160_display(canvas, &display)) {
            presented = ui160_present_legacy_home(&display, pixels, size) == UI160_PRESENT_OK;
        }
    }
    /* The HAL's 160x128 fallback is also 1:1. It can repair the panel after
     * a partial native transfer or an allocation failure without stretching. */
    if(!presented && !(native160_panel_supported() && furi_hal_display_is_asleep())) {
        furi_hal_display_commit(pixels, (uint32_t)size);
    }
    canvas->native160_home_pending = false;
    canvas->native160_menu_presented = false;
    canvas->native160_snapshot_valid = false;
}
