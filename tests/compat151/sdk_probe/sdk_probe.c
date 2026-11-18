#include <furi.h>
#include <flipper_format/flipper_format.h>
#include <gui/modules/file_browser.h>
#include <toolbox/bit_buffer.h>
#include <toolbox/crc32_calc.h>

/* Compile and import check only. Physical-device execution is separate. */
int32_t sdk_151_probe_main(void* context) {
    UNUSED(context);
    const uint8_t data[] = "123456789";
    if(crc32_calc_buffer(0, data, sizeof(data) - 1) != 0xcbf43926u) return 1;

    BitBuffer* buffer = bit_buffer_alloc(1);
    bit_buffer_append_bit(buffer, true);
    bool bit_ok = bit_buffer_get_size(buffer) == 1;
    bit_buffer_free(buffer);
    if(!bit_ok) return 2;

    FlipperFormat* format = flipper_format_string_alloc();
    const int32_t value = 151;
    bool format_ok = flipper_format_write_int32(format, "Value", &value, 1);
    format_ok &= flipper_format_write_string_cstr(format, "Name", "first");
    format_ok &= flipper_format_update_string_cstr(format, "Name", "second");
    flipper_format_free(format);
    if(!format_ok) return 3;

    FuriString* path = furi_string_alloc_set("/ext");
    FileBrowser* browser = file_browser_alloc(path);
    file_browser_free(browser);
    furi_string_free(path);
    return 0;
}
