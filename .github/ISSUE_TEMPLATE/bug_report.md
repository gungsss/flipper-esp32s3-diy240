---
name: Laporan masalah firmware / hardware
about: Laporkan masalah dengan bukti log, tanpa data sensitif.
title: "[BUG] "
labels: bug
assignees: ''
---

## Gejala
Jelaskan singkat apa yang terjadi dan apa yang seharusnya terjadi.

## Perangkat
- Board ESP32-S3: (N16R8?)
- Layar: ST7789 240×240 / 7 pin tanpa CS
- microSD: jenis, kapasitas, FAT32 atau bukan
- Tombol: mapping GPIO yang benar-benar tersambung

## Reproduksi
1. ...
2. ...

## Build
- Upstream SHA: `e6ec11972a8e025d7ab686a6ef3016cf52360834`
- Commit repositori integrasi: ...
- `idf.py --version`: ...
- GitHub Actions run: ... (jika build via Actions)

## Log serial
Lampirkan log di sini **setelah menghapus password, token, SSID dan data sensitif**.

## Foto rangkaian
Foto tanpa data pribadi. Bila backlight atau keypad belum diuji multimeter, sebutkan.
