# Pengembangan, sumber, dan pengujian

## Model repositori

Repositori ini berisi **patch + konfigurasi + dokumentasi + workflow**, dan mengambil source lengkap Sor3nt pada waktu build. Alasan: memudahkan tracking upstream dan menghindari menggandakan banyak file FAP, gambar, serta library pihak ketiga yang belum diperiksa lisensinya satu per satu.

Upstream dipin ke commit `e6ec11972a8e025d7ab686a6ef3016cf52360834` untuk menjaga reproduktibilitas. Jangan mengganti pin ke `main` tanpa audit ulang patch, generator, build dependencies dan fitur yang relevan.

## Struktur penting

- `patch/patch_flipper.py`: patch berbasis string anchor, idempotent, validasi commit, stop bila source berubah.
- `patch/Pinout_ESP32S3_ST7789_240.txt`: profil GPIO khusus target.
- `scripts/fetch_upstream.sh`: fetch commit terpin ke `.work/upstream`.
- `scripts/build_local.sh`: menjalankan patch lalu build dengan ESP-IDF v5.4.1.
- `scripts/flash_local.sh`: flash via `build_diy.sh` setelah konfirmasi.
- `scripts/package_artifacts.py`: cek output build dan offset sebelum packaging.
- `.github/workflows/build.yml`: build otomatis Ubuntu + ESP-IDF v5.4.1.

## Penyesuaian target

`tools/gen_diy_board.py` upstream menghasilkan `board_DIY.h` dari `Pinout.txt`. Patch mengubah generator agar menerima SD SPI3 dan layar 240×240 no-CS, sehingga edit langsung di header tergenerasi **tidak permanen**. `fam_config.py` menonaktifkan aplikasi untuk modul yang belum tersedia.

## Memulai dari checkout bersih

```bash
rm -rf .work/upstream
./scripts/build_local.sh
```

**Hati-hati:** perintah di atas menghapus **hanya** checkout upstream `.work/upstream` yang dibuat oleh script; jangan gunakan jika kamu menyimpan perubahan manual penting di sana. Patch juga membuat backup sebelum perubahan di `.work/upstream/.flipper-diy240-backups`.

## Test lokal

```bash
python3 -m unittest discover -s tests -v
```

Unit tests memeriksa sejumlah invariant patch dan aturan validasi packaging. Mereka bukan pengganti build ESP-IDF atau hardware-in-the-loop. CI menjalankan unittest sebelum build.

## Mengubah pinout

Profil pin ada di `patch/Pinout_ESP32S3_ST7789_240.txt`. Untuk mengubah pin, edit profil lalu hapus `.work/upstream` untuk membangun ulang dari clean checkout. Generator upstream menolak pin duplikat dan GPIO flash/PSRAM/USB yang dilindungi; jangan menonaktifkan validator untuk mengakali konflik hardware.

## Memperbarui versi upstream

1. Buat branch terpisah.
2. Tinjau changelog dan perubahan di file generator, display, SD, build, FAM.
3. Ganti SHA di `patch/patch_flipper.py`, `scripts/fetch_upstream.sh` dan metadata artifact **secara konsisten**; perbarui dokumentasi.
4. Jalankan unittest, lalu CI full firmware. Catat pinout, offset, dan tingkat keberhasilan sebelum melakukan flash.
5. Lakukan pengujian fisik ulang, terutama bus SD, layar tanpa CS, Wi-Fi/BLE, dan penggunaan internal PSRAM.

## Pengujian perangkat fisik

Tiap hasil harus disertai:

- Foto board, TFT dan keypad sesuai wiring aktual.
- Log boot awal sampai menu tampil dan hasil percobaan SD.
- Status monitor 30–60 detik, bukan hanya screenshot UI.
- SHA commit upstream dan commit integrasi.
- Cek 6 tombol, mount dan menulis file SD, Wi-Fi/BLE bergantian.
- Catatan bila display memiliki `GAP_Y` selain 0 atau inversion berbeda.

## Lisensi dan atribusi

Sor3nt adalah pemilik/maintainer upstream yang disebut di dokumentasi proyek. Repo ini tidak mengklaim hak atas source upstream atau perangkat lunak pihak ketiga yang terkandung di dalamnya. Jangan menghapus atribusi; periksa lisensi/kepemilikan komponen sebelum mendistribusikan hasil build.
