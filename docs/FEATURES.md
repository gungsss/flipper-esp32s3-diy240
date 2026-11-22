# Cakupan fitur port ESP32-S3 ST7735S

Target adalah ESP32-S3 N16R8 dengan ST7735S 160×128 landscape, microSD SPI3, dan
enam tombol. Firmware port komunitas ini dikembangkan by m4145 dari source
ESP32 berlisensi dan perubahan terpilih Flipper 1.5.1. Ini bukan firmware resmi
Flipper Zero dan tidak mengklaim kesetaraan penuh dengan semua aplikasi, HAL,
dan aksesori resmi.

| Area | Status port |
|---|---|
| UI dan navigasi | Kanvas native 160×128 1-bit. Beranda pixel-art, launcher lima baris, browser berkas, daftar pengaturan, kotak teks, keyboard teks, editor angka/byte, editor tanggal-waktu, dan submenu umum memakai area layar landscape. Semua aplikasi yang memakai API Canvas bersama dipetakan ke panel 160×128; halaman native dan overlay pairing BLE memakai koordinat panel langsung. Audit source memeriksa primitive Canvas, jalur callback, dan geometri layar pairing. Pemeriksaan visual fisik tetap perlu dilakukan di board. |
| Kontrol | Tombol fisik UP/DOWN/LEFT/RIGHT dikirim sesuai label board. Profil menandai input sebagai D-pad agar keyboard, editor byte, dan panel tombol memakai arah yang semestinya; navigasi daftar tetap atas/bawah. |
| Keyboard teks | Huruf mulai lowercase. Tombol keyboard di kiri bawah berpindah ke layout simbol dengan tekan singkat; tahan OK saat tombol itu dipilih untuk mengaktifkan atau mematikan Caps Lock. Status `abc`/`CAPS`/`SYM` terlihat di bawah. |
| Pairing BLE | Kode pairing tampil pada layar penuh native 160×128, dengan kode besar dan petunjuk jelas. Tombol BACK menutup overlay kode. |
| microSD / Archive | Bus SPI3 terpisah dari LCD dan radio; perlu uji pada kartu fisik. |
| Wi-Fi dan BLE | Koneksi biasa tersedia dari port. App Wi-Fi deauth, raw-frame TX, WPS PIN, dan Bluetooth spam tidak dimasukkan di image uji ini. |
| USB HID / BadUSB | Didukung oleh port ESP32-S3; perlu uji pada perangkat target dan hanya untuk sistem yang berizin. |
| Sub-GHz | App memeriksa respons CC1101 saat dibuka dan menampilkan nama modul serta pinout jika tidak terdeteksi. Band serta protokol dibatasi oleh CC1101, antena, dan aturan setempat. |
| 2,4 GHz nRF24 | Probe mengecek baca-tulis register. Menu uji hanya menyediakan survei kanal pasif; bus SPI memakai GPIO tersendiri dari CC1101. |
| NFC | Belum diaktifkan di profil uji radio ini. PN532 bukan front-end ST25R3916 Flipper Zero sehingga kapabilitasnya berbeda. |
| BadUSB | Layout keyboard Jepang `ja-JP` tersedia di isi kartu SD, mengikuti perubahan 1.5.1. |
| Infrared | Belum diaktifkan di profil uji radio ini. |
| LF RFID | Belum diaktifkan di profil uji radio ini. RDM6300 pada port ini hanya mendukung baca; tidak untuk menulis atau emulasi. |
| iButton | Belum tersedia karena HAL iButton ESP32 belum diimplementasikan pada upstream port. |
| Speaker / audio | Tidak tersedia pada profil dasar; aplikasi yang memerlukan speaker dapat terbatas. |
| OTA Wi-Fi | Tidak direkomendasikan untuk saat ini; gunakan flashing USB dari image build yang cocok. |
| Aplikasi FAP | Aplikasi ARM Flipper Zero tidak dapat dijalankan langsung; perlu port source dan build khusus ESP32-S3. |

Build uji ini mengaktifkan CC1101 dan nRF24 saja. Hubungkan modul ke GPIO pada
`patch/Pinout_ESP32S3_ST7735S_160.txt`; jangan pindah pin tanpa membangun ulang.
Display CS terikat ke GND, microSD memakai SPI3, dan dua radio memiliki bus SPI
mandiri. CC1101 dicek saat inisialisasi; nRF24 dicek saat app dibuka. Aplikasi
nRF24 hanya menampilkan survei kanal pasif selama pemeriksaan wiring ini. Menu
Wi-Fi untuk deauth/raw-frame TX, WPS PIN adapter, Bluetooth spam, dan FAP eksternal
tidak disertakan. PN532, IR, dan LF RFID juga belum diaktifkan pada profil ini.

Fitur yang tidak punya HAL setara memerlukan desain tambahan, bukan sekadar
menambah menu. iButton belum memiliki modul dan driver pengganti di rilis ini;
RDM6300 hanya pembaca sehingga tidak menggantikan penulisan/emulasi LF RFID.
Kedua batas ini dicatat supaya image tunggal tidak menyatakan dukungan yang
belum benar-benar ada.

Validasi panel landscape, warna, enam tombol, SD, dan modul tambahan masih perlu
dilakukan pada board fisik. Hasil kompilasi saja tidak menjamin seluruh menu dan
periferal berjalan di perangkat.
