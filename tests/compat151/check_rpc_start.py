#!/usr/bin/env python3
"""Run the port's RPC app-start handler against a small mocked transport."""

import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1], 'components/rpc/rpc_app.c').read_text()
start = source.index('static void rpc_system_app_start_process(')
end = source.index('\nstatic void rpc_system_app_lock_status_process(', start)
handler = source[start:end]

prelude = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define FURI_LOG_D(...) ((void)0)
#define FURI_LOG_E(...) ((void)0)
#define furi_assert(expr) assert(expr)
#define furi_crash() abort()
#define RECORD_LOADER "loader"
#define RPC_SYSTEM_APP_TEMP_ARGS_SIZE 16
#define PB_Main_app_start_request_tag 1
#define RpcAppEventTypeInvalid 0

typedef enum { LoaderStatusErrorAppStarted, LoaderStatusErrorInternal,
               LoaderStatusErrorUnknownApp, LoaderStatusOk } LoaderStatus;
typedef enum { PB_CommandStatus_ERROR_APP_SYSTEM_LOCKED,
               PB_CommandStatus_ERROR_APP_CANT_START,
               PB_CommandStatus_ERROR_INVALID_PARAMETERS, PB_CommandStatus_OK } PB_CommandStatus;
typedef struct { int unused; } Loader;
typedef struct { int unused; } RpcSession;
typedef struct { RpcSession* session; uint32_t last_command_id; int last_event_type; } RpcAppSystem;
typedef struct {
    uint32_t which_content, command_id;
    struct { struct { const char* name; const char* args; } app_start_request; } content;
} PB_Main;

static Loader loader;
static LoaderStatus next_loader_status;
static PB_CommandStatus result_status;
static uint32_t result_command_id;
static unsigned loader_calls;
static char captured_args[64];
static bool captured_null;

static void* furi_record_open(const char* name) { assert(!strcmp(name, RECORD_LOADER)); return &loader; }
static void furi_record_close(const char* name) { assert(!strcmp(name, RECORD_LOADER)); }
static void rpc_system_app_error_reset(RpcAppSystem* app) { assert(app); }
static LoaderStatus loader_start(Loader* instance, const char* name, const char* args, void* error) {
    assert(instance == &loader && name && !error);
    ++loader_calls;
    captured_null = args == NULL;
    if(args) snprintf(captured_args, sizeof(captured_args), "%s", args);
    return next_loader_status;
}
static void rpc_send_and_release_empty(RpcSession* session, uint32_t command_id, PB_CommandStatus status) {
    assert(session);
    result_command_id = command_id;
    result_status = status;
}
'''

tests = r'''
int main(void) {
    RpcSession session = {0};
    RpcAppSystem app = {.session = &session};
    PB_Main request = {.which_content = PB_Main_app_start_request_tag, .command_id = 42};
    next_loader_status = LoaderStatusOk;

    rpc_system_app_start_process(&request, &app);
    assert(result_status == PB_CommandStatus_ERROR_INVALID_PARAMETERS && loader_calls == 0);

    request.content.app_start_request.name = "Example";
    rpc_system_app_start_process(&request, &app);
    assert(result_status == PB_CommandStatus_OK && result_command_id == 42);
    assert(loader_calls == 1 && captured_null);

    request.content.app_start_request.args = "hello world";
    rpc_system_app_start_process(&request, &app);
    assert(result_status == PB_CommandStatus_OK && !strcmp(captured_args, "hello world"));

    request.content.app_start_request.args = "RPC DEADBEEF";
    rpc_system_app_start_process(&request, &app);
    assert(result_status == PB_CommandStatus_ERROR_INVALID_PARAMETERS && loader_calls == 2);

    request.content.app_start_request.args = "RPC";
    rpc_system_app_start_process(&request, &app);
    assert(result_status == PB_CommandStatus_OK && !strncmp(captured_args, "RPC ", 4));
    assert(loader_calls == 3);

    next_loader_status = LoaderStatusErrorAppStarted;
    request.content.app_start_request.args = NULL;
    rpc_system_app_start_process(&request, &app);
    assert(result_status == PB_CommandStatus_ERROR_APP_SYSTEM_LOCKED);
    next_loader_status = LoaderStatusErrorInternal;
    rpc_system_app_start_process(&request, &app);
    assert(result_status == PB_CommandStatus_ERROR_APP_CANT_START);
    next_loader_status = LoaderStatusErrorUnknownApp;
    rpc_system_app_start_process(&request, &app);
    assert(result_status == PB_CommandStatus_ERROR_INVALID_PARAMETERS);
    return 0;
}
'''

with tempfile.TemporaryDirectory(prefix='flipper-rpc-') as temp:
    root = Path(temp)
    harness = root / 'rpc_start.c'
    harness.write_text(prelude + '\n' + handler + '\n' + tests)
    executable = root / 'rpc_start'
    # The host is 64-bit; the real ESP32 pointer is 32-bit and fits the buffer.
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wno-format-truncation',
                    str(harness), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)

print('RPC start: ordinary requests and errors handled; forged RPC context rejected.')
