# Crow 🐦‍⬛

**Crow** adalah FTP Harness yang dirancang khusus untuk mempermudah asisten AI dalam mengelola file di server FTP secara aman.

## 🚀 Instalasi (Direkomendasikan)
Cara terbaik untuk menginstal Crow adalah menggunakan [pipx](https://pypa.github.io/pipx/):

```bash
pipx install .
```
*Jika kamu masih dalam tahap pengembangan dan ingin perubahan kode langsung aktif, gunakan:*
```bash
pipx install --editable .
```

Setelah diinstal, perintah `crow` akan tersedia secara global di terminal kamu tanpa perlu aktivasi virtual environment manual.

## 💡 Tips Penggunaan (Sangat Disarankan)
Agar file kamu tetap rapi, selalu **buat folder baru** untuk setiap projek FTP yang berbeda:

```bash
mkdir my-web-projek
cd my-web-projek
crow init
```
Dengan cara ini:
- Konfigurasi `.ftp-tool.json` tidak akan tertukar antar projek.
- Folder `.crow_backups/` hanya berisi cadangan untuk projek tersebut.
- AI akan lebih fokus memetakan struktur folder yang spesifik.

## 🛠️ Cara Penggunaan
Setelah menjalankan `crow init` di folder projekmu:

Perintah populer:
- `crow list /` : Lihat isi server.
- `crow map` : Buat peta struktur projek (`FTP_TREE.md`).
- `crow read file.php` : Baca isi file secara utuh.
- `crow tail error_log -n 20` : Intip 20 baris terakhir file besar.
- `crow write file.php "content"` : Update file (aman dengan backup).
- `crow edit file.php` : Edit langsung pakai editor favoritmu.

## ✨ Fitur Unggulan
- **Safeguard System**: Backup lokal otomatis & Validasi sintaks.
- **Project Mapping**: Mapping struktur folder Laravel/Besar secara instan.
- **Smart Tail**: Efisiensi membaca log besar via FTP.
- **Bulk Ops**: `pull` & `push` untuk sinkronisasi folder.

## 🛡️ Keamanan
- Kredensial disimpan di `.ftp-tool.json` (Otomatis di-ignore oleh Git).
- Backup tersimpan di folder `.crow_backups/`.

---
Dibuat dengan ❤️ untuk efisiensi koding bersama AI.
