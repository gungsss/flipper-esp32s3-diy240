# Build firmware melalui Windows + WSL2 (alternatif saat GitHub Actions terblokir)

Proyek ini mengutamakan **Windows**. Jika GitHub Actions tidak bisa menjalankan runner, kamu dapat **menghasilkan binary firmware di komputer Windows sendiri** melalui **WSL2 Ubuntu**, kemudian menggunakan **PowerShell Windows** untuk flashing.

> [!IMPORTANT]
> **Belum diuji end-to-end di komputer Windows maupun ESP32-S3 fisik.** Script ini menyediakan proses yang dapat dijalankan dan diperiksa, bukan jaminan kompilasi sukses. Jika ada error, kirim log **error pertama** dan konteksnya; jangan mengganti binary dari board lain.

## Syarat

- Windows 10 versi yang mendukung WSL2, atau Windows 11.
- Hak untuk memasang WSL Ubuntu dan paket build; koneksi internet stabil dan ruang disk cukup besar untuk ESP-IDF, upstream Sor3nt, cache, dan output firmware.
- Python dan `esptool` di Windows untuk flashing. USB ESP32-S3 tidak perlu diteruskan ke WSL karena **flashing dilakukan dari Windows**.

## 1. Instal Ubuntu di WSL2

Di PowerShell Windows yang berjalan sebagai administrator:

```powershell
wsl --install -d Ubuntu
```

Ikuti petunjuk Windows untuk reboot jika diminta; buka aplikasi **Ubuntu** dan buat akun Linux. Pastikan `wsl --list --verbose` menunjukkan WSL **versi 2**. Bila Ubuntu sudah ada, langkah pemasangan dapat dilewati.

## 2. Clone repositori di filesystem Linux WSL

**Jangan mengompilasi dari `/mnt/c/...`** bila bisa dihindari, karena performa akses file build akan menurun. Buka Terminal Ubuntu:

```bash
cd ~
git clone https://github.com/gungsss/flipper-esp32s3-diy240.git
cd flipper-esp32s3-diy240
```

Jika `git` belum ada:

```bash
sudo apt-get update
sudo apt-get install -y git
```

## 3. Bangun dan kemas firmware

Jalankan dari folder repositori di Ubuntu:

```bash
bash scripts/build_in_wsl.sh
```

Script melakukan lima tahap:

1. Instal dependensi build Linux.
2. Clone **ESP-IDF v5.4.1** ke folder **khusus** `~/esp-flipper/esp-idf` dan memvalidasi tag. Penting: upstream melakukan patch pada library Wi-Fi IDF.
3. Jalankan unit tests repositori.
4. Unduh Sor3nt pada commit tetap `e6ec11972a8e025d7ab686a6ef3016cf52360834`, terapkan patch dan jalankan build DIY.
5. **Hanya jika kompilasi sukses**, kemas `.bin`, cek offset dan checksum, lalu sediakan file `dist/firmware/`.

Tahap ini bisa mengunduh dependensi besar. Jika gagal, simpan error lengkap dari langkah yang pertama gagal. Jangan menganggap firmware siap flash ketika file output tidak ada atau script mengeluarkan error.

## 4. Buka hasil build dari Windows

Pada Terminal Ubuntu:

```bash
explorer.exe "$(wslpath -w "$PWD/dist/firmware")"
```

File Explorer Windows akan membuka folder yang berisi `BUILD_INFO.json`, `flash_windows.ps1`, dan image build. Salin **seluruh folder** ke drive Windows (misalnya `C:\ESP32\firmware`), jangan hanya menyalin satu `.bin`.

## 5. Flash dari PowerShell Windows

Pasang Python 3 untuk Windows dan pilih COM port ESP32-S3 di **Device Manager → Ports**. Di PowerShell, masuk ke folder firmware hasil build:

```powershell
cd C:\ESP32\firmware
py -3 -m pip install "esptool>=4.8,<5"
.\flash_windows.ps1 -Port COM5
```

**Ganti COM5** dengan port board yang sebenarnya. Script memeriksa board, tiga offset, dan hash SHA256 sebelum flash. Lihat [panduan Windows](INSTALL_WINDOWS.md) dan [wiring](HARDWARE.md).

## 6. Jika build gagal

- Jika error saat instal WSL: pastikan virtualisasi Windows diaktifkan dan WSL2 tersedia.
- Jika akses jaringan bermasalah: pastikan `git clone` dan installer ESP-IDF dapat mengunduh dependensi.
- Jika ESP-IDF versi salah: jangan menimpa instalasi project lain. Gunakan folder `~/esp-flipper/esp-idf` dengan tag tepat v5.4.1.
- Jika patch menolak source: script mematok commit upstream; jangan memaksakan patch ke `main` terbaru.
- Jika gagal kompilasi C/CMake: **inilah titik pertama compiler benar-benar berjalan**; catat error pertama untuk perbaikan lanjutan.
- Jika Python packaging menolak offset: jangan bypass validasi; periksa `flash_project_args` build.

**Status verifikasi:** Windows WSL builder disiapkan dan dapat diuji di mesin pengguna; belum ada bukti build penuh ESP-IDF sukses. Selalu periksa [laporan pengujian](TEST_REPORT.md).
