# ESP32-S3 + ST7735S landscape profile

The default build target is ESP32-S3 N16R8 with an ST7735S 160×128 panel in
landscape orientation. The panel uses SPI2 (SCK GPIO12, MOSI GPIO11, DC GPIO15,
RST GPIO16) and its CS pin is tied to GND. The panel runs at 5 MHz. The microSD
module stays on a separate SPI3 bus (SCK 40, MOSI 39, MISO 38, CS 14); do not
move it onto the display or radio bus.

The standard Flipper UI framebuffer is 128×64 and is scaled to the ST7735S
panel. The panel mode is 160×128 landscape, but some upstream views still use
the original Flipper layout; this port does not claim that every screen has a
native 160×128 redesign.

## Optional modules

The base pinout keeps external modules off. The generator enables a module and
its menu only when its required pins are assigned in the selected pinout file.
Each pin must match the actual wiring. The generator rejects duplicate pins and
the ESP32-S3 N16R8 flash, PSRAM, and USB pins. Avoid strapping pins and GPIOs
already used by the board. There are not enough free GPIOs for every module to
be attached at once without changing the board wiring. An example profile that
assigns candidate pins for all listed modules is at
`patch/Pinout_ESP32S3_ST7735S_160_all_modules.example.txt`; those GPIOs have not
been checked on the user's exact PCB. Modules are compile-time options, not
automatic hot-plug detection: wire the module, select its pinout, rebuild, and
flash that build.

| Module | Required pin fields | Current ESP32 port support |
|---|---|---|
| CC1101 Sub-GHz | `CC1101_SCK`, `CC1101_MOSI`, `CC1101_MISO`, `CC1101_CS`, `CC1101_GDO0` | Uses a dedicated bit-banged SPI bus, isolated from the CS-less display and microSD. |
| nRF24L01+ | Radio bus pins above, `NRF24_CS`, `NRF24_CE` | Shares the dedicated radio bus with CC1101; it can be used without a CC1101 chip if wired to that same bus. |
| PN532 NFC | `NFC_SDA`, `NFC_SCL` | PN532 I²C HAL; `NFC_IRQ` and `NFC_RST` are optional. This is not the stock Flipper ST25R3916 hardware. |
| Infrared | `IR_TX`, `IR_RX` | ESP32 RMT transmit and receive. |
| LF RFID | `RFID_TX`, `RFID_RX` | RDM6300 UART reader, read-only. It does not provide native LF RFID writing or emulation. |

The upstream ESP32 port does not currently implement the iButton HAL, so the
iButton app is not enabled for this target. Software features that need a
speaker, analog LF RFID frontend, or other absent board hardware remain limited
even if the corresponding Flipper Zero app exists upstream.

To build, install ESP-IDF v5.4.1 and run:

```sh
bash scripts/build_local.sh
```

The default pinout is `patch/Pinout_ESP32S3_ST7735S_160.txt`. The example
module-ready pinout can be selected with
`ST7735_PINOUT=patch/Pinout_ESP32S3_ST7735S_160_all_modules.example.txt`;
first confirm that its GPIOs are exposed and free on the actual board. Any
custom profile must preserve the display, SD, and button wiring. The build
script regenerates the board header from that file before compiling.

The Flipper 1.5.1 changes are an ESP32 backport, not the official Flipper Zero
firmware binary or full feature parity. A successful compile still needs a
physical check of the screen, buttons, SD card, and every attached module.
