#!/usr/bin/env python3
"""Exercise the port's real ELF-open path with synthetic Xtensa and ARM files."""

import subprocess
import sys
import tempfile
from pathlib import Path

port = Path(sys.argv[1])
elf_dir = port / 'components/flipper_application/flipper_application/elf'
source = (elf_dir / 'elf_file.c').read_text()
start = source.index('bool elf_file_open(ELFFile* elf, const char* path) {')
end = source.index('\nElfLoadSectionTableResult elf_file_load_section_table(', start)
open_function = source[start:end]

prelude = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <sys/types.h>
#include "elf.h"

#define CONFIG_IDF_TARGET_ESP32S3 1
#define FSAM_READ 0
#define FSOM_OPEN_EXISTING 0
#define FURI_LOG_I(...) ((void)0)
#define FURI_LOG_E(...) ((void)0)

typedef struct { unsigned char bytes[512]; size_t pos; size_t reads; } FakeFile;
typedef struct {
    FakeFile* fd;
    size_t sections_count;
    off_t section_table, section_table_strings, entry;
} ELFFile;

static bool storage_file_open(FakeFile* file, const char* path, int mode, int open_mode) {
    (void)path; (void)mode; (void)open_mode;
    file->pos = 0;
    return true;
}
static bool storage_file_seek(FakeFile* file, off_t offset, bool from_start) {
    if(!from_start || offset < 0 || (size_t)offset >= sizeof(file->bytes)) return false;
    file->pos = (size_t)offset;
    return true;
}
static size_t storage_file_read(FakeFile* file, void* output, size_t size) {
    if(size > sizeof(file->bytes) - file->pos) return 0;
    memcpy(output, file->bytes + file->pos, size);
    file->pos += size;
    file->reads++;
    return size;
}
'''

tests = r'''
static void create_elf(FakeFile* file, uint16_t machine) {
    memset(file, 0, sizeof(*file));
    Elf32_Ehdr h = {0};
    h.e_ident[EI_MAG0] = ELFMAG0;
    h.e_ident[EI_MAG1] = ELFMAG1;
    h.e_ident[EI_MAG2] = ELFMAG2;
    h.e_ident[EI_MAG3] = ELFMAG3;
    h.e_ident[EI_CLASS] = ELFCLASS32;
    h.e_ident[EI_DATA] = ELFDATA2LSB;
    h.e_type = ET_REL;
    h.e_machine = machine;
    h.e_shoff = sizeof(h);
    h.e_shnum = 2;
    h.e_shstrndx = 1;
    memcpy(file->bytes, &h, sizeof(h));
    Elf32_Shdr section = {0};
    section.sh_offset = 240;
    memcpy(file->bytes + sizeof(h) + sizeof(section), &section, sizeof(section));
}
int main(void) {
    FakeFile file;
    ELFFile elf = {.fd = &file};

    create_elf(&file, EM_XTENSA);
    assert(elf_file_open(&elf, "test.fap"));
    assert(file.reads == 2 && elf.sections_count == 2);

    create_elf(&file, 40); /* EM_ARM */
    assert(!elf_file_open(&elf, "official-arm.fap"));
    assert(file.reads == 1); /* rejected before attempting to load sections */

    create_elf(&file, 0);
    assert(!elf_file_open(&elf, "unknown-machine.fap"));
    assert(file.reads == 1);

    create_elf(&file, EM_XTENSA);
    file.bytes[EI_MAG0] = 0;
    assert(!elf_file_open(&elf, "invalid.fap"));
    return 0;
}
'''

with tempfile.TemporaryDirectory(prefix='flipper-elf-') as temp:
    root = Path(temp)
    harness = root / 'elf_open.c'
    harness.write_text(prelude + '\n' + open_function + '\n' + tests)
    executable = root / 'elf_open'
    subprocess.run([
        'gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
        '-I', str(elf_dir), str(harness), '-o', str(executable),
    ], check=True)
    subprocess.run([str(executable)], check=True)

print('ELF-open check: Xtensa accepted; ARM, unknown machine and malformed ELF rejected.')
