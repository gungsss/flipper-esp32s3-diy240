#!/usr/bin/env python3
"""Verify the actual ESP32-S3 binary contains the expected board profile."""
import struct
import sys
from pathlib import Path

image = Path(sys.argv[1]).read_bytes()\ndisplay_controller = int(sys.argv[2]) if len(sys.argv) > 2 else 7735
# ESP-IDF v5.4: image header (24), first segment header (8), app description (256).
offset = 24 + 8 + 256
expected = struct.pack(
    '<8sHH16H', b'DIYOTA1\0', 1, 7735,
    11, 12, 15, 16, 65535, 7,
    40, 39, 38, 14, 4, 5, 6, 17, 8, 18,
)
assert len(image) >= offset + len(expected), 'application image too small'
assert image[0] == 0xe9 and image[12:14] == b'\x09\x00', 'image is not ESP32-S3'
assert image[offset:offset + len(expected)] == expected, 'missing or incorrect OTA board profile'
print(f'ESP32-S3 image contains the expected display {display_controller}/SD/button wiring profile.')
