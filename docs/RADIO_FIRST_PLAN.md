# Radio-first development plan (CC1101 + nRF24L01+)

Status: integration specification; **not yet implemented or hardware-verified**.

## Non-regression contract
- Preserve upstream feature categories, menu entries, and existing functional drivers.
- Unsupported hardware must show an honest unavailable/needs-module status, never a fake success.
- Keep firmware profile variants for ST7789 240x240 and ST7735S 160x128; never silently substitute one panel for the other.
- Keep six-button navigation, microSD, Wi-Fi/BLE and USB intact.

## Hardware baseline from existing docs
- ESP32-S3 N16R8; microSD SPI3 CLK40/MOSI39/MISO38/CS14.
- Existing ST7789 SPI2 CLK12/MOSI11/DC15/RST16 (subject to confirmation for current ST7735S panel).
- Keys UP4/DOWN5/LEFT6/RIGHT17/OK8/BACK18.
- Radio pin assignment **unconfirmed**. Do not use GPIO46 as CS: it is a strapping pin with special boot constraints. Avoid reserved flash/PSRAM and native USB pins.
- Both radio modules require stable 3.3 V supply and common ground; nRF24L01+ modules can be sensitive to supply transients.

## Milestone R0: establish exact physical pinout
Record CC1101 SCK/MOSI/MISO/CS/GDO0/GDO2 and nRF24 SCK/MOSI/MISO/CSN/CE/IRQ as actually wired. Confirm screen controller and dimensions. Identify bus sharing and CS behavior. No firmware binary may be marked hardware-ready until these are checked.

## Milestone R1: radio bring-up
Implement independent SPI bus transactions and register-read self tests with timeouts, retries, and structured error codes. CC1101: read PARTNUM/VERSION and validate response. nRF24: read CONFIG/RF_CH/SETUP_AW and validate writable register readback with restoration. Handle absent modules gracefully.

## Milestone R2: controlled lab TX/RX
Implement selectable channel, packet payloads, receive counters, RSSI where supported, packet loss and latency measurement using paired owned test devices or a shielded conducted RF path. No indiscriminate interference transmitter.

## Milestone R3: user interface and diagnostics
Radio menu: CC1101, nRF24, hardware status, diagnostics, saved test logs. Keep other menu categories visible and label hardware-dependent status honestly. Store CSV/JSON logs to microSD with firmware revision, radio model, pin profile, test settings, and outcomes.

## Milestone R4: future extensions
NFC, LF RFID, infrared, iButton, SDR, and protocol testing remain in roadmap; implement each behind a separate driver capability flag with explicit validation. Preserve upstream license and attribution.

## Acceptance criteria
- Boot and existing menus function on the selected display profile.
- Both radios detected reliably over repeated cold boots.
- Register tests produce distinct missing-device, SPI error, and success results.
- Paired packet test works in isolated bench setup and logs real measurements.
- Build artifacts include the exact pin profile, git SHA, and test status; CI compile success must not be presented as physical validation.
