# Audit tampilan ST7735S 160×128

Profil ini mengalokasikan framebuffer 1-bit sebesar 160×128 dan mengirimkannya
ke seluruh panel ST7735S. Tidak ada letterbox atau pita kosong atas/bawah pada
jalur display.

## Cakupan pemeriksaan source

Semua halaman firmware memakai dua jalur gambar bersama: callback `View` dan
callback `ViewPort`. `View` lama dipetakan dari koordinat 128×64 ke area panel;
`ViewPort` memakai adapter yang sama. Halaman inti yang dirancang khusus untuk
160×128 ditandai native agar tidak diskalakan dua kali.

Halaman inti yang memiliki layout native:

- Beranda dan launcher lima baris
- Browser berkas dan daftar pengaturan
- Kotak teks dan keyboard teks
- Editor angka, byte, tanggal, dan waktu
- Submenu umum

Skrip `scripts/audit_st7735_ui.py` mengecek geometri panel, alokasi framebuffer,
semua 17 API Canvas publik yang menggambar, kedua dispatcher GUI, dan penanda
layout native untuk sepuluh modul layar. Skrip ini dijalankan sebelum kompilasi
di `scripts/build_local.sh`. Build ESP-IDF berikutnya mengompilasi seluruh
aplikasi yang terpilih pada profil core dan profil contoh modul.

## Batas verifikasi

Audit source dan kompilasi membuktikan bahwa halaman masuk ke jalur gambar dan
kode berhasil dibangun. Keduanya tidak dapat memastikan keterbacaan, kontras,
warna, posisi panel, atau interaksi tombol pada unit fisik. Pemeriksaan visual
akhir perlu dilakukan dengan firmware yang sama pada ESP32-S3 dan ST7735S yang
dipakai pengguna.
