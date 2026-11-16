# Perakitan hardware dan wiring

Dokumen ini khusus untuk **ESP32-S3 N16R8 (16 MB flash/8 MB PSRAM)** dengan layar ST7789 240×240 **7 pin tanpa CS**, pembaca microSD SPI 6 pin, dan PCB keypad dengan label `COM UP DWN LET RHT MID SET RST`.

> **Perhatian:** foto board ESP32-S3 menunjukkan tulisan N16R8. Namun jenis rangkaian **BLK**, variasi ST7789, dan jalur internal PCB keypad belum diverifikasi dengan multimeter. Semua sambungan dilakukan **ketika daya USB dicabut**. Gunakan logika **3,3 V**. Jangan memakai 5 V pada modul yang hanya diberi label 3V3.

## 1. TFT ST7789 240×240 (7 pin)

| Dari layar | Ke ESP32-S3 | Fungsi |
|---|---|---|
| `GND` | `GND` | Ground |
| `VCC` | `3V3` | Catu daya 3,3 V |
| `SCL` / `SCK` | **GPIO12** | SPI2 clock |
| `SDA` / `DIN` | **GPIO11** | SPI2 MOSI (bukan I²C SDA) |
| `RES` / `RST` | **GPIO16** | Reset LCD |
| `DC` / `A0` | **GPIO15** | Data/command |
| `BLK` / `LED` | Lihat **Backlight** | Jangan asal sambung GPIO |

**Tidak ada pin CS** pada modul. Driver `esp_lcd` diatur dengan `cs_gpio_num = -1`; SPI2 digunakan **khusus layar**. GPIO13 disiapkan pada konfigurasi SPI2 sebagai MISO tetapi **tidak perlu disambungkan ke TFT**.

### Backlight (BLK)

BLK pada modul ST7789 7-pin dapat berupa masukan kontrol atau sambungan LED backlight; implementasinya tidak seragam. Opsi:

- Jika datasheet/hasil pemeriksaan memastikan BLK merupakan **input yang aman diberi 3,3 V** dan sudah ada resistor/rangkaian penggeraknya, hubungkan ke **3V3** agar lampu terus menyala. Dalam mode ini, **GPIO7 tidak disambung** dan pengaturan brightness fisik tidak efektif.
- Jika backlight memerlukan arus lebih besar, gunakan **MOSFET/transistor driver yang sesuai** dikendalikan PWM GPIO7, dengan resistor dan suplai backlight sesuai spesifikasi modul. **Jangan langsung menghubungkan beban LED mentah ke GPIO7**.
- Jangan memberi tegangan pada BLK sebelum tahu spesifikasinya; kondisi awal panel bisa blank karena backlight belum dinyalakan.

Driver memperlakukan pin GPIO7 sebagai PWM aktif-high. Jika memilih GPIO7 sebagai input BLK berimpedansi tinggi, pastikan memang kompatibel dengan logika 3,3 V.

## 2. MicroSD SPI (modul biru 6 pin)

**Baca tulisan di PCB, bukan posisi kanan/kiri ketika modul dibalik**. Pengguna menyebut label dari kanan ke kiri: `GND, MISO, CLK, MOSI, CS, 3V3`.

| Dari microSD | Ke ESP32-S3 | Fungsi |
|---|---|---|
| `GND` | `GND` | Ground |
| `MISO` | **GPIO38** | SPI3 data dari kartu |
| `CLK` / `SCK` | **GPIO40** | SPI3 clock |
| `MOSI` | **GPIO39** | SPI3 data menuju kartu |
| `CS` | **GPIO14** | SPI3 chip-select |
| `3V3` | `3V3` | Daya 3,3 V |

MicroSD menggunakan `SPI3_HOST` dengan frekuensi awal 10 MHz. Keenam kabel di tabel wajib dihubungkan. **Tidak cukup hanya MISO/CLK/MOSI**. Untuk percobaan pertama gunakan microSD **FAT32**, kabel pendek, sambungan ground baik, dan bukan exFAT.

## 3. PCB keypad hijau (6 tombol)

| Label PCB | Ke ESP32-S3 | Aksi |
|---|---|---|
| `COM` | `GND` | Ground bersama semua sakelar |
| `UP` | **GPIO4** | Atas |
| `DWN` | **GPIO5** | Bawah |
| `LET` | **GPIO6** | Kiri |
| `RHT` | **GPIO17** | Kanan |
| `MID` | **GPIO8** | OK / pilih |
| `SET` | **GPIO18** | Back / kembali |
| `RST` | **Biarkan tidak tersambung** | Reset opsional setelah uji multimeter |

GPIO input menggunakan internal pull-up dan tombol **active-low** (ditekan → GND). Tidak perlu menghubungkan 3V3 ke keypad. GPIO0 sengaja dihindari untuk mencegah mode download tak sengaja pada saat boot.

**Sebelum menyalakan:** dengan multimeter mode kontinuitas, pastikan setiap tombol ketika ditekan menghubungkan labelnya ke COM. Lihat juga tombol `RST`: **jangan otomatis menghubungkan RST ke 3V3 atau GPIO0**. Jika benar merupakan tombol sakelar ke COM, baru bisa mempertimbangkan RST → EN (reset aktif-rendah) sesuai rangkaian board, setelah diverifikasi.

## 4. Peta wiring total

```text
                        ┌─────────────────────────────┐
        3V3 ────────────┤ ESP32-S3 N16R8             │
        GND ────────────┤ semua GND                  │
                        │                             │
   TFT SCL ── GPIO12 ◀──┤ SPI2 CLK                    │
   TFT SDA ── GPIO11 ◀──┤ SPI2 MOSI                   │
   TFT RES ── GPIO16 ◀──┤ TFT RESET                   │
   TFT DC  ── GPIO15 ◀──┤ TFT DC                      │
   TFT BLK ── (3V3 jika sudah diverifikasi; opsional driver PWM GPIO7)
                        │                             │
    SD CLK ── GPIO40 ◀──┤ SPI3 CLK                    │
   SD MOSI ── GPIO39 ◀──┤ SPI3 MOSI                   │
   SD MISO ── GPIO38 ◀──┤ SPI3 MISO                   │
     SD CS ── GPIO14 ◀──┤ SPI3 CS                     │
                        │                             │
   Key UP  ── GPIO4  ◀──┤ Active-low buttons          │
   Key DWN ── GPIO5  ◀──┤                             │
   Key LET ── GPIO6  ◀──┤                             │
   Key RHT ── GPIO17 ◀──┤                             │
   Key MID ── GPIO8  ◀──┤                             │
   Key SET ── GPIO18 ◀──┤                             │
   Key COM ── GND    ◀──┤                             │
                        └─────────────────────────────┘
```

**Pin belum digunakan:** GPIO0 (strapping boot), GPIO19–20 (USB internal), GPIO26–37 (flash/PSRAM pada N16R8), GPIO43–44 (UART), GPIO45–46 (strapping). Jangan mengubah pinout tanpa memeriksa batasan modul fisik.

## 5. Checklist sebelum kabel USB dipasang

- [ ] Tulisan pin TFT sudah dicek satu per satu, termasuk apakah ada `CS` tersembunyi.
- [ ] Semua komponen menggunakan 3,3 V yang sesuai, tidak ada 5 V keliru.
- [ ] Ground TFT, SD, tombol, dan ESP32 terhubung bersama.
- [ ] TFT dan microSD benar-benar pada bus SPI yang **berbeda**.
- [ ] Tidak ada sambungan GPIO langsung ke LED backlight berarus besar.
- [ ] Semua 6 pin microSD terpasang dan kartu FAT32 sudah disiapkan.
- [ ] Tombol COM diuji sebagai common yang terhubung ke tombol ketika ditekan.
- [ ] Tidak ada korsleting 3V3 ke GND; kabel cukup pendek.
- [ ] Board ESP32-S3 dihubungkan USB hanya **setelah** rangkaian diperiksa.

## 6. Risiko catu daya

LCD backlight, microSD, dan Wi-Fi ESP32-S3 bisa menarik arus sesaat cukup besar. Jika terjadi reset berulang/brownout, evaluasi suplai 3,3 V dan kabel USB; **jangan menonaktifkan brownout detector sebagai solusi pertama**.
