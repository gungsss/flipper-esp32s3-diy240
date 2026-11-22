# Radio probe integration status

This directory contains an **initial ESP-IDF SPI probe component**, not a complete CC1101/nRF24 driver or a flash-ready firmware.

## Current implementation
- Runtime SPI host and pin configuration
- CC1101 PARTNUM/VERSION register reads
- nRF24 CONFIG/RF_CH/SETUP_AW register reads
- Device add/remove and basic error propagation

## Integration work still required
1. Copy/register this component in the pinned upstream ESP-IDF build (the integration repository fetches upstream source at build time). The component is **not automatically included** by the current build workflow.
2. Connect the runtime GPIO profile to a board configuration and add a menu entry with actual driver status.
3. Implement CC1101 chip-select-ready handshake and reset/oscillator startup handling; a bare SPI register read is insufficient for robust CC1101 detection.
4. Configure nRF24 CE and optional IRQ; add safe TX/RX packet tests using a second owned device.
5. Add repeated cold-boot tests, missing-device tests, and regression tests for TFT, SD, keys, Wi-Fi and BLE.
6. Compile through CI and test physically. **No CI build or physical test has been performed for this component yet.**

## Hardware
Use 3.3V and shared ground. SPI lines may be shared between radios with separate CS pins, subject to available SPI hosts and the display/SD bus topology. A single ESP32-S3 has limited hardware SPI controllers; do not assume three independent general-purpose SPI buses. Avoid ESP32-S3 strapping pins, flash/PSRAM pins, and native USB pins.

The initial probe uses simple read-only SPI transactions. It does not transmit RF, implement jamming, or claim complete Flipper functionality.
