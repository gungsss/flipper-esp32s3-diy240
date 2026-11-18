#pragma once
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define furi_check(expr) assert(expr)
#define FURI_BIT(x, n) (((x) >> (n)) & 1)
