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

## Single firmware for the current radio wiring

The current hardware test profile keeps the tested display, SD, and button
assignments unchanged and enables only CC1101 and nRF24L01+ on independent
bit-banged SPI buses. The exact wiring is in `docs/HARDWARE.md` and the selected
pinout. CC1101 is probed at startup and again when its status/app is opened;
nRF24 is checked when its app opens and from its status row. During hardware
bring-up, Jammer and MouseJacker remain visible but show that transmit actions
are unavailable; the spectrum survey is passive. The
build is tailored to test these two modules first; PN532, IR, and LF RFID pins
are disabled until their wiring is separately assigned.

| Module | Required pin fields | Current ESP32 port support |
|---|---|---|
| CC1101 Sub-GHz | `CC1101_SCK`, `CC1101_MOSI`, `CC1101_MISO`, `CC1101_CS`, `CC1101_GDO0` | Dedicated bit-banged SPI on GPIO9/10/21; CSN TX/GPIO43; GDO0 GPIO13. |
| nRF24L01+ | `NRF24_SCK`, `NRF24_MOSI`, `NRF24_MISO`, `NRF24_CS`, `NRF24_CE` | Independent bit-banged SPI on GPIO41/42/47; CSN GPIO1; CE GPIO2. |
| PN532 NFC | `NFC_SDA`, `NFC_SCL` | Disabled in this test profile pending separate pin assignment. |
| Infrared | `IR_TX`, `IR_RX` | Disabled in this test profile pending separate pin assignment. |
| LF RFID | `RFID_TX`, `RFID_RX` | Disabled in this test profile pending separate pin assignment. |

The current port does not implement the iButton HAL. RDM6300 is read-only, and
does not replace LF RFID writing or emulation. Those functions need a compatible
external frontend and a separate M4145 driver/app implementation; they are not
presented as working until implemented. ESP32-S3 also lacks the onboard speaker
and several dedicated Flipper Zero circuits.

The hardware bring-up image excludes the Wi-Fi attack app, raw-frame transmit
patch, Wifite WPS/Pixie Dust stack, Bluetooth spam app, and external attack FAPs.
These are not needed to check the CC1101/nRF24 wiring. PN532, IR, and LF RFID
remain disabled in this pinout until their GPIOs are assigned and a new profile
is built.

To build, install ESP-IDF v5.4.1 and run:

```sh
bash scripts/build_local.sh
```

The default pinout is `patch/Pinout_ESP32S3_ST7735S_160.txt`; it preserves the
existing display, SD, and button wiring. GPIO46 is not used because it is an
ESP32-S3 strap pin. The board labels GPIO43 as TX; move the CC1101 CSN lead from
GPIO46 to TX before flashing. The build script disables the UART console and
regenerates the board header from that file.

The Flipper 1.5.1 changes are an ESP32 backport, not the official Flipper Zero
firmware binary or full feature parity. A successful compile still needs a
physical check of the screen, buttons, SD card, and every attached module.
