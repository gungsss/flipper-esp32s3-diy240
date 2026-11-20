# Status build ST7735S landscape — 20 November 2026

Profil yang sedang disiapkan adalah ESP32-S3 N16R8, ST7735S 160×128 landscape,
microSD SPI3, dan enam tombol. Perubahan 1.5.1 adalah backport terpilih ke port
ESP32; ini bukan firmware resmi Flipper Zero dan tidak memiliki kesetaraan penuh.

| Pemeriksaan | Status saat ini |
|---|---|
| Generator board dari pinout dasar | Berhasil menghasilkan 160×128 landscape, CS layar ke GND, 5 MHz, SD SPI3, dan tombol yang ditentukan. |
| Penerapan ulang patch ST7735S/landscape | Berhasil pada source fixture lokal; patch dapat diterapkan ulang tanpa menggandakan perubahan. |
| Profil modul opsional | File contoh tersedia untuk CC1101, nRF24, PN532, IR, dan RDM6300; perlu pencocokan GPIO dengan PCB dan modul fisik. |
| Build ESP-IDF dari konfigurasi modul yang diperbarui | Percobaan CI pertama berhenti saat konfigurasi FAM karena `fam_config.py` tidak menerima `__file__`; perbaikannya sedang dibangun ulang. |
| Flash dan uji layar, tombol, SD, radio, NFC, IR, RFID pada perangkat pengguna | Belum diverifikasi. |

## Image yang sudah tersedia sebelumnya

Ada artifact ST7735S landscape hasil [GitHub Actions run #44117359364](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/44117359364).
Build itu memakai backport 1.5.1 dan layar landscape, tetapi dibuat sebelum
profil pemilihan modul berdasarkan pinout diperbarui. Metadata artifact lama
tidak mencatat fitur modul yang aktif. Karena itu artifact tersebut bukan
build yang dihasilkan dari profil semua modul terbaru di proyek ini.

Build CI terbaru adalah [run #44681535383](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/44681535383).
Kedua job berhenti sebelum kompilasi C karena konfigurasi FAM memakai
`__file__`, yang tidak disediakan loader FAM. Patch sekarang memberi FAM path
source eksplisit dari `build_diy.sh`; hasil build ulang akan dicatat setelah
workflow selesai.

Build [run #43889135916](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43889135916)
adalah build historis profil ST7789, bukan target ST7735S saat ini.

## Batas klaim

- Kompilasi tidak membuktikan layar, pin, atau modul bekerja secara fisik.
- Pin pada profil contoh semua modul perlu diperiksa terhadap skema board dan
  koneksi aktual sebelum dipakai.
- Modul eksternal harus terpasang sesuai profil build. Menyambungkan modul
  setelah firmware dibuat tidak otomatis menambahkan menunya; build dan flash
  ulang dengan pinout yang sesuai.
