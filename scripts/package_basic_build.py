#!/usr/bin/env python3
"""Prepare a transparently labeled test bundle from verified ESP-IDF outputs."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

root, out = map(lambda x: Path(x).resolve(), sys.argv[1:3])
here = Path(__file__).resolve().parent
subprocess.run([sys.executable, str(here / 'package_artifacts.py'), '--source', str(root),
                '--output', str(out)], check=True)
info_path = out / 'BUILD_INFO.json'
info = json.loads(info_path.read_text())
info.update({
    'lcd': 'ST7735S landscape 160x128, CS tied to ground',
    'display_driver': 'waveshare/esp_lcd_st7735==2.0.0',
    'reported_flipper_version': '1.4.3',
    'reported_esp_app_api_version': '1.0',
    'official_151_app_api_version': '88.2',
    'scope': 'ESP32 port with selected 1.5.1 core, GUI, storage, loader, CLI, RPC, USB HID, toolbox and date/time example; not a complete 1.5.1 port',
    'native_ui_profile': 'Native 160x128 home, primary menu, and selected settings lists; unsupported views retain compatibility rendering',
    'native_ui_source': 'patch/native160/integration/native160_integration_only.patch',
    'hardware_validation': 'Landscape orientation, panel colors, buttons, and SD behavior still require confirmation on the physical board',
})

native_example = root / 'build_diy/fap/example_date_time_input.fap'
if not native_example.is_file():
    raise SystemExit('Missing compiled 1.5.1 example application')
example_destination = out / 'sdcard/apps/Examples/example_date_time_input.fap'
example_destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(native_example, example_destination)
info['native_151_example'] = {
    'path': str(example_destination.relative_to(out)),
    'sha256': hashlib.sha256(example_destination.read_bytes()).hexdigest(),
    'architecture': 'Xtensa ESP32-S3',
    'application_api': 'ESP 1.0',
    'hardware_validation': 'not tested on physical device',
}

records = info['images']
intervals = []
for row in records:
    data = (out / row['file']).read_bytes()
    start = int(row['offset'], 16)
    end = start + len(data)
    if end > 16 * 1024 * 1024:
        raise SystemExit('Flash image exceeds 16 MiB')
    if row['file'] in ('bootloader/bootloader.bin', 'furi_esp32.bin'):
        if len(data) < 16 or data[0] != 0xe9 or data[12:14] != bytes((9, 0)):
            raise SystemExit(f"Image is not for ESP32-S3: {row['file']}")
    intervals.append((start, end))
intervals.sort()
if any(end > next_start for (_, end), (next_start, _) in zip(intervals, intervals[1:])):
    raise SystemExit('Overlapping flash image ranges')
info_path.write_text(json.dumps(info, indent=2) + '\n')

for old in ('FLASH.md', 'HARDWARE.md', 'INSTALL_WINDOWS.md'):
    (out / old).unlink()

manifest = {
    'name': 'ESP32-S3 ST7735S Landscape Native160 (1.5.1 compatibility preview)',
    'version': '2.0.0-st7735s-native160-151-dev.20261119',
    'new_install_prompt_erase': False,
    'builds': [{'chipFamily': 'ESP32-S3', 'parts': [
        {'path': row['file'], 'offset': int(row['offset'], 16)} for row in records
    ]}],
}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
(out / 'install.html').write_text('''<!doctype html>
<html lang="id"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Flasher ESP32-S3 ST7735S</title>
<script type="module" src="https://unpkg.com/esp-web-tools@10/dist/web/install-button.js?module"></script>
<style>body{font-family:system-ui;background:#101720;color:#edf4f4;max-width:45rem;margin:8vh auto;padding:1.5rem;line-height:1.6}button{padding:.9rem 1.3rem;font-size:1rem}p{color:#c7d3d3}</style>
<h1>Firmware ESP32-S3 ST7735S Landscape</h1><p>Home, menu utama, dan daftar pengaturan memakai tata letak native 160×128. Tampilan yang belum didukung tetap memakai render kompatibilitas.</p>
<p>Ini build pengembangan dengan sebagian perubahan 1.5.1. Versi dasar yang dilaporkan masih 1.4.3.</p>
<p>Sambungkan ESP32 menggunakan kabel USB data, tutup qFlipper/serial monitor, lalu pilih port ESP32-S3.</p>
<esp-web-install-button manifest="./manifest.json"><button slot="activate">Hubungkan dan flash</button>
<span slot="unsupported">Gunakan Chrome atau Edge di komputer.</span>
<span slot="not-allowed">Buka melalui localhost atau HTTPS.</span></esp-web-install-button></html>''')
(out / 'BACA_DULU.txt').write_text('''FIRMWARE ESP32-S3 - ST7735S LANDSCAPE / UI NATIVE 160x128

Dasar: Sor3nt ESP32 port e6ec119 (versi Flipper yang dilaporkan 1.4.3).
Build ini memakai UI native 160x128 untuk beranda, menu utama, dan daftar
pengaturan tertentu. Build juga membawa sebagian perubahan GUI, loader, CLI,
RPC, USB HID, toolbox, dan contoh tanggal/waktu dari Flipper 1.5.1. Ini BELUM
port 1.5.1 lengkap dan orientasi landscape belum diuji di papan fisik.
Versi API aplikasi ESP masih 1.0, sedangkan API resmi 1.5.1 adalah 88.2.
Aplikasi FAP resmi berbasis ARM tidak dapat langsung berjalan pada ESP32.
NFC dan modul lain yang tidak terpasang tidak menjadi target build ini.

Menjalankan flasher lokal di macOS/Windows/Linux:
1. Ekstrak seluruh isi ZIP ke satu folder.
2. Buka Terminal/PowerShell di folder tersebut, lalu jalankan:
   python3 -m http.server 8000 --bind 127.0.0.1
   Di Windows bisa memakai: py -3 -m http.server 8000 --bind 127.0.0.1
3. Buka http://127.0.0.1:8000/install.html di Chrome atau Edge.
4. Hubungkan ESP32 dengan kabel USB data, tutup qFlipper atau serial monitor,
   klik tombol flash dan pilih port ESP32-S3.

Flashing menulis ulang bootloader, tabel partisi, dan firmware. Simpan dahulu
data yang diperlukan. Jika memakai microSD, pasang kartu yang sesuai pada
modulnya sebelum memeriksa fungsi penyimpanan.

Contoh aplikasi Date/Time Input bersumber dari Flipper 1.5.1 dan dikompilasi
ulang untuk ESP32. Jika ingin mencobanya sebagai aplikasi dari microSD, salin
isi folder sdcard ke akar kartu; build dan simbolnya sudah diperiksa, tetapi
aplikasi ini belum diuji pada perangkat fisik.
''')
print('Experimental ST7735S package prepared and image headers/offsets verified.')
