# Cakupan fitur dan tingkat kesiapan

Dokumen ini **tidak menyatakan hasil uji fisik**. Tiga status berbeda dipakai:

- **Termasuk dalam source/build candidate**: ada implementasi dan dipertahankan oleh konfigurasi aplikasi.
- **Tidak tersedia tanpa modul**: membutuhkan rangkaian tambahan, sengaja dimatikan pada profil awal.
- **Perlu uji hardware**: keberhasilan kompilasi saja tidak membuktikan pengalaman perangkat di lapangan.

| Area | Kondisi saat ini | Catatan |
|---|---|---|
| UI dan navigasi | Termasuk, perlu uji | Flipper framebuffer 128×64 diskalakan ke panel 240×240 |
| microSD / Archive | Termasuk, perlu uji | SPI3 terpisah, FAT32, berkas SD mengikuti upstream |
| Wi-Fi scan dan koneksi | Termasuk, perlu uji | Gunakan pada jaringan sendiri/berizin |
| Bluetooth BLE | Termasuk, perlu uji | Dapat saling eksklusif dengan Wi-Fi |
| USB HID / BadUSB | Termasuk upstream, perlu uji | USB native ESP32-S3, hanya untuk sistem sendiri/berizin |
| U2F | Bergantung dukungan build | Memerlukan uji USB, attestation, relying party; jangan jadikan kredensial utama sebelum tervalidasi |
| JavaScript runtime | Sebagian modul upstream | Modul serial/gpio/i2c/spi tidak otomatis tersedia |
| Game / media native | Tidak dijamin | Sejumlah aplikasi diasumsikan panel 320×170 dan speaker |
| Sub-GHz CC1101 | **Nonaktif** | Modul CC1101 belum terpasang |
| 2,4 GHz nRF24 | **Nonaktif** | Modul nRF24L01 belum terpasang |
| NFC PN532 | **Nonaktif** | Tidak ada reader NFC |
| Infrared | **Nonaktif** | Tidak ada pemancar/penerima IR |
| LF RFID | **Nonaktif** | Tidak ada hardware 125 kHz |
| OTA firmware lewat Wi-Fi | **Tidak direkomendasikan** | Mekanisme upstream perlu perbaikan verifikasi TLS dan autentisitas image |
| Firmware flash via USB | Jalur yang direkomendasikan | ESP-IDF local atau esptool dari artifact CI sukses |

## Apa yang perlu pengembangan lanjutan?

Fokus masuk akal adalah **stabilitas hardware dasar** (boot/UI/tombol/SD), lalu ketahanan Wi-Fi/BLE dan kompatibilitas aplikasi. Menambahkan radio eksternal mengubah kebutuhan bus/pin, dan perlu desain baru karena TFT tanpa CS harus tetap menjadi satu-satunya perangkat pada SPI2. Tidak cukup sekadar mengubah flag `BOARD_HAS_SUBGHZ` menjadi 1.

## Definisi selesai (Milestone M1)

1. Workflow CI sukses menghasilkan tiga `.bin` dan `flash_project_args`.
2. ESP32-S3 N16R8 menjalankan firmware tanpa boot loop selama pengujian awal.
3. Tampilan ST7789 terbaca baik, termasuk rotasi, warna, dan margin yang sesuai.
4. Keenam tombol berfungsi konsisten tanpa memicu boot mode.
5. microSD FAT32 bisa mount, browse, dan menyimpan file secara persisten.
6. Wi-Fi scan jaringan sendiri dan BLE pairing secara bergantian dapat digunakan.
7. Hasil uji dicatat bersama commit, foto dan log.

**Status M1 saat dokumentasi ini dibuat: belum diverifikasi secara fisik.**
