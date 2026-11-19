#!/usr/bin/env python3
"""Verify the actual ESP32-S3 binary contains the expected board profile."""
import struct
import sys
from pathlib import Path

image = Path(sys.argv[1]).read_bytes()
display_controller = int(sys.argv[2]) if len(sys.argv) > 2 else 7735
# ESP-IDF v5.4: image header (24), first segment header (8), app description (256).
offset = 24 + 8 + 256
expected = struct.pack(
    '<8sHH16H', b'DIYOTA1\0', 1, display_controller,
    11, 12, 15, 16, 65535, 7,
    40, 39, 38, 14, 4, 5, 6, 17, 8, 18,
)
assert len(image) >= offset + len(expected), 'application image too small'
assert image[0] == 0xe9 and image[12:14] == b'\x09\x00', 'image is not ESP32-S3'
actual = image[offset:offset + len(expected)]
if actual != expected:
    marker = b'DIYOTA1\0'
    markers = []
    start = 0
    while True:
        position = image.find(marker, start)
        if position < 0:
            break
        markers.append(position)
        start = position + 1
    print(f'OTA profile diagnostic: expected_offset={offset}, marker_offsets={markers}')
    print(f'OTA profile bytes at expected offset: {actual.hex()}')
    print(f'OTA profile expected bytes:          {expected.hex()}')
assert actual == expected, 'missing or incorrect OTA board profile'
print(f'ESP32-S3 image contains the expected display {display_controller}/SD/button wiring profile.')
