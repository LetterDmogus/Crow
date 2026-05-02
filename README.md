# Crow

**Crow** adalah Smart FTP Agent & Browser yang dirancang khusus untuk mempermudah asisten AI dan developer dalam mengelola file di server FTP secara aman dan visual.

<p align="center">
  <img src="logo.png" width="200" alt="Crow Logo">
</p>

Speedrun mengerjakan projek ini karena tugas sekolah mendadak menjadi cloud based coding, sebagai vibe coder, ini adalah mimpi buruk.
Jadi saya menghabiskan beberapa jam untuk mengerjakan versi awalnya, dan kemudian membuat versi browser untuk mempercepat quick edit.
Update terbaru ada 2 fitur besar, Crow Watchout dan Crow FTP Manager, habis ini kalau gak ada ide kayaknya akan fokus ke security improve aja.

## Fitur Unggulan (V1.6.0)
---
- **Visual TUI Browser**: Jalankan `crow browse` untuk membuka FTP Browser di dalam terminal. Lengkap dengan double panel system dan shorcut edit.
- **Integrated Shell**: Akses command-line penuh langsung dari dalam TUI (`:`).
- **Parallel Sessions**: Kelola banyak server/folder sekaligus dengan sistem ID (`--id`).
- **Watch-out System**: Fitur keamanan lengkap dengan local backup, versioning check, conflict detect, dan quota watch.
- **Push-Pull System**: Fitur multiple file editing agar ai bisa melakukan perubahan ke folder spesifik tanpa harus ulang download semua file.

## Instalasi Cepat
---
Gunakan [pipx](https://pypa.github.io/pipx/) untuk isolasi otomatis:

```bash
pipx install .
```

## Cara Penggunaan
---
Untuk panduan lengkap langkah demi langkah, silakan baca:
👉 **[GUIDE.md — Panduan Memulai Crow](./GUIDE.md)**

Ringkasan perintah:
1. **Setup**: `crow init` di dalam folder projekmu.
2. **TUI Mode**: `crow browse` (Sangat disarankan).
3. **Interactive Shell**: `crow shell`.

## Shortcut Keyboard (TUI Mode)
---
- **Panah**: Navigasi kursor.
- **Enter / Panah Kanan**: Masuk folder.
- **Backspace / Panah Kiri**: Keluar folder.
- **Space**: Preview isi file.
- **e**: Edit file (otomatis buka editor & upload kembali).
- **s**: Switch Panel (pindah fokus ke sidebar Sesi).
- **/**: Filter/Search nama file secara cepat.
- **:**: Masuk ke mode Crow Shell.
- **h**: Lompat ke folder root (`/`).
- **q**: Keluar aplikasi.

## Keamanan
---
- Kredensial aman di `.ftp-tool.json` (Otomatis di-ignore oleh Git).
- Backup otomatis tersimpan di folder lokal `.crow_backups/`.

---
Dibuat oleh Letter dengan menggunakan Gemini CLI + Oh-My-GeminiCLI
