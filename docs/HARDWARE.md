# Wiring ST7735S landscape

Target dokumen ini adalah ESP32-S3 N16R8, layar ST7735S 160×128, microSD SPI
6-pin, dan keypad 6 tombol. Profil pin tetap mengikuti
`patch/Pinout_ESP32S3_ST7735S_160.txt`. Cabut USB sebelum mengubah kabel dan
gunakan logika 3,3 V.

## 1. Layar ST7735S 160×128

| Pin layar | ESP32-S3 | Fungsi |
|---|---:|---|
| GND | GND | Ground bersama |
| VCC | 3V3 | Daya layar sesuai label modul |
| SCL / SCK | GPIO12 | SPI2 clock |
| SDA / MOSI / DIN | GPIO11 | SPI2 data |
| RES / RST | GPIO16 | Reset panel |
| DC / A0 | GPIO15 | Data / command |
| CS | GND | Panel pada modul pengguna tidak memakai CS GPIO |
| BL / BLK / LED | GPIO7 atau rangkaian backlight yang sesuai | Periksa rangkaian modul sebelum disambungkan |

Jangan sambungkan CS layar ke GPIO yang dialokasikan untuk modul lain. Saat CS
terikat ke GND, layar selalu terpilih pada SPI2; karena itu CC1101 dan nRF24
menggunakan bus radio terpisah. Driver layar diatur pada 5 MHz.

## 2. microSD SPI 6-pin

Ikuti label di PCB modul, karena urutan pin dapat berbeda jika modul diputar.

| Pin microSD | ESP32-S3 | Fungsi |
|---|---:|---|
| GND | GND | Ground bersama |
| MISO | GPIO38 | Data dari kartu, SPI3 |
| CLK / SCK | GPIO40 | Clock SPI3 |
| MOSI | GPIO39 | Data ke kartu, SPI3 |
| CS | GPIO14 | Chip select SPI3 |
| 3V3 | 3V3 | Daya kartu |

Bus microSD terpisah dari LCD. Untuk awal gunakan kartu FAT32, kabel pendek, dan
pastikan semua enam sambungan terpasang.

## 3. Keypad 6 tombol

| Label PCB | ESP32-S3 | Aksi |
|---|---:|---|
| COM | GND | Ground tombol |
| UP | GPIO4 | Atas |
| DWN | GPIO5 | Bawah |
| LET | GPIO6 | Kiri |
| RHT | GPIO17 | Kanan |
| MID | GPIO8 | OK / pilih |
| SET | GPIO18 | Back / kembali |
| RST | Jangan sambungkan ke GPIO tanpa pengecekan | Reset opsional board |

Tombol aktif-rendah menggunakan pull-up internal: saat ditekan, pin ditarik ke
GND. Tidak perlu menyambungkan 3V3 ke keypad. Pastikan dengan multimeter bahwa
setiap sakelar menghubungkan label tombol ke COM saat ditekan.

## 4. Modul tambahan pada image tunggal

Firmware ST7735S universal sudah mengompilasi menu dan driver modul di bawah.
Display, microSD, dan keypad memakai sambungan yang sama seperti sebelumnya.
Untuk menambah modul, sambungkan sinyalnya ke GPIO pada tabel ini; tidak perlu
rebuild atau reflash. Board pengguna harus mengekspos pin itu dan tidak boleh
memakainya untuk rangkaian lain. Semua sinyal memakai logika 3,3 V; cek tegangan
dan kebutuhan arus modul sebelum menyalakannya.

CC1101 dan nRF24 berbagi bus radio, terpisah dari LCD CS yang terikat GND dan
microSD SPI3. Generator menolak pin bentrok dan GPIO yang dicadangkan untuk
flash, PSRAM, atau USB. Pinout image ini adalah:

| Fungsi modul | GPIO |
|---|---:|
| CC1101: SCK / MOSI / MISO / CS / GDO0 | 9 / 10 / 21 / 22 / 23 |
| nRF24: CS / CE, bus radio bersama | 24 / 25 |
| PN532: SDA / SCL | 41 / 42 |
| IR: TX / RX | 1 / 2 |
| RDM6300: UART TX / RX | 47 / 48 |

Tabel ini mengikuti firmware tunggal. Periksa skema atau label PCB ESP32-S3-mu
sebelum memasang kabel; GPIO yang tidak tersedia di board tertentu tidak dapat
digunakan meski drivernya sudah ada di image. PN532 memakai mode I²C. Modul
RDM6300 hanya memberikan fungsi baca. iButton dan fungsi tulis/emulasi LF RFID
belum memiliki padanan driver di rilis ini. Lihat
[daftar kompatibilitas modul](../variants/st7735/README.md).

## 5. Sebelum dinyalakan

- Pastikan tipe layar **ST7735S 160×128** dan CS layar ke GND.
- Pastikan microSD pada SPI3: GPIO40 / 39 / 38 / 14.
- Pastikan keenam tombol active-low dan ground-nya bersama.
- Periksa label tegangan dan polaritas setiap modul.
- Jangan memakai pin opsional hanya karena tertulis di contoh; pastikan cocok dengan board dan wiring fisik.
