# M4145 Flipper ESP32-S3 Flasher

Situs firmware komunitas by m4145 untuk **ESP32-S3 N16R8 + ST7735S 160×128 landscape**. Root situs menampilkan satu opsi flash universal, panduan wiring, dan riwayat rilis. Vercel yang sama dipakai untuk seluruh pembaruan.

## Isi dan build

- Frontend statis HTML, CSS, dan JavaScript; Vite menyalin direktori `public/` ke `dist/`.
- Installer menggunakan ESP Web Tools 10 dan manifest empat partisi di `public/flipper-st7735-151/landscape/manifest.json`.
- Metadata `BUILD_INFO.json` menjadi sumber validasi board, versi, modul, ukuran, offset, dan SHA256.
- Riwayat versi ditulis di `public/updates.json`; setiap rilis baru ditambahkan di bagian paling atas.
- Project Vercel tetap `flipper-diy240-flasher`, Root Directory `web`, Build Command `npm run build`, Output Directory `dist`. Domain utama yang sudah terpasang: `diy240.vercel.app`.
- Rilis baru tidak memerlukan project Vercel baru. Workflow firmware mengganti direktori paket universal; Git integration Vercel membangun ulang situs dari project yang sama.

## Development

```bash
cd web
npm install
npm run dev
```

Installer hanya aktif setelah pengguna memeriksa hardware dan menyetujui konfirmasi. Pemeriksaan awal memastikan satu target ESP32-S3, empat partisi, offset yang cocok, file yang tersedia, serta metadata build universal.

## Pembaruan firmware

1. Jalankan workflow `.github/workflows/build-st7735s-151-modules.yml` dan tunggu build serta pemeriksaan CI berhasil.
2. Workflow menerbitkan satu paket ke `public/flipper-st7735-151/landscape/`; tidak ada pilihan profil core/all-modules pada halaman flash.
3. Tambahkan catatan versi baru di awal `public/updates.json`, termasuk tanggal, perubahan, batasan yang relevan, dan tautan build.
4. Commit perubahan ke branch yang terhubung ke project Vercel yang sama. Vercel akan membuat deployment project yang sama; alias utama tetap `diy240.vercel.app`.

## Kompatibilitas dan batasan

Firmware ini bukan firmware resmi Flipper Zero dan bukan implementasi penuh source, SDK, runtime, atau hardware Flipper. Modul opsional harus dipasang dan memakai pinout yang benar. RDM6300 read-only; iButton HAL belum tersedia; file FAP ARM tidak kompatibel langsung dengan ESP32-S3. Build CI dan flashing sukses belum menggantikan tes fisik layar, tombol, microSD, Wi-Fi, BLE, dan modul.

Flashing USB browser membutuhkan HTTPS dan dukungan Web Serial/WebUSB. iOS tidak dapat flash langsung dari halaman ini; Android bergantung pada USB OTG dan browser.
