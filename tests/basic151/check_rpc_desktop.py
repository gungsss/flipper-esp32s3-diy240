#!/usr/bin/env python3
"""Exercise desktop RPC status, subscriptions and the locked-device boundary."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1]).resolve() / 'components/rpc/rpc_desktop.c'
with tempfile.TemporaryDirectory(prefix='esp-rpc-desktop-') as directory:
    temp = Path(directory)
    (temp / 'desktop').mkdir()
    shutil.copyfile(source, temp / 'rpc_desktop.c')
    (temp / 'flipper.pb.h').write_text(r'''
#pragma once
#include <stdbool.h>
#include <stdint.h>
typedef enum { PB_CommandStatus_OK, PB_CommandStatus_ERROR } PB_CommandStatus;
enum { PB_Main_desktop_is_locked_request_tag = 66, PB_Main_desktop_unlock_request_tag,
       PB_Main_desktop_status_subscribe_request_tag, PB_Main_desktop_status_unsubscribe_request_tag,
       PB_Main_desktop_status_tag };
typedef struct { uint32_t command_id; PB_CommandStatus command_status; bool has_next; int which_content;
    struct { struct { bool locked; } desktop_status; } content; } PB_Main;
''')
    (temp / 'rpc_i.h').write_text(r'''
#pragma once
#include <assert.h>
#include "flipper.pb.h"
#define furi_assert(c) assert(c)
#define FURI_LOG_D(...) ((void)0)
typedef struct RpcSession { int unused; } RpcSession;
typedef struct { int unused; } Desktop;
typedef struct { int unused; } FuriPubSub;
typedef struct { int unused; } FuriPubSubSubscription;
typedef void (*Callback)(const void*, void*);
typedef struct { void (*message_handler)(const PB_Main*, void*); void* decode_submessage; void* context; } RpcHandler;
void rpc_add_handler(RpcSession*, int, RpcHandler*);
void rpc_send_and_release_empty(RpcSession*, uint32_t, PB_CommandStatus);
void rpc_send_and_release(RpcSession*, PB_Main*);
void* furi_record_open(const char*);
void furi_record_close(const char*);
FuriPubSubSubscription* furi_pubsub_subscribe(FuriPubSub*, Callback, void*);
void furi_pubsub_unsubscribe(FuriPubSub*, FuriPubSubSubscription*);
''')
    (temp / 'desktop/desktop.h').write_text(r'''
#pragma once
#include "rpc_i.h"
#define RECORD_DESKTOP "desktop"
typedef struct { bool locked; } DesktopStatus;
bool desktop_api_is_locked(Desktop*);
FuriPubSub* desktop_api_get_status_pubsub(Desktop*);
''')
    (temp / 'test.c').write_text(r'''
#include "rpc_i.h"
#include "desktop/desktop.h"
#include <stdio.h>
void* rpc_desktop_alloc(RpcSession*);
void rpc_desktop_free(void*);
static RpcHandler handlers[80];
static Desktop desktop;
static FuriPubSub pubsub;
static FuriPubSubSubscription subscription;
static Callback cb;
static void* cb_context;
static int closes, unsubscribes, sends;
static bool locked, observed_status;
static PB_CommandStatus result;
bool desktop_api_is_locked(Desktop* p) { assert(p == &desktop); return locked; }
FuriPubSub* desktop_api_get_status_pubsub(Desktop* p) { assert(p == &desktop); return &pubsub; }
void* furi_record_open(const char* name) { (void)name; return &desktop; }
void furi_record_close(const char* name) { (void)name; closes++; }
FuriPubSubSubscription* furi_pubsub_subscribe(FuriPubSub* p, Callback f, void* c) {
    assert(p == &pubsub); cb = f; cb_context = c; return &subscription;
}
void furi_pubsub_unsubscribe(FuriPubSub* p, FuriPubSubSubscription* s) {
    assert(p == &pubsub && s == &subscription); unsubscribes++;
}
void rpc_add_handler(RpcSession* s, int tag, RpcHandler* h) { assert(s && tag < 80); handlers[tag] = *h; }
void rpc_send_and_release_empty(RpcSession* s, uint32_t id, PB_CommandStatus status) {
    assert(s && id == 42); result = status; sends++;
}
void rpc_send_and_release(RpcSession* s, PB_Main* message) {
    assert(s && message->which_content == PB_Main_desktop_status_tag);
    observed_status = message->content.desktop_status.locked;
}
static void request(int tag) {
    PB_Main message = {.command_id = 42, .which_content = tag};
    assert(handlers[tag].message_handler); handlers[tag].message_handler(&message, handlers[tag].context);
}
int main(void) {
    RpcSession session = {0}; void* context = rpc_desktop_alloc(&session); assert(context);
    locked = false; request(PB_Main_desktop_is_locked_request_tag); assert(result == PB_CommandStatus_ERROR);
    locked = true; request(PB_Main_desktop_is_locked_request_tag); assert(result == PB_CommandStatus_OK);
    request(PB_Main_desktop_unlock_request_tag); assert(result == PB_CommandStatus_ERROR && locked);
    request(PB_Main_desktop_status_subscribe_request_tag); assert(result == PB_CommandStatus_OK && cb);
    request(PB_Main_desktop_status_subscribe_request_tag); assert(result == PB_CommandStatus_ERROR);
    DesktopStatus status = {.locked = true}; cb(&status, cb_context); assert(observed_status);
    request(PB_Main_desktop_status_unsubscribe_request_tag); assert(result == PB_CommandStatus_OK && unsubscribes == 1);
    request(PB_Main_desktop_status_unsubscribe_request_tag); assert(result == PB_CommandStatus_ERROR);
    request(PB_Main_desktop_status_subscribe_request_tag); assert(result == PB_CommandStatus_OK);
    rpc_desktop_free(context); assert(unsubscribes == 2 && closes == 1 && sends == 8);
    puts("Desktop RPC status and subscriptions work; locked device cannot be remotely unlocked.");
}
''')
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I', str(temp),
                    str(temp / 'rpc_desktop.c'), str(temp / 'test.c'), '-o', str(temp / 'test')], check=True)
    subprocess.run([str(temp / 'test')], check=True)
