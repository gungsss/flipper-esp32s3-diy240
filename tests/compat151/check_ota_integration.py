#!/usr/bin/env python3
"""Exercise the real OTA inspection and flash entrypoint with mock IDF/storage."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

port = Path(sys.argv[1]).resolve()
stubs = {
    'board.h': '''#pragma once
#include <stdint.h>
#define BOARD_OTA_PROFILE_ST7735 1
#define BOARD_PIN_LCD_MOSI 11
#define BOARD_PIN_LCD_SCLK 12
#define BOARD_PIN_LCD_DC 15
#define BOARD_PIN_LCD_RST 16
#define BOARD_PIN_LCD_CS UINT16_MAX
#define BOARD_PIN_LCD_BL 7
#define BOARD_PIN_SD_SCK 40
#define BOARD_PIN_SD_MOSI 39
#define BOARD_PIN_SD_MISO2 38
#define BOARD_PIN_SD_CS 14
#define BOARD_PIN_BTN_UP 4
#define BOARD_PIN_BTN_DOWN 5
#define BOARD_PIN_BTN_LEFT 6
#define BOARD_PIN_BTN_RIGHT 17
#define BOARD_PIN_BTN_OK 8
#define BOARD_PIN_BTN_BACK 18
''',
    'furi.h': '''#pragma once
#define RECORD_STORAGE "storage"
#define FURI_LOG_I(...) ((void)0)
#define FURI_LOG_E(...) ((void)0)
void* furi_record_open(const char*);
void furi_record_close(const char*);
''',
    'storage/storage.h': '''#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef struct Storage { int unused; } Storage;
typedef struct File { size_t pos; } File;
typedef struct { uint64_t size; } FileInfo;
typedef enum {FSE_OK, FSE_NOT_EXIST} FS_Error;
typedef enum {FSAM_READ, FSAM_WRITE} FS_AccessMode;
typedef enum {FSOM_OPEN_EXISTING, FSOM_CREATE_ALWAYS} FS_OpenMode;
FS_Error storage_common_stat(Storage*, const char*, FileInfo*);
File* storage_file_alloc(Storage*);
void storage_file_free(File*);
bool storage_file_open(File*, const char*, FS_AccessMode, FS_OpenMode);
bool storage_file_close(File*);
bool storage_file_seek(File*, uint32_t, bool);
size_t storage_file_read(File*, void*, size_t);
size_t storage_file_write(File*, const void*, size_t);
''',
    'toolbox/fw_version.h': '#pragma once\n#define FURI_ESP32_VERSION "test"\n',
    'sdkconfig.h': '''#pragma once
#define CONFIG_IDF_TARGET_ESP32S3 0
#define CONFIG_IDF_TARGET_ESP32S2 0
#define CONFIG_IDF_FIRMWARE_CHIP_ID 9
''',
    'freertos/FreeRTOS.h': '''#pragma once
#define pdMS_TO_TICKS(x) (x)
#define pdPASS 1
''',
    'freertos/task.h': '''#pragma once
#include <stdint.h>
void vTaskDelay(uint32_t);
int xTaskCreate(void (*)(void*), const char*, unsigned, void*, unsigned, void*);
''',
    'esp_attr.h': '#pragma once\n#define RTC_NOINIT_ATTR\n',
    'esp_system.h': '#pragma once\nvoid esp_restart(void);\n',
    'esp_partition.h': '''#pragma once
typedef struct esp_partition { const char* label; } esp_partition_t;
''',
    'esp_ota_ops.h': '''#pragma once
#include <stddef.h>
#include <esp_partition.h>
typedef int esp_err_t;
typedef unsigned esp_ota_handle_t;
#define ESP_OK 0
const esp_partition_t* esp_ota_get_next_update_partition(const void*);
const esp_partition_t* esp_ota_get_running_partition(void);
esp_err_t esp_ota_begin(const esp_partition_t*, size_t, esp_ota_handle_t*);
esp_err_t esp_ota_write(esp_ota_handle_t, const void*, size_t);
esp_err_t esp_ota_end(esp_ota_handle_t);
esp_err_t esp_ota_abort(esp_ota_handle_t);
esp_err_t esp_ota_set_boot_partition(const esp_partition_t*);
''',
    'esp_app_format.h': '''#pragma once
#include <stdint.h>
#define ESP_IMAGE_HEADER_MAGIC 0xe9
typedef struct __attribute__((packed)) {
    uint8_t magic;
    uint8_t reserved1[11];
    uint16_t chip_id;
    uint8_t reserved2[10];
} esp_image_header_t;
typedef struct { uint32_t addr; uint32_t size; } esp_image_segment_header_t;
''',
    'esp_app_desc.h': '''#pragma once
#include <stdint.h>
#define ESP_APP_DESC_MAGIC_WORD 0xabcd5432u
typedef struct {
    uint32_t magic_word, secure_version, reserved1[2];
    char version[32], project_name[32], time[16], date[16], idf_ver[32];
    uint8_t sha256[32];
    uint32_t reserved2[20];
} esp_app_desc_t;
''',
    'esp_heap_caps.h': '''#pragma once
#include <stddef.h>
#define MALLOC_CAP_INTERNAL 1
#define MALLOC_CAP_8BIT 2
void* heap_caps_malloc(size_t, unsigned);
''',
}

with tempfile.TemporaryDirectory(prefix='esp151-ota-integration-') as directory:
    temp = Path(directory)
    for name, contents in stubs.items():
        path = temp / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    ota = port / 'components/fw_ota'
    exe = temp / 'ota-integration'
    subprocess.run([
        'gcc', '-std=gnu11', '-g', '-O1', '-fsanitize=address,undefined',
        '-fno-omit-frame-pointer', '-ffunction-sections', '-fdata-sections',
        '-I', str(temp), '-I', str(ota),
        str(Path(__file__).with_name('ota_integration_regression.c')),
        str(ota / 'fw_ota.c'), str(ota / 'fw_ota_profile.c'),
        '-Wl,--gc-sections', '-o', str(exe),
    ], check=True)
    subprocess.run([str(exe)], env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'}, check=True)
print('OTA accepts a matching image and rejects wrong board/chip/header before erase.')
