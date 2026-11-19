#pragma once
#define M_POD_OPLIST 0
#define ARRAY_DEF(name, type, opts) typedef struct { int unused; } name##_t
#define ARRAY_OPLIST(name, opts) 0
