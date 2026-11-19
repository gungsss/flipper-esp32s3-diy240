#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
    const char* label;
    const char* value;
    bool has_value;
    bool locked;
    bool separator;
    bool centered;
    bool can_decrease;
    bool can_increase;
} List160Item;

/* The item and its strings must remain valid during the synchronous draw. */
typedef bool (*List160GetItem)(void* context, size_t index, List160Item* item);
typedef struct {
    const char* title;
    size_t count;
    size_t selected;
    bool editing;
    List160GetItem get_item;
    void* context;
} List160Model;

/* False means use the original view. This keeps unsupported characters and
 * long, scrollable text from silently changing meaning on the small font. */
bool list160_supported(const List160Model* model);
bool list160_render_strip(uint16_t* pixels, size_t pixel_count, unsigned first_y,
                          unsigned rows, const List160Model* model);
