# Publikasi firmware ke situs

Workflow `publish-web-firmware.yml` menghasilkan image yang cocok untuk `ESP Web Tools`. Sumbernya adalah artifact **firmware yang berhasil dibangun dan diperiksa** pada [GitHub Actions #43889135916](https://github.com/gungsss/flipper-esp32s3-diy240/actions/runs/43889135916).

## Mengapa harus merged binary?

Firmware ESP-IDF memiliki empat bagian:
- Bootloader: `0x0`
- Partition table: `0x8000`
- Aplikasi: `0x10000`
- OTA initializer: `0xBF0000`

Untuk web installer, [ESP Web Tools](https://esphome.github.io/esp-web-tools/) merekomendasikan **merging terlebih dahulu** dengan esptool karena browser tidak dapat mengubah header flash seperti CLI. Merge memakai `--flash_mode dio --flash_freq 80m --flash_size 16MB` sesuai flash args build.

## Alur

1. Download artifact dari run sukses (satu versi saja, dipatok).
2. Validasi 4 image, offset dan SHA256 terhadap `BUILD_INFO.json`.
3. Validasi bahwa header bootloader dan aplikasi adalah untuk ESP32-S3 (chip ID 9).
4. Merge empat image dengan `esptool==4.8.1`.
5. Periksa ukuran, header dan isi binary gabungan.
6. Tulis `web/public/firmware/manifest.json` untuk ESP Web Tools dan `release.json` dengan SHA256 merged.
7. Commit binary+manifest ke repo. Vercel melakukan deploy otomatis setelah repo ditautkan.

**Jangan edit metadata release atau binary secara manual.** Bila ingin mempublikasikan firmware versi baru, ubah sumber artifact secara sadar dan ulangi validasi untuk layout flash, kompatibilitas board, dan uji hardware.

## Keterbatasan

- Build yang sukses hanya memastikan kompilasi, bukan hasil uji hardware.
- Firmware yang dilayani secara publik dapat diunduh siapa saja; tidak ada data sensitif pada binary yang dipublikasikan.
- Flashing web memerlukan HTTPS dan Web Serial yang didukung browser/platform.
- iOS tidak mendukung flashing USB langsung melalui situs.
