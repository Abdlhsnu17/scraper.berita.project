import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import urllib.parse
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
                        date_tag = article.find('span', class_='media__date')
                        link_tag = article.find('a', href=True)

                        print(f"Title tag: {title_tag}, Date tag: {date_tag}, Link tag: {link_tag}")
                        if not (title_tag and link_tag):
                            print(f"Artikel tidak memiliki elemen lengkap (judul atau tautan). Missing: title={not title_tag}, link={not link_tag}")
                            continue

                        title = title_tag.text.strip()
                        if keyword_lower not in title.lower():
                            print(f"Judul tidak mengandung keyword '{keyword}': {title}")
                            continue

                        link = link_tag['href']

                        article_date = None
                        if date_tag:
                            article_date_str = date_tag.find('span')['title'].strip() if date_tag.find('span') else ''
                            print(f"Raw date string: {article_date_str}")
                            try:
                                article_date = datetime.strptime(article_date_str, '%d %b %Y %H:%M WIB')
                            except ValueError as e:
                                print(f"Error parsing date: {e}, Raw date: {article_date_str}")
                                article_date = None

                        if article_date is None or (start_date <= article_date.date() <= end_date):
                            self.data.append({
                                'platform': 'Detik.com',
                                'date': start_date,
                                'title': title,
                                'url': link,
                                'keyword': keyword
                            })
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
        keyword_lower = keyword.lower()

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
                articles = soup.find_all('div', class_='article__item')  
                print(f"Halaman {page}: Ditemukan {len(articles)} artikel.")
                print(f"Articles: {articles[:2]}")
                # print(f"Raw HTML (first 1000 chars): {response.text[:1000]}")

                response = requests.get(search_url, headers=self.headers, timeout=10)
                print(f"Status kode untuk halaman {page}: {response.status_code}")
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('div', class_='article__item')
                print(f"Halaman {page}: Ditemukan {len(articles)} artikel.")
                print(f"Articles: {articles}")

                if not articles:
                    print("Tidak ada artikel lagi di Kompas.com atau halaman habis.")
                    break

                for article in articles:
                    try:
                        title_tag = article.find('h3', class_='article__title')
                        date_tag = article.find('div', class_='article__date')
                        link_tag = article.find('a', class_='article__link', href=True)

                        print(f"Title tag: {title_tag}")
                        print(f"Date tag: {date_tag}")
                        print(f"Link tag: {link_tag}")

                        if not (title_tag and link_tag):
                            print(f"Artikel tidak memiliki elemen lengkap (judul atau tautan). Missing: title={not title_tag}, link={not link_tag}")
                            continue

                        title = title_tag.text.strip()
                        if keyword_lower not in title.lower():
                            print(f"Judul tidak mengandung keyword '{keyword}': {title}")
                            continue

                        date_str = date_tag.text.strip().split(', ')[1] if date_tag else ''
                        try:
                            article_date = datetime.strptime(date_str, '%d/%m/%Y %H:%M') if date_str else None
                        except ValueError as e:
                            print(f"Error parsing date: {e}, Raw date: {date_str}")
                            article_date = None
                        link = link_tag['href']

                        if article_date is None or (start_date <= article_date.date() <= end_date):
                            self.data.append({
                                'platform': 'Kompas.com',
                                'date': start_date,
                                'title': title,
                                'url': link,
                                'keyword': keyword
                            })
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

    def scrape_cnn(self, keyword, start_date, end_date, max_articles=50):
        """Scrape CNNIndonesia.com berdasarkan keyword dan periode waktu."""
        print(f"Scraping CNNIndonesia.com untuk keyword: {keyword}")
        encoded_keyword = urllib.parse.quote(keyword)
        page = 1
        articles_found = 0
        keyword_lower = keyword.lower()

        while articles_found < max_articles:
            search_url = f"https://www.cnnindonesia.com/search/?query={encoded_keyword}&page={page}"
            try:
                response = requests.get(search_url, headers=self.headers, timeout=10)
                print(f"Status kode untuk halaman {page}: {response.status_code}")
                if response.status_code == 404:
                    print(f"Halaman tidak ditemukan untuk URL: {search_url}")
                    break
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # class_names = ['list', 'article', 'news-item', 'media__item']
                class_names = ['nhl-box', 'article-list', 'list-news', 'article-item', 'list', 'article', 'news-item', 'media__item']
                articles = None
                for class_name in class_names:
                    articles = soup.find_all('article', class_=class_name) or soup.find_all('div', class_=class_name)
                    if articles:
                        print(f"Ditemukan artikel dengan class: {class_name}")
                        break

                if not articles:
                    print("Tidak ditemukan artikel. Mencoba mencari class lain...")
                    divs_with_class = soup.find_all(['div', 'article'], class_=True)
                    unique_classes = set(div['class'][0] for div in divs_with_class if div.get('class'))
                    print(f"Class unik yang ditemukan: {unique_classes}")
                    print("Tidak ada artikel lagi di CNNIndonesia.com atau halaman habis.")
                    break

                print(f"Halaman {page}: Ditemukan {len(articles)} artikel.")

                for article in articles:
                    try:
                        title_tag = article.find('h2', class_='title') or article.find('h3', class_='title')
                        date_tag = article.find('span', class_='date') or article.find('div', class_='date')
                        link_tag = article.find('a', href=True)

                        if not (title_tag and link_tag):
                            print(f"Artikel tidak memiliki elemen lengkap (judul atau tautan). Missing: title={not title_tag}, link={not link_tag}, date={not date_tag}")
                            continue

                        title = title_tag.text.strip()
                        if keyword_lower not in title.lower():
                            print(f"Judul tidak mengandung keyword '{keyword}': {title}")
                            continue

                        link = link_tag['href']

                        article_date = None
                        if date_tag:
                            date_str = date_tag.text.strip()
                            print(f"Raw date string: {date_str}")
                            try:
                                article_date = datetime.strptime(date_str, '%d %b %Y %H:%M')
                            except ValueError:
                                try:
                                    article_date = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                                except ValueError as e:
                                    print(f"Error parsing date: {e}, Raw date: {date_str}")
                                    article_date = None

                        if article_date is None or (start_date <= article_date.date() <= end_date):
                            self.data.append({
                                'platform': 'CNNIndonesia.com',
                                'date': start_date,
                                'title': title,
                                'url': link,
                                'keyword': keyword
                            })
                            articles_found += 1
                            print(f"Artikel ditemukan: {title}")

                        if articles_found >= max_articles:
                            break

                    except Exception as e:
                        print(f"Error parsing artikel CNNIndonesia.com: {e}")
                        continue

                page += 1
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"Error saat scraping CNNIndonesia.com: {e}")
                break

        print(f"Selesai scraping CNNIndonesia.com: {articles_found} artikel ditemukan.")

    def scrape_tempo(self, keyword, start_date, end_date, max_articles=50):
        """Scrape Tempo.co berdasarkan keyword dan periode waktu."""
        print(f"Scraping Tempo.co untuk keyword: {keyword}")
        encoded_keyword = urllib.parse.quote(keyword)
        page = 1
        articles_found = 0
        keyword_lower = keyword.lower()

        while articles_found < max_articles:
            search_url = f"https://www.tempo.co/search?q={encoded_keyword}&page={page}"
            try:
                response = requests.get(search_url, headers=self.headers, timeout=10)
                print(f"Status kode untuk halaman {page}: {response.status_code}")
                if response.status_code == 404:
                    print(f"Halaman tidak ditemukan untuk URL: {search_url}")
                    break
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                class_names = ['card', 'article', 'list-item', 'news-item']
                articles = None
                for class_name in class_names:
                    articles = soup.find_all('div', class_=class_name) or soup.find_all('article', class_=class_name)
                    if articles:
                        print(f"Ditemukan artikel dengan class: {class_name}")
                        break

                if not articles:
                    print("Tidak ditemukan artikel. Mencoba mencari class lain...")
                    divs_with_class = soup.find_all(['div', 'article'], class_=True)
                    unique_classes = set(div['class'][0] for div in divs_with_class if div.get('class'))
                    print(f"Class unik yang ditemukan: {unique_classes}")
                    print("Tidak ada artikel lagi di Tempo.co atau halaman habis.")
                    break

                print(f"Halaman {page}: Ditemukan {len(articles)} artikel.")

                for article in articles:
                    try:
                        title_tag = article.find('h2', class_='title') or article.find('h3', class_='title') or article.find('h2', class_='judul')
                        date_tag = article.find('span', class_='date') or article.find('div', class_='date') or article.find('span', class_='tanggal')
                        link_tag = article.find('a', href=True)

                        if not (title_tag and link_tag):
                            print(f"Artikel tidak memiliki elemen lengkap (judul atau tautan). Missing: title={not title_tag}, link={not link_tag}, date={not date_tag}")
                            continue

                        title = title_tag.text.strip()
                        if keyword_lower not in title.lower():
                            print(f"Judul tidak mengandung keyword '{keyword}': {title}")
                            continue

                        link = link_tag['href']

                        article_date = None
                        if date_tag:
                            date_str = date_tag.text.strip()
                            print(f"Raw date string: {date_str}")
                            try:
                                article_date = datetime.strptime(date_str, '%d %b %Y, %H:%M WIB')
                            except ValueError:
                                try:
                                    article_date = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                                except ValueError as e:
                                    print(f"Error parsing date: {e}, Raw date: {date_str}")
                                    article_date = None

                        if article_date is None or (start_date <= article_date.date() <= end_date):
                            self.data.append({
                                'platform': 'Tempo.co',
                                'date': start_date,
                                'title': title,
                                'url': link,
                                'keyword': keyword
                            })
                            articles_found += 1
                            print(f"Artikel ditemukan: {title}")

                        if articles_found >= max_articles:
                            break

                    except Exception as e:
                        print(f"Error parsing artikel Tempo.co: {e}")
                        continue

                page += 1
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"Error saat scraping Tempo.co: {e}")
                break

        print(f"Selesai scraping Tempo.co: {articles_found} artikel ditemukan.")

    def scrape_liputan6(self, keyword, start_date, end_date, max_articles=50):
        """Scrape Liputan6.com berdasarkan keyword dan periode waktu."""
        print(f"Scraping Liputan6.com untuk keyword: {keyword}")
        encoded_keyword = urllib.parse.quote(keyword)
        page = 1
        articles_found = 0
        keyword_lower = keyword.lower()

        while articles_found < max_articles:
            search_url = f"https://www.liputan6.com/search?q={encoded_keyword}&page={page}"
            try:
                response = requests.get(search_url, headers=self.headers, timeout=10)
                print(f"Status kode untuk halaman {page}: {response.status_code}")
                if response.status_code == 404:
                    print(f"Halaman tidak ditemukan untuk URL: {search_url}")
                    break
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                class_names = ['articles--item', 'article', 'list-item', 'news-item']
                articles = None
                for class_name in class_names:
                    articles = soup.find_all('article', class_=class_name) or soup.find_all('div', class_=class_name)
                    if articles:
                        print(f"Ditemukan artikel dengan class: {class_name}")
                        break

                if not articles:
                    print("Tidak ditemukan artikel. Mencoba mencari class lain...")
                    divs_with_class = soup.find_all(['div', 'article'], class_=True)
                    unique_classes = set(div['class'][0] for div in divs_with_class if div.get('class'))
                    print(f"Class unik yang ditemukan: {unique_classes}")
                    print("Tidak ada artikel lagi di Liputan6.com atau halaman habis.")
                    break

                print(f"Halaman {page}: Ditemukan {len(articles)} artikel.")

                for article in articles:
                    try:
                        title_tag = article.find('h4', class_='articles--title') or article.find('h3', class_='articles--title') or article.find('h2', class_='title')
                        date_tag = article.find('span', class_='articles--date') or article.find('div', class_='articles--date') or article.find('time')
                        link_tag = article.find('a', href=True)

                        if not (title_tag and link_tag):
                            print(f"Artikel tidak memiliki elemen lengkap (judul atau tautan). Missing: title={not title_tag}, link={not link_tag}, date={not date_tag}")
                            continue

                        title = title_tag.text.strip()
                        if keyword_lower not in title.lower():
                            print(f"Judul tidak mengandung keyword '{keyword}': {title}")
                            continue

                        link = link_tag['href']

                        article_date = None
                        if date_tag:
                            date_str = date_tag.text.strip()
                            print(f"Raw date string: {date_str}")
                            try:
                                article_date = datetime.strptime(date_str, '%d %b %Y, %H:%M WIB')
                            except ValueError:
                                try:
                                    article_date = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                                except ValueError as e:
                                    print(f"Error parsing date: {e}, Raw date: {date_str}")
                                    article_date = None

                        if article_date is None or (start_date <= article_date.date() <= end_date):
                            self.data.append({
                                'platform': 'Liputan6.com',
                                'date': start_date,
                                'title': title,
                                'url': link,
                                'keyword': keyword
                            })
                            articles_found += 1
                            print(f"Artikel ditemukan: {title}")

                        if articles_found >= max_articles:
                            break

                    except Exception as e:
                        print(f"Error parsing artikel Liputan6.com: {e}")
                        continue

                page += 1
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"Error saat scraping Liputan6.com: {e}")
                break

        print(f"Selesai scraping Liputan6.com: {articles_found} artikel ditemukan.")

    def scrape_viva(self, keyword, start_date, end_date, max_articles=50):
        """Scrape Viva.co.id berdasarkan keyword dan periode waktu."""
        print(f"Scraping Viva.co.id untuk keyword: {keyword}")
        encoded_keyword = urllib.parse.quote(keyword)
        page = 1
        articles_found = 0
        keyword_lower = keyword.lower()

        while articles_found < max_articles:
            search_url = f"https://www.viva.co.id/search?q={encoded_keyword}&page={page}"
            try:
                response = requests.get(search_url, headers=self.headers, timeout=10)
                print(f"Status kode untuk halaman {page}: {response.status_code}")
                if response.status_code == 404:
                    print(f"Halaman tidak ditemukan untuk URL: {search_url}")
                    break
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Try possible class names for article containers
                class_names = ['article-list', 'article', 'list-item', 'news-item']
                articles = None
                for class_name in class_names:
                    articles = soup.find_all('div', class_=class_name) or soup.find_all('article', class_=class_name)
                    if articles:
                        print(f"Ditemukan artikel dengan class: {class_name}")
                        break

                if not articles:
                    print("Tidak ditemukan artikel. Mencoba mencari class lain...")
                    divs_with_class = soup.find_all(['div', 'article'], class_=True)
                    unique_classes = set(div['class'][0] for div in divs_with_class if div.get('class'))
                    print(f"Class unik yang ditemukan: {unique_classes}")
                    print("Tidak ada artikel lagi di Viva.co.id atau halaman habis.")
                    break

                print(f"Halaman {page}: Ditemukan {len(articles)} artikel.")

                for article in articles:
                    try:
                        title_tag = article.find('h3', class_='title') or article.find('h4', class_='title') or article.find('h2', class_='article-title')
                        date_tag = article.find('span', class_='date') or article.find('div', class_='date') or article.find('time')
                        link_tag = article.find('a', href=True)

                        if not (title_tag and link_tag):
                            print(f"Artikel tidak memiliki elemen lengkap (judul atau tautan). Missing: title={not title_tag}, link={not link_tag}, date={not date_tag}")
                            continue

                        title = title_tag.text.strip()
                        if keyword_lower not in title.lower():
                            print(f"Judul tidak mengandung keyword '{keyword}': {title}")
                            continue

                        link = link_tag['href']

                        # Parse date for filtering, use None if missing
                        article_date = None
                        if date_tag:
                            date_str = date_tag.text.strip()
                            print(f"Raw date string: {date_str}")
                            try:
                                # Viva.co.id dates might be like "14 Mei 2025, 09:00 WIB" or "14/05/2025 09:00"
                                article_date = datetime.strptime(date_str, '%d %b %Y, %H:%M WIB')
                            except ValueError:
                                try:
                                    article_date = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                                except ValueError as e:
                                    print(f"Error parsing date: {e}, Raw date: {date_str}")
                                    article_date = None

                        if article_date is None or (start_date <= article_date.date() <= end_date):
                            self.data.append({
                                'platform': 'Viva.co.id',
                                'date': start_date,
                                'title': title,
                                'url': link,
                                'keyword': keyword
                            })
                            articles_found += 1
                            print(f"Artikel ditemukan: {title}")

                        if articles_found >= max_articles:
                            break

                    except Exception as e:
                        print(f"Error parsing artikel Viva.co.id: {e}")
                        continue

                page += 1
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"Error saat scraping Viva.co.id: {e}")
                break

        print(f"Selesai scraping Viva.co.id: {articles_found} artikel ditemukan.")

    def scrape_antara(self, keyword, start_date, end_date, max_articles=50):
        """Scrape AntaraNews.com berdasarkan keyword dan periode waktu."""
        print(f"Scraping AntaraNews.com untuk keyword: {keyword}")
        encoded_keyword = urllib.parse.quote(keyword)
        page = 1
        articles_found = 0
        keyword_lower = keyword.lower()

        while articles_found < max_articles:
            search_url = f"https://www.antaranews.com/search?q={encoded_keyword}&page={page}"
            try:
                response = requests.get(search_url, headers=self.headers, timeout=10)
                print(f"Status kode untuk halaman {page}: {response.status_code}")
                if response.status_code == 404:
                    print(f"Halaman tidak ditemukan untuk URL: {search_url}")
                    break
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                class_names = ['search-result-item', 'news-article', 'post-item', 'article-item', 'news-post', 'post', 'article', 'list-item', 'news-item']
                articles = None
                for class_name in class_names:
                    articles = soup.find_all('div', class_=class_name) or soup.find_all('article', class_=class_name)
                    if articles:
                        print(f"Ditemukan artikel dengan class: {class_name}")
                        break

                if not articles:
                    print("Tidak ditemukan artikel. Mencoba mencari class lain...")
                    divs_with_class = soup.find_all(['div', 'article'], class_=True)
                    unique_classes = set(div['class'][0] for div in divs_with_class if div.get('class'))
                    print(f"Class unik yang ditemukan: {unique_classes}")
                    print("Tidak ada artikel lagi di AntaraNews.com atau halaman habis.")
                    break

                print(f"Halaman {page}: Ditemukan {len(articles)} artikel.")

                for article in articles:
                    try:
                        title_tag = article.find('h3', class_=['post-title', 'title', 'article-title']) or \
                                    article.find('h2', class_=['post-title', 'title', 'article-title']) or \
                                    article.find('h4', class_=['post-title', 'title', 'article-title'])
                        date_tag = article.find('span', class_=['post-date', 'date', 'article-date']) or \
                                article.find('div', class_=['post-date', 'date', 'article-date']) or \
                                article.find('time')
                        link_tag = article.find('a', href=True)

                        if not (title_tag and link_tag):
                            print(f"Artikel tidak memiliki elemen lengkap (judul atau tautan). Missing: title={not title_tag}, link={not link_tag}, date={not date_tag}")
                            continue

                        title = title_tag.text.strip()
                        summary_tag = article.find('p', class_='summary') or article.find('div', class_='excerpt')
                        summary = summary_tag.text.strip() if summary_tag else ""
                        if keyword_lower not in title.lower() and keyword_lower not in summary.lower():
                            print(f"Judul atau ringkasan tidak mengandung keyword '{keyword}': {title}")
                            continue

                        link = link_tag['href']
                        if not link.startswith('http'):
                            link = f"https://www.antaranews.com{link}"

                        article_date = None
                        if date_tag:
                            date_str = date_tag.text.strip()
                            print(f"Raw date string: {date_str}")
                            for date_format in ['%d %b %Y, %H:%M WIB', '%d/%m/%Y %H:%M', '%d %b %Y', '%Y-%m-%d %H:%M']:
                                try:
                                    article_date = datetime.strptime(date_str, date_format)
                                    break
                                except ValueError:
                                    continue
                            if article_date is None:
                                print(f"Error parsing date: Tidak ada format yang cocok, Raw date: {date_str}")

                        if article_date is None or (start_date <= article_date.date() <= end_date):
                            self.data.append({
                                'platform': 'AntaraNews.com',
                                'date': start_date,
                                'title': title,
                                'url': link,
                                'keyword': keyword
                            })
                            articles_found += 1
                            print(f"Artikel ditemukan: {title}")

                        if articles_found >= max_articles:
                            break

                    except Exception as e:
                        print(f"Error parsing artikel AntaraNews.com: {e}")
                        continue

                page += 1
                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"Error saat scraping AntaraNews.com: {e}")
                break

        print(f"Selesai scraping AntaraNews.com: {articles_found} artikel ditemukan.")

    def save_to_csv(self, filename_prefix="scraped_media"):
        """Simpan data yang di-scrape ke file CSV."""
        print(f"Jumlah artikel yang dikumpulkan: {len(self.data)}")
        if not self.data:
            print("Tidak ada data untuk disimpan, membuat CSV dengan placeholder.")
            df = pd.DataFrame([{
                'platform': 'N/A',
                'date': 'N/A',
                'title': 'No articles found',
                'url': 'N/A',
                'keyword': 'N/A'
            }])
        else:
            df = pd.DataFrame(self.data)

        output_path = os.path.join(self.output_dir, f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Data disimpan ke: {output_path}")

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
    scraper.save_to_csv(keyword.replace(' ', '_'))

    if scraper.data:
        print(f"\nJudul artikel yang ditemukan:")
        for i, article in enumerate(scraper.data, 1):
            print(f"{i}. {article['title']} ({article['platform']})")
    else:
        print(f"\nTidak ada artikel yang ditemukan untuk keyword '{keyword}'.")

if __name__ == "__main__":
    main()
