# M4145 ESP32-S3 + ST7735S landscape profile

The default build target is ESP32-S3 N16R8 with an ST7735S 160×128 panel in
landscape orientation. The panel uses SPI2 (SCK GPIO12, MOSI GPIO11, DC GPIO15,
RST GPIO16) and its CS pin is tied to GND. The panel runs at 5 MHz. The microSD
module stays on a separate SPI3 bus (SCK 40, MOSI 39, MISO 38, CS 14); do not
move it onto the display or radio bus.

This profile changes the GUI canvas to native 160×128 and renders it directly
to the full panel. The home screen adds a compact clock/date above the pixel-art
animation. Its `FLIPPER ZERO` label now sits lower with spacing before the
divider, correcting the top-edge crowding visible on the user's panel. The
launcher uses five full-height rows; the file browser, settings, text and number
editors, date-time editor, and common submenus have layouts for landscape. Other
app views using the shared Canvas API are routed through a 128×64-to-160×128
adapter. The six-button profile declares a D-pad, so text/byte editors and button
panels use the correct physical arrow directions. New text begins lowercase;
hold OK on the keyboard-layout key to toggle Caps Lock. The BLE pairing code uses
a separate native full-screen layout, avoiding the old 128×64 illustration and
overlapping text. Source audit checks the Canvas primitives, shared GUI paths,
keyboard/navigation contracts, and pairing geometry; the board still needs a
physical screen-by-screen check.

## Single universal firmware and optional modules

The single downloadable firmware compiles all module menus and drivers listed
below. The tested display, SD, and button assignments stay unchanged; optional
module GPIOs are reserved in `patch/Pinout_ESP32S3_ST7735S_160.txt`. Connect a
supported module to those exact GPIOs and 3.3 V. No rebuild or reflash is needed
when adding a supported module. Check that the selected ESP32-S3 board exposes
each GPIO and has no onboard component using it. CC1101 is probed at startup;
PN532 and nRF24 are checked when their app opens. IR and RDM6300 have no module
identity signal, so their screens explain how to confirm the wiring and test
them instead of claiming automatic presence detection.

| Module | Required pin fields | Current ESP32 port support |
|---|---|---|
| CC1101 Sub-GHz | `CC1101_SCK`, `CC1101_MOSI`, `CC1101_MISO`, `CC1101_CS`, `CC1101_GDO0` | Dedicated bit-banged SPI bus, isolated from the CS-less display and microSD. |
| nRF24L01+ | Radio bus pins above, `NRF24_CS`, `NRF24_CE` | Shares the dedicated radio bus with CC1101; can be used without a CC1101 if wired to that same bus. |
| PN532 NFC | `NFC_SDA`, `NFC_SCL` | PN532 I²C HAL; `NFC_IRQ` and `NFC_RST` optional. Different capabilities from the stock ST25R3916 hardware. |
| Infrared | `IR_TX`, `IR_RX` | ESP32 RMT transmit and receive; IR LED driver and receiver are separate hardware. |
| LF RFID | `RFID_TX`, `RFID_RX` | RDM6300 UART read-only support. No writing or emulation. |

The current port does not implement the iButton HAL. RDM6300 is read-only, and
does not replace LF RFID writing or emulation. Those functions need a compatible
external frontend and a separate M4145 driver/app implementation; they are not
presented as working until implemented. ESP32-S3 also lacks the onboard speaker
and several dedicated Flipper Zero circuits.

To build, install ESP-IDF v5.4.1 and run:

```sh
bash scripts/build_local.sh
```

The sole default pinout is `patch/Pinout_ESP32S3_ST7735S_160.txt`; it preserves
the existing display, SD, and button wiring and reserves the module pins above.
The build script regenerates the board header from that file before compiling.

The Flipper 1.5.1 changes are an ESP32 backport, not the official Flipper Zero
firmware binary or full feature parity. A successful compile still needs a
physical check of the screen, buttons, SD card, and every attached module.
