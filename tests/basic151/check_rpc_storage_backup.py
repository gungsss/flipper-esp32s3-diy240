#!/usr/bin/env python3
"""Exercise the ESP port's actual 1.5.1 backup and archive RPC handlers."""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1]).resolve()
rpc = (source / 'components/rpc/rpc_storage.c').read_text()
names = ('backup_create', 'backup_restore', 'tar_extract')
functions = []
for name in names:
    full = f'rpc_system_storage_{name}_process'
    match = re.search(rf'static void {full}\([^{{]+\) \{{', rpc)
    assert match, full
    start, depth, end = match.start(), 0, None
    for pos in range(rpc.index('{', start), len(rpc)):
        if rpc[pos] == '{':
            depth += 1
        elif rpc[pos] == '}':
            depth -= 1
            if depth == 0:
                end = pos + 1
                break
    assert end
    functions.append(rpc[start:end])
    assert re.search(rf'rpc_handler\.message_handler\s*=\s*{full};\s*'
                     rf'rpc_add_handler\(session,\s*PB_Main_storage_{name}_request_tag', rpc)

test = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#define furi_assert(x) assert(x)
#define FURI_LOG_D(...) ((void)0)
enum { PB_Main_storage_backup_create_request_tag = 42,
       PB_Main_storage_backup_restore_request_tag = 43,
       PB_Main_storage_tar_extract_request_tag = 71 };
typedef enum { PB_CommandStatus_OK, PB_CommandStatus_ERROR,
    PB_CommandStatus_ERROR_STORAGE_INVALID_PARAMETER,
    PB_CommandStatus_ERROR_STORAGE_INVALID_NAME,
    PB_CommandStatus_ERROR_STORAGE_INTERNAL } PB_CommandStatus;
typedef struct { uint32_t command_id; int which_content; struct {
    struct { const char* archive_path; } storage_backup_create_request;
    struct { const char* archive_path; } storage_backup_restore_request;
    struct { const char* tar_path; const char* out_path; } storage_tar_extract_request;
} content; } PB_Main;
typedef struct { int id; } Storage;
typedef struct { int id; } RpcSession;
typedef struct { Storage* api; RpcSession* session; } RpcStorageSystem;
typedef struct { int id; } TarArchive;
typedef enum { PlainTar, HeatshrinkTar } TarOpenMode;
static bool outcome, open_ok, unpack_ok;
static int resets, allocations, releases, calls, sends;
static const char* last_path;
static PB_CommandStatus last_status;
static TarArchive archive;
static void rpc_system_storage_reset_state(RpcStorageSystem* s, RpcSession* p, bool send) {
    assert(s && p == s->session && send); resets++;
}
static bool int_backup_create(Storage* s, const char* path) {
    assert(s); last_path = path; calls++; return outcome;
}
static bool int_backup_unpack(Storage* s, const char* path) {
    assert(s); last_path = path; calls++; return outcome;
}
static void rpc_send_and_release_empty(RpcSession* s, uint32_t id, PB_CommandStatus status) {
    assert(s && id == 99); last_status = status; sends++;
}
static TarArchive* tar_archive_alloc(Storage* s) { assert(s); allocations++; return &archive; }
static void tar_archive_free(TarArchive* a) { assert(a == &archive); releases++; }
static bool path_contains_only_ascii(const char* p) { return strchr(p, '?') == NULL; }
static TarOpenMode tar_archive_get_mode_for_path(const char* p) {
    return strstr(p, ".ths") ? HeatshrinkTar : PlainTar;
}
static bool tar_archive_open(TarArchive* a, const char* p, TarOpenMode mode) {
    assert(a == &archive && p && mode == HeatshrinkTar); return open_ok;
}
static bool tar_archive_unpack_to(TarArchive* a, const char* p, void* cb) {
    assert(a == &archive && strcmp(p, "/ext/out") == 0 && !cb); return unpack_ok;
}
FUNCTIONS
int main(void) {
    Storage store = {0}; RpcSession session = {0};
    RpcStorageSystem sys = {&store, &session};
    PB_Main request = {.command_id = 99};
    request.which_content = PB_Main_storage_backup_create_request_tag;
    request.content.storage_backup_create_request.archive_path = "/ext/custom.tar";
    outcome = true; rpc_system_storage_backup_create_process(&request, &sys);
    assert(last_status == PB_CommandStatus_OK && !strcmp(last_path, "/ext/custom.tar"));
    request.which_content = PB_Main_storage_backup_restore_request_tag;
    request.content.storage_backup_restore_request.archive_path = "/ext/backup.tar";
    outcome = false; rpc_system_storage_backup_restore_process(&request, &sys);
    assert(last_status == PB_CommandStatus_ERROR && !strcmp(last_path, "/ext/backup.tar"));
    request.which_content = PB_Main_storage_tar_extract_request_tag;
    request.content.storage_tar_extract_request.tar_path = NULL;
    request.content.storage_tar_extract_request.out_path = "/ext/out";
    rpc_system_storage_tar_extract_process(&request, &sys);
    assert(last_status == PB_CommandStatus_ERROR_STORAGE_INVALID_PARAMETER);
    request.content.storage_tar_extract_request.tar_path = "/ext/data.ths";
    request.content.storage_tar_extract_request.out_path = "/ext/?";
    rpc_system_storage_tar_extract_process(&request, &sys);
    assert(last_status == PB_CommandStatus_ERROR_STORAGE_INVALID_NAME);
    request.content.storage_tar_extract_request.out_path = "/ext/out";
    open_ok = false; rpc_system_storage_tar_extract_process(&request, &sys);
    assert(last_status == PB_CommandStatus_ERROR_STORAGE_INVALID_PARAMETER);
    open_ok = true; unpack_ok = false; rpc_system_storage_tar_extract_process(&request, &sys);
    assert(last_status == PB_CommandStatus_ERROR_STORAGE_INTERNAL);
    unpack_ok = true; rpc_system_storage_tar_extract_process(&request, &sys);
    assert(last_status == PB_CommandStatus_OK);
    assert(calls == 2 && resets == 7 && sends == 7 && allocations == 5 && releases == 5);
    return 0;
}
'''.replace('FUNCTIONS', '\n'.join(functions))

backup_test = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "int_backup.h"
static int result;
static const char* path_seen;
bool furi_string_empty(FuriString* s) { return s->data[0] == 0; }
char furi_string_get_char(FuriString* s, size_t n) { return s->data[n]; }
bool furi_string_equal(FuriString* s, const char* c) { return strcmp(s->data, c) == 0; }
void furi_string_set(FuriString* s, const char* c) { snprintf(s->data, sizeof(s->data), "%s", c); }
FS_Error storage_int_backup(Storage* s, const char* p) { assert(s); path_seen = p; return result; }
FS_Error storage_common_stat(Storage* s, const char* p, void* info) {
    assert(s && !info); path_seen = p; return result;
}
FS_Error storage_int_restore(Storage* s, const char* p, StorageNameConverter converter) {
    assert(s); path_seen = p;
    const char* values[] = {"bt.settings", "bt.keys", "desktop.settings", "notification.settings",
                            "slideshow", "dolphin.state", ".existing", "other", ""};
    const char* expected[] = {".bt.settings", ".bt.keys", ".desktop.settings", ".notification.settings",
                              ".slideshow", ".dolphin.state", ".existing", "other", ""};
    for(size_t i = 0; i < sizeof(values) / sizeof(values[0]); ++i) {
        FuriString f = {0}; furi_string_set(&f, values[i]); converter(&f);
        assert(strcmp(f.data, expected[i]) == 0);
    }
    return result;
}
int main(void) {
    Storage storage = {0}; result = FSE_OK;
    assert(int_backup_create(&storage, NULL)); assert(!strcmp(path_seen, "/ext/backup.tar"));
    assert(int_backup_exists(&storage, "")); assert(!strcmp(path_seen, "/ext/backup.tar"));
    assert(int_backup_unpack(&storage, "/ext/file.tar")); assert(!strcmp(path_seen, "/ext/file.tar"));
    result = FSE_INTERNAL;
    assert(!int_backup_create(&storage, "/ext/bad.tar"));
    assert(!int_backup_exists(&storage, "/ext/bad.tar"));
    assert(!int_backup_unpack(&storage, NULL));
    return 0;
}
'''

with tempfile.TemporaryDirectory(prefix='esp-rpc-backup-') as directory:
    root = Path(directory)
    (root / 'rpc_test.c').write_text(test)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(root / 'rpc_test.c'),
                    '-o', str(root / 'rpc_test')], check=True)
    subprocess.run([str(root / 'rpc_test')], check=True)
    for path in ('components/rpc/int_backup.c', 'components/rpc/int_backup.h',
                 'components/btshim/bt_settings_filename.h', 'components/btshim/bt_keys_filename.h',
                 'applications/services/dolphin/helpers/dolphin_state_filename.h',
                 'applications/services/desktop/helpers/slideshow_filename.h',
                 'applications/services/desktop/desktop_settings_filename.h'):
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / path, dest)
    include = root / 'include'
    (include / 'storage').mkdir(parents=True)
    (include / 'toolbox/tar').mkdir(parents=True)
    (include / 'toolbox/tar/tar_archive.h').write_text('#pragma once\n')
    (include / 'furi.h').write_text('#pragma once\n#define COUNT_OF(a) (sizeof(a)/sizeof((a)[0]))\n')
    (include / 'storage/storage.h').write_text(r'''
#pragma once
#include <stdbool.h>
#include <stddef.h>
#define EXT_PATH(name) "/ext/" name
typedef struct { int unused; } Storage;
typedef struct { char data[256]; } FuriString;
typedef void (*StorageNameConverter)(FuriString*);
typedef enum { FSE_OK, FSE_INTERNAL } FS_Error;
bool furi_string_empty(FuriString*);
char furi_string_get_char(FuriString*, size_t);
bool furi_string_equal(FuriString*, const char*);
void furi_string_set(FuriString*, const char*);
FS_Error storage_int_backup(Storage*, const char*);
FS_Error storage_int_restore(Storage*, const char*, StorageNameConverter);
FS_Error storage_common_stat(Storage*, const char*, void*);
''')
    (root / 'backup_test.c').write_text(backup_test)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I', str(include),
                    '-I', str(root / 'components/rpc'), str(root / 'components/rpc/int_backup.c'),
                    str(root / 'backup_test.c'), '-o', str(root / 'backup_test')], check=True)
    subprocess.run([str(root / 'backup_test')], check=True)

print('1.5.1 backup, restore and archive RPC handlers pass path, status and error checks.')
