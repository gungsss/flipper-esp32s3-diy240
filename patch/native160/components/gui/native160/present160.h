#pragma once

#include "home160.h"
#include "list160.h"
#include "menu160.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define UI160_STRIP_ROWS 10u
#define UI160_DMA_PIXELS (MENU160_WIDTH * UI160_STRIP_ROWS)

/* The transport must finish using pixels before returning, including DMA. */
typedef bool (*Ui160Flush)(
    void* context, unsigned y, unsigned rows, const uint16_t* pixels);

typedef struct {
    uint16_t* dma_pixels;
    size_t capacity_pixels;
    Ui160Flush flush;
    void* context;
    bool swap_rgb565_bytes;
} Ui160Display;

typedef enum {
    UI160_PRESENT_OK,
    UI160_PRESENT_INVALID,
    UI160_PRESENT_TRANSPORT_ERROR,
} Ui160PresentResult;

Ui160PresentResult ui160_present_menu(Ui160Display* display, const Menu160Model* model);
Ui160PresentResult ui160_present_home(Ui160Display* display, const Home160Model* model);
Ui160PresentResult ui160_present_list(Ui160Display* display, const List160Model* model);
