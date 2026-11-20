# Flash ESP32-S3 ST7735S

Panduan ini berlaku untuk paket **ESP32-S3 N16R8 + ST7735S 160×128 landscape**
yang dibangun dari profil proyek ini. Pastikan `BUILD_INFO.json` menyebut ST7735S
landscape, bukan ST7789 atau portrait. Gunakan empat image dari satu paket yang
sama: bootloader pada `0x0`, partition table `0x8000`, aplikasi `0x10000`, dan
`ota_data_initial.bin` pada `0xBF0000`.

Pilih sistem operasi:

- [Windows dan PowerShell](INSTALL_WINDOWS.md)
- Linux/macOS: gunakan `flash_macos_linux.sh` dari artifact, setelah memastikan
  port serial board benar.

Sebelum flash, pastikan semua image, offset, dan checksum cocok dengan
`BUILD_INFO.json`. Flash dapat menimpa firmware dan data board yang lama.
Cadangkan data penting. Jangan gunakan file ST7789 karena layar CS-nya berbeda.

Sesudah flash, periksa layar ST7735S, tombol, microSD FAT32, Wi-Fi/BLE, dan
setiap modul yang pinout-nya diaktifkan. Sukses menulis image tidak membuktikan
semua fitur berjalan di perangkat.
