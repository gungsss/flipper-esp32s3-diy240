# Troubleshooting ST7735S landscape

Cabut USB sebelum mengganti kabel. Cocokkan gejala dengan wiring di
[HARDWARE.md](HARDWARE.md); jangan mencoba profil ST7789 pada panel ST7735S.

## Layar gelap tetapi ada log serial

- Pastikan VCC ke 3V3, ground bersama, backlight, SCK=GPIO12, MOSI=GPIO11, DC=GPIO15, dan RST=GPIO16.
- CS panel harus terikat ke GND sesuai profil. Jangan sambungkan CS ke GPIO10.
- Periksa log `FuriHalDisplay` dan `esp_lcd`. Jika panel tidak merespons saat init, matikan daya sepenuhnya sebelum menyalakan kembali.
- Pastikan firmware yang dipasang dibangun untuk ST7735S 160×128 landscape dan frekuensi LCD 5 MHz.

## Ada backlight tetapi tidak ada gambar atau warnanya salah

- Verifikasi kabel SPI dan urutan pin modul. Pin SDA pada layar berfungsi sebagai MOSI, bukan I²C.
- Jangan mengubah resolusi atau driver ke ST7789. Profil ini menggunakan driver `waveshare/esp_lcd_st7735`.
- Periksa apakah modul butuh penyesuaian backlight atau orientasi. `patch_landscape.py` menetapkan geometri 160×128, axis swap, dan orientasi panel.
- Jangan ubah mirror, inversion, atau gap secara acak; ubah profil sumber dan bangun ulang agar metadata cocok.

## microSD tidak terdeteksi

- Cek keenam kabel: MISO38, CLK40, MOSI39, CS14, 3V3, dan GND.
- Pastikan kartu FAT32, bukan exFAT; gunakan kabel pendek dan sambungan ground yang kuat.
- SD memakai SPI3 terpisah. Jangan pindahkan SD ke jalur LCD SPI2 atau bus radio opsional.
- Cek log `FuriHalSd` atau `sdmmc_card_init` sebelum menyimpulkan kartunya rusak.

## Tombol tidak terbaca atau arahnya salah

Verifikasi label: UP4, DOWN5, LEFT6, RIGHT17, OK8, BACK18. Tombol aktif-rendah:
saat ditekan pin harus terhubung ke COM/GND. Hindari GPIO0 saat wiring tombol agar
board tidak masuk ke mode download ketika boot.

## Fitur modul tidak muncul

Menu Sub-GHz dan nRF24 dibangun saat pin wajibnya terisi pada pinout. Profil uji
ini memakai CC1101 SCK/MOSI/MISO/CSN/GDO0 = GPIO9/10/21/43/13 dan nRF24
SCK/MOSI/MISO/CSN/CE = GPIO41/42/47/1/2. Dua radio memakai bus SPI terpisah;
microSD tetap pada SPI3. Pindahkan CC1101 CSN dari GPIO46 ke pad TX/GPIO43 sebelum
menyalakan firmware ini. PN532, IR, dan LF RFID tidak diaktifkan di profil ini.

## Board tidak terdeteksi saat flash

- Gunakan kabel USB data dan coba port board yang berbeda.
- Di Windows cek Device Manager → Ports (COM & LPT). Tutup serial monitor atau IDE yang sedang memakai COM.
- Untuk mode download, gunakan tombol BOOT bawaan board saat reset; jangan gunakan GPIO layar sebagai pengganti BOOT.
- Jika memakai image hasil build lokal, pastikan semua image, offset, dan `BUILD_INFO.json` berasal dari paket yang sama.

## Build gagal

- Gunakan ESP-IDF v5.4.1 dan `ESP_IDF_EXPORT_SCRIPT` yang benar.
- Berikan log error pertama, bukan hanya baris terakhir. Jangan memaksa patch ke source selain commit upstream yang dipatok.
- Jika file build lama tertinggal setelah perubahan pinout, jalankan build dengan opsi `--clean`.
