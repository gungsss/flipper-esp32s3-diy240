# Status build ST7735S landscape — 20 November 2026

Target build adalah ESP32-S3 N16R8, ST7735S 160×128 landscape, microSD SPI3,
dan enam tombol. Perubahan Flipper 1.5.1 merupakan backport terpilih ke port
ESP32, bukan firmware resmi Flipper Zero atau kesetaraan penuh seluruh fitur.

| Pemeriksaan | Status |
|---|---|
| Geometri panel dan orientasi | 160×128 landscape; ST7735S CS ke GND, SPI 5 MHz, SD di SPI3. |
| Renderer layar penuh | Berhasil dibangun untuk profil inti dan modul pada GitHub Actions run [#44714718694](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/44714718694). Framebuffer Flipper 128×64 kini diskalakan memenuhi panel, tanpa bar atas/bawah. |
| Profil inti | Berhasil dikompilasi; modul opsional tidak diaktifkan. |
| Profil modul | Berhasil dikompilasi dengan CC1101 Sub-GHz, nRF24L01+, PN532 NFC, Infrared, dan RDM6300 LF RFID hanya-baca. |
| Packaging | Metadata mencatat ST7735S landscape, mode full-panel, pinout, offset image, ukuran, dan SHA-256. |
| Flash dan uji panel, tombol, SD, serta modul secara fisik | Belum diverifikasi. |

Paket tersedia di [halaman flasher ST7735S landscape](https://flipper-diy240-flasher-lob48s1c3-agungs79u-8246s-projects.vercel.app/flipper-st7735-151/).
Pilih **Flash profil inti** untuk wiring dasar atau **Flash profil modul** setelah
pinout modul dicocokkan dengan rangkaian fisik.

## Catatan tampilan dan modul

Rasio canvas asli 128×64 berbeda dari panel 160×128. Renderer mengisi seluruh
panel dengan skala horizontal dan vertikal berbeda, sehingga UI terlihat lebih
tinggi dibanding Flipper asli. Aplikasi tertentu yang menggambar langsung ke
layar mungkin memerlukan penyesuaian resolusi sendiri.

Pin profil modul contoh harus dicocokkan dengan PCB dan kabel aktual. Modul
eksternal perlu terpasang sesuai pinout; firmware harus dibangun dan di-flash
ulang setelah perubahan pin. RDM6300 hanya mendukung baca LF RFID. iButton belum
tersedia pada HAL ESP32 ini.

## Batas validasi

- Build CI memastikan kedua profil berhasil dikompilasi, tetapi tidak
  membuktikan tampilan dan modul bekerja pada perangkat fisik.
- Build historis ST7789 dan build landscape lama bukan paket pada halaman
  flasher ST7735S terbaru.
