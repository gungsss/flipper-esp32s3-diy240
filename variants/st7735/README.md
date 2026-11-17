# Flipper ESP32-S3 + ST7735S variant

This build targets ESP32-S3 N16R8 and the 8-pin ST7735S TFT used in the
successful color diagnostic. The LCD uses SPI2 with SCL=12, SDA=11, DC=15,
RST=16, CS physically tied to GND, and BLK left as used in the diagnostic.
It uses waveshare/esp_lcd_st7735 2.0.0 at 5 MHz. The UI uses a 128x64
framebuffer centered on the 128x160 display. SD remains on SPI3 with
SCK=40, MOSI=39, MISO=38, CS=14; buttons use the existing DIY pinout.

To reproduce, use ESP-IDF 5.4.1 and a fresh pinned upstream checkout:

```sh
bash scripts/fetch_upstream.sh
python3 patch/patch_flipper.py .work/upstream
python3 variants/st7735/patch_st7735.py .work/upstream
cd .work/upstream
./build_diy.sh --build-only
```

The dedicated web installer uses separate images and verified ESP-IDF flash
offsets. A successful build and color diagnostic do not verify that the full
Flipper firmware, SD card, or buttons work on any particular device.
