#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <assert.h>
typedef struct FuriString FuriString;
typedef struct FuriTimer FuriTimer;
typedef enum { FuriTimerTypeOnce, FuriTimerTypePeriodic } FuriTimerType;
FuriString* furi_string_alloc(void);
FuriString* furi_string_alloc_set(const FuriString*);
void furi_string_free(FuriString*);
void furi_string_set(FuriString*,const void*);
void furi_string_set_str(FuriString*,const char*);
void furi_string_reset(FuriString*);
const char* furi_string_get_cstr(const FuriString*);
size_t furi_string_size(const FuriString*);
bool furi_string_empty(const FuriString*);
FuriTimer* furi_timer_alloc(void(*)(void*),FuriTimerType,void*);
void furi_timer_free(FuriTimer*);
void furi_timer_start(FuriTimer*,uint32_t);
void furi_timer_stop(FuriTimer*);
uint32_t furi_kernel_get_tick_frequency(void);
#define furi_assert(x) assert(x)
#define furi_check(x) assert(x)
#define UNUSED(x) ((void)(x))
