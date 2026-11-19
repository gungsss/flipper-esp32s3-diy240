#!/usr/bin/env python3
"""Run the real tar and internal-backup sources against a temporary host filesystem."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1]).resolve()

storage_header = r'''
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define STORAGE_INT_PATH_PREFIX "/int"
#define EXT_PATH(name) "/ext/" name
typedef struct Storage { char root[1024]; } Storage;
typedef struct File File;
typedef struct FuriString { char data[2048]; } FuriString;
typedef struct { bool dir; size_t size; } FileInfo;
typedef enum { FSE_OK, FSE_INTERNAL } FS_Error;
typedef enum { FSAM_READ, FSAM_WRITE } FS_AccessMode;
typedef enum { FSOM_OPEN_EXISTING, FSOM_CREATE_ALWAYS } FS_OpenMode;
typedef void (*StorageNameConverter)(FuriString*);
FuriString* furi_string_alloc(void);
FuriString* furi_string_alloc_set(const char*);
FuriString* furi_string_alloc_set_str(const char*);
void furi_string_free(FuriString*);
bool furi_string_empty(FuriString*);
char furi_string_get_char(FuriString*, size_t);
bool furi_string_equal(FuriString*, const char*);
void furi_string_set(FuriString*, const char*);
const char* furi_string_get_cstr(FuriString*);
File* storage_file_alloc(Storage*);
void storage_file_free(File*);
bool storage_file_open(File*, const char*, FS_AccessMode, FS_OpenMode);
bool storage_file_close(File*);
bool storage_file_is_open(File*);
size_t storage_file_read(File*, void*, size_t);
size_t storage_file_write(File*, const void*, size_t);
bool storage_file_seek(File*, uint32_t, bool);
uint32_t storage_file_tell(File*);
uint32_t storage_file_size(File*);
bool storage_dir_open(File*, const char*);
bool storage_dir_read(File*, FileInfo*, char*, uint16_t);
bool storage_simply_mkdir(Storage*, const char*);
bool file_info_is_dir(const FileInfo*);
FS_Error storage_common_stat(Storage*, const char*, FileInfo*);
FS_Error storage_int_backup(Storage*, const char*);
FS_Error storage_int_restore(Storage*, const char*, StorageNameConverter);
'''

harness = r'''
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <storage/storage.h>
#include <toolbox/tar/tar_archive.h>
#include <toolbox/compress.h>
#include "int_backup.h"
struct File { Storage* storage; FILE* file; DIR* dir; char full[2048]; char virtual_path[1024]; };
static bool force_short_write;
static void full_path(Storage* storage, const char* path, char* out, size_t size) {
    assert(path && path[0] == '/');
    assert(snprintf(out, size, "%s%s", storage->root, path) < (int)size);
}
FuriString* furi_string_alloc(void) { return calloc(1, sizeof(FuriString)); }
FuriString* furi_string_alloc_set(const char* s) { FuriString* p = furi_string_alloc(); furi_string_set(p, s); return p; }
FuriString* furi_string_alloc_set_str(const char* s) { return furi_string_alloc_set(s); }
void furi_string_free(FuriString* s) { free(s); }
bool furi_string_empty(FuriString* s) { return !*s->data; }
char furi_string_get_char(FuriString* s, size_t n) { return s->data[n]; }
bool furi_string_equal(FuriString* s, const char* p) { return strcmp(s->data, p) == 0; }
void furi_string_set(FuriString* s, const char* p) { assert(snprintf(s->data, sizeof(s->data), "%s", p) < (int)sizeof(s->data)); }
const char* furi_string_get_cstr(FuriString* s) { return s->data; }
void path_concat(const char* base, const char* suffix, FuriString* out) {
    assert(snprintf(out->data, sizeof(out->data), "%s/%s", base, suffix) < (int)sizeof(out->data));
}
void path_extract_extension(FuriString* path, char* ext, size_t len) {
    const char* dot = strrchr(path->data, '.'); snprintf(ext, len, "%s", dot ? dot : "");
}
File* storage_file_alloc(Storage* s) { File* f = calloc(1, sizeof(*f)); f->storage = s; return f; }
bool storage_file_close(File* f) {
    if(f->file) { fclose(f->file); f->file = NULL; }
    if(f->dir) { closedir(f->dir); f->dir = NULL; }
    return true;
}
void storage_file_free(File* f) { storage_file_close(f); free(f); }
bool storage_file_open(File* f, const char* p, FS_AccessMode access, FS_OpenMode mode) {
    full_path(f->storage, p, f->full, sizeof(f->full));
    snprintf(f->virtual_path, sizeof(f->virtual_path), "%s", p);
    f->file = fopen(f->full, access == FSAM_READ && mode == FSOM_OPEN_EXISTING ? "rb" : "wb");
    return f->file != NULL;
}
bool storage_file_is_open(File* f) { return f->file != NULL; }
size_t storage_file_read(File* f, void* p, size_t n) { return fread(p, 1, n, f->file); }
size_t storage_file_write(File* f, const void* p, size_t n) {
    if(force_short_write && strcmp(f->virtual_path, "/int/file.txt") == 0 && n) {
        force_short_write = false; return fwrite(p, 1, n - 1, f->file);
    }
    return fwrite(p, 1, n, f->file);
}
bool storage_file_seek(File* f, uint32_t n, bool from_start) { return fseek(f->file, n, from_start ? SEEK_SET : SEEK_CUR) == 0; }
uint32_t storage_file_tell(File* f) { return (uint32_t)ftell(f->file); }
uint32_t storage_file_size(File* f) { long pos = ftell(f->file); fseek(f->file, 0, SEEK_END); long n = ftell(f->file); fseek(f->file, pos, SEEK_SET); return (uint32_t)n; }
bool storage_dir_open(File* f, const char* p) {
    full_path(f->storage, p, f->full, sizeof(f->full)); f->dir = opendir(f->full); return f->dir != NULL;
}
bool storage_dir_read(File* f, FileInfo* info, char* name, uint16_t cap) {
    struct dirent* entry;
    while((entry = readdir(f->dir))) {
        if(!strcmp(entry->d_name, ".") || !strcmp(entry->d_name, "..")) continue;
        assert(strlen(entry->d_name) < cap); strcpy(name, entry->d_name);
        char path[4096]; assert(snprintf(path, sizeof(path), "%s/%s", f->full, name) < (int)sizeof(path));
        struct stat st; assert(stat(path, &st) == 0); info->dir = S_ISDIR(st.st_mode); info->size = st.st_size; return true;
    }
    return false;
}
bool storage_simply_mkdir(Storage* s, const char* p) {
    char path[2048]; full_path(s, p, path, sizeof(path));
    struct stat st; return mkdir(path, 0700) == 0 || (stat(path, &st) == 0 && S_ISDIR(st.st_mode));
}
bool file_info_is_dir(const FileInfo* i) { return i->dir; }
FS_Error storage_common_stat(Storage* s, const char* p, FileInfo* info) {
    (void)info; char path[2048]; struct stat st; full_path(s, p, path, sizeof(path));
    return stat(path, &st) == 0 ? FSE_OK : FSE_INTERNAL;
}
void furi_delay_ms(int n) { (void)n; }
/* These cases use plain tar; compressed streams are outside this test. */
struct CompressStreamDecoder { int unused; };
CompressStreamDecoder* compress_stream_decoder_alloc(CompressType t, const void* c, CompressIoCallback cb, void* p) { (void)t; (void)c; (void)cb; (void)p; abort(); }
void compress_stream_decoder_free(CompressStreamDecoder* p) { (void)p; abort(); }
bool compress_stream_decoder_read(CompressStreamDecoder* p, uint8_t* b, size_t n) { (void)p; (void)b; (void)n; abort(); }
bool compress_stream_decoder_seek(CompressStreamDecoder* p, size_t n) { (void)p; (void)n; abort(); }
bool compress_stream_decoder_rewind(CompressStreamDecoder* p) { (void)p; abort(); }
static void write_fixture(Storage* s, const char* path, const char* data) {
    char full[2048]; full_path(s, path, full, sizeof(full)); FILE* f = fopen(full, "wb");
    assert(f); size_t size = strlen(data); assert(fwrite(data, 1, size, f) == size); assert(fclose(f) == 0);
}
static void check_fixture(Storage* s, const char* path, const char* expected) {
    char full[2048], data[128] = {0}; full_path(s, path, full, sizeof(full));
    FILE* f = fopen(full, "rb"); assert(f); size_t n = fread(data, 1, sizeof(data) - 1, f); fclose(f);
    assert(n == strlen(expected) && strcmp(data, expected) == 0);
}
static void remove_fixture(Storage* s, const char* path) { char full[2048]; full_path(s, path, full, sizeof(full)); assert(unlink(full) == 0); }
int main(int argc, char** argv) {
    assert(argc == 2); Storage s = {0}; snprintf(s.root, sizeof(s.root), "%s", argv[1]);
    assert(storage_simply_mkdir(&s, "/int")); assert(storage_simply_mkdir(&s, "/ext"));
    assert(storage_simply_mkdir(&s, "/int/folder"));
    write_fixture(&s, "/int/file.txt", "firmware settings");
    write_fixture(&s, "/int/.bt.keys", "pairing data");
    write_fixture(&s, "/int/folder/nested.txt", "nested data");
    assert(int_backup_create(&s, NULL)); assert(int_backup_exists(&s, NULL));
    remove_fixture(&s, "/int/file.txt"); remove_fixture(&s, "/int/.bt.keys");
    remove_fixture(&s, "/int/folder/nested.txt");
    assert(int_backup_unpack(&s, NULL));
    check_fixture(&s, "/int/file.txt", "firmware settings");
    check_fixture(&s, "/int/.bt.keys", "pairing data");
    check_fixture(&s, "/int/folder/nested.txt", "nested data");
    force_short_write = true; assert(!int_backup_unpack(&s, NULL));
    write_fixture(&s, "/int/source.txt", "xyz");
    TarArchive* a = tar_archive_alloc(&s); assert(tar_archive_open(a, "/ext/invalid.tar", TarOpenModeWrite));
    assert(tar_archive_add_file(a, "/int/source.txt", "../escape.txt", 3));
    assert(tar_archive_finalize(a)); tar_archive_free(a);
    a = tar_archive_alloc(&s); assert(tar_archive_open(a, "/ext/invalid.tar", TarOpenModeRead));
    assert(!tar_archive_unpack_to(a, "/int", NULL)); tar_archive_free(a);
    char outside[2048]; struct stat st; full_path(&s, "/escape.txt", outside, sizeof(outside));
    assert(stat(outside, &st) != 0); return 0;
}
'''

with tempfile.TemporaryDirectory(prefix='esp-archive-integration-') as directory:
    root = Path(directory)
    include = root / 'include'
    for part in ('storage', 'core', 'toolbox/tar'):
        (include / part).mkdir(parents=True, exist_ok=True)
    (include / 'storage/storage.h').write_text(storage_header)
    (include / 'core/record.h').write_text('#pragma once\n#include <furi.h>\n')
    (include / 'furi.h').write_text(r'''
#pragma once
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <storage/storage.h>
#define furi_check(x) assert(x)
#define furi_assert(x) assert(x)
#define FURI_LOG_W(...) ((void)0)
#define FURI_LOG_I(...) ((void)0)
#define FURI_LOG_D(...) ((void)0)
#define FURI_PACKED __attribute__((packed))
#define UNUSED(x) (void)(x)
#define COUNT_OF(a) (sizeof(a)/sizeof((a)[0]))
#define malloc(size) calloc(1, (size))
void furi_delay_ms(int);
''')
    (include / 'toolbox/path.h').write_text(r'''
#pragma once
#include <storage/storage.h>
void path_concat(const char*, const char*, FuriString*);
void path_extract_extension(FuriString*, char*, size_t);
''')
    shutil.copyfile(source / 'components/toolbox/compress.h', include / 'toolbox/compress.h')
    shutil.copyfile(source / 'components/toolbox/tar/tar_archive.h', include / 'toolbox/tar/tar_archive.h')
    for path in ('components/rpc/int_backup.c', 'components/rpc/int_backup.h',
                 'components/btshim/bt_settings_filename.h', 'components/btshim/bt_keys_filename.h',
                 'applications/services/dolphin/helpers/dolphin_state_filename.h',
                 'applications/services/desktop/helpers/slideshow_filename.h',
                 'applications/services/desktop/desktop_settings_filename.h',
                 'applications/services/storage/storage_internal_api.c'):
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / path, dest)
    (root / 'applications/services/storage/storage.h').write_text('#include <storage/storage.h>\n')
    (root / 'harness.c').write_text(harness)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I', str(include),
                    '-I', str(source / 'components/toolbox'), '-I', str(root / 'components/rpc'),
                    str(source / 'components/toolbox/microtar.c'),
                    str(source / 'components/toolbox/tar/tar_archive.c'),
                    str(root / 'applications/services/storage/storage_internal_api.c'),
                    str(root / 'components/rpc/int_backup.c'), str(root / 'harness.c'),
                    '-o', str(root / 'integration')], check=True)
    (root / 'files').mkdir()
    subprocess.run([str(root / 'integration'), str(root / 'files')], check=True)

print('Real tar backup and restore preserve files; short writes and traversal fail.')
