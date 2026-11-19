#!/usr/bin/env python3
"""Validate the native example's architecture and honestly versioned manifest."""
import struct
import sys
from pathlib import Path
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

path = Path(sys.argv[1])
with path.open('rb') as stream:
    elf = ELFFile(stream)
    assert elf['e_machine'] == 'EM_XTENSA', 'not an ESP32 Xtensa app'
    assert elf['e_type'] == 'ET_REL', 'app is not relocatable'
    metadata = elf.get_section_by_name('.fapmeta')
    assert metadata is not None, 'missing FAP manifest'
    magic, fmt_version, minor, major, target, stack_size = struct.unpack_from('<IIHHHH', metadata.data())
    assert (magic, fmt_version, major, minor, target) == (0x52474448, 1, 1, 0, 32)
    assert stack_size >= 4096
    supported_relocations = {0, 1, 11, 17, 18, 19, 20}
    for section in elf.iter_sections():
        if isinstance(section, RelocationSection) and elf.get_section(section['sh_info'])['sh_flags'] & 2:
            for relocation in section.iter_relocations():
                assert relocation['r_info_type'] in supported_relocations, (
                    f"unsupported ESP loader relocation: {relocation['r_info_type']}"
                )
print('Official 1.5.1 example compiled for Xtensa, target 32, ESP app API 1.0.')
