#!/usr/bin/env python3
"""Host test of the actual loader CLI and quoted-argument parser."""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

root = Path(sys.argv[1]).resolve()
cli = root / 'components/loader/loader_cli.c'
args = (root / 'components/toolbox/args.c').read_text()

def extract(name, return_type):
    match = re.search(r'(?m)^' + return_type + ' ' + name + r'\([^)]*\) \{', args)
    assert match, name
    i, depth = match.end(), 1
    while depth:
        if args[i] == '{': depth += 1
        if args[i] == '}': depth -= 1
        i += 1
    return args[match.start():i]

header = r"""
#pragma once
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
typedef struct { char s[256]; } FuriString;
typedef struct { int unused; } Loader;
typedef struct { int unused; } CliRegistry;
typedef struct { int unused; } PipeSide;
typedef int LoaderStatus;
typedef int StrintParseError;
typedef void (*CliCommandExecuteCallback)(PipeSide*, FuriString*, void*);
typedef struct { const char* name; } FlipperApplication;
enum { LoaderStatusOk = 0, FuriSignalExit = 1, CliCommandFlagParallelSafe = 1 };
#define FURI_STRING_FAILURE ((size_t)-1)
#define RECORD_LOADER "loader"
#define UNUSED(x) ((void)(x))
extern const FlipperApplication FLIPPER_APPS[], FLIPPER_SETTINGS_APPS[], FLIPPER_EXTSETTINGS_APPS[];
extern const size_t FLIPPER_APPS_COUNT, FLIPPER_SETTINGS_APPS_COUNT, FLIPPER_EXTSETTINGS_APPS_COUNT;
FuriString* furi_string_alloc(void);
void furi_string_free(FuriString*);
size_t furi_string_size(const FuriString*);
char furi_string_get_char(const FuriString*, size_t);
const char* furi_string_get_cstr(const FuriString*);
bool furi_string_empty(const FuriString*);
bool furi_string_equal(const FuriString*, const char*);
void furi_string_set(FuriString*, const FuriString*);
void furi_string_set_n(FuriString*, const FuriString*, size_t, size_t);
void furi_string_right(FuriString*, size_t);
void furi_string_trim(FuriString*);
void furi_string_cat_printf(FuriString*, const char*, ...);
size_t search2(const FuriString*, char);
size_t search3(const FuriString*, char, size_t);
#define GETSEARCH(_1,_2,_3,NAME,...) NAME
#define furi_string_search_char(...) GETSEARCH(__VA_ARGS__,search3,search2)(__VA_ARGS__)
bool args_read_string_and_trim(FuriString*, FuriString*);
bool args_read_probably_quoted_string_and_trim(FuriString*, FuriString*);
StrintParseError strint_to_uint32(const char*, char**, uint32_t*, uint8_t);
void* furi_record_open(const char*);
void furi_record_close(const char*);
bool loader_get_application_name(Loader*, FuriString*);
bool loader_is_locked(Loader*);
bool loader_signal(Loader*, uint32_t, void*);
LoaderStatus loader_start(Loader*, const char*, const char*, FuriString*);
void cli_registry_add_command(CliRegistry*, const char*, int, CliCommandExecuteCallback, void*);
"""

harness = r"""
#include "mock.h"
static Loader loader;
static CliRegistry registry;
static CliCommandExecuteCallback registered;
static int starts, signals;
static uint32_t last_signal;
static uintptr_t last_arg;
static char last_name[256], last_args[256];
const FlipperApplication FLIPPER_APPS[]={{"A"}}, FLIPPER_SETTINGS_APPS[]={{"S"}}, FLIPPER_EXTSETTINGS_APPS[]={{"E"}};
const size_t FLIPPER_APPS_COUNT=1, FLIPPER_SETTINGS_APPS_COUNT=1, FLIPPER_EXTSETTINGS_APPS_COUNT=1;
FuriString* furi_string_alloc(void) { return calloc(1, sizeof(FuriString)); }
void furi_string_free(FuriString* s) { free(s); }
size_t furi_string_size(const FuriString* s) { return strlen(s->s); }
char furi_string_get_char(const FuriString* s, size_t p) { return s->s[p]; }
const char* furi_string_get_cstr(const FuriString* s) { return s->s; }
bool furi_string_empty(const FuriString* s) { return !s->s[0]; }
bool furi_string_equal(const FuriString* s, const char* x) { return strcmp(s->s,x)==0; }
void furi_string_set(FuriString* s, const FuriString* v) { snprintf(s->s,sizeof(s->s),"%s",v->s); }
void furi_string_set_n(FuriString* s, const FuriString* v, size_t start, size_t n) {
    assert(n<sizeof(s->s)); memcpy(s->s,v->s+start,n); s->s[n]=0;
}
void furi_string_right(FuriString* s,size_t n) { size_t len=strlen(s->s); if(n>len)n=len; memmove(s->s,s->s+n,len-n+1); }
void furi_string_trim(FuriString* s) {
    while(isspace((unsigned char)s->s[0]))furi_string_right(s,1);
    size_t n=strlen(s->s); while(n && isspace((unsigned char)s->s[n-1]))s->s[--n]=0;
}
void furi_string_cat_printf(FuriString* s,const char* fmt,...) {
    size_t n=strlen(s->s); va_list ap; va_start(ap,fmt); vsnprintf(s->s+n,sizeof(s->s)-n,fmt,ap); va_end(ap);
}
size_t search3(const FuriString* s,char c,size_t pos) {
    const char* p=strchr(s->s+pos,c); return p?(size_t)(p-s->s):FURI_STRING_FAILURE;
}
size_t search2(const FuriString* s,char c) { return search3(s,c,0); }
void* furi_record_open(const char* name) {
    if(!strcmp(name,RECORD_LOADER))return &loader;
    assert(!strcmp(name,"cli")); return &registry;
}
void furi_record_close(const char* name) { assert(!strcmp(name,"cli") || !strcmp(name,RECORD_LOADER)); }
bool loader_get_application_name(Loader* l,FuriString* name) { assert(l==&loader); strcpy(name->s,"Running"); return true; }
bool loader_is_locked(Loader* l) { assert(l==&loader); return true; }
bool loader_signal(Loader* l,uint32_t s,void* arg) { assert(l==&loader); signals++; last_signal=s; last_arg=(uintptr_t)arg; return true; }
LoaderStatus loader_start(Loader* l,const char* name,const char* arg,FuriString* err) {
    assert(l==&loader && err); starts++; snprintf(last_name,sizeof(last_name),"%s",name);
    snprintf(last_args,sizeof(last_args),"%s",arg?arg:""); return LoaderStatusOk;
}
void cli_registry_add_command(CliRegistry* r,const char* name,int flags,CliCommandExecuteCallback cb,void* ctx) {
    assert(r==&registry && !strcmp(name,RECORD_LOADER) && flags==CliCommandFlagParallelSafe && !ctx);
    registered=cb;
}
""" + '\n'.join(extract(n,t) for n,t in (
    ('args_get_first_word_length','size_t'),
    ('args_read_string_and_trim','bool'),
    ('args_read_probably_quoted_string_and_trim','bool'),
)) + r"""
#include "CLI_FILE"
static void invoke(const char* input) {
    FuriString s={0}; snprintf(s.s,sizeof(s.s),"%s",input); registered(NULL,&s,NULL);
}
int main(void) {
    loader_on_system_start(); assert(registered);
    invoke("open \"Settings\" \"/ext/my file.txt\"");
    assert(starts==1 && !strcmp(last_name,"Settings") && !strcmp(last_args,"/ext/my file.txt"));
    invoke("open App /ext/another file.txt");
    assert(starts==2 && !strcmp(last_name,"App") && !strcmp(last_args,"/ext/another file.txt"));
    invoke("open App \"unterminated");
    assert(starts==2);
    invoke("signal 5");
    assert(signals==1 && last_signal==5 && last_arg==0);
    invoke("signal 6 FF");
    assert(signals==2 && last_signal==6 && last_arg==255);
    invoke("signal xyz");
    assert(signals==2);
    invoke("close");
    assert(signals==3 && last_signal==FuriSignalExit);
    return 0;
}
"""

with tempfile.TemporaryDirectory() as d:
    p = Path(d)
    (p/'mock.h').write_text(header)
    for file in ('furi.h','loader.h','applications.h','toolbox/args.h','toolbox/strint.h',
                 'toolbox/cli/cli_registry.h','toolbox/cli/cli_command.h','toolbox/pipe.h'):
        item=p/file
        item.parent.mkdir(parents=True,exist_ok=True)
        item.write_text('#include "mock.h"\n')
    test=p/'test.c'
    cli_copy=p/'loader_cli_under_test.c'
    cli_copy.write_bytes(cli.read_bytes())
    test.write_text(harness.replace('CLI_FILE', str(cli_copy)))
    exe=p/'test'
    subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                    '-I',str(p),str(test),str(root/'components/toolbox/strint.c'),
                    '-o',str(exe)],check=True)
    subprocess.run([str(exe)],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'},check=True)
print('Loader CLI registration, quoted app paths, invalid quotes, signals and close passed.')
