# Menerbitkan proyek ke GitHub

Gunakan **repositori baru**, bukan subfolder di repo aplikasi lain. Nama yang disarankan: `flipper-esp32s3-diy240`. Repo ini berisi patch/workflow dan **mengunduh upstream saat build**, sehingga jumlah file kecil dan riwayat sumber mudah ditelusuri.

## Metode 1 — GitHub Web + Git CLI

1. Masuk akun GitHub yang memiliki akses proyek. Buka https://github.com/new.
2. Buat repo bernama **flipper-esp32s3-diy240**, pilih **Private** bila hanya untuk eksperimen pribadi; atau **Public** bila ingin dibagikan.
3. **Jangan** centang *Initialize with README*, `.gitignore`, atau license; semua sudah disiapkan di proyek ini.
4. Dari terminal Mac, masuk ke folder yang berisi `README.md`, `patch/`, `docs/`, dan `.github/`:

   ```bash
   git init -b main
   git add README.md .gitignore .gitattributes patch scripts docs tests .github
   git commit -m "Add ESP32-S3 N16R8 DIY firmware integration and docs"
   git remote add origin https://github.com/gungsss/flipper-esp32s3-diy240.git
   git push -u origin main
   ```

   Jika Git menolak autentikasi HTTPS, gunakan `gh auth login` atau Git Credential Manager.

5. Buka tab **Actions** di repo, pilih workflow **Build DIY ESP32-S3 N16R8**, jalankan `Run workflow` dan lihat hasilnya.
6. Jika workflow sukses, unduh ZIP artifact, lalu ikuti [FLASH.md](FLASH.md).

## Metode 2 — GitHub CLI satu perintah

Jika `gh` sudah terpasang dan login di Mac (`gh auth login`), dari folder proyek:

```bash
git init -b main
git add .
git commit -m "Initial ESP32-S3 DIY firmware integration"
gh repo create flipper-esp32s3-diy240 --private --source . --remote origin --push
```

Ganti `--private` menjadi `--public` jika kamu memang ingin membagikannya. Jangan gunakan nama repositori yang sudah ada/berisi proyek berbeda.

## Yang harus ada sesudah publikasi

- `README.md` muncul sebagai halaman depan proyek.
- `.github/workflows/build.yml` ada dan GitHub Actions bisa dijalankan.
- Folder `docs/` memuat wiring, instalasi Mac, flash, penggunaan awal, dan troubleshooting.
- `patch/` berisi patch dan pinout; **jangan** mengunggah `.work/upstream` atau file `.bin` hasil build lewat commit source.
- Workflow melaporkan apakah build benar-benar sukses sebelum artifact tersedia.

## Catatan jika proses GitHub dikerjakan lewat koneksi ChatGPT

Koneksi GitHub yang hanya menyediakan baca/tulis file **tidak selalu mengizinkan pembuatan repositori/fork**. Dalam kasus seperti itu, buat repo kosong dulu lewat GitHub web, lalu file proyek bisa diunggah ke repo khusus tersebut. Jangan meminta penimpaan repo yang sudah berisi karya lain.
