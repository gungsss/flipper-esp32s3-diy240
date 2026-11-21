# Cara menerbitkan pembaruan

Situs memakai satu project Vercel dan satu URL utama (`diy240.vercel.app`). Jangan membuat project Vercel baru untuk tiap versi firmware.

1. Jalankan workflow `Build M4145 Flipper 1.5.1 ST7735S universal firmware`.
2. Pastikan build, audit UI, dan pemeriksaan paket berhasil. Workflow menerbitkan paket universal ke `web/public/flipper-st7735-151/landscape/`.
3. Tambahkan satu objek baru di awal `web/public/updates.json`. Pertahankan daftar versi lama supaya pengguna dapat membaca riwayat.
4. Commit perubahan ke branch yang terhubung ke Vercel. Build situs berjalan di project yang sama.
5. Sesudah deployment `READY`, verifikasi halaman flash, manifest, metadata, dan domain utama sebelum mengumumkan update.

Manifest di halaman flash selalu menunjuk paket universal terbaru; pilihan firmware tidak digandakan di UI. Catat batas hardware atau fitur pada catatan rilis agar riwayat tidak mengklaim uji fisik yang belum dilakukan.
