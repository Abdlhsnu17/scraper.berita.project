import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import urllib.parse
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Peta nama bulan Bahasa Indonesia -> nomor bulan, untuk parsing tanggal artikel.
BULAN_ID = {
    'januari': 1, 'februari': 2, 'maret': 3, 'april': 4, 'mei': 5, 'juni': 6,
    'juli': 7, 'agustus': 8, 'september': 9, 'oktober': 10, 'november': 11, 'desember': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7,
    'agu': 8, 'agt': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'des': 12,
}


def parse_tanggal_id(date_str):
    """Coba parse string tanggal Indonesia (mis. '18 Juli 2026', '18 Jul 2026, 09:00 WIB',
    atau waktu relatif '2 jam lalu'). Mengembalikan objek datetime atau None jika gagal."""
    if not date_str:
        return None
    import re
    from datetime import timedelta
    s = date_str.strip()

    # Waktu relatif: "5 menit lalu", "2 jam lalu", "3 hari lalu", "1 minggu lalu".
    rel = re.search(r'(\d+)\s*(menit|jam|hari|minggu|bulan)\s+lalu', s.lower())
    if rel:
        n = int(rel.group(1))
        satuan = {'menit': timedelta(minutes=n), 'jam': timedelta(hours=n),
                  'hari': timedelta(days=n), 'minggu': timedelta(weeks=n),
                  'bulan': timedelta(days=30 * n)}
        return datetime.now() - satuan[rel.group(2)]
    # Ambil pola: <hari> <nama_bulan> <tahun> dengan jam opsional.
    m = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})(?:[,\s]+(\d{1,2})[:.](\d{2}))?', s)
    if m:
        hari, nama_bulan, tahun = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        bulan = BULAN_ID.get(nama_bulan)
        if bulan:
            jam = int(m.group(4)) if m.group(4) else 0
            menit = int(m.group(5)) if m.group(5) else 0
            try:
                return datetime(tahun, bulan, hari, jam, menit)
            except ValueError:
                return None
    # Fallback: format numerik dd/mm/YYYY.
    for fmt in ('%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


class OnlineMediaScraper:
    def __init__(self):
        self.data = []
        self.output_dir = "scraped_media_data"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        self.data = []
        # Set URL yang sudah dikumpulkan, untuk membuang duplikat antar-portal.
        self.seen_urls = set()

    # Kata umum yang diabaikan saat mencocokkan relevansi keyword.
    STOPWORDS = {
        'di', 'ke', 'dari', 'dan', 'atau', 'yang', 'untuk', 'pada', 'dengan',
        'the', 'a', 'an', 'of', 'in', 'on', 'for', 'to',
    }

    @staticmethod
    def _tokenize(text):
        """Pecah teks menjadi token kata (huruf/angka) dalam huruf kecil."""
        import re
        return [t for t in re.findall(r'\w+', text.lower()) if len(t) > 1]

    def relevance(self, title, keyword):
        """Skor relevansi judul terhadap keyword (0..1). Mengembalikan None bila TIDAK
        relevan (mensyaratkan semua kata penting keyword muncul di judul), sehingga
        judul yang cuma menyerempet keyword tidak ikut terjaring."""
        title_lower = title.lower()
        keyword_lower = keyword.lower().strip()
        if not keyword_lower:
            return 0.0
        # Kecocokan frasa persis = paling relevan.
        if keyword_lower in title_lower:
            return 1.0
        kw_tokens = [t for t in self._tokenize(keyword) if t not in self.STOPWORDS]
        if not kw_tokens:
            # Keyword hanya berisi stopword -> jatuh ke pencocokan substring biasa.
            return 1.0 if keyword_lower in title_lower else None
        title_tokens = set(self._tokenize(title))
        present = [t for t in kw_tokens if t in title_tokens]
        if len(present) < len(kw_tokens):
            return None  # tidak semua kata keyword ada -> anggap tidak relevan
        # Semua kata ada tapi tidak berurutan sebagai frasa.
        return round(0.6 + 0.35 * (len(present) / len(kw_tokens)), 2)

    @staticmethod
    def _clean_title(title):
        """Rapikan judul: rapatkan spasi & buang prefix waktu relatif/label kategori."""
        import re
        t = re.sub(r'\s+', ' ', title or '').strip()
        t = re.sub(r'^\s*\d+\s*(?:menit|jam|hari|minggu|bulan)\s+lalu\s*', '', t, flags=re.I)
        return t.strip(' -|·••')

    @staticmethod
    def _norm_url(url):
        """Bentuk kanonik URL untuk deteksi duplikat (buang fragmen & trailing slash)."""
        return url.split('#')[0].rstrip('/').lower()

    def _add_article(self, platform, title, url, keyword, article_date, start_date, end_date):
        """Validasi, saring, dan simpan satu artikel. Mengembalikan True jika ditambahkan.
        Menerapkan: pembersihan judul, skor relevansi keyword, filter tanggal ketat,
        dan de-duplikasi URL lintas portal."""
        title = self._clean_title(title)
        if len(title) < 5 or not url:
            return False
        score = self.relevance(title, keyword)
        if score is None:
            return False  # tidak relevan dengan keyword
        # Filter tanggal ketat: jika tanggal diketahui, harus dalam rentang.
        if article_date is not None and not (start_date <= article_date.date() <= end_date):
            return False
        key = self._norm_url(url)
        if key in self.seen_urls:
            return False  # duplikat (mungkin dari portal lain)
        self.seen_urls.add(key)
        self.data.append({
            'platform': platform,
            'date': article_date.date().isoformat() if article_date else 'N/A',
            'title': title,
            'url': url,
            'keyword': keyword,
            'relevance': score,
        })
        return True

    def scrape_detik(self, keyword, start_date, end_date, max_articles=50):
        print(f"Scraping Detik.com untuk keyword: {keyword}")
        encoded_keyword = urllib.parse.quote(keyword)
        page = 1
        articles_found = 0
        keyword_lower = keyword.lower()

        while articles_found < max_articles:
            search_url = f"https://www.detik.com/search/searchall?query={encoded_keyword}&page={page}&result_type=relevansi"
            try:
                response = requests.get(search_url, headers=self.headers, timeout=10)
                print(f"Status kode untuk halaman {page}: {response.status_code}")
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('article')
                print(f"Halaman {page}: Ditemukan {len(articles)} artikel.")

                if not articles:
                    print("Tidak ada artikel lagi di Detik.com atau halaman habis.")
                    break

                for article in articles:
                    try:
                        title_tag = article.find('h3', class_='media__title') or article.find('h3', class_='dtr-ttl')
                        date_tag = article.find('span', class_='media__date') or article.find('div', class_='media__date')
                        link_tag = article.find('a', href=True)

                        if not (title_tag and link_tag):
                            print(f"Artikel tidak memiliki elemen lengkap (judul atau tautan). Missing: title={not title_tag}, link={not link_tag}")
                            continue

                        title = title_tag.text.strip()
                        link = link_tag['href']

                        article_date = None
                        if date_tag:
                            inner = date_tag.find('span')
                            article_date_str = inner.get('title', inner.text) if inner else date_tag.text
                            article_date = parse_tanggal_id(article_date_str)

                        if self._add_article('Detik.com', title, link, keyword,
                                             article_date, start_date, end_date):
                            articles_found += 1
                            print(f"Artikel ditemukan: {title}")

                        if articles_found >= max_articles:
                            break

                    except Exception as e:
                        print(f"Error parsing artikel Detik.com: {e}")
                        continue

                page += 1
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"Error saat scraping Detik.com: {e}")
                break

        print(f"Selesai scraping Detik.com: {articles_found} artikel ditemukan.")

    def scrape_kompas(self, keyword, start_date, end_date, max_articles=50):
        """Scrape Kompas.com berdasarkan keyword dan periode waktu."""
        print(f"Scraping Kompas.com untuk keyword: {keyword}")
        encoded_keyword = urllib.parse.quote(keyword)
        page = 1
        articles_found = 0

        while articles_found < max_articles:
            search_url = f"https://search.kompas.com/search?q={encoded_keyword}&page={page}"
            try:
                session = requests.Session()
                retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
                session.mount('https://', HTTPAdapter(max_retries=retries))
                response = session.get(search_url, headers=self.headers, timeout=15)
                print(f"Status kode untuk halaman {page}: {response.status_code}")
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                # Struktur Kompas terbaru: div.articleItem (lama: div.article__item).
                articles = soup.find_all('div', class_='articleItem') or soup.find_all('div', class_='article__item')
                print(f"Halaman {page}: Ditemukan {len(articles)} artikel.")

                if not articles:
                    print("Tidak ada artikel lagi di Kompas.com atau halaman habis.")
                    break

                for article in articles:
                    try:
                        title_tag = article.find('h2', class_='articleTitle') or article.find('h3', class_='article__title')
                        date_tag = article.find('div', class_='articlePost-date') or article.find('div', class_='article__date')
                        link_tag = article.find('a', class_='article-link', href=True) or article.find('a', class_='article__link', href=True) or article.find('a', href=True)

                        if not (title_tag and link_tag):
                            print(f"Artikel tidak memiliki elemen lengkap (judul atau tautan). Missing: title={not title_tag}, link={not link_tag}")
                            continue

                        title = title_tag.text.strip()
                        article_date = parse_tanggal_id(date_tag.text) if date_tag else None
                        link = link_tag['href']

                        if self._add_article('Kompas.com', title, link, keyword,
                                             article_date, start_date, end_date):
                            articles_found += 1
                            print(f"Artikel ditemukan: {title}")

                        if articles_found >= max_articles:
                            break

                    except Exception as e:
                        print(f"Error parsing artikel Kompas.com: {e}")
                        continue

                page += 1
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"Error saat scraping Kompas.com: {e}")
                break

        print(f"Selesai scraping Kompas.com: {articles_found} artikel ditemukan.")

    # ==================== Situs berbasis JavaScript (Selenium) ====================

    def _get_driver(self):
        """Buat (sekali) driver Chrome headless. Mengembalikan None jika Selenium/Chrome
        tidak tersedia, sehingga situs JavaScript dilewati tanpa membuat aplikasi crash."""
        if getattr(self, '_selenium_failed', False):
            return None
        if getattr(self, '_driver', None) is not None:
            return self._driver
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            opt = Options()
            for arg in ['--headless=new', '--no-sandbox', '--disable-gpu',
                        '--window-size=1280,2500', '--blink-settings=imagesEnabled=false']:
                opt.add_argument(arg)
            opt.page_load_strategy = 'eager'
            opt.add_argument('user-agent=' + self.headers['User-Agent'])
            driver = webdriver.Chrome(options=opt)
            driver.set_page_load_timeout(30)
            self._driver = driver
            return driver
        except Exception as e:
            print(f"Selenium/Chrome tidak tersedia ({e}). Situs berbasis JavaScript dilewati.")
            self._selenium_failed = True
            return None

    def close(self):
        """Tutup browser Selenium jika terbuka. Panggil setelah selesai scraping."""
        driver = getattr(self, '_driver', None)
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
            self._driver = None

    def _scrape_js_site(self, platform, url_template, keyword, start_date, end_date,
                        max_articles, href_regex, pages=3, wait=6):
        """Scraper generik untuk situs yang dirender JavaScript. Merender halaman pencarian
        dengan browser, lalu memanen tautan artikel yang cocok dengan pola & keyword."""
        import re
        from selenium.webdriver.common.by import By
        print(f"Scraping {platform} (via browser) untuk keyword: {keyword}")
        driver = self._get_driver()
        if driver is None:
            print(f"Selesai scraping {platform}: 0 artikel (Selenium tidak tersedia).")
            return

        pattern = re.compile(href_regex)
        found = 0

        for page in range(1, pages + 1):
            if found >= max_articles:
                break
            url = url_template.format(kw=urllib.parse.quote(keyword), page=page)
            print(f"Halaman {page}: {url}")
            try:
                driver.get(url)
            except Exception as e:
                print(f"  Timeout/kesalahan memuat halaman, mencoba lanjut: {repr(e)[:80]}")
            time.sleep(wait)

            anchors = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
            page_new = 0
            for a in anchors:
                if found >= max_articles:
                    break
                href = a.get_attribute('href') or ''
                if not pattern.search(href):
                    continue
                text = (a.text or '').strip()
                if not text:
                    continue
                # Judul = baris terpanjang (buang prefix waktu relatif spt "2 jam lalu").
                title = max(text.split('\n'), key=len).strip()
                if len(title) < 15:
                    continue
                if self._add_article(platform, title, href, keyword, None,
                                     start_date, end_date):
                    found += 1
                    page_new += 1
                    print(f"  Artikel ditemukan: {title}")

            if page_new == 0:
                print(f"  Tidak ada artikel baru di halaman {page}, berhenti.")
                break

        print(f"Selesai scraping {platform}: {found} artikel ditemukan.")

    def scrape_cnn(self, keyword, start_date, end_date, max_articles=50):
        """Scrape CNNIndonesia.com (dirender JavaScript)."""
        self._scrape_js_site(
            'CNNIndonesia.com',
            'https://www.cnnindonesia.com/search/?query={kw}&page={page}',
            keyword, start_date, end_date, max_articles,
            r'cnnindonesia\.com/[a-z-]+/\d{14}-')

    def scrape_tempo(self, keyword, start_date, end_date, max_articles=50):
        """Scrape Tempo.co (dirender JavaScript)."""
        self._scrape_js_site(
            'Tempo.co',
            'https://www.tempo.co/search?q={kw}&page={page}',
            keyword, start_date, end_date, max_articles,
            r'tempo\.co/[^/]+/\d{6,}/')

    def scrape_liputan6(self, keyword, start_date, end_date, max_articles=50):
        """Scrape Liputan6.com (dirender JavaScript)."""
        self._scrape_js_site(
            'Liputan6.com',
            'https://www.liputan6.com/search?q={kw}&page={page}',
            keyword, start_date, end_date, max_articles,
            r'liputan6\.com/[^/]+/read/\d+/')

    # ==================== Situs statis (requests + BeautifulSoup) ====================

    def scrape_viva(self, keyword, start_date, end_date, max_articles=50):
        """Scrape Viva.co.id (HTML statis)."""
        print(f"Scraping Viva.co.id untuk keyword: {keyword}")
        found = 0

        for page in range(1, 6):
            if found >= max_articles:
                break
            url = f"https://www.viva.co.id/search?q={urllib.parse.quote(keyword)}&page={page}"
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                print(f"Status kode Viva halaman {page}: {r.status_code}")
                r.raise_for_status()
            except Exception as e:
                print(f"Error saat scraping Viva.co.id: {e}")
                break

            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.find_all('div', class_='article-list-row')
            print(f"Halaman {page}: Ditemukan {len(rows)} artikel.")
            if not rows:
                break

            page_new = 0
            for row in rows:
                if found >= max_articles:
                    break
                title_tag = row.find('a', class_='article-list-title')
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                link = title_tag.get('href', '')
                date_tag = row.find(class_='article-list-date')
                article_date = parse_tanggal_id(date_tag.get_text(strip=True)) if date_tag else None
                if self._add_article('Viva.co.id', title, link, keyword,
                                     article_date, start_date, end_date):
                    found += 1
                    page_new += 1
                    print(f"Artikel ditemukan: {title}")

            if page_new == 0:
                break
            time.sleep(random.uniform(1, 3))

        print(f"Selesai scraping Viva.co.id: {found} artikel ditemukan.")

    def scrape_antara(self, keyword, start_date, end_date, max_articles=50):
        """Scrape AntaraNews.com (HTML statis)."""
        print(f"Scraping AntaraNews.com untuk keyword: {keyword}")
        found = 0

        for page in range(1, 6):
            if found >= max_articles:
                break
            url = f"https://www.antaranews.com/search?q={urllib.parse.quote(keyword)}&page={page}"
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                print(f"Status kode Antara halaman {page}: {r.status_code}")
                r.raise_for_status()
            except Exception as e:
                print(f"Error saat scraping AntaraNews.com: {e}")
                break

            soup = BeautifulSoup(r.text, 'html.parser')
            posts = soup.find_all('div', class_='card__post')
            print(f"Halaman {page}: Ditemukan {len(posts)} artikel.")
            if not posts:
                break

            page_new = 0
            for post in posts:
                if found >= max_articles:
                    break
                title_tag = post.find(class_='card__post__title')
                link_tag = post.find('a', href=True)
                if not (title_tag and link_tag):
                    continue
                title = title_tag.get_text(strip=True)
                link = link_tag['href']
                if not link.startswith('http'):
                    link = f"https://www.antaranews.com{link}"
                date_tag = post.find(class_='card__post__author-info')
                article_date = parse_tanggal_id(date_tag.get_text(' ', strip=True)) if date_tag else None
                if self._add_article('AntaraNews.com', title, link, keyword,
                                     article_date, start_date, end_date):
                    found += 1
                    page_new += 1
                    print(f"Artikel ditemukan: {title}")

            if page_new == 0:
                break
            time.sleep(random.uniform(1, 3))

        print(f"Selesai scraping AntaraNews.com: {found} artikel ditemukan.")


    def _sort_data(self):
        """Urutkan hasil: relevansi tertinggi dulu, lalu tanggal terbaru (N/A paling bawah)."""
        # Sort stabil: kunci sekunder (tanggal desc) dulu, lalu primer (relevansi desc).
        self.data.sort(key=lambda a: (a['date'] != 'N/A', a['date']), reverse=True)
        self.data.sort(key=lambda a: a.get('relevance', 0), reverse=True)

    def save_to_csv(self, filename_prefix="scraped_media"):
        """Simpan data yang di-scrape ke file CSV dan Excel (.xlsx)."""
        print(f"Jumlah artikel yang dikumpulkan: {len(self.data)}")
        self._sort_data()
        if not self.data:
            print("Tidak ada data untuk disimpan, membuat CSV dengan placeholder.")
            df = pd.DataFrame([{
                'platform': 'N/A',
                'date': 'N/A',
                'title': 'No articles found',
                'url': 'N/A',
                'keyword': 'N/A',
                'relevance': 'N/A',
            }])
        else:
            df = pd.DataFrame(self.data)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(self.output_dir, f"{filename_prefix}_{timestamp}.csv")
        # utf-8-sig agar karakter Indonesia tampil benar saat dibuka di Excel.
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"Data disimpan ke: {output_path}")

        # Ekspor Excel (butuh openpyxl). Dilewati dengan pesan bila paket tak tersedia.
        xlsx_path = os.path.join(self.output_dir, f"{filename_prefix}_{timestamp}.xlsx")
        try:
            df.to_excel(xlsx_path, index=False, sheet_name='Hasil')
            print(f"Data disimpan ke: {xlsx_path}")
        except Exception as e:
            print(f"Ekspor Excel dilewati ({e}). Jalankan: pip install openpyxl")

        self.save_to_txt(filename_prefix, timestamp)

    def save_to_txt(self, filename_prefix="scraped_media", timestamp=None):
        """Simpan daftar judul artikel bernomor ke file .txt agar mudah dibaca."""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(self.output_dir, f"{filename_prefix}_{timestamp}.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Daftar artikel yang ditemukan ({len(self.data)} artikel)\n")
            f.write("=" * 60 + "\n\n")
            if not self.data:
                f.write("Tidak ada artikel yang ditemukan.\n")
            else:
                for i, article in enumerate(self.data, 1):
                    f.write(f"{i}. {article['title']} ({article['platform']})\n")
                    f.write(f"   Tanggal : {article['date']}\n")
                    f.write(f"   URL     : {article['url']}\n\n")
        print(f"Daftar judul disimpan ke: {output_path}")

def main():
    keyword = input("Masukkan keyword (contoh: teknologi): ")
    start_date = input("Masukkan tanggal mulai (YYYY-MM-DD): ")
    end_date = input("Masukkan tanggal akhir (YYYY-MM-DD): ")
    max_articles = int(input("Masukkan jumlah maksimum artikel per situs (default 50): ") or 50)

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        if start_date > end_date:
            print("Tanggal mulai harus sebelum tanggal akhir.")
            return
    except ValueError:
        print("Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
        return

    scraper = OnlineMediaScraper()
    scraper.scrape_detik(keyword, start_date, end_date, max_articles)
    scraper.scrape_kompas(keyword, start_date, end_date, max_articles)
    scraper.scrape_cnn(keyword, start_date, end_date, max_articles)
    scraper.scrape_tempo(keyword, start_date, end_date, max_articles)
    scraper.scrape_liputan6(keyword, start_date, end_date, max_articles)
    scraper.scrape_viva(keyword, start_date, end_date, max_articles)
    scraper.scrape_antara(keyword, start_date, end_date, max_articles)
    scraper.close()
    scraper.save_to_csv(keyword.replace(' ', '_'))

    if scraper.data:
        print(f"\nJudul artikel yang ditemukan:")
        for i, article in enumerate(scraper.data, 1):
            print(f"{i}. {article['title']} ({article['platform']})")
    else:
        print(f"\nTidak ada artikel yang ditemukan untuk keyword '{keyword}'.")

if __name__ == "__main__":
    main()
