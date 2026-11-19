# Native160 firmware build integration

Status: integration source and CI workflow are prepared; no firmware binary has been built yet.

## Target

- ESP32-S3 N16R8
- ST7735S, 160x128 landscape, CS tied to ground
- microSD on SPI3 and the six-button DIY pin profile
- Selected Flipper 1.5.1 compatibility changes; this is not a complete 1.5.1 port

## Build

The workflow applies the existing DIY, ST7735S, landscape, and compatibility patches first. It then checks every Native160 baseline and target-profile SHA256, applies the UI integration patch, runs its host render checks, builds with ESP-IDF 5.4.1, and validates the flash image offsets and headers.

A successful CI artifact is named `esp32s3-st7735-native160-151-preview`. The landscape panel and controls still need a physical-device boot check after flashing.
