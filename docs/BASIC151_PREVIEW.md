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
The build also verifies a manifest of 189 byte-identical supported core source
files against the official 1.5.1 tree. Adapted files and unsupported modules
remain separate work; this file count is not a complete-port claim.
The original upstream 1.5.1 date/time example is also compiled for ESP32;
its files are verified byte for byte. USB HID has both input and output
endpoints and accepts keyboard LED reports through either USB transport.
The example is also cross-compiled as a separate Xtensa FAP using the DIY
board configuration and the port's API 1.0; required imports and its target
metadata must pass before packaging. This is not an official ARM FAP and
has not yet been tested on physical hardware.
The CLI can load compatible Xtensa command plugins from storage; the loader
continues to reject plugins compiled for incompatible architectures.
The application loader resolves external app names and file paths, rejects
plugin-only modules without terminating the firmware, reports preload and
link failures separately, and holds the app's power state until it stops.
Desktop RPC lock status and subscriptions are included; remote unlocking of
a locked device is disabled because this port permits BLE RPC while locked.
The 1.5.1 internal-backup and archive RPC handlers are enabled for testing;
archive paths are checked before extraction. Backup covers files under `/int`
on the microSD, but does not include settings stored only in the ESP's NVS.
These operations have host tests but have not yet been exercised with qFlipper
or a physical microSD card and are not a complete device backup.
The checked-in tests verify the resolver and compare these exported function
signatures with the 1.5.1 SDK. Signature checks do not establish complete
behavioral or binary compatibility with Flipper applications.
The export set includes the ten APIs newly introduced by the 1.5.1 SDK and
additional data, archive, command-line, and pipe APIs. Unsupported hardware
APIs and official ARM application binaries remain outside this preview.
The storage directory check, clock and locale setters, and dolphin service
APIs have also been added to the ESP resolver with 1.5.1 signature checks.
The ESP application loader and Protocol Buffers encoding/decoding functions
are additionally exported to compatible native ESP applications.
RPC application and session interfaces are also exposed to native ESP apps.
The empty-screen GUI module, filename validators, name generator and value
lookup helpers are available through the same resolver.
The ESP `cli_vcp_disable` legacy application symbol returns a status used by
the USB-UART bridge. The 1.5.1 source signature is `void`: new ESP apps can
opt into that signature through `components/compat/cli_vcp_151.h`, while the
legacy resolver keeps its old behavior. This is an adapter for one API, not a
claim of complete official 88.2 ABI compatibility.
The firmware base still reports version **1.4.3** and the ESP application API
is not the complete official 88.2 SDK.
These changes do not constitute a complete port of 1.5.1; do not label this
build as such or offer an official Flipper update for it.

This particular build has not yet been tested on the physical device. The
portrait predecessor and display diagnostic were tested by the device owner.
