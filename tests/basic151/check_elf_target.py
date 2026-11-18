#!/usr/bin/env python3
"""Run the ESP loader's real ELF open routine against Xtensa and ARM headers."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
source = (root / 'components/flipper_application/flipper_application/elf/elf_file.c').read_text()
match = re.search(r'(?m)^bool elf_file_open\(ELFFile\* elf, const char\* path\) \{', source)
assert match
index, depth = match.end(), 1
while depth:
    if source[index] == '{':
        depth += 1
    elif source[index] == '}':
        depth -= 1
    index += 1
function = source[match.start():index]
prelude = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <sys/types.h>
#include "elf.h"
#define FURI_LOG_I(...) ((void)0)
#define FURI_LOG_E(...) ((void)0)
enum { FSAM_READ, FSOM_OPEN_EXISTING };
typedef struct { unsigned char bytes[sizeof(Elf32_Ehdr) + sizeof(Elf32_Shdr)]; size_t offset; } File;
typedef struct {
    File* fd;
    Elf32_Addr entry;
    uint16_t sections_count;
    uint32_t section_table;
    uint32_t section_table_strings;
} ELFFile;
static bool storage_file_open(File* file, const char* path, int mode, int open_mode) {
    (void)path; (void)mode; (void)open_mode; file->offset = 0; return true;
}
static bool storage_file_seek(File* file, off_t offset, bool from_start) {
    assert(from_start);
    if(offset < 0 || (size_t)offset > sizeof(file->bytes)) return false;
    file->offset = (size_t)offset; return true;
}
static size_t storage_file_read(File* file, void* dst, size_t size) {
    if(size > sizeof(file->bytes) - file->offset) return 0;
    memcpy(dst, file->bytes + file->offset, size); file->offset += size; return size;
}
'''
tests = r'''
int main(void) {
    File file = {0}; ELFFile elf = {.fd = &file};
    Elf32_Ehdr h = {0}; Elf32_Shdr section = {0};
    h.e_ident[EI_MAG0] = ELFMAG0; h.e_ident[EI_MAG1] = ELFMAG1;
    h.e_ident[EI_MAG2] = ELFMAG2; h.e_ident[EI_MAG3] = ELFMAG3;
    h.e_ident[EI_CLASS] = ELFCLASS32; h.e_ident[EI_DATA] = ELFDATA2LSB;
    h.e_type = ET_REL; h.e_shoff = sizeof(h); h.e_shnum = 1; h.e_shstrndx = 0;
    h.e_machine = 40; /* ARM: official Flipper application */
    memcpy(file.bytes, &h, sizeof(h)); memcpy(file.bytes + sizeof(h), &section, sizeof(section));
    assert(!elf_file_open(&elf, "arm.fap"));
    h.e_machine = EM_XTENSA; memcpy(file.bytes, &h, sizeof(h));
    assert(elf_file_open(&elf, "xtensa.fap"));
    h.e_machine = 0; memcpy(file.bytes, &h, sizeof(h));
    assert(!elf_file_open(&elf, "unknown.fap"));
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='esp-elf-target-') as temp:
    temp = Path(temp)
    (temp / 'test.c').write_text(prelude + '\n' + function + '\n' + tests)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-I', str(root / 'components/flipper_application/flipper_application/elf'),
                    str(temp / 'test.c'), '-o', str(temp / 'test')], check=True)
    subprocess.run([str(temp / 'test')], check=True)
print('ESP ELF loader accepts Xtensa and rejects ARM/unknown applications.')
