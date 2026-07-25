# 📰 Scraper Berita Online Indonesia

Aplikasi Python untuk mengumpulkan artikel berita dari berbagai portal berita online Indonesia berdasarkan **keyword** dan **rentang tanggal**, lalu menyimpan hasilnya ke file **CSV** dan **TXT**.

Tersedia dua cara pakai:
- 🖥️ **Web** (`app.py`) — tampilan browser, pilih portal, lihat tabel, tombol Download CSV
- ⌨️ **Terminal / CLI** (`main.py`) — tanya-jawab di terminal

---

## 📋 Daftar Isi
- [Portal yang Didukung](#-portal-yang-didukung)
- [Persyaratan](#-persyaratan)
- [Instalasi](#-instalasi)
- [Cara Menjalankan](#-cara-menjalankan)
  - [A. Tampilan Web](#a-tampilan-web-disarankan)
  - [B. Tampilan Terminal](#b-tampilan-terminal-cli)
- [Hasil / Output](#-hasil--output)
- [Contoh Alur Lengkap](#-contoh-alur-lengkap)
- [Troubleshooting](#-troubleshooting)

---

## 📰 Portal yang Didukung

| Portal | Metode | Keterangan |
|--------|--------|------------|
| Detik.com | 🟢 Statis | Cepat & andal, ada tanggal |
| Kompas.com | 🟢 Statis | Cepat & andal, ada tanggal |
| Viva.co.id | 🟢 Statis | Cepat & andal, ada tanggal |
| AntaraNews.com | 🟢 Statis | Cepat & andal, ada tanggal |
| CNNIndonesia.com | 🟠 Browser | Perlu Chrome + Selenium (render JavaScript), tanpa tanggal |
| Liputan6.com | 🟠 Browser | Perlu Chrome + Selenium, hasil tergantung keyword |
| Tempo.co | 🟠 Browser | Perlu Chrome + Selenium, kadang kosong (situs membatasi bot) |

> **🟢 Statis** = cepat, cukup koneksi internet.
> **🟠 Browser** = perlu Google Chrome terpasang. Selenium mengunduh driver otomatis.
> Jika Chrome/Selenium tidak ada, portal 🟠 dilewati otomatis **tanpa membuat aplikasi error**.

---

## 🔧 Persyaratan

- Python 3.8+ (diuji di Python 3.12)
- Koneksi internet
- Google Chrome — **hanya** jika ingin memakai portal 🟠 (CNN, Liputan6, Tempo)

---

## 📦 Instalasi

Jalankan sekali saja di folder proyek:

```bash
cd scraper.berita.project

# 1. Buat virtual environment
python3 -m venv venv

# 2. Aktifkan virtual environment
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Install semua dependency
pip install -r requirements.txt
```

Setelah aktif, prompt terminal akan diawali `(venv)`. Selama itu kamu cukup memakai
perintah `python ...`. Jika **belum** mengaktifkan venv, ganti `python` menjadi
`venv/bin/python`.

---

## 🚀 Cara Menjalankan

### A. Tampilan Web (disarankan)

```bash
python app.py
```

Lalu buka di browser: **http://127.0.0.1:5050**

Langkah di halaman web:
1. Isi **Keyword** (contoh: `teknologi`)
2. Isi **Tanggal Mulai** dan **Tanggal Akhir**
3. Atur **Maks. artikel / situs**
4. Centang **portal** yang ingin di-scrape
5. Klik **🔍 Mulai Scraping**
6. Hasil muncul sebagai tabel → klik **⬇️ Download CSV**

> 💡 Di macOS port 5000 dipakai AirPlay, jadi aplikasi ini memakai port **5050**.
> Ganti port dengan: `PORT=8000 python app.py`
> Hentikan server dengan `Ctrl + C`.

### B. Tampilan Terminal (CLI)

```bash
python main.py
```

Aplikasi akan menanyakan 4 hal:

```
Masukkan keyword (contoh: teknologi): teknologi
Masukkan tanggal mulai (YYYY-MM-DD): 2020-01-01
Masukkan tanggal akhir (YYYY-MM-DD): 2026-12-31
Masukkan jumlah maksimum artikel per situs (default 50): 5
```

**Tanpa mengetik manual** (langsung isi lewat pipe):

```bash
printf 'teknologi\n2020-01-01\n2026-12-31\n5\n' | python main.py
```

---

## 📊 Hasil / Output

Setiap kali dijalankan, aplikasi membuat **dua file** di dalam folder `scraped_media_data/`:

| File | Isi | Kegunaan |
|------|-----|----------|
| `<keyword>_<tanggal>_<jam>.csv` | Data lengkap | Dibuka di Excel / Google Sheets / analisis data |
| `<keyword>_<tanggal>_<jam>.txt` | Daftar judul bernomor | Dibaca cepat langsung |

Contoh nama: `teknologi_20260725_111323.csv`

**Kolom pada CSV:**

| Kolom | Deskripsi |
|-------|-----------|
| `platform` | Nama portal (Detik.com, Kompas.com, dll) |
| `date` | Tanggal artikel (`N/A` jika portal 🟠 tidak menyediakan tanggal) |
| `title` | Judul artikel |
| `url` | Link artikel |
| `keyword` | Keyword yang dicari |

**Contoh isi CSV:**

```csv
platform,date,title,url,keyword
Detik.com,2026-07-24,"Lima Teknologi Kereta di RI, Ada Whoosh 350 Km/Jam",https://finance.detik.com/...,teknologi
Kompas.com,2026-07-18,Lamborghini Sebut Teknologi EV Belum Matang,https://otomotif.kompas.com/...,teknologi
Viva.co.id,2026-07-25,Yamaha Siapkan Motor Listrik Baru Pakai Teknologi Baru,https://www.viva.co.id/...,teknologi
```

---

## 🧪 Contoh Alur Lengkap

Dari nol sampai dapat CSV, lewat terminal:

```bash
# 1. Masuk folder & aktifkan venv
cd scraper.berita.project
source venv/bin/activate

# 2. Jalankan scraper (keyword "teknologi", 5 artikel/situs)
printf 'teknologi\n2020-01-01\n2026-12-31\n5\n' | python main.py

# 3. Lihat file CSV yang dihasilkan
ls scraped_media_data/

# 4. Buka isinya (macOS)
open scraped_media_data/*.csv
```

---

## 🐛 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `ModuleNotFoundError: No module named 'flask'` / `requests` | Belum install / venv belum aktif. Jalankan `pip install -r requirements.txt` |
| `Port 5050 is in use` | Ganti port: `PORT=8000 python app.py` |
| Portal 🟠 (CNN/Liputan6/Tempo) hasilnya 0 | Chrome belum terpasang, atau situs membatasi bot. Portal 🟢 tetap jalan. |
| CSV hanya berisi `No articles found` | Tidak ada artikel cocok. Coba keyword lebih umum atau perlebar rentang tanggal. |
| Tanggal artikel tampil `N/A` | Wajar untuk portal 🟠 — tanggal tidak tersedia dari hasil render. |
| Kolom `title` ada koma tapi CSV tetap rapi | Aman — judul otomatis dibungkus tanda kutip sesuai standar CSV. |

---

## ⚠️ Disclaimer

Aplikasi ini dibuat untuk tujuan **pendidikan dan penelitian**. Gunakan secara etis,
patuhi Terms of Service dan robots.txt masing-masing situs, serta jangan membebani
server portal berita secara berlebihan.
