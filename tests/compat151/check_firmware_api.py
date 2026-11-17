#!/usr/bin/env python3
"""Verify the binary-search symbol table stays sorted and collision-free."""
import re
import sys
from pathlib import Path

source = Path(sys.argv[1], 'components/flipper_application/flipper_application/firmware_api.c').read_text()
rows = re.findall(r'\.hash = 0x([0-9a-fA-F]+),\s*\.address = \(uint32_t\).*?/\* (.*?) \*/', source)
assert rows, 'no firmware API table entries found'
hashes = [int(value, 16) for value, _ in rows]
assert hashes == sorted(hashes), 'firmware API table must be sorted by hash'
assert len(hashes) == len(set(hashes)), 'firmware API table has a hash collision'
names = [name for _, name in rows]
for name in ('canvas_get_buffer', 'canvas_get_buffer_size', 'variable_item_set_item_label',
             'view_dispatcher_check_id', 'gui_view_port_send_to_back',
             'date_time_input_alloc', 'date_time_input_free', 'date_time_input_get_view',
             'date_time_input_set_editable_fields', 'date_time_input_set_result_callback',
             'subghz_device_cc1101_preset_2fsk_dev12khz_async_regs',
             'view_dispatcher_send_to_back'):
    assert names.count(name) == 1, f'missing or duplicated API export: {name}'
print(f'Validated {len(rows)} sorted API exports.')
