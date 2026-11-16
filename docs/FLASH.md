# Flash ESP32-S3 DIY240 — Windows, Linux, macOS

**Windows adalah panduan utama proyek ini.** Ketiga OS dapat melakukan flashing ke ESP32-S3 melalui USB; `.bin` tidak tergantung pada komputer pembuat firmware.

> [!IMPORTANT]
> **Firmware sudah berhasil dikompilasi dan artifact ZIP telah diverifikasi** pada [GitHub Actions run #43889135916](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43889135916). **Perangkat fisik belum diuji.** Pakai hanya ZIP build sukses yang kompatibel dengan ESP32-S3 N16R8 dan wiring DIY240; jangan menggunakan image board lain. Lihat [TEST_REPORT.md](TEST_REPORT.md).

## Windows (disarankan untuk kebanyakan pengguna)

Ikuti **[Panduan Windows lengkap](INSTALL_WINDOWS.md)** untuk Python, port COM, unduhan artifact, PowerShell, verifikasi checksum, mode BOOT dan troubleshooting.

Setelah ZIP firmware hasil build sukses diekstrak:

```powershell
py -3 -m pip install "esptool>=4.8,<5"
.\flash_windows.ps1 -Port COM5
```

**Ganti `COM5` dengan COM port sebenarnya.** Script Windows disertakan otomatis dalam artifact build dan mengecek SHA256 serta mapping partisi.

## Linux (dari ZIP artifact yang sama)

Gunakan port aktual, biasanya `/dev/ttyACM0` atau `/dev/ttyUSB0`. Pastikan paket Python venv dan permission serial sudah benar.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "esptool>=4.8,<5"
ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
bash flash_macos_linux.sh /dev/ttyACM0
```

Jika permission ditolak, sesuaikan akses serial pengguna (pada banyak distro melalui grup `dialout`) dan masuk ulang ke sesi. Jangan memakai `sudo` jika permission telah benar.

## macOS (dari ZIP artifact yang sama)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "esptool>=4.8,<5"
ls /dev/cu.usb*
bash flash_macos_linux.sh /dev/cu.usbmodemXXXX
```

Untuk build lokal Mac dan flash langsung setelah kompilasi, baca [INSTALL_MAC.md](INSTALL_MAC.md) lalu gunakan `./scripts/flash_local.sh <PORT> --monitor` setelah `./scripts/build_local.sh` sukses.

## Catatan file image dan data

Artifact yang sukses harus memiliki **empat** image: `bootloader/bootloader.bin` pada `0x0`, `partition_table/partition-table.bin` pada `0x8000`, `furi_esp32.bin` pada `0x10000`, dan `ota_data_initial.bin` pada `0xBF0000`. Sertakan `BUILD_INFO.json`, `flash_project_args` dan script flash dari ZIP **yang sama**. Packaging menguji semua offset dan SHA256; jangan menggabungkan file dari beberapa run. ZIP awal sebelum [perbaikan OTA](https://github.com/gungsss/flipper-esp32s3-diy240/commit/3f6d8bccad4b8731f1ece7118dd2d75ce0a7d976) **tidak boleh digunakan** untuk flash.

Isi microSD **bukan** bagian dari flash chip: format ke FAT32 dan salin isi paket `sdcard.zip` dari [rilis resmi Sor3nt](https://github.com/Sor3nt/Flipper-Zero-ESP32-Port/releases/latest) ke root kartu.

Jangan menggunakan `erase_flash` sebagai langkah diagnosis pertama: perintah itu menghapus seluruh data internal. Jika muncul masalah, cek [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

Flashing dianggap selesai hanya bila esptool melaporkan sukses dan board restart. **Boot dan fungsi hardware harus diuji terpisah**.
