# Crow 🐦‍⬛

**Crow** adalah FTP Harness yang dirancang khusus untuk mempermudah asisten AI (seperti Gemini CLI atau Claude Code) dalam mengelola file di server FTP secara aman.

## ✨ Fitur Utama
- **Modular Arsitektur**: Kode bersih dan mudah dikembangkan.
- **Safeguard System**: Backup lokal otomatis sebelum menulis/menghapus file.
- **Syntax Validation**: Mencegah upload kode Python/PHP yang error secara sintaks.
- **Project Mapping**: Fitur `map` untuk memahami struktur projek Laravel/Besar dalam sekejap.
- **Smart Tail**: Mengintip bagian akhir file besar tanpa mendownload seluruh isinya.
- **Bulk Ops**: Dukungan `pull` dan `push` untuk sinkronisasi folder (Power User).

## 🚀 Instalasi Cepat
1. Clone repository ini.
2. Buat virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   ```
3. Install secara editable:
   ```bash
   pip install -e .
   ```

## 🛠️ Cara Penggunaan
Setup pertama kali:
```bash
crow init
```

Perintah populer:
- `crow list /` : Lihat isi server.
- `crow map` : Buat peta struktur projek (`FTP_TREE.md`).
- `crow read file.php` : Baca isi file secara utuh.
- `crow tail error_log -n 20` : Intip 20 baris terakhir dari file besar.
- `crow write file.php "content"` : Update file (aman dengan backup).
- `crow edit file.php` : Edit langsung pakai editor favoritmu.

## 🛡️ Keamanan
- Kredensial disimpan di `.ftp-tool.json` (Otomatis di-ignore oleh Git).
- Backup tersimpan di folder `.crow_backups/`.

---
Dibuat dengan ❤️ untuk efisiensi koding bersama AI.
