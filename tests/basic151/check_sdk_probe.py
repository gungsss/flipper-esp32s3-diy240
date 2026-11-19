#!/usr/bin/env python3
"""Check the ESP SDK probe is Xtensa and imports the newly exported symbols."""
import struct
import sys
from pathlib import Path
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

artifact, imports = map(Path, sys.argv[1:3])
required = {'bit_buffer_append', 'bit_buffer_copy_bytes', 'bit_buffer_get_byte_from_bit',
            'varint_int32_pack', 'varint_int32_unpack', 'hex_chars_to_uint8',
            'menu_alloc', 'menu_free', 'aligned_malloc', 'aligned_free',
            'memmgr_get_minimum_free_heap'}
actual = set(imports.read_text().split())
assert required <= actual, f'probe imports missing: {sorted(required - actual)}'
with artifact.open('rb') as stream:
    elf = ELFFile(stream)
    assert elf['e_machine'] == 'EM_XTENSA' and elf['e_type'] == 'ET_REL'
    meta = elf.get_section_by_name('.fapmeta')
    assert meta is not None
    magic, fmt, minor, major, target, stack = struct.unpack_from('<IIHHHH', meta.data())
    assert (magic, fmt, major, minor, target) == (0x52474448, 1, 1, 0, 32)
    assert stack >= 4096
    for section in elf.iter_sections():
        if isinstance(section, RelocationSection) and elf.get_section(section['sh_info'])['sh_flags'] & 2:
            for relocation in section.iter_relocations():
                assert relocation['r_info_type'] in {0, 1, 11, 17, 18, 19, 20}
print('Native Xtensa SDK probe imports the added data, menu and memory APIs.')
