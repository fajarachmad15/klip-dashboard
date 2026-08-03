# 📊 KLIP Finance Engagement Dashboard 2026

Dashboard interaktif berbasis **Streamlit** dan **Plotly** untuk monitoring dan analisis partisipasi *KLIP Engagement (CORP-FINANCE)*. 

Arsitektur sistem ini menggunakan pendekatan **Direct Ingestion dari Google Drive**, menggantikan metode browser scraping/Playwright sebelumnya sehingga proses sinkronisasi jauh lebih cepat, ringan, stabil, dan tidak memerlukan login manual / headless browser.

---

## 🏗️ Arsitektur Sistem

```
+-------------------------------------------------------------------------------+
|                        Google Drive (Cloud Storage)                           |
|  Folder ID : 1eKbKPKRtTKdnxGephe6cUTWhcSxEUMKj                               |
|  File Target: KLIP Engagement_Detail Engagement 2026_Tabel.csv                |
+-------------------------------------------------------------------------------+
                                       │
                                       │ (Unduh via gdown / Direct Link)
                                       ▼
+-------------------------------------------------------------------------------+
|                         fetch_drive_data.py                                   |
|  - Mengunduh & memvalidasi file CSV dari Google Drive                         |
|  - Menyimpan ke: ./data/klip_finance_latest.csv                               |
|  - Error handling untuk permission Google Drive (401 / Restricted Access)     |
+-------------------------------------------------------------------------------+
                                       │
                                       │ (@st.cache_data / Fast Ingestion)
                                       ▼
+-------------------------------------------------------------------------------+
|                               app.py                                          |
|  - Streamlit Dashboard Interaktif                                             |
|  - Tombol "🔄 Refresh Data dari Drive" di Sidebar                             |
|  - KPI Metric Cards (Total Karyawan, Engaged %, Non-Engaged %)                |
|  - Visualisasi Plotly: Donut Status, Bar Direktorat, Divisi, Perusahaan       |
|  - Interactive Data Table dengan Search NIK/Nama & Export CSV                 |
+-------------------------------------------------------------------------------+
```

---

## ⚙️ Persyaratan Akses Google Drive (Penting!)

Agar script dapat mengunduh file CSV secara otomatis tanpa memerlukan kredensial login akun Google:

1. Buka folder Google Drive: [https://drive.google.com/drive/folders/1eKbKPKRtTKdnxGephe6cUTWhcSxEUMKj](https://drive.google.com/drive/folders/1eKbKPKRtTKdnxGephe6cUTWhcSxEUMKj)
2. Klik kanan pada folder target -> pilih **Share** (Bagikan).
3. Pada bagian **General Access** (Akses Umum), ubah dari *Restricted* menjadi **"Anyone with the link" (Siapa saja yang memiliki link)** dengan peran **Viewer (Pelihat)**.
4. Klik **Done / Selesai**.

> 💡 **Catatan:** Jika folder belum diset menjadi publik ("Anyone with the link"), sistem akan menampilkan panduan solusi dan menyediakan opsi **Mode Data Demo (Simulasi)** agar Anda tetap dapat menjelajahi seluruh fitur visualisasi dashboard.

---

## 🚀 Instalasi & Menjalankan Aplikasi

### 1. Install Dependensi Python
Pastikan Python 3.10+ telah terpasang, lalu jalankan:

```bash
pip install -r requirements.txt
```

Dependensi minimal yang digunakan:
- `streamlit` - Framework dashboard web interaktif
- `pandas` - Pemrosesan dan manipulasi dataset tabel
- `plotly` - Visualisasi grafik interaktif modern
- `gdown` - Modul pengunduhan file/folder dari Google Drive
- `requests` - HTTP client untuk verifikasi koneksi

---

### 2. Menjalankan Dashboard Streamlit

Untuk membuka dashboard web interaktif:

```bash
streamlit run app.py
```

Dashboard akan otomatis terbuka di browser pada alamat `http://localhost:8501`.

---

### 3. Menjalankan Sinkronisasi Data Manual (Opsional)

Jika Anda ingin menguji atau mengunduh data CSV secara mandiri melalui CLI / terminal:

```bash
python fetch_drive_data.py
```

---

## 📁 Struktur Direktori Project

```
klip-dashboard/
├── data/
│   └── klip_finance_latest.csv      # File dataset CSV aktif hasil sinkronisasi
├── app.py                           # Dashboard Streamlit utama (UI, Charts, Table)
├── fetch_drive_data.py              # Script modul pengunduh Google Drive (gdown)
├── requirements.txt                 # Daftar dependensi Python minimal
└── README.md                        # Dokumentasi arsitektur dan panduan penggunaan
```

---

## 📊 Fitur Dashboard

- **Top Metric Cards**: Menampilkan ringkasan total karyawan, jumlah & persentase *Engaged*, *Non-Engaged*, dan jumlah cakupan Direktorat/Divisi.
- **Visualisasi Interaktif (Plotly)**:
  - *Donut Chart*: Proporsi partisipasi status Engagement secara keseluruhan.
  - *Horizontal Bar Chart*: Distribusi Engagement per Direktorat.
  - *Grouped Bar Chart*: Distribusi Engagement per Divisi (Top 12 Divisi).
  - *Stacked Bar Chart*: Distribusi per Perusahaan (*Company Name*).
- **Sidebar Kontrol & Dynamic Filtering**:
  - Tombol **🔄 Refresh Data dari Drive** dengan *live spinner* dan *cache invalidation*.
  - Multi-select filter untuk Direktorat, Divisi (dinamis menyesuaikan Direktorat terpilih), dan Perusahaan.
  - Filter radio status *Engaged* / *Non-Engaged*.
  - Kotak pencarian instan berdasarkan Nama Karyawan atau NIK.
- **Interactive Data Table**:
  - Tabel `st.dataframe` modern dengan progress bar untuk skor dan badge status.
  - Tombol ekspor data terfilter langsung ke file CSV lokal.
