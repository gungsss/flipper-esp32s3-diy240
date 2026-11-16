# Status verifikasi awal — 16 November 2026

Dokumen ini memisahkan pengujian yang berhasil dilakukan di lingkungan penyusunan proyek dari pengujian yang masih memerlukan toolchain ESP-IDF dan perangkat fisik.

| Pemeriksaan | Hasil | Cakupan |
|---|---|---|
| Penilaian struktur source upstream | **Diperiksa** | Git tree pada `e6ec11972a8e025d7ab686a6ef3016cf52360834` |
| Pengujian patch source sebelumnya | **Lulus pada fixture lokal** | Generator menghasilkan header 240×240 no-CS, SD SPI3, 6 tombol; idempotensi |
| Unit tests repositori ini | **8 tes lulus** | Pinout, anchor patch, FAM, build defaults, metadata dan offset packaging |
| Python syntax | **Lulus** | `py_compile` pada script utama dan tests |
| Bash syntax | **Lulus** | `bash -n` pada seluruh `.sh` |
| Parsing workflow GitHub Actions | **Diperiksa** | YAML dan jalur job, **belum dijalankan di repo milik pengguna** |
| Full ESP-IDF v5.4.1 build | **Belum diuji** | Tidak ada toolchain lengkap di lingkungan penyusunan |
| Flash ke N16R8 milik pengguna | **Belum diuji** | Tidak ada board fisik tersambung |
| Uji panel/tombol/microSD/Wi-Fi/BLE | **Belum diuji** | Wajib uji setelah firmware benar-benar ter-flash |

## Kriteria mengubah status

- Status build hanya menjadi **lulus** jika workflow/`idf.py` sukses dan tiga `.bin` terverifikasi.
- Status flash hanya menjadi **lulus** jika tertera esptool/IDF flash success dan board dapat boot.
- Status hardware hanya menjadi **lulus** jika ada bukti fungsi tiap periferal, bukan sekadar firmware berhasil dipasang.
- Jika ada kegagalan, simpan log dan ubah issue; jangan menyembunyikan atau menebak perbaikannya.

Proyek ini secara sengaja tidak menyertakan firmware `.bin` yang tidak pernah dibangun dan tidak mengklaim fitur sudah bekerja tanpa uji.
