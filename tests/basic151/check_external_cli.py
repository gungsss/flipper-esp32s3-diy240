#!/usr/bin/env python3
"""Exercise the actual shell's external-command lifecycle using host mocks."""
import subprocess
import sys
import tempfile
from pathlib import Path

source = (Path(sys.argv[1]) / 'components/toolbox/cli/shell/cli_shell.c').read_text()
start = source.index('void cli_shell_execute_command(')
brace = source.index('{', start)
depth = 0
for i in range(brace, len(source)):
    if source[i] == '{':
        depth += 1
    elif source[i] == '}':
        depth -= 1
        if depth == 0:
            function = source[start:i + 1]
            break
else:
    raise AssertionError('CLI execute function not found')

test = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#define FURI_STRING_FAILURE ((size_t)-1)
#define ANSI_FG_RED ""
#define ANSI_RESET ""
#define RECORD_LOADER "loader"
#define CLI_PLUGIN_API_VERSION 1
enum { CliCommandFlagParallelSafe = 1, CliCommandFlagUseShellThread = 8, CliCommandFlagExternal = 16 };
typedef struct { char text[256]; } FuriString;
typedef struct {} Loader;
typedef struct {} PipeSide;
typedef struct { const char* search_directory; const char* fal_prefix; const char* appid; } CliCommandExternalConfig;
typedef void (*CommandCallback)(PipeSide*, FuriString*, void*);
typedef struct { void* context; CommandCallback execute_callback; unsigned flags; size_t stack_depth; } CliRegistryCommand;
typedef struct { char* name; CommandCallback execute_callback; unsigned flags; size_t stack_depth; } CliCommandDescriptor;
typedef struct { void* registry; PipeSide* pipe; const CliCommandExternalConfig* ext_config; } CliShell;
typedef struct { CliRegistryCommand* command; PipeSide* pipe; FuriString* args; } CliCommandThreadData;
typedef struct { int (*fn)(void*); void* context; } FuriThread;
typedef struct {} PluginManager;
typedef enum { PluginManagerErrorNone = 0, PluginManagerErrorLoaderError = 1 } PluginManagerError;
static const void* firmware_api_interface;
static bool external_mode, load_fail, invalid_name, invalid_flags, no_config, lock_fails;
static int call_count, alloc_count, free_count, lock_count;
static PluginManager manager;
static CliCommandDescriptor descriptor;
static const CliCommandExternalConfig config = {"/ext/apps_data/cli/plugins", "cli_", "cli"};
static FuriString* copy_string(const char* s) { FuriString* p=calloc(1,sizeof(*p)); snprintf(p->text,sizeof(p->text),"%s",s); return p; }
static FuriString* furi_string_alloc_set(FuriString* s) { return copy_string(s->text); }
static size_t furi_string_search_char(FuriString* s, char c) { char* p=strchr(s->text,c); return p ? (size_t)(p-s->text) : FURI_STRING_FAILURE; }
static size_t furi_string_size(FuriString* s) { return strlen(s->text); }
static void furi_string_left(FuriString* s, size_t n) { s->text[n]=0; }
static void furi_string_right(FuriString* s, size_t n) { size_t len=strlen(s->text); memmove(s->text,s->text+(n>len?len:n),len-(n>len?len:n)+1); }
static const char* furi_string_get_cstr(FuriString* s) { return s->text; }
static int furi_string_cmp_str(FuriString* s, const char* t) { return strcmp(s->text,t); }
static FuriString* furi_string_alloc_printf(const char* fmt, ...) { FuriString* p=calloc(1,sizeof(*p)); va_list a; va_start(a,fmt); vsnprintf(p->text,sizeof(p->text),fmt,a); va_end(a); return p; }
static void furi_string_free(FuriString* s) { free(s); }
static void command(PipeSide* pipe, FuriString* args, void* context) { (void)pipe; (void)context; assert(strcmp(args->text,"hello")==0); call_count++; }
static bool cli_registry_get_command(void* registry,FuriString* name,CliRegistryCommand* out) {
    (void)registry; assert(strcmp(name->text,"echo")==0);
    *out=(CliRegistryCommand){.execute_callback=command,.flags=external_mode?CliCommandFlagExternal:CliCommandFlagUseShellThread,.stack_depth=4096}; return true;
}
static Loader* furi_record_open(const char* name) { static Loader l; assert(strcmp(name,"loader")==0); return &l; }
static void furi_record_close(const char* name) { assert(strcmp(name,"loader")==0); }
static bool loader_lock(Loader* l) { (void)l; lock_count++; return !lock_fails; }
static void loader_unlock(Loader* l) { (void)l; lock_count--; }
static PluginManager* plugin_manager_alloc(const char* appid,unsigned version,const void* api) { (void)api; assert(strcmp(appid,"cli")==0 && version==1); alloc_count++; return &manager; }
static uint32_t plugin_manager_get_count(PluginManager* p) { assert(p==&manager); return 0; }
static PluginManagerError plugin_manager_load_single(PluginManager* p,const char* path) { assert(p==&manager); assert(strcmp(path,"/ext/apps_data/cli/plugins/cli_echo.fal")==0); return load_fail?PluginManagerErrorLoaderError:PluginManagerErrorNone; }
static const CliCommandDescriptor* plugin_manager_get_ep(PluginManager* p,uint32_t index) { assert(p==&manager && index==0); descriptor=(CliCommandDescriptor){.name=invalid_name?"wrong":"echo",.execute_callback=command,.flags=invalid_flags?CliCommandFlagUseShellThread:0,.stack_depth=4096}; return &descriptor; }
static void plugin_manager_free(PluginManager* p) { assert(p==&manager); free_count++; }
static void cli_shell_detach_pipe(CliShell* s) { (void)s; }
static void cli_shell_install_pipe(CliShell* s) { (void)s; }
static int cli_command_thread(void* p) { CliCommandThreadData* d=p; d->command->execute_callback(d->pipe,d->args,d->command->context); return 0; }
static FuriThread* furi_thread_alloc_ex(const char* n,size_t stack,int (*fn)(void*),void* ctx) { assert(strcmp(n,"echo")==0 && stack==4096); FuriThread* t=malloc(sizeof(*t)); *t=(FuriThread){fn,ctx}; return t; }
static void furi_thread_start(FuriThread* t) { t->fn(t->context); }
static void furi_thread_join(FuriThread* t) { (void)t; }
static void furi_thread_free(FuriThread* t) { free(t); }
FUNCTION
static void run(bool ext, bool fail_load, bool wrong_name, bool wrong_flags, bool missing_config, bool fail_lock) {
    external_mode=ext; load_fail=fail_load; invalid_name=wrong_name; invalid_flags=wrong_flags; no_config=missing_config; lock_fails=fail_lock;
    call_count=alloc_count=free_count=lock_count=0; PipeSide pipe; CliShell s={.pipe=&pipe,.ext_config=no_config?NULL:&config};
    FuriString* input=copy_string("echo hello"); cli_shell_execute_command(&s,input); furi_string_free(input);
    if(!ext) { assert(call_count==1 && alloc_count==0 && free_count==0); return; }
    assert(call_count==(!fail_load&&!wrong_name&&!wrong_flags&&!missing_config&&!fail_lock));
    assert(alloc_count==!missing_config && free_count==alloc_count);
    if(!fail_lock) assert(lock_count==0);
}
int main(void) {
    run(false,false,false,false,false,false);
    run(true,false,false,false,false,false);
    run(true,true,false,false,false,false);
    run(true,false,true,false,false,false);
    run(true,false,false,true,false,false);
    run(true,false,false,false,true,false);
    run(true,false,false,false,false,true);
    return 0;
}
'''.replace('FUNCTION', function)
with tempfile.TemporaryDirectory(prefix='esp-cli-plugin-') as directory:
    root = Path(directory)
    (root / 'test.c').write_text(test)
    subprocess.run(['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                    str(root / 'test.c'), '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True)
print('External CLI commands load, execute, and clean up; invalid paths fail safely.')
