# Instalasi dan flash lewat Windows — panduan utama

Proyek ini **Windows-first** untuk pengguna. **Kamu tidak memerlukan Mac, Linux, atau ESP-IDF untuk flash** bila file firmware sudah tersedia dari build GitHub Actions yang **sukses**. Perangkat target adalah **ESP32-S3 N16R8**, TFT ST7789 240×240 7 pin tanpa CS, microSD SPI3, dan enam tombol.

> [!WARNING]
> Saat panduan ini dibuat, workflow build firmware belum berhasil dan belum ada `.bin` yang terverifikasi. Langkah flash di bawah **hanya untuk artifact hasil build sukses** dari repositori ini. Jangan menggunakan firmware acak atau milik LilyGo/board lain.

## 1. Persiapan

1. Pastikan [wiring hardware](HARDWARE.md) benar dan semua modul menggunakan **3,3 V** sesuai label. Lepaskan kabel USB ketika mengubah wiring.
2. Gunakan **kabel USB-C data**. Board memiliki dua port USB-C; uji masing-masing bila COM port tidak muncul.
3. Pasang [Python 3 resmi](https://www.python.org/downloads/windows/) dengan **Python Launcher `py`**. Di Windows, cek dengan membuka PowerShell:

```powershell
py -3 --version
py -3 -m pip install "esptool>=4.8,<5"
py -3 -m esptool version
```

4. Buka **Device Manager → Ports (COM & LPT)**. Hubungkan ESP32-S3, lalu lihat port baru, misalnya **COM5**. Nomor COM bisa berbeda. Jika tidak muncul, baca [troubleshooting](TROUBLESHOOTING.md).

## 2. Unduh firmware yang benar

1. Buka [Actions repo ini](https://github.com/gungsss/flipper-esp32s3-diy240/actions).
2. Pilih workflow **Build DIY ESP32-S3 N16R8** dan pastikan run berwarna **hijau / success**.
3. Pada bagian **Artifacts**, unduh `flipper-diy-s3-n16r8-st7789-240`.
4. Ekstrak ZIP ke folder biasa, misalnya `C:\ESP32\firmware`. Jangan menggabungkan file dari run berbeda.
5. Pastikan di folder itu ada `BUILD_INFO.json`, `flash_windows.ps1`, `furi_esp32.bin`, `bootloader/bootloader.bin`, dan `partition_table/partition-table.bin`.

**Penting:** jika run GitHub Actions masih gagal, **tidak ada firmware siap flash**. Jangan melanjutkan ke langkah berikutnya.

## 3. Flash menggunakan PowerShell

Masuk ke folder hasil ekstraksi melalui File Explorer, klik kanan area kosong → **Open in Terminal**, atau buka PowerShell lalu `cd` ke folder tersebut.

```powershell
cd C:\ESP32\firmware
.\flash_windows.ps1 -Port COM5
```

Ubah `COM5` dengan port di Device Manager. Script melakukan **validasi target board, mapping offset, dan SHA256** ketiga image sebelum meminta konfirmasi `FLASH`. Hanya ketik konfirmasi jika hardware dan data penting sudah dicek.

Jika kebijakan PowerShell mencegah script berjalan, **jangan ubah kebijakan secara permanen**. Kamu dapat menggunakan perintah manual berikut **setelah memverifikasi ZIP berasal dari run sukses**:

```powershell
py -3 -m esptool --chip esp32s3 --port COM5 --baud 460800 write_flash 0x0 bootloader/bootloader.bin 0x8000 partition_table/partition-table.bin 0x10000 furi_esp32.bin
```

Perintah manual **tidak otomatis memeriksa checksum**. Offset di atas berlaku khusus layout artifact proyek ini, tidak berlaku universal untuk semua ESP32.

## 4. Sesudah flash

1. ESP32-S3 akan restart. Jika tidak, lepas-pasang USB secara aman.
2. Periksa gambar di TFT, respons keenam tombol, dan akses microSD.
3. Format microSD ke **FAT32**, lalu isi root kartu dengan paket SD resmi dari [Sor3nt Releases](https://github.com/Sor3nt/Flipper-Zero-ESP32-Port/releases/latest), bukan folder berlapis.
4. Uji Wi-Fi dan BLE secara bergantian pada jaringan/perangkat yang kamu miliki atau diizinkan.
5. Catat hasilnya menurut [pengujian pertama](FIRST_BOOT.md). **Flashing sukses belum membuktikan seluruh fungsi hardware bekerja.**

## 5. Jika perangkat tidak terdeteksi

- Cek kabel data dan port USB-C alternatif di board.
- Cek Device Manager. Untuk board dengan USB-UART bridge, mungkin perlu driver **CP210x** atau **CH34x** sesuai chip fisik di board; jangan memasang driver acak.
- Coba mode download manual: tahan **BOOT bawaan board**, tekan-lepas **RST**, lalu lepaskan BOOT; jalankan ulang esptool.
- Jika muncul `PermissionError` atau port sedang dipakai, tutup Serial Monitor/Arduino IDE sebelum flash.
- Jika `Failed to connect`, baca [troubleshooting](TROUBLESHOOTING.md).

## 6. Pengembang Windows: build lokal

Untuk **build** (bukan sekadar flash), kode integrasi saat ini masih menggunakan script **Bash**, sehingga metode praktis Windows adalah WSL2 Ubuntu untuk build, **lalu flash dari PowerShell Windows**. Instal ESP-IDF **v5.4.1** di WSL sesuai [panduan resmi Espressif](https://docs.espressif.com/projects/esp-idf/en/v5.4.1/esp32s3/get-started/linux-macos-setup.html), gunakan instalasi terpisah karena upstream memodifikasi library Wi-Fi IDF, jalankan `./scripts/build_local.sh`, kemudian kemas output dengan `scripts/package_artifacts.py` dan gunakan script flashing Windows. **Alur build via WSL ini belum divalidasi end-to-end**.

Untuk jalur flash dan pemulihan pada Linux/macOS juga, baca [FLASH.md](FLASH.md).
