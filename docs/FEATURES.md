# Cakupan fitur port ESP32-S3 ST7735S

Target adalah ESP32-S3 N16R8 dengan ST7735S 160×128 landscape, microSD SPI3, dan
enam tombol. Firmware port komunitas ini dikembangkan by m4145 dari source
ESP32 berlisensi dan perubahan terpilih Flipper 1.5.1. Ini bukan firmware resmi
Flipper Zero dan tidak mengklaim kesetaraan penuh dengan semua aplikasi, HAL,
dan aksesori resmi.

| Area | Status port |
|---|---|
| UI dan navigasi | Kanvas native 160×128 1-bit. Beranda pixel-art, launcher lima baris, browser berkas, daftar pengaturan, kotak teks, keyboard teks, editor angka/byte, editor tanggal-waktu, dan submenu umum memakai area layar landscape. Semua aplikasi yang memakai API Canvas bersama dipetakan dari koordinat lama 128×64 ke panel 160×128; halaman inti yang sudah didesain native tidak terkena skala ganda. Audit source memeriksa seluruh primitive Canvas dan kedua jalur callback GUI. Pemeriksaan fisik setiap halaman tetap perlu dilakukan di board. |
| microSD / Archive | Bus SPI3 terpisah dari LCD dan radio; perlu uji pada kartu fisik. |
| Wi-Fi dan BLE | Fitur ESP32-S3 dari port; beberapa penggunaan radio bersamaan bisa berbagi resource. |
| USB HID / BadUSB | Didukung oleh port ESP32-S3; perlu uji pada perangkat target dan hanya untuk sistem yang berizin. |
| Sub-GHz | Menu dan driver CC1101 sudah ada di image tunggal; perlu modul dan sambungan pada pinout. Band serta protokol dibatasi oleh CC1101, antena, dan aturan setempat. |
| 2,4 GHz nRF24 | Menu dan driver nRF24L01+ sudah ada di image tunggal; berbagi bus radio CC1101 tetapi memakai CS dan CE sendiri. |
| NFC | Menu PN532 melalui I²C sudah ada di image tunggal; bukan front-end ST25R3916 Flipper Zero sehingga beberapa teknologi/fungsi berbeda. Parser hotel Saflok, Onity, dan VingCard dari lini 1.5.1 ikut ditambahkan. |
| BadUSB | Layout keyboard Jepang `ja-JP` tersedia di isi kartu SD, mengikuti perubahan 1.5.1. |
| Infrared | Driver RMT TX/RX sudah ada di image tunggal; LED IR, transistor/driver, dan penerima IR tetap perlu dipasang. |
| LF RFID | RDM6300 UART sudah ada di image tunggal untuk membaca ID; tidak mendukung penulisan atau emulasi. |
| iButton | Belum tersedia karena HAL iButton ESP32 belum diimplementasikan pada upstream port. |
| Speaker / audio | Tidak tersedia pada profil dasar; aplikasi yang memerlukan speaker dapat terbatas. |
| OTA Wi-Fi | Tidak direkomendasikan untuk saat ini; gunakan flashing USB dari image build yang cocok. |
| Aplikasi FAP | Aplikasi ARM Flipper Zero tidak dapat dijalankan langsung; perlu port source dan build khusus ESP32-S3. |

Semua menu modul di atas sudah disertakan dalam satu build. Hubungkan modul ke
GPIO yang ditulis pada `patch/Pinout_ESP32S3_ST7735S_160.txt`; jangan memindah
pin tanpa membuat dan membangun profil lain. Display CS terikat ke GND, jadi
bus CC1101/nRF24 tetap terpisah dari LCD dan microSD. Modul tidak otomatis
terdeteksi saat ditancapkan; buka aplikasi terkait untuk memeriksa komunikasi
setelah pemasangan.

Fitur yang tidak punya HAL setara memerlukan desain tambahan, bukan sekadar
menambah menu. iButton belum memiliki modul dan driver pengganti di rilis ini;
RDM6300 hanya pembaca sehingga tidak menggantikan penulisan/emulasi LF RFID.
Kedua batas ini dicatat supaya image tunggal tidak menyatakan dukungan yang
belum benar-benar ada.

Validasi panel landscape, warna, enam tombol, SD, dan modul tambahan masih perlu
dilakukan pada board fisik. Hasil kompilasi saja tidak menjamin seluruh menu dan
periferal berjalan di perangkat.
