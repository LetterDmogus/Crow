# Design Spec: Crow v2 — Virtual Workspace & Watching Agent

**Status:** Draft / Approved
**Date:** 2026-05-07
**Author:** Gemini CLI (as Crow Architect)

## 1. Vision & Purpose
Transisi Crow dari sekadar "FTP Tool" menjadi "Virtual Workspace" yang memungkinkan developer bekerja secara lokal dengan struktur FTP yang dicerminkan (mirip dengan *cloud-based IDE experience* namun di terminal lokal).

## 2. Core Components

### 2.1 Virtual Workspace (The Foundation)
- **Concept**: Menggunakan **Ghost Files** (file 0kb) untuk mencerminkan struktur folder FTP tanpa harus mendownload seluruh isinya di awal.
- **Manifest-Centric Architecture (Opsi A)**:
  - File utama: `.crow-manifest.json`.
  - Fungsi: Menyimpan *state* sinkronisasi, *checksum* (lokal & remote), dan metadata file.
  - **Status File**:
    - `synced`: Lokal & Remote identik.
    - `skeleton`: File ada di lokal (0kb), isi hanya di server.
    - `untracked`: File baru di lokal, belum ada di server.
    - `modified`: Perubahan lokal siap di-push.
    - `outdated`: Perubahan server perlu di-pull.
- **Preset System**:
  - `laravel`: Otomatis mengabaikan (total ignore) folder berat seperti `vendor/`, `node_modules/`, `storage/`, dan `.git/`.

### 2.2 Crow Watching Agent (The "Live Sync")
- **Mechanism**: Menjalankan proses `watchdog` di terminal terpisah.
- **Workflow**:
  - Deteksi perubahan lokal -> Auto-push jika file sudah ter-track.
  - Deteksi file baru/hapus -> **Staging Mode** (Tanya `y/n` di terminal watcher).
  - **Loop Prevention**: Menandai sesi upload agar watcher tidak mendeteksi perubahan yang ia buat sendiri.

### 2.3 Concurrency & Queue Management
- **Mechanism**: Menggunakan file lock `.crow.lock`.
- **Queue Mode (Opsi B)**:
  - Jika dua perintah berjalan bersamaan (misal: Watcher sedang upload, user jalankan `crow push`), perintah kedua akan masuk ke antrian (**Pending**).
  - Sistem akan memberikan **Alert** di terminal utama bahwa proses sedang menunggu antrian tanpa menghentikan eksekusi.

## 3. Command Specifications

### 3.1 Workspace Management
- `crow workspace init [--preset Name]`: Inisialisasi workspace baru, scan FTP, buat ghost files, generate manifest.
- `crow workspace status`: Menampilkan statistik file (berapa yang synced, skeleton, dll).
- `crow workspace sync`: Sinkronisasi paksa antara manifest dengan server.

### 3.2 Watcher Control
- `crow watch start`: Menjalankan agent di *background* atau terminal aktif.
- `crow watch stop`: Menghentikan agent.
- `crow watch logs`: Melihat aktifitas sinkronisasi secara real-time.

### 3.3 Migration
- `crow migrate`: Mengimpor kredensial dari `.ftp-tool.json` (v1) dan membangun manifest awal berdasarkan file lokal yang sudah ada.

## 4. Security & Safety Guards
- **No YOLO by Default**: Semua file baru dan penghapusan memerlukan konfirmasi manual.
- **Conflict Guard**: Sebelum auto-sync, watcher melakukan pengecekan `remote_mtime`. Jika server lebih baru, proses dihentikan dan user diminta melakukan `pull`.
- **Ignore Rules**: Dukungan file `.crowignore` untuk kustomisasi folder yang tidak ingin masuk workspace.

## 5. Technical Stack
- **Language**: Python 3.8+
- **Libraries**:
  - `watchdog`: Untuk file system monitoring.
  - `rich`: Untuk tampilan terminal dan alert.
  - `ftplib` / `pysftp`: Core FTP communication.
  - `json`: Manifest management.

---

## Self-Review Check
- [x] **Placeholder Scan**: Tidak ada TBD/TODO yang menggantung.
- [x] **Internal Consistency**: Mekanisme Queue (Opsi B) konsisten dengan sistem Locking.
- [x] **Scope Check**: Fokus pada Workspace & Watcher, fitur Merge ditunda sesuai permintaan.
- [x] **Ambiguity Check**: Status file didefinisikan dengan jelas.
