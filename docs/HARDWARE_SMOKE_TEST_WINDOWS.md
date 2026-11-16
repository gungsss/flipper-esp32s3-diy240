# Uji hardware pertama di Windows (Arduino IDE)

Ini **bukan Flipper-Zero-ESP32-Port**. Sketch diagnostik ini adalah firmware sementara untuk menguji sambungan **ST7789 240×240 tanpa CS**, **microSD pada SPI3**, dan **enam tombol**. Sketch bisa dicoba tanpa GitHub Actions atau toolchain Flipper.

> **Belum dikompilasi atau diuji pada board nyata oleh penyusun proyek.** Verifikasi bahwa label dan wiring modul sesuai [HARDWARE.md](HARDWARE.md) sebelum menyambungkan USB. Simpan backup firmware sebelumnya jika diperlukan.

## 1. Instal software

1. Instal [Arduino IDE 2](https://www.arduino.cc/en/software) pada Windows.
2. Buka **File → Preferences** dan tambahkan URL Boards Manager resmi ESP32: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`.
3. Buka **Boards Manager** → cari `esp32` → instal **esp32 by Espressif Systems**. Pilih **ESP32S3 Dev Module**.
4. Melalui **Library Manager**, pasang **Adafruit GFX Library** dan **Adafruit ST7735 and ST7789 Library**. Instal dependensi yang diminta IDE.

## 2. Pengaturan ESP32-S3

- Board: **ESP32S3 Dev Module**.
- Flash Size: **16 MB** sesuai modul N16R8.
- PSRAM: gunakan **OPI PSRAM** jika tersedia dan sesuai modul. Sketch diagnostik sendiri tidak membutuhkan PSRAM, tetapi build Flipper akan membutuhkannya.
- Port: pilih COM port ESP32-S3 yang muncul pada **Tools → Port**.
- USB CDC / upload mode: pengaturan berbeda antar board; ikuti hasil deteksi dua USB-C. Jangan mengubah GPIO USB19/20.

## 3. Buka dan upload sketch

Buka `examples/hardware-smoke-test/hardware-smoke-test.ino` dari repo ini. Periksa kabel berikut:

| Modul | Jalur GPIO |
|---|---|
| TFT ST7789 | SCL12, SDA11, DC15, RES16; VCC3V3 dan GND; BLK sesuai rangkaian modul |
| microSD | CLK40, MOSI39, MISO38, CS14, 3V3, GND |
| 6 tombol | UP4, DWN5, LET6, RHT17, MID8, SET18, COM ke GND |

Tekan **Verify** lalu **Upload**. Jika gagal masuk mode download: tahan tombol BOOT bawaan ESP32-S3, tekan-lepas RST, lalu lepas BOOT ketika proses upload dimulai. Pastikan kabel data USB benar.

## 4. Hasil yang diharapkan

- TFT menampilkan judul `DIY240 TEST` dan enam tombol.
- Status microSD `OK` jika kartu terdeteksi, atau `NOT FOUND` bila gagal mount.
- Ketika tombol ditekan, kotak berubah hijau dan Serial Monitor 115200 baud mencatat nama tombol.
- Serial Monitor menampilkan ukuran kartu SD jika berhasil.

Jika gambar bergeser/warna aneh, panel mungkin butuh penyesuaian `setRotation` / inversion / gap. Jika TFT gelap, periksa **BLK**; belum tentu firmware salah.

**Peringatan:** Upload sketch ini akan mengganti aplikasi pada flash ESP32-S3, termasuk Flipper jika sudah ada. Tidak melakukan `erase_flash` total, tetapi jangan gunakan jika perangkat menyimpan data penting tanpa backup.

Jika sketch ini lulus, barulah lanjut uji **firmware Flipper lengkap** dari [BUILD_WINDOWS_WSL.md](BUILD_WINDOWS_WSL.md) atau artifact CI sukses. Hasil smoke test **tidak membuktikan firmware Flipper telah dibangun/berjalan**.
