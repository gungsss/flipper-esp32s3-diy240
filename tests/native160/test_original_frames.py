#!/usr/bin/env python3
"""Decode the upstream internal TV animation using its vendored decoder.

Only the named animation asset and heatshrink decoder are read. This host
check does not build the firmware and does not include extracted frames in it.
"""
from __future__ import annotations

import ctypes
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def decode(lib, icon: bytes) -> bytes:
    if not icon or icon[0] != 1 or len(icon) < 4:
        raise ValueError("unexpected compressed icon header")
    compressed_size = int.from_bytes(icon[2:4], "little")
    if compressed_size != len(icon) - 4:
        raise ValueError("compressed icon length mismatch")
    data = icon[4:]
    decoder = lib.heatshrink_decoder_alloc(256, 8, 4)
    if not decoder:
        raise MemoryError("heatshrink decoder allocation failed")
    result = bytearray()

    def poll() -> None:
        while True:
            out = (ctypes.c_uint8 * 1024)()
            count = ctypes.c_size_t()
            status = lib.heatshrink_decoder_poll(decoder, out, len(out), ctypes.byref(count))
            if status < 0:
                raise ValueError("heatshrink poll failed")
            result.extend(bytes(out[:count.value]))
            if status == 0:
                return

    try:
        offset = 0
        while offset < len(data):
            chunk = (ctypes.c_uint8 * (len(data) - offset)).from_buffer_copy(data[offset:])
            sunk = ctypes.c_size_t()
            status = lib.heatshrink_decoder_sink(decoder, chunk, len(chunk), ctypes.byref(sunk))
            if status < 0 or not sunk.value:
                raise ValueError("heatshrink sink failed")
            offset += sunk.value
            poll()
        while True:
            status = lib.heatshrink_decoder_finish(decoder)
            if status < 0:
                raise ValueError("heatshrink finish failed")
            if status == 0:
                break
            poll()
        return bytes(result)
    finally:
        lib.heatshrink_decoder_free(decoder)


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: test_original_frames.py SOURCE_ROOT [FRAME_DIR]")
    root = Path(sys.argv[1]).resolve()
    asset = root / "components/desktop/animations/assets_dolphin_internal.c"
    heat = root / "components/heatshrink"
    text = asset.read_text(encoding="utf-8")
    order_match = re.search(
        r"const uint8_t L1_Tv_128x47_frame_order\[\] = \{(.*?)\};", text, re.DOTALL
    )
    animation_match = re.search(
        r"const BubbleAnimation BA_L1_Tv_128x47 = \{(.*?)\n\};", text, re.DOTALL
    )
    if not order_match or not animation_match:
        raise ValueError("missing original animation metadata")
    order = [int(value) for value in re.findall(r"\d+", order_match.group(1))]
    animation_text = animation_match.group(1)
    fields = {}
    for field in ("width", "height", "frame_count", "frame_rate", "passive_frames",
                  "active_frames", "active_cycles", "active_cooldown"):
        match = re.search(rf"\.{field}\s*=\s*(\d+)", animation_text)
        if not match:
            raise ValueError(f"missing animation field {field}")
        fields[field] = int(match.group(1))
    fields["order"] = order
    if (fields["width"], fields["height"], fields["frame_count"]) != (128, 47, 8):
        raise ValueError("unexpected source animation geometry")
    if not fields["frame_rate"] or len(order) != fields["passive_frames"] + fields["active_frames"]:
        raise ValueError("invalid animation timing or frame order")
    if any(index >= fields["frame_count"] for index in order):
        raise ValueError("invalid animation frame index")

    with tempfile.TemporaryDirectory(prefix="native-ui-test-") as temp:
        library = Path(temp) / "libheatshrink.so"
        subprocess.run(
            ["gcc", "-shared", "-fPIC", "-O2", "-I", str(heat),
             str(heat / "heatshrink_decoder.c"), "-o", str(library)],
            check=True,
        )
        lib = ctypes.CDLL(str(library))
        ptr = ctypes.c_void_p
        u8ptr = ctypes.POINTER(ctypes.c_uint8)
        sizeptr = ctypes.POINTER(ctypes.c_size_t)
        lib.heatshrink_decoder_alloc.argtypes = [ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint8]
        lib.heatshrink_decoder_alloc.restype = ptr
        lib.heatshrink_decoder_sink.argtypes = [ptr, u8ptr, ctypes.c_size_t, sizeptr]
        lib.heatshrink_decoder_poll.argtypes = [ptr, u8ptr, ctypes.c_size_t, sizeptr]
        lib.heatshrink_decoder_finish.argtypes = [ptr]
        lib.heatshrink_decoder_free.argtypes = [ptr]

        frames = []
        for index in range(8):
            pattern = rf"const uint8_t _A_L1_Tv_128x47_{index}\[\] = \{{(.*?)\}};"
            match = re.search(pattern, text, re.DOTALL)
            if not match:
                raise ValueError(f"missing original animation frame {index}")
            icon = bytes(int(v, 16) for v in re.findall(r"0x([0-9a-fA-F]+)", match.group(1)))
            frame = decode(lib, icon)
            if len(frame) != 16 * 47:
                raise ValueError(f"frame {index}: unexpected decoded length {len(frame)}")
            frames.append(frame)

    if len(set(frames)) < 2:
        raise ValueError("animation frames unexpectedly identical")
    if len(sys.argv) == 3:
        target = Path(sys.argv[2])
        target.mkdir(parents=True, exist_ok=True)
        for index, frame in enumerate(frames):
            (target / f"frame-{index}.raw").write_bytes(frame)
        (target / "animation.json").write_text(json.dumps(fields, indent=2) + "\n")
    print("PASS: 8 original 128x47 frames decoded; order and timing checked")


if __name__ == "__main__":
    main()
