#include "present160.h"

typedef bool (*RenderStrip)(uint16_t*, size_t, unsigned, unsigned, const void*);

static bool render_menu(
    uint16_t* pixels, size_t count, unsigned y, unsigned rows, const void* model) {
    return menu160_render_strip(pixels, count, y, rows, model);
}

static bool render_home(
    uint16_t* pixels, size_t count, unsigned y, unsigned rows, const void* model) {
    return home160_render_strip(pixels, count, y, rows, model);
}

static bool render_list(
    uint16_t* pixels, size_t count, unsigned y, unsigned rows, const void* model) {
    return list160_render_strip(pixels, count, y, rows, model);
}

static Ui160PresentResult present(Ui160Display* display, const void* model, RenderStrip render) {
    if(!display || !display->dma_pixels || display->capacity_pixels < UI160_DMA_PIXELS ||
       !display->flush || !model) {
        return UI160_PRESENT_INVALID;
    }
    for(unsigned y = 0; y < MENU160_HEIGHT; y += UI160_STRIP_ROWS) {
        unsigned rows = MENU160_HEIGHT - y;
        if(rows > UI160_STRIP_ROWS) rows = UI160_STRIP_ROWS;
        const size_t count = (size_t)MENU160_WIDTH * rows;
        if(!render(display->dma_pixels, display->capacity_pixels, y, rows, model)) {
            return UI160_PRESENT_INVALID;
        }
        if(display->swap_rgb565_bytes) {
            for(size_t i = 0; i < count; i++) {
                uint16_t pixel = display->dma_pixels[i];
                display->dma_pixels[i] = (uint16_t)((pixel << 8) | (pixel >> 8));
            }
        }
        if(!display->flush(display->context, y, rows, display->dma_pixels)) {
            return UI160_PRESENT_TRANSPORT_ERROR;
        }
    }
    return UI160_PRESENT_OK;
}

Ui160PresentResult ui160_present_menu(Ui160Display* display, const Menu160Model* model) {
    if(!menu160_supported(model)) return UI160_PRESENT_INVALID;
    return present(display, model, render_menu);
}

Ui160PresentResult ui160_present_home(Ui160Display* display, const Home160Model* model) {
    return present(display, model, render_home);
}

Ui160PresentResult ui160_present_list(Ui160Display* display, const List160Model* model) {
    if(!list160_supported(model)) return UI160_PRESENT_INVALID;
    return present(display, model, render_list);
}
