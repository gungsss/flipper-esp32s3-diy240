# Security notes dan penggunaan yang bertanggung jawab

Firmware ini merupakan integrasi dari port upstream, **bukan hasil security audit yang lengkap**. Source upstream memuat fitur untuk riset radio/jaringan yang dapat disalahgunakan. Jalankan hanya pada perangkat, jaringan, dan frekuensi yang memang boleh kamu uji. Ikuti peraturan radio setempat.

## Risiko yang sudah terlihat saat inspeksi source upstream

1. **OTA HTTPS:** file `applications/main/wlan_app/wlan_fw_update.c` mengaktifkan `skip_cert_common_name_check=true` dan tidak memasang CA, sementara `sdkconfig.defaults` mengaktifkan opsi TLS insecure/skip certificate verification. Pemeriksaan project/chip/image tidak setara dengan pemeriksaan publisher/signature firmware. **Rekomendasi:** jangan menggunakan update OTA Wi-Fi sampai autentikasi firmware dan TLS dibenahi. Gunakan flash USB dari build lokal yang kamu percayai.
2. **Web Filesystem:** handler `applications/main/wlan_app/wlan_webfs.c` menyediakan endpoint list/download/upload/delete melalui HTTP. Tidak tampak autentikasi per-request dalam handler yang ditinjau. Jika fitur diaktifkan, hanya gunakan pada jaringan terisolasi, ubah password AP default, dan jangan membukanya di LAN tak terpercaya.
3. **ESP-NOW buddy:** source `buddy_firmware/main/buddy_espnow.c` mengeset peer `.encrypt = false`, dan `buddy_config.h` mengizinkan auto-accept pairing default. **Jangan mengasumsikan lalu lintas/perintah buddy autentikasi kuat.** Profil perangkat awal ini tidak memakai board buddy eksternal.
4. **Wi-Fi password:** source `components/wifi/wlan_passwords.c` menyimpan kredensial pada `/ext/wifi/<ssid>.txt` tanpa enkripsi tambahan. Lindungi microSD; jangan membagikan isi kartu atau data capture mentah.
5. **Firmware dan ekstensi dari sumber tak dikenal:** jangan flash image atau FAP yang tidak jelas asalnya. Baca [peringatan upstream](https://github.com/Sor3nt/Flipper-Zero-ESP32-Port#readme).

## Perlindungan operasional

- Jaga microSD seperti media yang dapat berisi kredensial dan capture.
- Jangan mengunggah log berisi password, SSID privat, MAC atau token ke issue publik.
- Jangan memberi Wi-Fi yang dipakai untuk file server akses langsung ke jaringan sensitif.
- Untuk sistem autentikasi penting (U2F), jangan gunakan sebagai faktor utama sebelum uji keamanan dan interoperabilitas.
- Firmware ini **tidak mengklaim secure boot / flash encryption**, dan perubahan tersebut memerlukan strategi provisioning serta pemulihan tersendiri.
- Jangan mengunduh firmware terbaru otomatis dari upstream yang mungkin ditujukan untuk board LilyGo; konfigurasi pin N16R8 DIY ini khusus.

## Model ancaman singkat

| Aset | Ancaman | Mitigasi sementara |
|---|---|---|
| Flash firmware | Image tidak sah/mismatch board | Flash lokal dari commit terpin, audit build, cek offset dan checksum |
| Isi microSD | Pencurian data/password | Batasi akses fisik, hindari kredensial sensitif |
| Server WebFS | File terbaca/berubah melalui HTTP | Jangan aktifkan pada LAN tidak tepercaya |
| ESP-NOW buddy | Paket/perintah tidak terenkripsi | Hindari pairing di lingkungan publik sampai desain keamanan diperbarui |

## Pengembangan keamanan di masa depan

Perbaikan nyata mencakup TLS certificate bundle/pinning yang valid, manifest update bertanda tangan, validasi versi/anti-rollback yang tepat, autentikasi WebFS dan pembatasan operasi file, serta pairing dan enkripsi komunikasi buddy. Fitur-fitur tersebut **belum diimplementasikan oleh patch hardware ini**.
