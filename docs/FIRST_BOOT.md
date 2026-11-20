# Penggunaan pertama dan prosedur uji

Panduan ini digunakan **setelah firmware selesai di-build dan flash sukses**. Ini adalah urutan uji yang diusulkan, **bukan laporan bahwa semua fitur sudah terbukti bekerja pada hardware pengguna**.

## 1. Boot pertama

1. Pastikan perangkat dalam keadaan mati; microSD FAT32 berisi aset firmware yang sesuai sudah terpasang.
2. Hubungkan USB data atau suplai yang aman ke board ESP32-S3.
3. Amati serial monitor dari Mac: `./scripts/flash_local.sh PORT --monitor` setelah proses flash, atau jalankan `idf.py -p PORT monitor` dalam lingkungan IDF.
4. Tunggu inisialisasi GUI, sistem file, dan layanan; jangan langsung menekan banyak tombol sebelum UI tampil.
5. Jika layar tidak menyala, periksa jalur BLK/backlight, jangan menganggap ESP32 mati. Serial log adalah alat diagnosis utama.

## 2. Navigasi 6 tombol

| Tombol PCB | Aksi yang diharapkan |
|---|---|
| UP | Menu ke atas |
| DWN | Menu ke bawah |
| LET | Navigasi ke kiri |
| RHT | Navigasi ke kanan |
| MID | OK / buka pilihan |
| SET | Back / kembali |

Tombol RST pada PCB eksternal **tidak disambungkan** pada profil awal. Jika perlu reset gunakan tombol `RST` bawaan board ESP32-S3. Uji tombol dengan penekanan singkat dan panjang, terutama saat menu tidak merespons. Keypad adalah input active-low internal pull-up.

## 3. Pemeriksaan microSD

- Buka **Archive / File Browser** jika tersedia di build.
- Periksa isi folder dasar, misalnya `/ext/` atau direktori aplikasi yang disalin dari `sdcard.zip`.
- Cobalah membuat file kecil melalui fitur file browser jika tersedia, lalu restart dan cek persistensinya.
- Bila kartu tidak mount, cek kabel **MISO 38 / CLK 40 / MOSI 39 / CS 14** serta FAT32. Kartu bukan penyebab layar tetap hitam jika serial boot juga gagal; periksa secara terpisah.

## 4. Pemeriksaan Wi-Fi

- Gunakan **pemindaian jaringan pasif** pada Wi-Fi app untuk melihat SSID milikmu sendiri/lingkungan yang diizinkan.
- Bila akan terhubung ke access point, gunakan jaringan milikmu dan masukkan kredensial secara lokal pada perangkat.
- Jangan mengaktifkan fitur yang mengganggu komunikasi jaringan atau meniru jaringan orang lain tanpa izin. Fitur tertentu pada upstream adalah alat penelitian jaringan, bukan untuk digunakan sembarangan.
- Ingat bahwa **Wi-Fi dan BLE dapat saling menonaktifkan** pada konfigurasi port ini.

## 5. Pemeriksaan BLE / USB

- Matikan Wi-Fi saat menguji BLE.
- Mulai dari Bluetooth settings dan pairing ke perangkat milikmu.
- Uji USB HID hanya pada komputer pribadi/lingkungan pengujian yang sah. Jangan menjalankan skrip BadUSB dari sumber tak dikenal.
- Antarmuka qFlipper upstream untuk komunikasi file **bukan** jaminan kompatibilitas flash via qFlipper original; flash ulang tetap melalui ESP-IDF atau esptool lokal.

## 6. Ekspektasi layar ST7735S 160×128

Build utama memakai kanvas native **160×128 landscape**. Beranda menampilkan
jam dan tanggal di atas animasi Flipper, launcher menyediakan lima baris penuh,
dan submenu umum menampilkan lebih banyak pilihan. Beberapa aplikasi yang
menggambar dengan koordinat tetap 128×64 masih dapat memerlukan penyesuaian.

## 7. Checklist hasil uji awal

| Pengujian | Hasil | Bukti yang perlu dicatat |
|---|---|---|
| Flash selesai | Belum diuji fisik | Log flashing |
| Boot tanpa panic | Belum diuji fisik | Log serial 30–60 detik |
| UI ST7735S 160×128 landscape | Belum diuji fisik | Foto layar |
| UP / DWN / LET / RHT | Belum diuji fisik | Foto/video navigasi |
| MID / SET | Belum diuji fisik | Foto/video pemilihan/back |
| microSD FAT32 | Belum diuji fisik | Log mount / daftar file |
| Wi-Fi scan | Belum diuji fisik | Hasil scan jaringan sendiri |
| BLE toggling | Belum diuji fisik | Status dan hasil pairing |

Jika menemukan masalah, kumpulkan log serial, nama modul/display, pinout yang dipakai, versi build, serta deskripsi singkat kondisi. Kemudian lihat [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
