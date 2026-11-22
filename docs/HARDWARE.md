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

## 4. Modul yang sedang diuji: CC1101 dan nRF24L01+

Kedua radio memakai bus SPI bit-bang yang terpisah. Jangan satukan kabel SCK,
MOSI, atau MISO keduanya. Daya modul diambil dari keluaran 3V3 expansion sesuai
rangkaian yang sudah dibuat; GND expansion harus tersambung ke GND ESP32-S3.
Gunakan tegangan logika 3,3 V.

| Pin modul | ESP32-S3 | Catatan |
|---|---:|---|
| **CC1101 SCK** | GPIO9 | Bus CC1101 |
| **CC1101 MOSI / SI** | GPIO10 | Bus CC1101 |
| **CC1101 MISO / SO** | GPIO21 | Bus CC1101 |
| **CC1101 CSN / CS** | **GPIO43 (pad TX)** | Pindahkan dari GPIO46 ke pin bertanda TX |
| **CC1101 GDO0** | GPIO13 | Input status radio; TFT tidak membaca jalur MISO |
| CC1101 GDO2 | — | Tidak dipakai |
| **nRF24 SCK** | GPIO41 | Bus nRF24 tersendiri |
| **nRF24 MOSI** | GPIO42 | Bus nRF24 tersendiri |
| **nRF24 MISO** | GPIO47 | Bus nRF24 tersendiri |
| **nRF24 CSN** | GPIO1 | Chip select |
| **nRF24 CE** | GPIO2 | Enable radio |
| nRF24 IRQ | — | Tidak dipakai |

Angka GPIO43 tidak dicetak di board kamu; pad bertanda `TX` adalah GPIO43.
Firmware mematikan console UART0 aplikasi agar log serial tidak mengambil alih
pin CSN itu. GPIO46 dihindari karena merupakan pin strap ESP32-S3 saat boot.
Untuk PN532, IR, dan LF RFID, pin belum dialokasikan pada build uji ini supaya
tidak berbagi GPIO dengan kedua radio.

### Urutan uji setelah flash

1. Nyalakan board dan buka **Settings → About → Module status**. Pastikan CC1101
   terbaca sebagai `detected`; halaman ini hanya melaporkan koneksi.
2. Buka aplikasi **NRF 2.4GHz**. Jika probe berhasil, masuk ke **Passive 2.4 GHz
   Survey** untuk melihat aktivitas kanal tanpa mengirim paket.
3. Buka **Sub-GHz** untuk memastikan app mengenali CC1101. Untuk uji pertama,
   gunakan layar penerimaan/spectrum saja; jangan memancarkan sinyal saat
   memeriksa sambungan.
4. Jika modul tertulis tidak terdeteksi, matikan daya lalu cek CSN, arah kabel,
   GND bersama, dan tegangan 3,3 V. Jangan mencabut kabel saat board menyala.

## 5. Sebelum dinyalakan

- Pastikan tipe layar **ST7735S 160×128** dan CS layar ke GND.
- Pastikan microSD pada SPI3: GPIO40 / 39 / 38 / 14.
- Pastikan keenam tombol active-low dan ground-nya bersama.
- Periksa label tegangan dan polaritas setiap modul.
- Pastikan CC1101 CSN sudah di pad TX/GPIO43, bukan GPIO46.
- Pastikan keenam sinyal radio cocok dengan tabel dan kedua bus tidak disatukan.
- Jangan menghubungkan keluaran 5 V ke pin ESP32-S3 atau modul radio.
