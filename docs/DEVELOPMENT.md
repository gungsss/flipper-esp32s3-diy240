# Pengembangan dan sumber

Repositori integrasi ini mengambil source Sor3nt pada commit tetap
`e6ec11972a8e025d7ab686a6ef3016cf52360834`, menerapkan backport pilihan dari
Flipper 1.5.1, lalu mengubah profil board ke ESP32-S3 ST7735S 160×128 landscape.
Jangan mengganti pin upstream tanpa meninjau ulang driver display, SD, dan modul.

## File utama

- `patch/flipper_1_5_1_port.patch`: perubahan software yang dipilih dari versi 1.5.1.
- `patch/patch_flipper.py`: adaptasi umum board DIY dan microSD SPI3.
- `patch/Pinout_ESP32S3_ST7735S_160.txt`: wiring inti layar, SD, dan tombol.
- `patch/Pinout_ESP32S3_ST7735S_160_all_modules.example.txt`: kandidat pin untuk menu semua modul opsional; cocokkan dengan PCB sebelum wiring.
- `variants/st7735/patch_st7735.py`: ST7735S, pemilihan pinout, kemampuan modul, dan filter menu.
- `variants/st7735/patch_landscape.py`: geometri 160×128 landscape.
- `scripts/build_local.sh`: alur build lengkap dengan profil ST7735S landscape.
- `scripts/package_artifacts.py`: validasi dan packaging image hasil build.

## Build lokal

Pasang ESP-IDF v5.4.1, lalu jalankan:

```bash
./scripts/build_local.sh
```

Alur ini mengunduh source terpin, menerapkan patch 1.5.1, mengatur profil
ST7735S landscape, menghasilkan `board_DIY.h` dari pinout, lalu mengompilasi
firmware tanpa flash.

Untuk profil modul, siapkan salinan pinout dengan field opsional yang sesuai
wiring nyata, lalu jalankan `ST7735_PINOUT=/path/to/Pinout.txt
./scripts/build_local.sh`. Jangan memakai ulang konfigurasi dari modul atau
board lain tanpa memeriksa GPIO dan tegangan.

## Mengganti source upstream

Buat branch terpisah, tinjau changelog serta perubahan generator, driver layar,
SD, FAM, dan ABI. Perbarui SHA sumber dan dokumentasi bersama-sama. Lakukan
build bersih dan uji fisik ulang pada layar, tombol, microSD, Wi-Fi/BLE, serta
modul yang dipasang. Image hanya boleh dipublikasikan setelah build dan metadata
flash diverifikasi.

Source upstream dan dependensinya mengikuti hak cipta dan lisensi masing-masing.
Repositori ini tidak mengklaim kepemilikan source tersebut.
