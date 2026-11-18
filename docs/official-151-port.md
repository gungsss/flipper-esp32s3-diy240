# Flipper 1.5.1 source port for the DIY ESP32-S3

## Status

This is **not yet a complete Flipper 1.5.1 ESP32 port**. Do not use a 1.5.1
identity or publish a build as complete until the remaining source and hardware
differences have been resolved and tested. The existing ST7735 web flasher is
kept separately for recovery.

The authoritative source is Flipper Devices firmware tag `1.5.1`, commit
`9e810dc399e027e48ce07751df72168abbb19065`. The ESP32 adaptation can reuse an
existing ESP-IDF hardware layer, but all portable application and service
behavior must be checked against that commit, not merely labeled 1.5.1.

`scripts/audit_official_151.py OFFICIAL_REPO PORT_REPO --output audit.json`
inventories C, header, and FAM source identity. Identical text does not prove
runtime or ABI compatibility. A missing match may be a build-system,
third-party, or STM32-specific file rather than a missing user feature; every
difference requires review. The inventory deliberately withholds the hotel NFC
parser, whose publication with embedded access keys was rejected by automatic
review.

## Target and constraints

- ESP32-S3 N16R8, 128x160 ST7735S, current tested wiring and landscape layout.
- SD module on an independent SPI bus; the panel's CS is permanently low.
- USB-serial flashing and qFlipper USB, BLE, input buttons, display and SD need
  regression tests. User settings/data must not be silently erased.
- NFC, Sub-GHz, infrared, iButton and LF RFID functionality need their own
  physical peripherals; the listed parts do not supply those radios/sensors.
- The reused Sub-GHz code changes the official frequency defaults and transmit
  region checks. It is disabled on the current DIY board and needs a separate
  implementation and hardware/regional verification before claiming parity.
- Official prebuilt ARM FAP files do not execute on the ESP32-S3's Xtensa CPU.
  Supporting applications requires an ESP32-compatible build and ABI or an
  independently tested execution layer.
- The development ELF loader rejects incompatible machine types on ESP32-S3;
  a host harness checks its real open path with ARM and Xtensa headers. This
  prevents incompatible applications from reaching the loader; it does not
  make ARM applications executable.

## Completed in this development branch

- Added the exact 1.5.1 CRC32 implementation and its two SDK exports. Host
  tests exercise buffer, incremental and file checksums against an independent
  reference; actual SD card access remains untested.
- Retained selected previously ported 1.5.1 source changes and compared the
  whole source tree against the pinned official commit.
- Matched the release's view-ID lookup behavior, including the discrepancy
  between its documented and implemented return value.
- Added the missing GUI/date-time and preset symbols from the official 1.5.1
  SDK API delta; this does not imply the rest of the official ABI is available.
- Added official GUI SDK exports for canvas, views, widgets, scenes, menus,
  buttons, icons, text input, dialogs, drawing elements and the file browser. All 252 selected
  functions have C signature checks against the 1.5.1 SDK list. These checks
  do not establish ABI or runtime equivalence across processor architectures.
- Added the remaining Flipper Format, bit buffer, and bit library function
  exports. All 61 format and 56 bit-utility functions in the 1.5.1 SDK have
  C signature checks. Actual behavior and target ABI still need validation.
- Added the remaining official stream SDK function exports, with signature
  checks for all 45 stream, string stream and file stream functions. A host
  test exercises the adapted memory stream and FuriString implementations.
- Added the missing portable archive, array, directory, path, argument, value
  and conversion exports, with C signature checks for all 66 selected functions.
- BLE Device Information identifies the actual selected ESP32 target rather
  than advertising an ESP32-C6 on S3. Bluetooth pairing on hardware is untested.
- Fixed an out-of-bounds read when retrieving a byte near the end of a bit
  buffer; the regression test catches this in the unchanged 1.5.1 source and
  passes against the adapted implementation under address/undefined sanitizers.
- Added 123 existing Furi core functions to the ESP32 SDK symbol table with
  the official 1.5.1 C signature checks, and the RTC format function used by
  the example; many other SDK exports remain absent.
- Exposed 25 additional storage, locale, and date/time functions; all 64
  official functions in those groups have 1.5.1 SDK C signature checks.
  Device storage behavior remains untested.
- Exposed 18 existing RPC functions with official C signature checks, and
  exercised the app-start request handler on the host. Bluetooth and USB
  communication still require tests on the physical board.
- Added an explicit DIY target to the FAP builder and CI checks that build the
  official 1.5.1 date/time, view-dispatcher and application-data examples for
  Xtensa, then check their imports. CI results and real-device execution must
  be verified separately.
- These three official examples also compile on the host against the port
  headers and their imports are checked against the firmware API table.
- Restored the Furi header visibility that official input headers provide,
  allowing the unchanged official view-dispatcher example to compile.
- Replaced the port's date/time input implementation and header with the exact
  official 1.5.1 sources. Host tests check the 12-hour and 24-hour render paths.
- Added the USB HID interrupt-OUT endpoint, like the 1.5.1 hardware interface,
  to both the standalone and qFlipper composite ESP32 USB configurations.
- Tested both real TinyUSB descriptor layouts and keyboard LED report handling
  on the host, including malformed and non-keyboard reports. These tests do not
  replace testing an ESP32 or a USB host.

The published 1.5.1-backport flasher is an earlier experiment and is not the
result of this branch. No new binary from this branch has been verified on the
physical device.
