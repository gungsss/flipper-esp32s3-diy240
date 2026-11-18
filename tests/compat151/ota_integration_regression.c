#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <furi.h>
#include <storage/storage.h>
#include <esp_app_format.h>
#include <esp_app_desc.h>
#include <esp_ota_ops.h>
#include "fw_ota.h"
#include "fw_ota_profile.h"

static uint8_t image[400];
static size_t image_size = sizeof(image);
static unsigned erase_calls;
static unsigned write_calls;
static size_t written_bytes;
static Storage storage;
static esp_partition_t partition = {.label = "ota_1"};

void* furi_record_open(const char* name) { (void)name; return &storage; }
void furi_record_close(const char* name) { (void)name; }
FS_Error storage_common_stat(Storage* s, const char* path, FileInfo* info) {
    (void)s;
    if(!path || strcmp(path, "/ext/update/furi_esp32.bin")) return FSE_NOT_EXIST;
    info->size = image_size;
    return FSE_OK;
}
File* storage_file_alloc(Storage* s) { (void)s; return calloc(1, sizeof(File)); }
void storage_file_free(File* f) { free(f); }
bool storage_file_open(File* f, const char* path, FS_AccessMode access, FS_OpenMode mode) {
    (void)access; (void)mode;
    if(strcmp(path, "/ext/update/furi_esp32.bin")) return false;
    f->pos = 0;
    return true;
}
bool storage_file_close(File* f) { (void)f; return true; }
bool storage_file_seek(File* f, uint32_t offset, bool from_start) {
    if(!from_start || offset > image_size) return false;
    f->pos = offset;
    return true;
}
size_t storage_file_read(File* f, void* dst, size_t count) {
    if(count > image_size - f->pos) count = image_size - f->pos;
    memcpy(dst, image + f->pos, count);
    f->pos += count;
    return count;
}
size_t storage_file_write(File* f, const void* src, size_t count) {
    (void)f; (void)src; return count;
}
const esp_partition_t* esp_ota_get_next_update_partition(const void* unused) {
    (void)unused; return &partition;
}
const esp_partition_t* esp_ota_get_running_partition(void) { return &partition; }
esp_err_t esp_ota_begin(const esp_partition_t* p, size_t size, esp_ota_handle_t* handle) {
    assert(p == &partition && size == image_size);
    ++erase_calls;
    *handle = 1;
    return ESP_OK;
}
esp_err_t esp_ota_write(esp_ota_handle_t handle, const void* data, size_t size) {
    assert(handle == 1 && data);
    ++write_calls;
    written_bytes += size;
    return ESP_OK;
}
esp_err_t esp_ota_end(esp_ota_handle_t handle) { assert(handle == 1); return ESP_OK; }
esp_err_t esp_ota_abort(esp_ota_handle_t handle) { (void)handle; return ESP_OK; }
esp_err_t esp_ota_set_boot_partition(const esp_partition_t* p) {
    assert(p == &partition); return ESP_OK;
}
void* heap_caps_malloc(size_t n, unsigned flags) { (void)flags; return malloc(n); }

static void make_image(void) {
    memset(image, 0, sizeof(image));
    image_size = sizeof(image);
    esp_image_header_t header = {.magic = ESP_IMAGE_HEADER_MAGIC, .chip_id = 9};
    esp_app_desc_t description = {.magic_word = ESP_APP_DESC_MAGIC_WORD};
    strcpy(description.project_name, FW_OTA_PROJECT_NAME);
    strcpy(description.version, "test-only");
    memcpy(image, &header, sizeof(header));
    size_t offset = sizeof(header) + sizeof(esp_image_segment_header_t);
    memcpy(image + offset, &description, sizeof(description));
    offset += sizeof(description);
    memcpy(image + offset, &fw_ota_board_profile, sizeof(fw_ota_board_profile));
    erase_calls = write_calls = 0;
    written_bytes = 0;
}

int main(void) {
    const char* path = "/ext/update/furi_esp32.bin";
    FwOtaImageInfo info;
    char error[64];

    make_image();
    assert(fw_ota_inspect_image(path, &info) == FwOtaImageOk);
    assert(info.chip_id == 9 && info.size == sizeof(image));
    assert(fw_ota_flash_file(path, NULL, NULL, error, sizeof(error)));
    assert(erase_calls == 1 && write_calls > 0 && written_bytes == sizeof(image));

    make_image();
    image[sizeof(esp_image_header_t) + sizeof(esp_image_segment_header_t) +
          sizeof(esp_app_desc_t) + 12] ^= 1;
    assert(fw_ota_inspect_image(path, NULL) == FwOtaImageBoardMismatch);
    memset(error, 0, sizeof(error));
    assert(!fw_ota_flash_file(path, NULL, NULL, error, sizeof(error)));
    assert(erase_calls == 0 && write_calls == 0);
    assert(strcmp(error, "firmware board mismatch") == 0);

    /* Same chip and project, but an older or other-board image has no profile. */
    make_image();
    memset(image + sizeof(esp_image_header_t) + sizeof(esp_image_segment_header_t) +
               sizeof(esp_app_desc_t), 0, sizeof(FwOtaBoardProfile));
    assert(fw_ota_inspect_image(path, NULL) == FwOtaImageBoardMismatch);
    assert(!fw_ota_flash_file(path, NULL, NULL, error, sizeof(error)));
    assert(erase_calls == 0);

    make_image();
    image[sizeof(esp_image_header_t) + sizeof(esp_image_segment_header_t) + 48] ^= 1;
    assert(fw_ota_inspect_image(path, NULL) == FwOtaImageWrongProject);
    assert(!fw_ota_flash_file(path, NULL, NULL, error, sizeof(error)));
    assert(erase_calls == 0);

    make_image();
    image[12] = 5;
    assert(fw_ota_inspect_image(path, NULL) == FwOtaImageChipMismatch);
    assert(!fw_ota_flash_file(path, NULL, NULL, error, sizeof(error)));
    assert(erase_calls == 0);

    make_image();
    image[0] = 0;
    assert(fw_ota_inspect_image(path, NULL) == FwOtaImageNotAnImage);
    assert(!fw_ota_flash_file(path, NULL, NULL, error, sizeof(error)));
    assert(erase_calls == 0);

    make_image();
    image_size = 25;
    assert(fw_ota_inspect_image(path, NULL) == FwOtaImageReadError);
    assert(!fw_ota_flash_file(path, NULL, NULL, error, sizeof(error)));
    assert(erase_calls == 0);
    return 0;
}
