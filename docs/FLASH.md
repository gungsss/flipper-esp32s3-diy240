# Cara flash firmware ke ESP32-S3 N16R8

Ada dua metode. Keduanya dilakukan melalui **USB**, bukan OTA upstream. **Tidak ada firmware siap flash yang dinyatakan berhasil hanya dari patch source**; gunakan hasil build yang sukses.

> [!WARNING]
> Flash bootloader, partition table dan firmware dapat menghapus/mengganggu firmware atau data lama dalam flash internal. Cadangkan data penting. Pastikan chip **ESP32-S3 N16R8**, bukan ESP32 klasik atau ESP32-C6. **Lepas kabel USB ketika mengubah wiring**.

## A. Flash dari build ESP-IDF lokal (disarankan untuk uji pertama)

### 1. Build dahulu

Ikuti [INSTALL_MAC.md](INSTALL_MAC.md):

```bash
export ESP_IDF_EXPORT_SCRIPT="$HOME/esp-flipper/esp-idf/export.sh"
./scripts/build_local.sh
```

Jangan lanjut kalau perintah build gagal.

### 2. Hubungkan ESP32-S3 ke Mac

Gunakan kabel USB-C **data**, bukan kabel charging-only. Board foto memiliki dua port USB-C, bisa berupa USB native dan USB-UART; pilih port yang terdeteksi saat board dihubungkan. Periksa sebelum dan sesudah colok:

```bash
ls /dev/cu.usb*
```

Jika beberapa port muncul, pilih yang baru terdeteksi. Jangan menebak nomor port.

### 3. Flash

```bash
./scripts/flash_local.sh /dev/cu.usbmodemXXXX --monitor
```

Ganti `/dev/cu.usbmodemXXXX` dengan port yang **betul-betul terdeteksi**. Script akan meminta kamu mengetik `FLASH` sebagai konfirmasi, lalu menjalankan build/flash/monitor sesuai konfigurasi target DIY. Bila flag `--monitor` dihilangkan, ia hanya flash tanpa membuka monitor.

**Jika flashing tidak dapat masuk mode download**, tahan tombol BOOT bawaan ESP32-S3 saat melakukan reset/tombol RST bawaan, lepas BOOT setelah mode download aktif, lalu ulang. Jangan memakai tombol MID pada PCB eksternal sebagai BOOT—MID dipasang ke GPIO8.

### 4. Hasil yang diharapkan

- `idf.py` melaporkan flash berhasil dan restart perangkat.
- Serial monitor tidak terus menerus mengulang panic/brownout.
- Backlight/tampilan muncul (jika wiring BLK sesuai modul).
- Enam tombol dapat berpindah menu.
- Kartu microSD FAT32 dikenali; isi file SD sudah tersedia.

Jika salah satu tidak terpenuhi, jangan mengasumsikan semua fitur bekerja. Baca [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## B. Flash dari ZIP firmware hasil GitHub Actions

Metode ini cocok bila firmware sukses dibuild pada GitHub dan kamu tidak ingin memasang seluruh ESP-IDF di Mac.

1. Buka **Actions** pada repo ini, pilih **Build DIY ESP32-S3 N16R8**.
2. Jalankan workflow; **pastikan statusnya hijau/success**.
3. Pada detail run, unduh artifact bernama `flipper-diy-s3-n16r8-st7789-240` dan ekstrak ke sebuah folder.
4. Di Terminal macOS, masuk ke folder tersebut:

   ```bash
   cd /folder/hasil-ekstrak-artifact
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install 'esptool>=4.8,<5'
   ls /dev/cu.usb*
   bash flash_macos_linux.sh /dev/cu.usbmodemXXXX
   ```

Script akan membaca file `flash_project_args` yang dihasilkan ESP-IDF. Sebelum artifact diunggah, proses packaging memeriksa tiga offset **untuk layout build ini**: bootloader `0x0`, partisi `0x8000`, aplikasi `0x10000`. Jangan memakai image dari board lain, versi lain, atau kombinasi file dari ZIP yang berbeda.

## C. Siapkan microSD

**Firmware dan isi SD card bukan hal yang sama.** Setelah flash, format microSD ke **FAT32** dan salin isi paket SD card asli Sor3nt yang cocok dengan versi firmware ke **root microSD**, bukan membuat folder tambahan bernama `sdcard`.

Sumber resmi: [Sor3nt Releases — sdcard.zip](https://github.com/Sor3nt/Flipper-Zero-ESP32-Port/releases/latest). Jangan menggunakan firmware dari pihak lain yang tidak diketahui asalnya. Karena source integrasi dipin ke commit di atas, ketidakcocokan antara aplikasi FAP di paket rilis dan perubahan terbaru di source **masih mungkin terjadi**; uji menu inti dulu. Jangan mengandalkan aplikasi eksternal sebelum cocok.

### Verifikasi SD

Pastikan microSD terpasang saat board mati, lalu boot. Jika file explorer/archive kosong, cek log SD dan [TROUBLESHOOTING.md](TROUBLESHOOTING.md). Pada macOS, file tersembunyi seperti `.DS_Store` tidak penting untuk aplikasi.

## D. Pemulihan dasar

- Jika board tidak boot setelah flash: lepaskan microSD dan modul lain **setelah daya dicabut**, lalu coba serial monitor lagi untuk membedakan masalah wiring vs firmware.
- Jika hanya TFT blank: cek backlight, resolusi, orientasi, dan SPI; jangan langsung `erase_flash`.
- Jika bootloader tertimpa dan tidak dapat masuk aplikasi: masuk mode download (BOOT + reset), kemudian lakukan full flash lagi dari hasil build yang sama.
- `erase_flash` akan menghapus seluruh flash internal dan tidak boleh dipakai sebagai langkah diagnostik pertama. Catat data yang akan hilang.

Lanjut: [FIRST_BOOT.md](FIRST_BOOT.md).
