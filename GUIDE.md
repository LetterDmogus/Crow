# 📖 Panduan Memulai Crow 🐦‍⬛

Selamat datang di **Crow**! Panduan ini akan membantumu melakukan setup hingga menguasai navigasi FTP hanya dalam 5 menit.

## 1. Persiapan
Pastikan kamu sudah menginstal Crow menggunakan perintah:
```bash
pipx install .
```

## 2. Inisialisasi Projek (Sangat Penting)
Agar file kamu tetap rapi, selalu buat folder baru untuk tiap website:
```bash
mkdir projek-saya
cd projek-projek
crow init
```
Ikuti petunjuk di layar untuk memasukkan Host FTP, Username, dan Password kamu.

## 3. Masuk ke Dunia Visual (TUI)
Setelah setup selesai, jalankan:
```bash
crow browse
```
Kamu akan melihat tampilan yang dibagi menjadi 3 panel. Gunakan **Panah** untuk bergerak.

## 4. Tips Cepat Menjelajah
- **Bingung di mana?** Lihat Activity Log di pojok kanan bawah.
- **Mau buka file?** Sorot file-nya, tekan `Space` untuk intip, atau tekan `e` untuk mengeditnya.
- **Cari file cepat?** Tekan `/` lalu ketik nama file.
- **Naik level?** Tekan `h` untuk langsung balik ke Root `/`.

## 5. Mengelola Banyak Sesi
Crow bisa mengingat banyak folder kerja sekaligus!
- Tekan `s` untuk pindah ke sidebar Sesi.
- Gunakan panah untuk pilih sesi lain.
- Tekan `Enter` untuk pindah folder kerja secara instan.

## 6. Integrasi dengan AI
Jika kamu menggunakan asisten AI (seperti Gemini CLI), cukup meminta ai nya untuk menjalankan:
```bash
crow skill
```
AI akan membaca instruksi tersebut dan siap membantumu mengedit file tanpa kamu perlu mengetik perintah FTP satu per satu. Jangan lupa untuk meminta AI menjalankan `crow map --refresh` tiap kali kamu membuka session baru di folder sama.
