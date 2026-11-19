/* Host integration of the real submenu and settings-list draw callbacks.
 * Hardware rendering and the ESP-IDF build are outside this test. */
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "submenu.c"
#include "variable_item_list.c"

struct FuriString { char text[128]; };
struct Canvas { int unused; };
struct Icon { int unused; };
struct FuriTimer { int unused; };
struct View { void* model; void* context; ViewDrawCallback draw; ViewInputCallback input; };
const Icon I_Lock_7x8 = {0};
const Icon I_WarningDolphin_45x42 = {0};
const uint8_t u8g2_font_5x7_tr[] = {0};

FuriString* furi_string_alloc(void) { return calloc(1, sizeof(FuriString)); }
FuriString* furi_string_alloc_set(const FuriString* s) {
    FuriString* result=furi_string_alloc();
    memcpy(result, s, sizeof(*result));
    return result;
}
void furi_string_free(FuriString* s) { free(s); }
void furi_string_set_str(FuriString* s, const char* value) {
    snprintf(s->text, sizeof(s->text), "%s", value);
}
void furi_string_set(FuriString* s, const void* value) {
    /* The tested draw path uses alloc_set or set_str; see notes in stub. */
    (void)s; (void)value; abort();
}
void furi_string_reset(FuriString* s) { s->text[0]=0; }
const char* furi_string_get_cstr(const FuriString* s) { return s->text; }
size_t furi_string_size(const FuriString* s) { return strlen(s->text); }
bool furi_string_empty(const FuriString* s) { return !s->text[0]; }
FuriTimer* furi_timer_alloc(void (*cb)(void*), FuriTimerType type, void* context) {(void)cb;(void)type;(void)context;return calloc(1,sizeof(FuriTimer));}
void furi_timer_free(FuriTimer* timer) {free(timer);}
void furi_timer_start(FuriTimer* timer,uint32_t ticks) {(void)timer;(void)ticks;}
void furi_timer_stop(FuriTimer* timer) {(void)timer;}
uint32_t furi_kernel_get_tick_frequency(void) {return 1000;}
View* view_alloc(void) {return calloc(1,sizeof(View));}
void view_free(View* view) {free(view->model);free(view);}
void view_set_context(View* view,void* context) {view->context=context;}
void view_allocate_model(View* view,ViewModelType type,size_t size) {
    (void)type;view->model=malloc(size);memset(view->model,0xA5,size);
}
void view_set_draw_callback(View* view,ViewDrawCallback cb) {view->draw=cb;}
void view_set_input_callback(View* view,ViewInputCallback cb) {view->input=cb;}
void* view_get_model(View* view) {return view->model;}
void view_commit_model(View* view,bool update) {(void)view;(void)update;}
void view_set_orientation(View* view,ViewOrientation orientation) {(void)view;(void)orientation;}

size_t canvas_width(const Canvas* canvas) { (void)canvas; return 128; }
size_t canvas_height(const Canvas* canvas) { (void)canvas; return 64; }
void canvas_clear(Canvas* c) {(void)c;}
void canvas_set_color(Canvas* c, Color x) {(void)c;(void)x;}
void canvas_set_font(Canvas* c, Font x) {(void)c;(void)x;}
void canvas_set_custom_u8g2_font(Canvas* c, const uint8_t* f) {(void)c;(void)f;}
void canvas_draw_str(Canvas* c, int32_t x, int32_t y, const char* s) {(void)c;(void)x;(void)y;(void)s;}
void canvas_draw_str_aligned(Canvas* c, int32_t x, int32_t y, Align h, Align v, const char* s) {(void)c;(void)x;(void)y;(void)h;(void)v;(void)s;}
void canvas_draw_line(Canvas* c, int32_t x, int32_t y, int32_t x2, int32_t y2) {(void)c;(void)x;(void)y;(void)x2;(void)y2;}
void canvas_draw_icon(Canvas* c, int32_t x, int32_t y, const Icon* i) {(void)c;(void)x;(void)y;(void)i;}
void canvas_draw_box(Canvas* c, int32_t x, int32_t y, size_t w, size_t h) {(void)c;(void)x;(void)y;(void)w;(void)h;}
void canvas_draw_rframe(Canvas* c, int32_t x, int32_t y, size_t w, size_t h, size_t r) {(void)c;(void)x;(void)y;(void)w;(void)h;(void)r;}
void elements_slightly_rounded_box(Canvas* c,int32_t x,int32_t y,size_t w,size_t h) {(void)c;(void)x;(void)y;(void)w;(void)h;}
void elements_string_fit_width(Canvas* c,FuriString* s,size_t w) {(void)c;(void)s;(void)w;}
void elements_scrollbar(Canvas* c,size_t pos,size_t total) {(void)c;(void)pos;(void)total;}
void elements_multiline_text_aligned(Canvas* c,int32_t x,int32_t y,Align h,Align v,const char* s) {(void)c;(void)x;(void)y;(void)h;(void)v;(void)s;}
void elements_scrollable_text_line_str(Canvas* c,uint8_t x,uint8_t y,uint8_t w,const char* s,size_t scroll,bool ellipsis,bool center) {(void)c;(void)x;(void)y;(void)w;(void)s;(void)scroll;(void)ellipsis;(void)center;}

static bool captured;
static size_t captured_count, captured_selected;
static bool captured_editing;
static List160Item captured_items[4];
static char captured_title[32], captured_labels[4][128], captured_values[4][128];
bool native160_canvas_present_list(Canvas* canvas, const List160Model* model) {
    (void)canvas;
    captured=true;
    captured_count=model->count;
    captured_selected=model->selected;
    captured_editing=model->editing;
    snprintf(captured_title,sizeof(captured_title),"%s",model->title);
    for(size_t i=0; i<model->count && i<4; i++) {
        assert(model->get_item(model->context,i,&captured_items[i]));
        snprintf(captured_labels[i],sizeof(captured_labels[i]),"%s",captured_items[i].label ? captured_items[i].label : "");
        snprintf(captured_values[i],sizeof(captured_values[i]),"%s",captured_items[i].value ? captured_items[i].value : "");
    }
    return true;
}

int main(void) {
    Canvas canvas={0};
    /* Seed freshly allocated models with non-zero bytes to verify that the
     * view constructors actually initialise flags used by native rendering. */
    Submenu* allocated_submenu=submenu_alloc();
    SubmenuModel* allocated_submenu_model=view_get_model(allocated_submenu->view);
    assert(!allocated_submenu_model->locked_message_visible && !allocated_submenu_model->is_vertical &&
           !allocated_submenu_model->header_centered);
    submenu_free(allocated_submenu);
    VariableItemList* allocated_variables=variable_item_list_alloc();
    VariableItemListModel* allocated_variables_model=view_get_model(allocated_variables->view);
    assert(!allocated_variables_model->locked_message_visible && !allocated_variables_model->editing);
    variable_item_list_free(allocated_variables);
    SubmenuItem source, copied;
    SubmenuItem_init(&source);
    source.has_extended_events=true;
    SubmenuItem_init_set(&copied,&source);
    assert(copied.has_extended_events);
    SubmenuItem_clear(&copied);
    SubmenuItem_clear(&source);

    SubmenuModel sub={0};
    SubmenuItemArray_init(sub.items);
    sub.header=furi_string_alloc();
    furi_string_set_str(sub.header,"Settings");
    SubmenuItem* first=SubmenuItemArray_push_new(sub.items);
    furi_string_set_str(first->label,"Display");
    SubmenuItem* second=SubmenuItemArray_push_new(sub.items);
    furi_string_set_str(second->label,"Locked");
    furi_string_set_str(second->locked_message,"Locked message");
    second->locked=true;
    sub.position=1;
    captured=false;
    submenu_view_draw_callback(&canvas,&sub);
    assert(captured && captured_count==2 && captured_selected==1);
    assert(strcmp(captured_title,"Settings")==0 && strcmp(captured_labels[0],"Display")==0);
    assert(captured_items[1].locked);
    sub.locked_message_visible=true;
    captured=false;
    submenu_view_draw_callback(&canvas,&sub);
    assert(!captured);
    sub.locked_message_visible=false;
    sub.is_vertical=true;
    captured=false;
    submenu_view_draw_callback(&canvas,&sub);
    assert(!captured);
    SubmenuItemArray_clear(sub.items);
    furi_string_free(sub.header);

    VariableItemListModel vars={0};
    VariableItemArray_init(vars.items);
    vars.header=furi_string_alloc();
    furi_string_set_str(vars.header,"Brightness");
    VariableItem* variable=VariableItemArray_push_new(vars.items);
    memset(variable,0,sizeof(*variable));
    variable->label="Level";
    variable->current_value_text=furi_string_alloc();
    furi_string_set_str(variable->current_value_text,"50%");
    variable->locked_message=furi_string_alloc();
    furi_string_set_str(variable->locked_message,"Locked message");
    variable->values_count=3;
    variable->current_value_index=1;
    vars.editing=true;
    captured=false;
    variable_item_list_draw_callback(&canvas,&vars);
    assert(captured && captured_count==1 && captured_selected==0 && captured_editing);
    assert(strcmp(captured_labels[0],"Level")==0 && strcmp(captured_values[0],"50%")==0);
    assert(captured_items[0].has_value && captured_items[0].can_decrease && captured_items[0].can_increase);
    vars.locked_message_visible=true;
    captured=false;
    variable_item_list_draw_callback(&canvas,&vars);
    assert(!captured);
    furi_string_free(variable->current_value_text);
    furi_string_free(variable->locked_message);
    VariableItemArray_clear(vars.items);
    furi_string_free(vars.header);
    puts("PASS: real submenu/settings models, locked dialogs and native list adapter");
}
