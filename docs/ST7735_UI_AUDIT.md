# Audit tampilan ST7735S 160×128

Profil ini mengalokasikan framebuffer 1-bit sebesar 160×128 dan mengirimkannya
ke seluruh panel ST7735S. Tidak ada letterbox atau pita kosong atas/bawah pada
jalur display.

## Cakupan pemeriksaan source

Semua halaman firmware memakai dua jalur gambar bersama: callback `View` dan
callback `ViewPort`. `View` lama dipetakan dari koordinat 128×64 ke area panel;
`ViewPort` memakai adapter yang sama kecuali overlay yang ditandai native.
Halaman inti yang dirancang khusus untuk 160×128 tidak diskalakan dua kali.

Halaman inti yang memiliki layout native:

- Beranda dan launcher lima baris
- Browser berkas dan daftar pengaturan
- Kotak teks dan keyboard teks
- Editor angka, byte, tanggal, dan waktu
- Submenu umum
- Overlay pairing BLE native 160×128 dengan kode numerik besar
- Keyboard lowercase default, Caps Lock, dan navigasi D-pad sesuai arah tombol
- Tombol LEFT tetap menjadi tombol arah; hanya tombol BACK yang menutup overlay pairing
- Pesan deteksi modul Sub-GHz, NFC, nRF24, IR, dan LF RFID pada titik masuk fitur

Skrip `scripts/audit_st7735_ui.py` mengecek geometri panel, alokasi framebuffer,
semua 17 API Canvas publik yang menggambar, callback semua aplikasi, pemetaan
empat arah D-pad pada editor dan panel tombol, kontrak keyboard lowercase/Caps
Lock, geometri serta tombol overlay pairing BLE, dan pemberitahuan kebutuhan
modul. Skrip ini dijalankan sebelum kompilasi di `scripts/build_local.sh`.
Build ESP-IDF mengompilasi semua aplikasi yang terpilih dalam satu image.

## Batas verifikasi

Audit source dan kompilasi membuktikan bahwa halaman masuk ke jalur gambar dan
kode berhasil dibangun. Keduanya tidak dapat memastikan keterbacaan, kontras,
warna, posisi panel, atau interaksi tombol pada unit fisik. Pemeriksaan visual
akhir perlu dilakukan dengan firmware yang sama pada ESP32-S3 dan ST7735S yang
dipakai pengguna.
