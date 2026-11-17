# DIY240 Web Flasher

Website untuk memasang firmware ESP32-S3 N16R8 / ST7789 240×240 melalui USB Serial dan memberikan panduan lintas platform.

## Arsitektur

- Frontend: HTML, CSS, JavaScript (Vite untuk bundling dan menyalin `public/` ke `dist/`).
- Installer: [ESP Web Tools](https://esphome.github.io/esp-web-tools/) versi mayor 10; dialog flashing mengikuti implementasi library, bukan simulasi.
- Image web: **merged firmware** dari empat image yang dibangun/terverifikasi di GitHub Actions. Manifest di `public/firmware/manifest.json` menggunakan `chipFamily: ESP32-S3`, offset `0`, dan `new_install_prompt_erase: true`.
- Output firmware diterbitkan oleh [`.github/workflows/publish-web-firmware.yml`](../.github/workflows/publish-web-firmware.yml) dari artifact CI sukses `43889135916`, bukan ditulis ulang secara manual. Sumber ZIP asli diverifikasi terhadap `BUILD_INFO.json`.
- Deployment: Vercel dari GitHub, **Root Directory = `web`**, Build Command = `npm run build`, Output Directory = `dist`. Push berikutnya membangun ulang situs secara otomatis.

## Development

```bash
cd web
npm install
npm run dev
```

Situs hanya mengaktifkan installer jika manifest, file binary, dan metadata tersedia serta pengguna mengonfirmasi model board. Pemeriksaan `HEAD` menghindari mengunduh ~12 MB hanya untuk status. Browser yang tidak mendukung USB Serial menerima instruksi manual, bukan tombol palsu.

## Batasan

- Web Serial/USB di browser memiliki keterbatasan platform. Windows/Linux/macOS melalui Chromium umumnya didukung. Android hanya pada perangkat/browser dengan USB OTG dan dukungan terkait. iOS **tidak bisa melakukan flashing USB dari website ini**.
- **Firmware yang sama tidak boleh dipasang pada board selain ESP32-S3 N16R8 dengan pinout DIY240**.
- Sukses build + flashing tidak otomatis membuktikan TFT, SD card, tombol atau semua aplikasi bekerja; lakukan pengujian hardware.
- Flashing adalah operasi penulisan flash internal. Backup data yang diperlukan.
- Port original Sor3nt dan dependensi memiliki lisensi, risiko keamanan, dan keterbatasan sendiri. Situs tidak melakukan telemetry atau menyimpan data port USB.
- Perangkat mungkin memakai driver USB-UART spesifik (mis. CP210x/CH34x) bergantung desain board, bukan ditentukan oleh website.

## Sources

- [Firmware integration](https://github.com/gungsss/flipper-esp32s3-diy240)
- [Build artifact](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43889135916)
- [Upstream Sor3nt](https://github.com/Sor3nt/Flipper-Zero-ESP32-Port)
- [ESP Web Tools official documentation](https://esphome.github.io/esp-web-tools/)
