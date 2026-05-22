# 📖 Panduan Memulai Crow v2 🐦‍⬛

Selamat datang di **Crow v2**! Versi ini dirancang untuk memberikan pengalaman coding lokal namun tersinkronisasi secara instan ke server FTP melalui sistem **Virtual Workspace**.

## 1. Persiapan
Pastikan kamu sudah menginstal Crow menggunakan perintah:
```bash
pipx install .
```

## 2. Inisialisasi Projek (Sangat Penting)

### Untuk Pengguna Baru:
```bash
mkdir projek-saya
cd projek-saya
crow init
crow workspace init --preset laravel
```

### Untuk Pengguna v1 (Upgrade):
```bash
cd folder-projek-v1
crow migrate
crow workspace init
```

Setelah `workspace init`, Crow akan membuat folder `workspace/` yang berisi **Ghost Files** (file 0kb) yang mencerminkan struktur FTP kamu.

## 3. Workflow Coding (The Watcher)
Ini adalah fitur utama v2. Kamu tidak perlu lagi upload manual.
1. Buka satu terminal, jalankan:
   ```bash
   crow watch start
   ```
2. Biarkan terminal itu menyala. Setiap kali kamu menyimpan file di dalam folder `workspace/`, Crow akan otomatis meng-upload-nya ke FTP.

## 4. Mengambil Isi File (Hydration)
Secara default, file di `workspace/` adalah 0kb. Untuk mulai mengedit, kamu perlu "menghidrasi" file tersebut:
```bash
# Ambil isi satu file
crow scan path/to/file.php --get

# Ambil satu folder (depth 1)
crow scan folder/ --get
```

## 5. Tips Cepat
- **Cek Status**: Jalankan `crow workspace status --list` untuk melihat file mana yang sudah synced atau masih skeleton.
- **TUI Mode**: Jalankan `crow browse` untuk navigasi visual dua panel.
- **Auto-Scan**: Atur folder yang ingin discan otomatis secara berkala di file `CROW.md`.

## 6. Integrasi dengan AI
Berikan file `SKILL.md` kepada asisten AI kamu (Claude/Gemini). AI akan paham cara menggunakan perintah `crow scan` untuk membantumu coding langsung di dalam folder `workspace/`.
