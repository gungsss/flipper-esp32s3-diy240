#include "bit_lib.h"
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>

static uint8_t reference(const uint8_t* data, size_t start, uint8_t count) {
    uint8_t value = 0;
    for(uint8_t index = 0; index < count; index++) {
        size_t bit = start + index;
        value = (uint8_t)((value << 1) | ((data[bit / 8] >> (7 - bit % 8)) & 1));
    }
    return value;
}

int main(void) {
    /* ASan places a redzone immediately after this one byte.  Reads that do
     * not cross the boundary must never access a second byte. */
    uint8_t* byte = malloc(1);
    assert(byte);
    for(unsigned value = 0; value <= UINT8_MAX; value++) {
        *byte = (uint8_t)value;
        for(size_t start = 0; start < 8; start++) {
            for(uint8_t count = 1; count <= 8 - start; count++) {
                assert(bit_lib_get_bits(byte, start, count) == reference(byte, start, count));
            }
        }
    }
    free(byte);

    /* Also verify reads that genuinely cross into the next byte. */
    uint8_t input[2] = {0xa5, 0x3c};
    for(size_t start = 0; start < 8; start++) {
        for(uint8_t count = 1; count <= 8; count++) {
            assert(bit_lib_get_bits(input, start, count) == reference(input, start, count));
        }
    }
    return 0;
}
