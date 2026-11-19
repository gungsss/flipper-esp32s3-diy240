#pragma once

#include "../canvas.h"
#include "menu160.h"
#include "list160.h"

#include <stdbool.h>

/* Internal GUI-thread APIs: do not call from other rendering threads. */
bool native160_panel_supported(void);
void native160_canvas_mark_home(Canvas* canvas);
bool native160_canvas_present_menu(Canvas* canvas, const Menu160Model* model);
bool native160_canvas_present_list(Canvas* canvas, const List160Model* model);
bool native160_canvas_present_home(Canvas* canvas);
void native160_canvas_commit(Canvas* canvas, const uint8_t* pixels, size_t size);
