# Scraper Berita Online Indonesia

Aplikasi Python untuk mengumpulkan dan menganalisis artikel berita dari berbagai portal berita online Indonesia berdasarkan keyword tertentu dan periode waktu yang ditentukan.

## 📋 Daftar Isi
- [Fitur Utama](#fitur-utama)
- [Portal Berita Terdukung](#portal-berita-terdukung)
- [Persyaratan Sistem](#persyaratan-sistem)
- [Instalasi](#instalasi)
- [Cara Penggunaan](#cara-penggunaan)
- [Struktur Data Output](#struktur-data-output)
- [Konfigurasi](#konfigurasi)
- [Troubleshooting](#troubleshooting)
- [Lisensi](#lisensi)

## ✨ Fitur Utama

- **Multi-Platform Scraping**: Mengumpulkan artikel dari 7 portal berita online terkemuka secara bersamaan
- **Filter Berdasarkan Keyword**: Cari artikel yang relevan dengan keyword tertentu
- **Filter Berdasarkan Tanggal**: Tentukan rentang waktu untuk pencarian artikel
- **Export CSV**: Simpan hasil scraping dalam format CSV untuk analisis lebih lanjut
- **Error Handling**: Penanganan error yang robust untuk stabilitas aplikasi
- **User-Agent Rotation**: Mencegah pemblokiran dengan menggunakan User-Agent yang tepat
- **Retry Mechanism**: Retry otomatis untuk koneksi yang gagal
- **Random Delay**: Jeda acak antar request untuk menghindari rate limiting

## 📰 Portal Berita Terdukung

Aplikasi ini dapat mengekstrak artikel dari:

1. **Detik.com** - Portal berita terlengkap Indonesia
2. **Kompas.com** - Media online terkemuka
3. **CNNIndonesia.com** - Berita utama nasional
4. **Tempo.co** - Berita investigatif
5. **Liputan6.com** - Berita terpercaya Indonesia
6. **Viva.co.id** - Portal multimedia
7. **AntaraNews.com** - Agensi berita resmi

## 🔧 Persyaratan Sistem

- Python 3.8 atau lebih tinggi
- pip (Python Package Manager)
- Koneksi internet yang stabil
- RAM minimal 2GB

### Dependencies

```
requests==2.31.0
beautifulsoup4==4.12.0
pandas==2.0.0
selenium==4.10.0
webdriver-manager==3.9.1
urllib3==2.0.0
```

## 📦 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/scraper.berita.project.git
cd scraper.berita.project-main
```

### 2. Buat Virtual Environment (Opsional tapi Disarankan)

```bash
# Untuk Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Untuk Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Atau install secara manual:

```bash
pip install requests beautifulsoup4 pandas selenium webdriver-manager urllib3
```

## 🚀 Cara Penggunaan

### Cara Paling Mudah

1. Jalankan script dengan command:
```bash
python main.py
```

2. Aplikasi akan meminta input:
   - **Keyword**: Kata kunci berita yang ingin dicari (contoh: `teknologi`, `sosial media`, `kesehatan`)
   - **Tanggal Mulai**: Format YYYY-MM-DD (contoh: `2024-01-01`)
   - **Tanggal Akhir**: Format YYYY-MM-DD (contoh: `2024-12-31`)
   - **Jumlah Maksimum Artikel**: Jumlah artikel per situs (default: 50, tekan Enter untuk skip)

### Contoh Sesi Interaktif

```
Masukkan keyword (contoh: teknologi): artificial intelligence
Masukkan tanggal mulai (YYYY-MM-DD): 2024-01-01
Masukkan tanggal akhir (YYYY-MM-DD): 2024-12-31
Masukkan jumlah maksimum artikel per situs (default 50): 100
```

### Output

Program akan menghasilkan:
- File CSV dengan nama format: `scraped_media_<keyword>_YYYYMMDD_HHMMSS.csv`
- File disimpan dalam folder: `scraped_media_data/`
- Log output menampilkan progress scraping di terminal

## 📊 Struktur Data Output

File CSV yang dihasilkan memiliki kolom berikut:

| Kolom | Tipe | Deskripsi |
|-------|------|-----------|
| `platform` | String | Nama portal berita (Detik.com, Kompas.com, dll) |
| `date` | Date | Tanggal artikel dipublikasikan |
| `title` | String | Judul artikel |
| `url` | String | Link URL artikel lengkap |
| `keyword` | String | Keyword yang digunakan untuk pencarian |

### Contoh Data CSV

```csv
platform,date,title,url,keyword
Detik.com,2024-06-15,Perkembangan AI Terbaru di Industri Tech,https://www.detik.com/...,artificial intelligence
Kompas.com,2024-06-14,ChatGPT Mendapat Update Baru,https://www.kompas.com/...,artificial intelligence
CNNIndonesia.com,2024-06-13,Regulasi AI di Indonesia,https://www.cnnindonesia.com/...,artificial intelligence
```

## ⚙️ Konfigurasi

### Mengubah User-Agent

Untuk mengganti User-Agent, edit bagian di `OnlineMediaScraper.__init__()`:

```python
self.headers = {
    'User-Agent': 'Ganti dengan User-Agent yang diinginkan',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}
```

### Mengubah Timeout

Default timeout adalah 10-15 detik. Untuk mengubahnya, ubah parameter `timeout` di setiap method `requests.get()`.

### Mengubah Delay Antar Request

Delay default adalah 1-3 detik secara random. Untuk mengubahnya:

```python
time.sleep(random.uniform(2, 5))  # Ubah 2 dan 5 sesuai kebutuhan
```

## 🐛 Troubleshooting

### 1. "ModuleNotFoundError: No module named 'requests'"
**Solusi**: Install dependencies dengan `pip install -r requirements.txt`

### 2. "Tidak ada artikel yang ditemukan"
**Kemungkinan Penyebab**:
- Website portal berita telah mengubah struktur HTML
- Keyword terlalu spesifik atau tidak relevan
- Tanggal yang dicari tidak memiliki artikel
- IP Anda diblokir oleh website

**Solusi**:
- Coba keyword yang lebih umum
- Periksa apakah website dapat diakses di browser
- Tunggu beberapa jam sebelum mencoba lagi
- Gunakan VPN jika diperlukan

### 3. "ConnectionError: Max retries exceeded"
**Solusi**:
- Periksa koneksi internet
- Tunggu beberapa detik dan coba lagi
- Website mungkin sedang down, coba nanti

### 4. "TimeoutError"
**Solusi**:
- Naikkan nilai timeout di parameter `timeout=15` menjadi lebih besar
- Periksa kecepatan koneksi internet

### 5. File CSV kosong atau hanya placeholder
**Penyebab**: Website telah memblokir atau mengubah struktur HTML mereka
**Solusi**:
- Update class selectors di method scraping
- Cek HTML structure website menggunakan browser developer tools
- Hubungi maintainer untuk update

## 📝 Catatan Penting

- **Robots.txt Compliance**: Pastikan scraping tidak melanggar robots.txt dari masing-masing website
- **Rate Limiting**: Aplikasi sudah dilengkapi delay untuk menghindari rate limiting
- **Terms of Service**: Periksa Terms of Service masing-masing website
- **Penggunaan Etis**: Gunakan data hanya untuk keperluan yang sah dan etis
- **Data Privacy**: Jaga privasi dan jangan publikasikan data pribadi

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan:

1. Fork repository ini
2. Buat branch fitur (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buka Pull Request

## ⚖️ Lisensi

Proyek ini dilisensikan di bawah MIT License - lihat file LICENSE untuk detail.

## 📧 Kontak & Support

Jika Anda memiliki pertanyaan atau menemukan bug:
- Buka issue di GitHub
- Hubungi melalui email di: your-email@example.com

## 🔍 Changelog

### v1.0.0 (2024)
- Release awal
- Support 7 portal berita online
- Export CSV functionality
- Multi-threaded scraping capability

## ⚠️ Disclaimer

Aplikasi ini dibuat hanya untuk tujuan pendidikan dan penelitian. Pengguna bertanggung jawab atas penggunaan aplikasi ini sesuai dengan hukum dan regulasi yang berlaku di yurisdiksi mereka.
