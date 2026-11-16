# Status verifikasi awal — 16 November 2026

Dokumen ini memisahkan pengujian yang berhasil dilakukan di lingkungan penyusunan proyek dari pengujian yang masih memerlukan toolchain ESP-IDF dan perangkat fisik.

| Pemeriksaan | Hasil | Cakupan |
|---|---|---|
| Penilaian struktur source upstream | **Diperiksa** | Git tree pada `e6ec11972a8e025d7ab686a6ef3016cf52360834` |
| Pengujian patch source sebelumnya | **Lulus pada fixture lokal** | Generator menghasilkan header 240×240 no-CS, SD SPI3, 6 tombol; idempotensi |
| Unit tests repositori ini | **11 tes lulus di CI** | Pinout, anchor patch, FAM, build defaults, metadata, 4 image OTA dan offset packaging |
| Python syntax | **Lulus** | `py_compile` pada script utama dan tests |
| Bash syntax | **Lulus** | `bash -n` pada seluruh `.sh` |
| GitHub Actions build workflow | **Lulus** | Build firmware, packaging, upload artifact sukses pada 16 November 2026 |
| Full ESP-IDF v5.4.1 build | **Lulus GitHub Actions** | [run #43889135916](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43889135916), all steps successful |
| Flash ke N16R8 milik pengguna | **Belum diuji** | Tidak ada board fisik tersambung |
| Uji panel/tombol/microSD/Wi-Fi/BLE | **Belum diuji** | Wajib uji setelah firmware benar-benar ter-flash |

## Kriteria mengubah status

- Status build hanya menjadi **lulus** jika workflow/`idf.py` sukses dan tiga `.bin` terverifikasi.
- Status flash hanya menjadi **lulus** jika tertera esptool/IDF flash success dan board dapat boot.
- Status hardware hanya menjadi **lulus** jika ada bukti fungsi tiap periferal, bukan sekadar firmware berhasil dipasang.
- Jika ada kegagalan, simpan log dan ubah issue; jangan menyembunyikan atau menebak perbaikannya.

Proyek ini tidak mengklaim fitur hardware sudah berjalan tanpa pengujian fisik. Namun, firmware `.bin` sudah benar-benar dibangun pada GitHub Actions dan bundelnya sudah diverifikasi.

## Hasil CI pada repositori GitHub

- Repo: [gungsss/flipper-esp32s3-diy240](https://github.com/gungsss/flipper-esp32s3-diy240)
- Run pertama: [GitHub Actions #1](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43880808741) (16 November 2026).
- Hasil run pertama: **failure**. GitHub API menunjukkan durasi total sekitar 3 detik, waktu komputasi ditagih 0 ms, serta **0 langkah job tercatat** dan tidak ada log job yang dapat diunduh. Karena itu, **penyebabnya belum dapat dipastikan**, dan hasil ini **bukan bukti bahwa kompilasi source gagal**. Periksa tampilan workflow di browser (pesan runner, kebijakan Actions, billing, atau izin) sebelum mengubah source.
- **Percobaan ulang (attempt 2) juga failure.** Pada attempt 2, GitHub kembali mencatat **0 langkah job**, tanpa runner terpasang. Periksa pesan pada halaman Actions untuk mengetahui apakah ada kendala konfigurasi runner, kebijakan repo, atau status layanan; bukti yang tersedia belum cukup menetapkan penyebab.
- **Riwayat di atas telah diselesaikan.** Runner aktif kembali dan firmware `.bin` berhasil dibangun pada [run #43889135916](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43889135916). Jangan menggunakan artifact lama yang dibuat sebelum perbaikan OTA packaging.

## Diagnostik tambahan

- Pada 16 November 2026, workflow minimal `Diagnostic - Runner availability` ([run](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43883153060)) juga **failure sebelum runner dan sebelum langkah pertama**. Job ID 133354094130; `runner_name` kosong; `steps=[]`.
- Kesimpulan yang didukung: kegagalan GitHub Actions saat ini **pre-runner**, bukan error compiler. Penyebab spesifik (billing, kebijakan atau provisioning) menunggu teks GitHub Annotations.
- Script build alternatif [Windows WSL2](BUILD_WINDOWS_WSL.md) disiapkan; tidak bisa dinyatakan lulus build atau flash tanpa menjalankannya pada mesin yang memiliki ESP-IDF dan hardware.
- Pemilik akun dapat mengikuti [diagnostik CI](CI_RUNNER_DIAGNOSTICS.md) dan [issue #1](https://github.com/gungsss/flipper-esp32s3-diy240/issues/1).

## Tes runner keempat (ubuntu-slim)

[Diagnostic ubuntu-slim](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43884809095) pada 16 November 2026 juga **failure sebelum runner**: job ID `133359941563`, `runner_name` kosong, `steps=[]`, durasi ~2 detik. Empat label diuji (ubuntu-24.04, ubuntu-latest, ubuntu-22.04, ubuntu-slim), seluruhnya gagal pra-eksekusi. Dengan bukti ini, pindah image Ubuntu tidak menyelesaikan blocker saat ini.

## Laporan build sukses dan verifikasi ZIP final

- **16 November 2026:** workflow [Build DIY ESP32-S3 N16R8 — run #43889135916](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43889135916) selesai **success**: unit tests, dependensi ESP-IDF v5.4.1, source Sor3nt commit e6ec119, penerapan patch, build, validasi offset, dan upload artifact.
- Artifact resmi: `flipper-diy-s3-n16r8-st7789-240` (artifact ID `14237320018`), ZIP SHA256 Actions `cc3704208b5102546e40cd30dbd427ecf24221c527475071e828097029eb9086`.
- Pemeriksaan ZIP yang diunduh: CRC semua entri valid; `BUILD_INFO.json` berisi **empat** image, masing-masing SHA256 dan ukuran cocok. Flash args memetakan bootloader `0x0`, partition `0x8000`, app `0x10000`, dan OTA initializer `0xBF0000`.
- Header bootloader dan aplikasi mempunyai ID chip **ESP32-S3 (9)**; tabel partisi menempatkan `ota_0` pada `0x10000`, `ota_1` pada `0x600000`, dan `otadata` pada `0xBF0000` sesuai argumen flashing.
- **Belum diuji:** flashing di hardware milik pengguna, orientasi/offset ST7789, suplai backlight, navigasi keenam tombol, pembacaan SD, Wi-Fi/BLE, dan aplikasi tambahan. Status `success` pada CI **tidak menjamin hardware langsung berfungsi**.
