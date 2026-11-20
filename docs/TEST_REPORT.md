# Status build ST7735S landscape — 20 November 2026

Target build: ESP32-S3 N16R8, ST7735S 160×128 landscape, microSD SPI3, and six
buttons. The source is an ESP32 port with selected changes from Flipper 1.5.1;
it is not the official Flipper Zero firmware and does not provide full hardware
or software parity.

## Build result

[GitHub Actions run #44725551712](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/44725551712)
completed successfully for both profiles and published the flash packages to
the branch flasher preview.

| Profile | Build result | Contents |
|---|---|---|
| Core | Compiled and packaged | ST7735S landscape display, six buttons, microSD; no optional module menus. |
| All-modules example | Compiled and packaged | CC1101 Sub-GHz, nRF24L01+, PN532 NFC, IR, and RDM6300 LF RFID read-only. Example pin assignments must match the physical wiring. |

The ST7735S renderer now uses a native 160×128 canvas. The home screen places a
clock and date above the centered pixel-art animation; the app launcher uses
five full-width rows; common submenus show more entries. These changes remove
the prior 128×64 vertical stretch and unused top/bottom bars. Applications with
fixed 128×64 coordinates may still need individual layout changes.

## Hardware validation

| Check | Status |
|---|---|
| ESP-IDF build and package validation | Passed for both profiles. |
| Display image, orientation, and colors on the physical panel | Not yet verified. |
| Six-button navigation on the physical board | Not yet verified. |
| microSD and optional modules | Not yet verified. |

The package metadata includes target dimensions, profile pinout hash, flash
offsets, and image SHA-256 values. A successful CI build confirms compilation
and packaging, not physical operation.

## Compatibility limits

- ESP32-S3 hardware differs from Flipper Zero; this firmware is a community
  port based on selected upstream 1.5.1 changes, not a full official 1.5.1 build.
- The module profile uses a sample pinout. Check every GPIO against the actual
  board and module wiring before flashing it.
- RDM6300 support is read-only; the ESP32 port does not implement the iButton
  HAL.
- If the physical screen does not match the expected ST7735S 160×128 landscape
  panel, stop and confirm the display model and wiring before flashing.
