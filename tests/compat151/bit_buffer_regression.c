#include <toolbox/bit_buffer.h>
#include <assert.h>
#include <stdint.h>

int main(void) {
    BitBuffer* one = bit_buffer_alloc(1);
    for(unsigned value = 0; value <= UINT8_MAX; ++value) {
        uint8_t data = (uint8_t)value;
        bit_buffer_copy_bytes(one, &data, 1);
        for(size_t offset = 0; offset < 8; ++offset) {
            assert(bit_buffer_get_byte_from_bit(one, offset) == (uint8_t)(value >> offset));
        }
    }
    bit_buffer_free(one);

    BitBuffer* two = bit_buffer_alloc(2);
    for(unsigned a = 0; a <= UINT8_MAX; a += 17) {
        for(unsigned b = 0; b <= UINT8_MAX; b += 31) {
            uint8_t data[] = {(uint8_t)a, (uint8_t)b};
            bit_buffer_copy_bytes(two, data, sizeof(data));
            for(size_t offset = 0; offset < 8; ++offset) {
                uint16_t pair = (uint16_t)(a | (b << 8));
                assert(bit_buffer_get_byte_from_bit(two, offset) == (uint8_t)(pair >> offset));
                assert(bit_buffer_get_byte_from_bit(two, 8 + offset) == (uint8_t)(b >> offset));
            }
        }
    }
    bit_buffer_free(two);
    return 0;
}
