# Changelog

## 0.1.0 — 2026-11-16

- Profil ESP32-S3 N16R8 dan TFT ST7789 240×240 7-pin tanpa CS.
- microSD lewat SPI3 terpisah dan keypad active-low 6 tombol.
- Integrasi source pin ke upstream commit e6ec11972a8e025d7ab686a6ef3016cf52360834.
- Script build/flash macOS, workflow GitHub Actions, packaging artifact dan unit tests.
- Dokumentasi perakitan, instalasi, flash, penggunaan pertama, keamanan, dan troubleshooting.

**Status:** integrasi source; belum ada klaim firmware berhasil build/flash pada hardware pengguna.

- Added a Windows WSL2 local-build fallback for environments with GitHub Actions runner allocation failures.
- Added pre-runner CI failure evidence and a diagnostic workflow for support escalation.
