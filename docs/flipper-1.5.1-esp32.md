# Flipper 1.5.1 changes for the ST7735S ESP32-S3 build

This experimental variant starts with Sor3nt/Flipper-Zero-ESP32-Port commit
`e6ec11972a8e025d7ab686a6ef3016cf52360834` and incorporates selected changes
from the official Flipper Zero `1.4.3` to `1.5.1` source comparison. It is not
the stock Flipper Zero binary, nor is every 1.5.1 feature available on ESP32.
The reported Flipper compatibility version is deliberately left at 1.4.3 until
the full compatibility implications are established; changing that string
would not by itself upgrade the firmware.

The patch adds or adapts upstream changes to RPC instance validation, GUI
APIs, CLI quoted arguments, bit extraction bounds checks, NFC protocol
handling, infrared bounds checks, tar extraction, JavaScript and loader code.
Some 1.5.1 features, including the Elplast protocol and the wider BLE HID
keyboard report, were already present in the ESP32 source. Existing ESP32
storage, hardware HAL, Bluetooth and custom protocol modifications are
retained. Changes that only target the original STM32 hardware cannot simply
be applied to the ESP32 HAL. The upstream hotel-card parser was deliberately
excluded because it contains access keys; NFC hardware is not part of this
build profile.

The official `view_dispatcher_check_id` implementation in tag `1.5.1`
returns the opposite of the public header's documented result. The current
development branch preserves the released implementation's behavior and
tests it explicitly. The five added FAP exports are inserted in hash order
without changing the ESP32 FAP API's existing major version.
Official Flipper FAPs are compiled for a different architecture and are not
made compatible by these exports.

`patch/flipper_1_5_1_port.patch` is applied against the pinned Sor3nt tree
before the existing DIY and ST7735S board patches. Both portrait and landscape
builds use the same pins and keep the known working build separately.
Neither variant has been tested on the owner's hardware as part of this change.
Bluetooth, qFlipper USB, microSD and peripheral behavior require hardware
validation. Keep the previously working flasher available for recovery.

The inherited updater continues to target Sor3nt's T-Embed release feed, not
this custom ST7735S build. Do not install the stock T-Embed update from it.
