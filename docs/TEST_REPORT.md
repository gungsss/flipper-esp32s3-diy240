# Status build ST7735S landscape — 20 November 2026

Profil yang dibangun adalah ESP32-S3 N16R8, ST7735S 160×128 landscape,
microSD SPI3, dan enam tombol. Perubahan Flipper 1.5.1 merupakan backport
terpilih ke port ESP32; hasilnya bukan firmware resmi Flipper Zero dan tidak
memiliki kesetaraan penuh pada source, runtime, atau perangkat keras.

| Pemeriksaan | Status |
|---|---|
| Generator board dari pinout inti | Berhasil menghasilkan konfigurasi ST7735S landscape 160×128, CS layar ke GND, SPI 5 MHz, SD SPI3, dan tombol. |
| Profil inti | Berhasil dikompilasi pada GitHub Actions run [#44682314089](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/44682314089). Fitur modul tambahan tidak diaktifkan. |
| Profil modul opsional | Berhasil dikompilasi pada run yang sama: CC1101 Sub-GHz, nRF24L01+, PN532 NFC, Infrared, dan RDM6300 LF RFID hanya-baca. |
| Packaging dan metadata | Berhasil; kedua paket mencatat board, layar ST7735S landscape, versi sumber, pinout, offset, ukuran, dan SHA-256 image. |
| Halaman flasher preview | Berhasil dipublikasikan ke deployment Vercel preview dari commit `45ca46e061e4b3e21f57fcd4b9ce792a8576b1da`. |
| Flash dan uji layar, tombol, SD, serta modul pada perangkat fisik | Belum diverifikasi. |

Paket tersedia melalui tombol **Flash profil inti** dan **Flash profil modul** di
[halaman flasher ST7735S landscape](https://flipper-diy240-flasher-e3z2y8spr-agungs79u-8246s-projects.vercel.app/flipper-st7735-151/).
Artifact build CI juga dapat diunduh dari [run #44682314089](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/44682314089).

## Catatan konfigurasi modul

Pin profil contoh modul harus dicocokkan dengan PCB dan kabel aktual sebelum
modul dipasang. Modul tidak terdeteksi otomatis; firmware harus dibangun dan
di-flash ulang dengan pinout yang sesuai. RDM6300 menyediakan pembacaan LF RFID
saja. iButton belum tersedia pada HAL ESP32 ini.

## Batas validasi

- Kompilasi CI memastikan kedua varian berhasil dibangun, tetapi tidak
  membuktikan layar, pin, tombol, SD, atau modul bekerja secara fisik.
- Firmware ini memuat perubahan Flipper 1.5.1 yang dipilih dan diadaptasi untuk
  port ESP32; bukan seluruh firmware resmi Flipper 1.5.1.
- Build historis ST7789 dan build landscape lama tidak digunakan sebagai paket
  pada halaman flasher baru.
