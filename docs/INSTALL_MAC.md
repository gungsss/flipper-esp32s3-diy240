# Build firmware di macOS

Target pengembangan: macOS, Git, Python 3, ESP-IDF **v5.4.1**, ESP32-S3 N16R8. Proses ini mengunduh upstream Sor3nt pada commit tertentu; **tidak men-flash hardware** sampai kamu menjalankan perintah flash sendiri.

## 0. Pastikan perangkat cocok

Periksa [HARDWARE.md](HARDWARE.md). Target build adalah ST7735S 160×128 landscape dengan CS layar ke GND, microSD pada SPI3, dan enam tombol. Sediakan microSD FAT32 dan koneksi internet untuk mengunduh ESP-IDF + source.

## 1. Perangkat lunak dasar

Xcode Command Line Tools:

```bash
xcode-select --install
```

Cek tools:

```bash
git --version
python3 --version
cmake --version
```

Jika `cmake` tidak tersedia, pakai Homebrew atau ikuti prasyarat dalam dokumentasi ESP-IDF resmi. Untuk Mac ARM/M1/M2/M3 dan Intel, ikuti [panduan instalasi Espressif](https://docs.espressif.com/projects/esp-idf/en/v5.4.1/esp32s3/get-started/).

## 2. Install ESP-IDF v5.4.1

Disarankan folder instalasi **terpisah** untuk proyek ini, karena build upstream menjalankan patch pada `libnet80211.a` yang ada di lingkungan IDF. Jangan gunakan instalasi yang sama untuk proyek lain yang membutuhkan library Wi-Fi original.

```bash
mkdir -p ~/esp-flipper
cd ~/esp-flipper
git clone --recursive --branch v5.4.1 --depth 1 \
  https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32s3
source ./export.sh
idf.py --version
```

Bila `idf.py` belum ditemukan, pastikan `source ~/esp-flipper/esp-idf/export.sh` sudah sukses. Untuk Mac ARM, bila masalah kompatibilitas Python/toolchain muncul, ikuti log installer ESP-IDF resmi dan jangan mencampur versi toolchain.

> Script proyek mencari `~/esp/esp-idf/export.sh` secara default. Karena panduan ini menggunakan folder terpisah `~/esp-flipper`, **set variabel berikut pada setiap sesi Terminal build/flash**, atau tambahkan ke konfigurasi shell-mu:
>
> ```bash
> export ESP_IDF_EXPORT_SCRIPT="$HOME/esp-flipper/esp-idf/export.sh"
> ```

## 3. Clone repositori integrasi

Setelah repo proyek tersedia di GitHub:

```bash
git clone https://github.com/gungsss/flipper-esp32s3-diy240.git
cd flipper-esp32s3-diy240
```

Alternatif: ekstrak ZIP paket proyek, lalu `cd` ke folder hasil ekstraksi. Build **tidak membutuhkan akses GitHub pribadi** jika kamu memiliki paket ZIP proyek.

## 4. Build satu perintah

```bash
export ESP_IDF_EXPORT_SCRIPT="$HOME/esp-flipper/esp-idf/export.sh"
./scripts/build_local.sh
```

Apa yang dilakukan otomatis:

1. Mengambil sumber upstream pada commit `e6ec11972a8e025d7ab686a6ef3016cf52360834` dan memverifikasi SHA.
2. Menerapkan patch software pilihan Flipper 1.5.1, lalu konfigurasi ST7735S 160×128 landscape, SD SPI3, keypad 6 tombol, dan ESP32-S3 N16R8.
3. Menjalankan generator `board_DIY.h` dari pinout ST7735S dan memilih fitur modul opsional berdasarkan pin yang diisi.
4. Menggunakan ESP-IDF **5.4.1** untuk mengompilasi firmware (tanpa flash).

Build output yang diharapkan:

```text
.work/upstream/build_diy/furi_esp32.bin
.work/upstream/build_diy/bootloader/bootloader.bin
.work/upstream/build_diy/partition_table/partition-table.bin
.work/upstream/build_diy/flash_project_args
```

**Penting:** daftar nama ini adalah output yang ditargetkan; klaim build berhasil hanya bila file tersebut benar-benar ada dan proses `idf.py` selesai tanpa error.

Jika ada error `ESP-IDF export.sh not found`, cek variabel `ESP_IDF_EXPORT_SCRIPT`. Jika target mengaku `esp32c6`, hapus build lama melalui `./scripts/build_local.sh --clean` (atau `.work/upstream/build_diy`) dan ulangi.

## 5. Verifikasi build

```bash
find .work/upstream/build_diy -maxdepth 3 -name '*.bin' -print
python3 -m unittest discover -s tests -v
```

**Belum otomatis diuji pada hardware.** Setelah build lolos, ikuti [FLASH.md](FLASH.md) untuk upload firmware ke board via USB.

## 6. Alternatif tanpa toolchain lokal: GitHub Actions

Repositori ini menyediakan `.github/workflows/build.yml`. Buka **GitHub → Actions → Build DIY ESP32-S3 N16R8 → Run workflow**. Workflow akan mengunduh ESP-IDF 5.4.1, upstream Sor3nt commit yang dipin, menerapkan patch, melakukan build, lalu menghasilkan artifact flash **hanya bila berhasil**. Setelah berhasil, baca [FLASH.md](FLASH.md) bagian artifact.
