#!/usr/bin/env python3
"""Add the official 1.5.1 hotel-card parser to the ESP32 NFC app."""
from pathlib import Path
import sys
import shutil


APP_BLOCK = '''\n\nApp(
    appid="hotels_parser",
    apptype=FlipperAppType.PLUGIN,
    entry_point="hotels_plugin_ep",
    targets=["f7", "f32"],
    requires=["nfc"],
    sources=["plugins/supported_cards/hotels.c"],
)
'''


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_hotels_151.py /path/to/patched/upstream")

    root = Path(sys.argv[1]).resolve()
    source = Path(__file__).resolve().with_name("hotels_151.c")
    plugin = root / "applications/main/nfc/plugins/supported_cards/hotels.c"
    plugin.parent.mkdir(parents=True, exist_ok=True)
    plugin.write_bytes(source.read_bytes())

    # Keep the 1.5.1 Japanese HID layout on the SD image, where BadUSB looks
    # for user-selectable keymaps at runtime.
    layout_source = root / "applications/main/bad_usb/resources/badusb/assets/layouts/ja-JP.kl"
    layout_target = root / "sdcard/badusb/assets/layouts/ja-JP.kl"
    if not layout_source.is_file():
        raise SystemExit("The pinned upstream Japanese BadUSB layout is missing")
    layout_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(layout_source, layout_target)

    fam = root / "applications/main/nfc/application.fam"
    text = fam.read_text(encoding="utf-8")
    if 'appid="hotels_parser"' not in text:
        fam.write_text(text.rstrip() + APP_BLOCK, encoding="utf-8")
    print("Added 1.5.1 hotel-card parser and Japanese BadUSB layout")


if __name__ == "__main__":
    main()
