# M4145 Flipper 1.5.1 compatibility roadmap

This branch is the canonical ST7735S 160x128 landscape / by m4145 development line.
**1.5.1 is a selective backport, not a full binary or hardware-compatible port.**

## Non-regression rules
- Preserve M4145 branding, native 160x128 UI, 6 keys, SD, USB, Wi-Fi/BLE, and existing CC1101/nRF24 driver integrations.
- Keep all original feature *categories* visible, with explicit available / missing hardware / not implemented / failed self-test states.
- Never claim a feature works solely because it appears in a menu or CI builds.
- Do not merge main branch's ST7789 240x240 hardware configuration over this profile.
- Existing ST7735S radio pinout is a **default hardware profile**, not universal wiring. Changing GPIO requires profile rebuild until runtime remapping exists.

## Feature parity work packages
| Area | Current evidence | Next acceptance test |
|---|---|---|
| GUI/animation/keyboard | Native 160x128 backport present | Physical screenshot and input regression |
| Storage/Archive | SPI3 microSD integration present | FAT32 mount, write, reopen, power-cycle |
| CC1101 | Probe and Sub-GHz app integration present | Repeated cold-boot detection, owned-device packet TX/RX, error handling |
| nRF24 | Probe and passive channel survey present | Repeatable register read/write test, paired-device packet TX/RX |
| Wi-Fi/BLE | Ordinary connection features present | Discovery and connection on authorized test network |
| USB HID/BadUSB | Port support present | Enumerate on owned host and verify safe keyboard script |
| NFC | Disabled; needs compatible frontend | Read supported lab test tag and log ID |
| LF RFID | RDM6300 read-only support upstream | Read lab tag; separate hardware for write/emulation |
| Infrared | Disabled | Decode and transmit known lab remote protocol |
| iButton | HAL not implemented | Add frontend and read lab token |
| Speaker/audio | No speaker in baseline | Add audio output driver and playback test |
| FAP/plugins | ARM Flipper binaries incompatible | Source port and build per ESP32-S3 application |

## Delivery gates
1. Compile + unit tests + source audit.
2. Binary packaging with exact target, flash offsets, checksum and provenance.
3. On-device boot, display, keys, SD, radio detection.
4. Real protocol tests with controlled owned lab targets.
5. Release notes listing features actually tested and unavailable.

No unrestricted RF disruption implementation is included in this roadmap; interference resilience can be tested using simulation or shielded conducted RF fixtures.
