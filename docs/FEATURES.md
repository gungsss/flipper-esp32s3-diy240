# Cakupan fitur port ESP32-S3 ST7735S

Target utama adalah ESP32-S3 N16R8 dengan ST7735S 160×128 landscape, microSD
SPI3, dan enam tombol. Source ini menggabungkan port ESP32 yang ada dengan
pilihan perubahan dari Flipper 1.5.1. Ini bukan firmware resmi Flipper Zero dan
belum memiliki kesetaraan penuh dengan semua aplikasi, HAL, dan aksesori resmi.

| Area | Status port |
|---|---|
| UI dan navigasi | Kanvas native 160×128 1-bit; layar beranda, daftar aplikasi, dan submenu umum diatur ulang agar memakai panel penuh tanpa pembesaran gambar 128×64. Sejumlah aplikasi dengan koordinat tetap masih dapat tampil dalam tata letak 128×64. |
| microSD / Archive | Bus SPI3 terpisah dari LCD dan radio; perlu uji pada kartu fisik. |
| Wi-Fi dan BLE | Fitur ESP32-S3 dari port; beberapa penggunaan radio bersamaan bisa berbagi resource. |
| USB HID / BadUSB | Didukung oleh port ESP32-S3; perlu uji pada perangkat target dan hanya untuk sistem yang berizin. |
| Sub-GHz | Opsional dengan CC1101 dan dedicated bit-bang SPI. Menu baru dibangun saat pinout modul lengkap. |
| 2,4 GHz nRF24 | Opsional, berbagi bus radio CC1101 tetapi memakai CS dan CE sendiri. |
| NFC | Opsional dengan PN532 melalui I²C; berbeda dari front-end ST25R3916 pada Flipper Zero. |
| Infrared | Opsional dengan pin TX dan RX untuk driver RMT. |
| LF RFID | RDM6300 melalui UART, hanya pembacaan; tidak menyediakan penulisan dan emulasi native. |
| iButton | Belum tersedia karena HAL iButton ESP32 belum diimplementasikan pada upstream port. |
| Speaker / audio | Tidak tersedia pada profil dasar; aplikasi yang memerlukan speaker dapat terbatas. |
| OTA Wi-Fi | Tidak direkomendasikan untuk saat ini; gunakan flashing USB dari image build yang cocok. |

Modul tambahan harus dipilih melalui file pinout dan firmware perlu dibangun
ulang setelah pinout diubah. Modul tidak otomatis terdeteksi hanya karena
dicolokkan. Jangan mengaktifkan flag board secara manual: aplikasi hanya
dimasukkan saat generator menemukan pin lengkap, dan bus CC1101/nRF24 harus
tetap terpisah dari layar ST7735 yang CS-nya terikat ke GND serta dari microSD.
Profil inti berada di `patch/Pinout_ESP32S3_ST7735S_160.txt`; contoh profil untuk
menyiapkan menu seluruh modul ada di
`patch/Pinout_ESP32S3_ST7735S_160_all_modules.example.txt`. Pin contoh harus
dicocokkan dengan board fisik sebelum dipakai.

Validasi panel landscape, warna, enam tombol, SD, dan modul tambahan masih perlu
dilakukan pada board fisik. Hasil kompilasi saja tidak menjamin seluruh menu dan
periferal berjalan di perangkat.
