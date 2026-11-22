# Status build ST7735S landscape — 22 November 2026

Target build: ESP32-S3 N16R8, ST7735S 160×128 landscape, microSD SPI3, and six
buttons. The source is an ESP32 port with selected changes from Flipper 1.5.1;
it is not the official Flipper Zero firmware and does not provide full hardware
or software parity.

## Build result

[GitHub Actions](https://github.com/gungsss/flipper-esp32s3-diy240/actions/workflows/build-st7735s-151-modules.yml)
will build one flash package for the current radio wiring profile.

| Profile | Build result | Contents |
|---|---|---|
| Radio bring-up | Awaiting this commit's CI result | ST7735S landscape, six buttons, microSD, CC1101 Sub-GHz, and nRF24L01+. The nRF24 menu is passive-survey only. |

The ST7735S renderer now uses a native 160×128 canvas. The home screen places a
clock and date above the centered pixel-art animation; the app launcher uses
five full-width rows; common submenus show more entries. These changes remove
the prior 128×64 vertical stretch and unused top/bottom bars. Applications with
fixed 128×64 coordinates may still need individual layout changes.

## Hardware validation

| Check | Status |
|---|---|
| ESP-IDF build and package validation | Pending CI for this pinout. |
| Display image, orientation, and colors on the physical panel | Not yet verified. |
| Six-button navigation on the physical board | Not yet verified. |
| microSD and both radio modules | Not yet verified. |

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

## Radio wiring update — 22 November 2026

The source profile now assigns CC1101 to its own SPI pins (SCK/MOSI/MISO 9/10/21,
CSN TX/GPIO43, GDO0 GPIO13) and nRF24 to a separate bus (SCK/MOSI/MISO
41/42/47, CSN GPIO1, CE GPIO2). GPIO46 is not used because it is an ESP32-S3
strapping pin. The nRF24 test menu exposes module detection and passive channel
survey only.

Source patch application and the static UI audit passed. The build profile
excludes the Wi-Fi attack app, raw-frame TX patch, Wifite WPS/Pixie Dust stack,
Bluetooth spam, and external attack FAPs. Streaming includes only the shared
LAN-list view it needs. Physical display, button, SD, and radio-module checks
are still pending. The CC1101 CSN wire must go to the board pad marked TX/GPIO43;
do not use GPIO46.
