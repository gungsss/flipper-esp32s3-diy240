# M4145 Flipper 1.5.1 · ESP32-S3 ST7735S

Firmware port komunitas **by m4145** untuk ESP32-S3 N16R8 dengan layar **ST7735S
160×128 landscape**. Firmware memakai perubahan terpilih dari Flipper 1.5.1 dan
satu image uji radio untuk rangkaian yang dipakai saat ini. Source dasar
ESP32 dan lisensinya tetap dicatat terpisah; ini bukan binary resmi Flipper Zero
atau klaim kesetaraan penuh dengan perangkat asli.

## Status saat ini

Rilis ST7735S dibangun dari satu pinout dan satu profil uji melalui
`.github/workflows/build-st7735s-151-modules.yml`. CI memeriksa source UI,
menyusun modul CC1101 dan nRF24 untuk rangkaian saat ini, lalu menerbitkan satu manifest di
`web/public/flipper-st7735-151/`. Build dan packaging belum menggantikan uji
layar, tombol, microSD, dan modul pada board fisik.

## Hardware inti

| Bagian | Sambungan |
|---|---|
| ESP32-S3 | N16R8, flash 16 MB / PSRAM 8 MB |
| ST7735S | SCK GPIO12, MOSI GPIO11, DC GPIO15, RST GPIO16, CS ke GND, 5 MHz |
| microSD | SPI3: SCK GPIO40, MOSI GPIO39, MISO GPIO38, CS GPIO14, FAT32 |
| Tombol | UP 4, DOWN 5, LEFT 6, RIGHT 17, OK 8, BACK 18; active-low ke GND |

Wiring lengkap dan batasan tegangan ada di [docs/HARDWARE.md](docs/HARDWARE.md).
Gunakan kabel daya dicabut saat mengubah sambungan. Jangan menghubungkan modul
3,3 V ke pin 5 V.

## Modul opsional

Satu firmware menyertakan driver CC1101 Sub-GHz dan nRF24L01+ sesuai wiring
yang sudah dipasang. Pin layar, SD, dan tombol tetap sama; pin kedua radio ada di
`patch/Pinout_ESP32S3_ST7735S_160.txt`. Setelah modul disambungkan ke GPIO yang
tertera dan level 3,3 V, tidak perlu build atau flash ulang. Pin tambahan belum
diverifikasi pada setiap varian PCB, jadi cocokkan dengan board sebelum
memasang kabel. PN532, Infrared, dan LF RFID belum diaktifkan pada image ini.
Menu nRF24 hanya menyediakan survei kanal pasif. Aplikasi Wi-Fi deauth, raw-TX,
WPS PIN, dan Bluetooth spam tidak disertakan dalam build uji ini. Detail di
[variants/st7735/README.md](variants/st7735/README.md).

## Build

Perlu ESP-IDF v5.4.1. Dari folder proyek jalankan:

```bash
./scripts/build_local.sh
```

Secara default build memakai pinout wiring saat ini
`patch/Pinout_ESP32S3_ST7735S_160.txt`.

Hasil build harus melewati validasi dan packaging sebelum dipakai untuk flash.
Panduan build Windows/WSL2 ada di [docs/BUILD_WINDOWS_WSL.md](docs/BUILD_WINDOWS_WSL.md).

## Batasan penting

- ESP32-S3 berbeda dari Flipper Zero asli; aplikasi FAP ARM tidak otomatis kompatibel.
- Profil ST7735S memakai kanvas native 160×128, bukan membesarkan framebuffer 128×64. Layar beranda, daftar aplikasi, dan submenu umum memakai area penuh panel; aplikasi yang menggambar dengan koordinat lama tertentu mungkin masih perlu penyesuaian.
- CC1101 dan nRF24 memerlukan modul fisik dan kabel ke GPIO yang dicantumkan; sekadar menancapkan modul ke pin acak tidak cukup. nRF24 dibatasi ke survei pasif dalam image uji.
- iButton, LF RFID tulis/emulasi, speaker, dan sebagian fitur periferal Flipper belum memiliki padanan penuh pada port ini. Aplikasi FAP ARM juga perlu dipindahkan dan dibangun ulang untuk ESP32-S3.
- Keberhasilan kompilasi tidak menggantikan uji tampilan, tombol, microSD, Wi-Fi/BLE, dan modul pada board fisik.

## Struktur

- `patch/`: backport 1.5.1, pinout dasar, dan patch board umum.
- `variants/st7735/`: driver layar ST7735S, orientasi landscape, pemilihan fitur modul.
- `scripts/`: fetch source, build, flash lokal, dan packaging.
- `docs/`: wiring, instalasi, build, flashing, batasan, dan troubleshooting.
