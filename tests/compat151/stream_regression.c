#include <toolbox/stream/string_stream.h>
#include <assert.h>
#include <string.h>

int main(void) {
    Stream* stream = string_stream_alloc();
    FuriString* line = furi_string_alloc();
    assert(stream_write_cstring(stream, "alpha\nbeta\n") == 11);
    assert(stream_rewind(stream));
    assert(stream_read_line(stream, line));
    assert(strcmp(furi_string_get_cstr(line), "alpha\n") == 0);
    assert(stream_read_line(stream, line));
    assert(strcmp(furi_string_get_cstr(line), "beta\n") == 0);
    assert(!stream_read_line(stream, line));

    stream_clean(stream);
    assert(stream_write_cstring(stream, "abcXYZ") == 6);
    assert(stream_seek(stream, 3, StreamOffsetFromStart));
    assert(stream_delete_and_insert_cstring(stream, 3, "123"));
    assert(stream_rewind(stream));
    uint8_t output[6];
    assert(stream_read(stream, output, sizeof(output)) == sizeof(output));
    assert(memcmp(output, "abc123", sizeof(output)) == 0);
    furi_string_free(line);
    stream_free(stream);
    return 0;
}
