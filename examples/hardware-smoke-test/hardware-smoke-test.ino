/*
 * ESP32-S3 N16R8 DIY240 hardware smoke test.
 * TFT ST7789 240x240 no CS on SPI2/FSPI.
 * microSD on SPI3/HSPI, 6 active-low keypad inputs.
 * Not the full Flipper firmware. Does not touch Wi-Fi or radio.
 *
 * Libraries: Adafruit GFX Library + Adafruit ST7735 and ST7789 Library
 * Target: ESP32S3 Dev Module, 16MB flash, OPI PSRAM (check actual board).
 */
#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>

static constexpr int TFT_CLK = 12;
static constexpr int TFT_MOSI = 11;
static constexpr int TFT_DC = 15;
static constexpr int TFT_RST = 16;
static constexpr int SD_CLK = 40;
static constexpr int SD_MOSI = 39;
static constexpr int SD_MISO = 38;
static constexpr int SD_CS = 14;

// ESP32-S3: FSPI=SPI2, HSPI=SPI3 under Arduino-ESP32.
SPIClass displayBus(FSPI);
SPIClass sdBus(HSPI);
Adafruit_ST7789 display(&displayBus, -1, TFT_DC, TFT_RST);

static constexpr int BTN_COUNT = 6;
static const int keyPins[BTN_COUNT] = {4, 5, 6, 17, 8, 18};
static const char* keyNames[BTN_COUNT] = {"UP", "DOWN", "LEFT", "RIGHT", "OK", "BACK"};
static bool lastPressed[BTN_COUNT] = {false, false, false, false, false, false};
static bool sdAvailable = false;
static uint32_t lastUiMs = 0;

void drawStatus() {
  display.fillScreen(ST77XX_BLACK);
  display.setTextWrap(false);
  display.setTextSize(2);
  display.setCursor(8, 8);
  display.setTextColor(ST77XX_CYAN);
  display.println("DIY240 TEST");
  display.setTextSize(1);
  display.setTextColor(ST77XX_WHITE);
  display.setCursor(8, 38);
  display.println("ESP32-S3 | ST7789 240");
  display.setCursor(8, 56);
  display.print("MicroSD SPI3: ");
  display.setTextColor(sdAvailable ? ST77XX_GREEN : ST77XX_RED);
  display.println(sdAvailable ? "OK" : "NOT FOUND");
  display.setTextColor(ST77XX_WHITE);
  display.setCursor(8, 80);
  display.println("Keypad (pressed = GREEN):");
  for (int i = 0; i < BTN_COUNT; ++i) {
    const int x = (i % 2) * 115 + 8;
    const int y = (i / 2) * 28 + 100;
    display.drawRect(x, y, 108, 22, ST77XX_WHITE);
    display.setTextColor(lastPressed[i] ? ST77XX_GREEN : ST77XX_YELLOW);
    display.setCursor(x + 6, y + 7);
    display.print(keyNames[i]);
  }
  display.setTextColor(ST77XX_WHITE);
  display.setCursor(8, 197);
  display.println("BLK needs proper power.");
  display.setCursor(8, 216);
  display.println("Serial Monitor: 115200");
}

void setup() {
  Serial.begin(115200);
  delay(800);
  Serial.println("\nESP32-S3 DIY240 hardware diagnostic");
  Serial.println("Target: ST7789 SPI2, microSD SPI3, 6 buttons");

  for (int i = 0; i < BTN_COUNT; ++i) {
    pinMode(keyPins[i], INPUT_PULLUP);
  }

  pinMode(SD_CS, OUTPUT);
  digitalWrite(SD_CS, HIGH);

  // The TFT has no chip-select; it must be the only device on its SPI bus.
  displayBus.begin(TFT_CLK, -1, TFT_MOSI, -1);
  display.init(240, 240);
  display.setRotation(0);
  display.invertDisplay(true);
  display.fillScreen(ST77XX_BLACK);
  Serial.println("ST7789 init commands sent. Visually verify pixels.");

  sdBus.begin(SD_CLK, SD_MISO, SD_MOSI, SD_CS);
  sdAvailable = SD.begin(SD_CS, sdBus, 4000000);
  if (sdAvailable) {
    const uint64_t bytes = SD.cardSize();
    Serial.printf("microSD detected, size: %llu MB\n",
                  static_cast<unsigned long long>(bytes / 1048576ULL));
  } else {
    Serial.println("microSD not mounted: check 3V3/GND/CS14/MISO38/MOSI39/CLK40 and FAT32");
  }
  for (int i = 0; i < BTN_COUNT; ++i) lastPressed[i] = digitalRead(keyPins[i]) == LOW;
  drawStatus();
}

void loop() {
  bool changed = false;
  for (int i = 0; i < BTN_COUNT; ++i) {
    const bool nowPressed = (digitalRead(keyPins[i]) == LOW);
    if (nowPressed != lastPressed[i]) {
      lastPressed[i] = nowPressed;
      changed = true;
      Serial.printf("%s: %s\n", keyNames[i], nowPressed ? "PRESSED" : "RELEASED");
    }
  }
  // Throttle display updates so GPIO chatter does not flood the SPI bus.
  if (changed && millis() - lastUiMs >= 40) {
    drawStatus();
    lastUiMs = millis();
  }
  delay(15);
}
