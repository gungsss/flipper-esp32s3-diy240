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
- Official prebuilt ARM FAP files do not execute on the ESP32-S3's Xtensa CPU.
  Supporting applications requires an ESP32-compatible build and ABI or an
  independently tested execution layer.

## Completed in this development branch

- Retained selected previously ported 1.5.1 source changes and compared the
  whole source tree against the pinned official commit.
- Matched the release's view-ID lookup behavior, including the discrepancy
  between its documented and implemented return value.
- Added the missing GUI/date-time and preset symbols from the official 1.5.1
  SDK API delta; this does not imply the rest of the official ABI is available.
- Added the remaining available official GUI SDK function exports and checked
  their C signatures against the 1.5.1 SDK list at compile time. These checks
  do not establish ABI or runtime equivalence across processor architectures.
- Added 123 existing Furi core functions to the ESP32 SDK symbol table with
  the official 1.5.1 C signature checks, and the RTC format function used by
  the example; many other SDK exports remain absent.
- Exposed 25 additional storage, locale, and date/time functions; all 64
  official functions in those groups have 1.5.1 SDK C signature checks.
  Device storage behavior remains untested.
- Added an explicit DIY target to the FAP builder and a CI check that builds
  the official 1.5.1 date/time example for Xtensa, then checks its imports.
  CI build results and real-device execution must be verified separately.
- The same official example compiles on the host against the port headers and
  its unresolved symbols are checked against the current firmware API table.
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
