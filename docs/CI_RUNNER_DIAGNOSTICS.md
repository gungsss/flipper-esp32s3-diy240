# Diagnostik GitHub Actions — job gagal sebelum mendapatkan runner

## Yang benar-benar diketahui (16 November 2026)

- Repositori `gungsss/flipper-esp32s3-diy240` berstatus **Public**, dan file workflow `.github/workflows/build.yml` ada.
- [Build firmware #3](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43882456859) memakai `runs-on: ubuntu-24.04`, gagal sebelum satu langkah berjalan.
- [Diagnostik sederhana](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43883153060) memakai `runs-on: ubuntu-latest`, hanya berisi perintah `echo`, `uname`, dan versi Python, **juga gagal sebelum ada langkah berjalan**.
- GitHub API pada job diagnostik menunjukkan `runner_name: ""`, `steps: []`, dan waktu selesai sekitar 3 detik setelah mulai. Check-run ID `133354094130` memuat **2 annotations** (isinya belum berhasil diambil oleh konektor).
- Belum ada log `git clone`, instal ESP-IDF, Ninja, atau compiler. **Tidak ada bukti bahwa source firmware gagal dikompilasi.**

## Interpretasi

Masalah terlokalisasi **sebelum alokasi GitHub-hosted runner**. Yang belum diketahui adalah alasan tepatnya, karena teks error dari **Annotations** belum terbaca. Jangan mengklaim billing pasti penyebabnya tanpa anotasi tersebut.

Menurut [dokumentasi resmi GitHub](https://docs.github.com/en/actions/concepts/billing-and-usage), runner standar pada repo publik gratis. Akan tetapi [GitHub juga menjelaskan](https://docs.github.com/en/billing/how-tos/troubleshooting/locked-account) bahwa masalah otorisasi pembayaran pada akun dapat mengunci akses Actions. Kebijakan workflow, runner, dan status layanan juga dapat menjadi penyebab.

## Pemeriksaan khusus akun yang perlu dilakukan pemilik

1. Buka [run diagnostik](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43883153060) dan lihat pesan **Annotations**. Biasanya alasan pra-eksekusi tampil di ringkasan workflow, bukan dalam log langkah.
2. Bila error menyebut tagihan atau spending limit: periksa **Settings → Billing and licensing → Usage / Budgets** dan notifikasi penagihan. Jangan membagikan nomor kartu atau data pembayaran ke issue publik.
3. Periksa **repo → Settings → Actions → General**, apakah Actions diizinkan, dan bahwa runner standar untuk repo publik tidak dilarang.
4. Periksa [GitHub Status](https://www.githubstatus.com/) untuk insiden GitHub Actions pada waktu run.
5. Jika tidak ada pengaturan bermasalah, ajukan [GitHub Support](https://support.github.com/) dengan **run ID 43883153060**, **job ID 133354094130**, waktu **2026-11-16 14:11:33 UTC**, dan teks anotasi.

## Apa yang dilakukan setelah runner pulih

1. Jalankan workflow `Diagnostic - Runner availability`, pastikan sukses dan mencatat setidaknya satu langkah.
2. Jalankan `Build DIY ESP32-S3 N16R8` dari tab Actions.
3. Jika compiler gagal, gunakan log pertama yang relevan dan perbaiki source/build script. Jangan menduga berdasarkan kegagalan sebelumnya.
4. Jika build sukses, periksa artifact `.bin`, checksum, dan offset. Setelah itu baru flashing dan uji TFT, SD, tombol, Wi-Fi/BLE di board fisik.

## Alternatif tanpa GitHub-hosted runner

Pengguna Windows: [build menggunakan WSL2 Ubuntu](BUILD_WINDOWS_WSL.md) dan flash dengan PowerShell. Ini bukan pengganti uji hardware, tetapi tidak bergantung pada runner GitHub.

Pelacakan: [GitHub Issue #1](https://github.com/gungsss/flipper-esp32s3-diy240/issues/1).
