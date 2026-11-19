#include <core/memmgr.h>
#include <gui/modules/menu.h>
#include <toolbox/bit_buffer.h>
#include <toolbox/hex.h>
#include <toolbox/varint.h>
#include <stdint.h>

int32_t generic_sdk_probe(void* context) {
    (void)context;
    const uint8_t data[] = {0xa5};
    BitBuffer* first = bit_buffer_alloc(1);
    BitBuffer* second = bit_buffer_alloc(2);
    bit_buffer_copy_bytes(first, data, sizeof(data));
    bit_buffer_append(second, first);
    uint8_t value = bit_buffer_get_byte_from_bit(second, 0);
    uint8_t packed[5];
    int32_t unpacked = 0;
    size_t packed_size = varint_int32_pack(-123, packed);
    size_t consumed = varint_int32_unpack(&unpacked, packed, packed_size);
    uint8_t parsed = 0;
    bool parsed_ok = hex_chars_to_uint8("7f", &parsed);
    Menu* menu = menu_alloc();
    menu_free(menu);
    void* aligned = aligned_malloc(16, 4);
    aligned_free(aligned);
    size_t low_water = memmgr_get_minimum_free_heap();
    bit_buffer_free(second);
    bit_buffer_free(first);
    return value + (int32_t)consumed + unpacked + parsed + parsed_ok + (int32_t)(low_water & 1);
}
