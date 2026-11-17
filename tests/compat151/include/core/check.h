#pragma once
#include <assert.h>
#include <stdlib.h>
#define furi_check(expr) assert(expr)
#define furi_crash(...) abort()
