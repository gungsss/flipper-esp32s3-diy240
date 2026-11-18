# ESP32-S3 ST7735S compatibility preview

This experimental build starts from the pinned Sor3nt ESP32 port and the
existing DIY ST7735S landscape board profile. The NFC application and its
card parser plugins are not part of this board profile; the source checkout is
checked for the excluded hotel parser and compile inputs are checked before
packaging. The normal upstream ESP32 firmware includes generic NFC support
libraries, even though the NFC app is disabled on this target.

The separate compatibility changes cover the loader, command-line parser,
some GUI API exports, RPC application context validation, and an archive read
fix from official 1.5.1. The firmware base still reports version **1.4.3**.
These changes do not constitute a complete port of 1.5.1; do not label this
build as such or offer an official Flipper update for it.

This particular build has not yet been tested on the physical device. The
portrait predecessor and display diagnostic were tested by the device owner.
