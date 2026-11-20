# Flipper ESP32-S3 · ST7735S Landscape

Port eksperimen untuk ESP32-S3 N16R8 dengan layar **ST7735S 160×128 landscape**.
Semua build di proyek ini memakai pinout ST7735S sebagai target utama. Source
menggabungkan port Sor3nt dengan perubahan yang dipilih dari firmware resmi
Flipper 1.5.1; ini bukan binary resmi Flipper Zero dan belum setara penuh dengan
seluruh software, hardware, dan aksesori Flipper asli.

## Status saat ini

Source dan generator board ST7735S landscape sudah disiapkan. **Image firmware
baru belum berhasil dibangun atau dipublikasikan**, jadi belum ada ZIP dari
perubahan ini yang boleh dianggap siap flash. ESP-IDF 5.4.1 diperlukan untuk
build; pengujian fisik tetap diperlukan setelah image tersedia.

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

Profil dasar menonaktifkan perangkat eksternal. Generator akan memasukkan menu
dan driver yang tersedia hanya bila pin modul diisi lengkap pada file pinout.
CC1101 dan nRF24 menggunakan bus radio khusus agar tidak berbagi SPI dengan LCD
yang CS-nya terikat ke GND atau microSD. Port saat ini memiliki dukungan PN532
NFC, IR RMT, serta RDM6300 LF RFID read-only; iButton belum tersedia karena
upstream belum memiliki HAL iButton untuk ESP32. Contoh profil yang menyiapkan
semua menu modul tersedia di
`patch/Pinout_ESP32S3_ST7735S_160_all_modules.example.txt`. Profil contoh itu
belum divalidasi pada board fisik. Modul tidak aktif hanya dengan dicolokkan:
pilih pinout yang cocok, build ulang, lalu flash image hasil build. Rincian di
[variants/st7735/README.md](variants/st7735/README.md).

## Build

Perlu ESP-IDF v5.4.1. Dari folder proyek jalankan:

```bash
./scripts/build_local.sh
```

Secara default build memakai
`patch/Pinout_ESP32S3_ST7735S_160.txt`. Untuk pinout modul yang sudah dicocokkan
dengan wiring nyata:

```bash
ST7735_PINOUT=/path/to/Pinout.txt ./scripts/build_local.sh
```

Hasil build harus melewati validasi dan packaging sebelum dipakai untuk flash.
Panduan build Windows/WSL2 ada di [docs/BUILD_WINDOWS_WSL.md](docs/BUILD_WINDOWS_WSL.md).

## Batasan penting

- ESP32-S3 berbeda dari Flipper Zero asli; aplikasi FAP ARM tidak otomatis kompatibel.
- Firmware Flipper memakai framebuffer 128×64 yang diskalakan pada panel 160×128. Sebagian layar aplikasi belum didesain ulang secara native untuk resolusi panel.
- Fitur Sub-GHz, nRF24, NFC, IR, dan LF RFID memerlukan modul fisik dan pinout yang sesuai.
- Ada lebih banyak sinyal modul daripada GPIO bebas yang aman untuk selalu memasang semua perangkat bersamaan. Profil perlu disesuaikan dengan rangkaian sebenarnya.
- Keberhasilan kompilasi tidak menggantikan uji tampilan, tombol, microSD, Wi-Fi/BLE, dan modul pada board fisik.

## Struktur

- `patch/`: backport 1.5.1, pinout dasar, dan patch board umum.
- `variants/st7735/`: driver layar ST7735S, orientasi landscape, pemilihan fitur modul.
- `scripts/`: fetch source, build, flash lokal, dan packaging.
- `docs/`: wiring, instalasi, build, flashing, batasan, dan troubleshooting.
