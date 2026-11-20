# Build dan flash di Windows

Target proyek ini adalah ESP32-S3 N16R8 dengan ST7735S 160×128 landscape. Jangan
memakai firmware ST7789 atau image ESP32 dari project lain. Gunakan hanya paket
yang `BUILD_INFO.json`-nya mencantumkan ST7735S landscape dan offset image yang
sesuai.

## Dapatkan firmware

Jika GitHub Actions sudah mengunggah artifact dari workflow **Flipper 1.5.1
ST7735S Landscape**, unduh artifact itu dan ekstrak ke satu folder. Paket flash
harus berisi `BUILD_INFO.json`, `flash_windows.ps1`, `bootloader/bootloader.bin`,
`partition_table/partition-table.bin`, `furi_esp32.bin`, dan
`ota_data_initial.bin`. Jangan menggabungkan file dari run berbeda.

Jika artifact baru belum tersedia, jangan flash ZIP lama yang memiliki metadata
ST7789, orientasi portrait, atau pinout yang berbeda. Bangun firmware melalui
[WSL2](BUILD_WINDOWS_WSL.md) atau ikuti [panduan build macOS](INSTALL_MAC.md),
lalu kemas hanya hasil build yang berhasil.

## Flash dari PowerShell

Pasang Python 3, hubungkan ESP32-S3 menggunakan kabel USB data, lalu periksa
port-nya pada **Device Manager → Ports (COM & LPT)**. Instal esptool:

```powershell
py -3 -m pip install "esptool>=4.8,<5"
```

Buka PowerShell di folder artifact dan jalankan:

```powershell
.\flash_windows.ps1 -Port COM5
```

Ganti `COM5` dengan port yang terlihat di Device Manager. Script memverifikasi
target, empat image, offset, dan SHA256 sebelum menulis flash. Flash pertama
dapat menimpa firmware dan pengaturan lama; salin data penting terlebih dahulu.

Jika board tidak tersambung, tutup aplikasi serial yang menggunakan COM, coba
kabel atau port USB lain, dan masuk mode download dengan tombol BOOT bawaan board
saat reset.

## Sesudah flash

Periksa tampilan ST7735S landscape, keenam tombol, microSD FAT32, lalu Wi-Fi dan
BLE secara bergantian. Fitur modul eksternal baru berfungsi jika modul dipasang
sesuai pinout build tersebut. Lihat [HARDWARE.md](HARDWARE.md) dan
[FEATURES.md](FEATURES.md).
