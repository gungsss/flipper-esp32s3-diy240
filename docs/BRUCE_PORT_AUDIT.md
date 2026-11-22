# Bruce → M4145 integration audit

Reference: https://github.com/BruceDevices/firmware (AGPL-3.0).
Target: M4145 ESP32-S3 N16R8, ST7735S 160x128 landscape.
This is a compatibility and provenance audit, **not** a claim that Bruce functionality has been ported.

| Bruce subsystem | M4145 target | Implementation boundary |
|---|---|---|
| CC1101 RF settings | frequency, modulation, RSSI/LQI, RX/TX of owned lab packets | Native ESP32-S3 driver, preserve existing GPIO profile |
| RF spectrum | live radio measurements and visualization | Use physical radio samples, no simulated measurements |
| nRF24 spectrum | real channel activity survey | Existing passive survey; hardware verification pending |
| nRF24 packet link | paired lab transceiver communication and loss metrics | Implement safe packet TX/RX and repeatable device tests |
| IR receiver and protocols | decode, save, and replay authorized remote controls | Requires IR receiver/transmitter and GPIO allocation |
| NFC/RFID | reader/writer on supported lab tags | Requires separate supported frontend; no equivalence claims |
| USB HID | device enumeration and lab automation | Use authorized host and bounded test scripts |
| SD file manager | import/export capture and test results | Existing SPI3 card mount must be verified |

## Deferred high-risk functionality
Bruce documents RF jamming and nRF24 jamming. This audit does not port indiscriminate interference transmission or device-takeover payloads. Real conducted/shielded RF interference studies can use calibrated lab equipment, with M4145 collecting receiver measurements.

## Source and licensing rules
- Bruce repository declares AGPL-3.0; do not copy code into M4145 until the project's full license compatibility and source-disclosure requirements have been reviewed.
- Track upstream file paths, commit SHAs, copyright notices, and any changes for each imported component.
- Prefer original M4145 implementations based on public chip datasheets for straightforward drivers.
- No feature may be marked functional until compilation and physical board tests pass.

## First implementation gate
1. Preserve ST7735S profile and by m4145 branding.
2. Verify CC1101 and nRF24 register reads on real hardware.
3. Establish paired radio packet TX/RX in a conducted/shielded setup.
4. Export timestamps, sequence numbers, loss rates, RSSI/LQI where supported, and error codes to microSD.
5. Package flash image only after CI and device acceptance evidence.
