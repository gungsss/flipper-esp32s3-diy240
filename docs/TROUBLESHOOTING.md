# Troubleshooting: dari kabel sampai firmware

Pemeriksaan dibagi menurut gejala agar tidak langsung menyimpulkan firmware rusak. **Selalu cabut USB sebelum mengubah kabel.**

## Layar hitam tetapi ESP32 mengeluarkan log serial

1. Pastikan VCC TFT ke 3V3, GND bersama, dan jalur SPI2: SCL=12, SDA=11, RES=16, DC=15.
2. Periksa **BLK**: bisa jadi backlight belum mendapat daya. Jangan memberi arus besar dari GPIO langsung.
3. Pastikan modul benar-benar **ST7789 240×240 SPI 7-pin**, bukan ST7735 atau modul 8 pin.
4. Periksa serial log untuk `FuriHalDisplay`, `esp_lcd`, serta `ESP_ERROR_CHECK`.
5. Jika driver reset panel terlalu cepat, coba daya mati penuh dan tunggu; jangan mengganti semua pin secara acak.

## Backlight menyala, tetapi gambar kosong/putih

- Tukar **bukan** kabel secara sembarangan: `SCL` pada TFT adalah clock (GPIO12), `SDA` adalah MOSI (GPIO11); bukan I²C.
- Periksa `DC` dan `RES` tidak tertukar.
- TFT **tanpa CS** pada SPI2; jangan menghubungkan pin clock/MOSI TFT ke SPI3 microSD.
- Baca log serial: error `esp_lcd_new_panel_io_spi`, `esp_lcd_panel_init`, atau panic adalah petunjuk spesifik.
- Bila display hanya blank di bagian tertentu, lihat pembahasan offset berikut.

## Gambar bergeser/terpotong

ST7789 240×240 memiliki beberapa varian dengan offset panel berbeda. Konfigurasi awal patch ini `BOARD_LCD_GAP_X=0`, `BOARD_LCD_GAP_Y=0`, rotasi awal `BOARD_LCD_SWAP_XY=false`, mirror X/Y false. Jika secara fisik gambar meleset, uji `GAP_Y=80` **hanya bila gejalanya sesuai panel**.

**Penting:** `board_DIY.h` digenerate otomatis. Koreksi permanen dilakukan di fungsi `patch_generator()` pada `patch/patch_flipper.py`, bukan hanya mengedit `board_DIY.h` yang akan ditimpa saat build. Untuk versi pertama, identifikasi gejalanya dulu sebelum memodifikasi.

## Warna bertukar merah/biru atau inverted

Panel ST7789 berbeda varian RGB/BGR dan inversion. Pada `patch/patch_flipper.py`, penyesuaian awal mempertahankan `BOARD_LCD_COLOR_ORDER_BGR=false` dan `BOARD_LCD_INVERT_COLOR=true` dari upstream. Uji perubahan satu parameter pada satu waktu dan lakukan full power cycle. Catat hasil tiap percobaan.

## microSD tidak terdeteksi

- Cek semua enam kabel, **termasuk CS dan daya**: MISO38, MOSI39, SCK40, CS14, 3V3, GND.
- Pastikan modul yang diberi label **3V3** mendapat **3,3 V**, bukan 5 V.
- Format kartu ke **FAT32**, bukan exFAT; salin isi folder `sdcard.zip` ke akar kartu.
- Gunakan kabel pendek dan kontak microSD yang bersih. Jika Wi-Fi mulai membuat sistem reset, curigai suplai daya/brownout.
- Default clock SPI3 adalah **10 MHz**. Jika stabilitas buruk, turunkan `BOARD_SD_SPI_FREQ_KHZ` di template `patch/patch_flipper.py` dari `10000` menjadi `4000`, buat ulang checkout bersih, patch dan build ulang.
- Baca log `FuriHalSd` dan error `sdmmc_card_init`; jangan menyalahkan microSD hanya karena menu Archive kosong.

## Tombol tidak bekerja atau salah arah

- Periksa PCB `COM` benar-benar ground dan menjadi common semua tombol. Uji kontinuitas tiap tombol saat ditekan.
- Label `LET` berarti left, `RHT` right; `MID` OK; `SET` Back.
- Pin wiring: UP4, DWN5, LET6, RHT17, MID8, SET18.
- Tombol aktif-rendah: *ditekan = GND*; tidak ada 3V3 ke kabel keypad.
- Jika perangkat selalu memasuki download mode, pastikan tidak ada keypad yang menghubungkan **GPIO0** ke GND pada saat reset.

## Windows tidak mendeteksi port COM

1. Buka **Device Manager → Ports (COM & LPT)** sebelum dan sesudah mencolok ESP32-S3; cari COM port baru.
2. Gunakan kabel USB-C **data** dan coba kedua port USB-C di board, satu per satu.
3. Jika USB-UART bridge pada board membutuhkan driver, identifikasi chip-nya dahulu. Driver CP210x dan CH34x berbeda; jangan memasang driver acak.
4. Jika COM port terlihat tetapi terkunci, tutup Serial Monitor, Arduino IDE, atau aplikasi serial lain.
5. Untuk download mode, tahan BOOT bawaan board, tekan-lepas RST, lalu lepaskan BOOT. Jalankan ulang script flash.
6. Untuk masalah Python, uji `py -3 --version` dan `py -3 -m esptool version` di PowerShell.

## Mac tidak mendeteksi port serial

```bash
ls /dev/cu.usb*
system_profiler SPUSBDataType | head -70
```

Gunakan kabel data USB-C. Board memiliki dua USB-C; coba satu per satu tanpa mengubah wiring saat hidup. Pada beberapa board native USB-Serial/JTAG bisa dipakai untuk flash, sementara port lain menggunakan USB-UART. Bila perlu tahan BOOT bawaan saat reset untuk masuk download mode, lalu ulang flash. `PORT` harus sesuai perangkat yang terdeteksi.

## Error instalasi / build

- Pastikan `idf.py --version` menunjukkan ESP-IDF 5.4.1 dalam environment terpisah.
- `ESP_IDF_EXPORT_SCRIPT` harus menunjuk ke path export.sh yang benar.
- Jika `git fetch` gagal, coba pastikan internet dan GitHub dapat diakses. Script **memverifikasi commit yang dipin**, tidak diam-diam pindah ke `main` terbaru.
- Jika `patch_flipper.py` menolak commit, checkout upstream harus kembali ke commit yang dipin. Jangan memaksakan patch ke versi lain.
- Jika script mengeluh pin duplikat/reserved, jangan bypass validator. Ubah susunan kabel dan dokumentasi bersama.
- Jika compile gagal, simpan **baris error pertama** dan sekitar 30 baris log sekitarnya; baris terakhir sering hanya ringkasan Ninja/CMake.
- Jika firmware `furi_esp32.bin` tidak ada, build **belum berhasil**, jadi jangan membuat klaim atau mencoba flash file acak.

## Boot loop / brownout / panic

1. Putuskan USB, cek apakah ada korsleting pada TFT/SD/keypad.
2. Coba boot dengan modul periferal yang tidak wajib dilepas secara aman (jangan cabut saat hidup) untuk isolasi.
3. Periksa log `Guru Meditation`, `abort`, `Brownout detector`, heap allocation, atau WDT.
4. Jangan menonaktifkan brownout detector untuk menutupi catu daya tidak stabil.
5. Jika image tertukar dari hardware lain, ulangi flash menggunakan **satu bundel build yang sama**.

## Wi-Fi bisa, BLE tidak (atau sebaliknya)

Pada upstream, Wi-Fi dan Bluetooth memiliki batasan koeksistensi; menu dapat mematikan salah satu stack saat stack lain aktif. Ini **belum tentu bug**. Pastikan fitur bergantian diuji, dan jangan menganggap keduanya simultan.

## Aplikasi `.fap` gagal dibuka

FAP Flipper Zero original ditargetkan untuk ARM dan bukan otomatis kompatibel dengan ESP32-S3. Bahkan FAP khusus port ESP32 harus sesuai ABI/source firmware dan periferalnya. Jangan menyalin aplikasi acak tanpa mengetahui sumber dan versi.

## Data penting untuk melaporkan bug

Sertakan: model board, jenis TFT 7-pin dan resolusi, foto konektor/pin, foto tampilan, tabel wiring aktual, jumlah dan filesystem SD card, SHA commit upstream, output `idf.py --version`, serta log serial lengkap sekitar awal error. Hilangkan password dan data pribadi dari log sebelum diunggah.
