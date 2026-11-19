# ESP32-S3 ST7735S compatibility preview

This experimental build starts from the pinned Sor3nt ESP32 port and the
existing DIY ST7735S landscape board profile. The NFC application and its
card parser plugins are not part of this board profile; the source checkout is
checked for the excluded hotel parser and compile inputs are checked before
packaging. The normal upstream ESP32 firmware includes generic NFC support
libraries, even though the NFC app is disabled on this target.

The separate compatibility changes cover the loader, command-line parser,
GUI, storage and Furi API exports, file/stream and locale API exports,
file-browser callback compatibility, 12/24-hour date-input fixes,
JavaScript timer validation, RPC application context validation, ELF
architecture validation, and archive/bit-reading fixes.
The original upstream 1.5.1 date/time example is also compiled for ESP32;
its files are verified byte for byte. USB HID has both input and output
endpoints and accepts keyboard LED reports through either USB transport.
The example is also cross-compiled as a separate Xtensa FAP using the DIY
board configuration and the port's API 1.0; required imports and its target
metadata must pass before packaging. This is not an official ARM FAP and
has not yet been tested on physical hardware.
The CLI can load compatible Xtensa command plugins from storage; the loader
continues to reject plugins compiled for incompatible architectures.
The checked-in tests verify the resolver and compare these exported function
signatures with the 1.5.1 SDK. Signature checks do not establish complete
behavioral or binary compatibility with Flipper applications.
The export set includes the ten APIs newly introduced by the 1.5.1 SDK and
additional data, archive, command-line, and pipe APIs. Unsupported hardware
APIs and official ARM application binaries remain outside this preview.
The existing ESP `cli_vcp_disable` returns a status used by the USB-UART
bridge; the 1.5.1 SDK declares it `void`. The legacy behavior is retained and
this symbol is explicitly excluded from the 1.5.1 signature-coverage claim.
The firmware base still reports version **1.4.3** and the ESP application API
is not the complete official 88.2 SDK.
These changes do not constitute a complete port of 1.5.1; do not label this
build as such or offer an official Flipper update for it.

This particular build has not yet been tested on the physical device. The
portrait predecessor and display diagnostic were tested by the device owner.
