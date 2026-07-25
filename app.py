"""
Web UI untuk Scraper Berita Online Indonesia.
Jalankan:  python app.py   lalu buka http://127.0.0.1:5000
"""
from flask import Flask, request, render_template_string, send_from_directory, abort
from datetime import datetime
import os

from main import OnlineMediaScraper

app = Flask(__name__)

# Definisi situs: key -> (label, nama_method, tipe)
SITES = [
    ('detik',    'Detik.com',        'scrape_detik',    'statis'),
    ('kompas',   'Kompas.com',       'scrape_kompas',   'statis'),
    ('viva',     'Viva.co.id',       'scrape_viva',     'statis'),
    ('antara',   'AntaraNews.com',   'scrape_antara',   'statis'),
    ('cnn',      'CNNIndonesia.com', 'scrape_cnn',      'browser'),
    ('liputan6', 'Liputan6.com',     'scrape_liputan6', 'browser'),
    ('tempo',    'Tempo.co',         'scrape_tempo',    'browser'),
]

TEMPLATE = """
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scraper Berita Online Indonesia</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
         margin: 0; background: #f4f6fb; color: #1a1d29; }
  @media (prefers-color-scheme: dark) {
    body { background: #10131a; color: #e6e8ef; }
    .card { background: #1a1e2a !important; }
    input, .site-chip { background: #10131a !important; color: #e6e8ef !important; border-color: #2c3242 !important; }
    th { background: #222838 !important; }
    tr:nth-child(even) td { background: #171b26 !important; }
    a { color: #7aa2ff; }
  }
  header { background: linear-gradient(135deg, #2b5cff, #6b3fff); color: #fff; padding: 28px 20px; }
  header h1 { margin: 0 0 4px; font-size: 22px; }
  header p { margin: 0; opacity: .9; font-size: 14px; }
  .wrap { max-width: 1080px; margin: 0 auto; padding: 20px; }
  .card { background: #fff; border-radius: 14px; padding: 22px; box-shadow: 0 4px 20px rgba(0,0,0,.06); margin-bottom: 22px; }
  label { display: block; font-weight: 600; font-size: 13px; margin-bottom: 6px; }
  input { width: 100%; padding: 10px 12px; border: 1px solid #d3d8e4; border-radius: 9px; font-size: 14px; background: #fff; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; }
  .sites { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 6px; }
  .site-chip { display: flex; align-items: center; gap: 7px; border: 1px solid #d3d8e4; border-radius: 999px;
               padding: 7px 13px; font-size: 13px; cursor: pointer; background: #fff; user-select: none; }
  .site-chip input { width: auto; }
  .badge { font-size: 10px; padding: 1px 7px; border-radius: 999px; font-weight: 700; }
  .badge.statis { background: #d9f2e4; color: #157347; }
  .badge.browser { background: #fde8cc; color: #9a5b00; }
  button { margin-top: 18px; background: #2b5cff; color: #fff; border: 0; padding: 12px 26px;
           border-radius: 9px; font-size: 15px; font-weight: 600; cursor: pointer; }
  button:hover { background: #1c46d4; }
  .stat { display: inline-block; background: #eef2ff; color: #2b5cff; border-radius: 8px;
          padding: 6px 12px; font-weight: 700; margin: 0 8px 8px 0; font-size: 13px; }
  @media (prefers-color-scheme: dark) { .stat { background: #1c2540; } }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .table-scroll { overflow-x: auto; }
  th, td { text-align: left; padding: 9px 11px; border-bottom: 1px solid #e6e9f0; }
  th { background: #eef1f7; font-size: 12px; text-transform: uppercase; letter-spacing: .03em; }
  td.title { max-width: 460px; }
  .dl { display: inline-block; margin-bottom: 14px; background: #157347; color: #fff;
        padding: 9px 16px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; }
  .muted { opacity: .6; font-size: 12px; }
  .empty { padding: 30px; text-align: center; opacity: .7; }
</style>
</head>
<body>
<header>
  <div class="wrap" style="padding-bottom:0;padding-top:0">
    <h1>📰 Scraper Berita Online Indonesia</h1>
    <p>Kumpulkan artikel dari 7 portal berita berdasarkan keyword & rentang tanggal</p>
  </div>
</header>

<div class="wrap">
  <form method="post" action="/scrape" class="card">
    <div class="grid">
      <div>
        <label>Keyword</label>
        <input name="keyword" value="{{ form.keyword or '' }}" placeholder="mis. teknologi" required>
      </div>
      <div>
        <label>Tanggal Mulai</label>
        <input type="date" name="start_date" value="{{ form.start_date or '' }}" required>
      </div>
      <div>
        <label>Tanggal Akhir</label>
        <input type="date" name="end_date" value="{{ form.end_date or '' }}" required>
      </div>
      <div>
        <label>Maks. artikel / situs</label>
        <input type="number" name="max_articles" value="{{ form.max_articles or 20 }}" min="1" max="200">
      </div>
    </div>

    <label style="margin-top:18px">Pilih Portal Berita</label>
    <div class="sites">
      {% for key, label, _m, tipe in sites %}
      <label class="site-chip">
        <input type="checkbox" name="site" value="{{ key }}" {{ 'checked' if key in selected else '' }}>
        {{ label }} <span class="badge {{ tipe }}">{{ 'CEPAT' if tipe=='statis' else 'BROWSER' }}</span>
      </label>
      {% endfor %}
    </div>
    <p class="muted">🟢 CEPAT = HTML statis (ringan). 🟠 BROWSER = perlu render JavaScript (Selenium, lebih lambat).</p>

    <button type="submit">🔍 Mulai Scraping</button>
  </form>

  {% if did_run %}
  <div class="card">
    <div>
      <span class="stat">Total: {{ results|length }} artikel</span>
      {% for plat, n in per_platform.items() %}<span class="stat">{{ plat }}: {{ n }}</span>{% endfor %}
    </div>
    {% if csv_name or xlsx_name %}
    <div style="margin-top:14px">
      {% if xlsx_name %}<a class="dl" href="/download/{{ xlsx_name }}">⬇️ Download Excel</a>{% endif %}
      {% if csv_name %}<a class="dl" style="background:#555" href="/download/{{ csv_name }}">⬇️ Download CSV</a>{% endif %}
    </div>
    {% endif %}

    {% if results %}
    <div class="table-scroll">
    <table>
      <thead><tr><th>#</th><th>Portal</th><th>Tanggal</th><th>Judul</th><th>Relevansi</th><th>Link</th></tr></thead>
      <tbody>
      {% for a in results %}
        <tr>
          <td>{{ loop.index }}</td>
          <td>{{ a.platform }}</td>
          <td>{{ a.date }}</td>
          <td class="title">{{ a.title }}</td>
          <td>{{ '%d%%' | format((a.relevance * 100) | round | int) if a.relevance is defined else '—' }}</td>
          <td><a href="{{ a.url }}" target="_blank" rel="noopener">buka ↗</a></td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
    {% else %}
    <div class="empty">Tidak ada artikel ditemukan untuk keyword ini.</div>
    {% endif %}
  </div>
  {% endif %}
</div>
</body>
</html>
"""


@app.route('/')
def index():
    default_selected = {'detik', 'kompas', 'viva', 'antara'}
    return render_template_string(TEMPLATE, sites=SITES, selected=default_selected,
                                  did_run=False, form={}, results=[], per_platform={},
                                  csv_name=None, xlsx_name=None)


@app.route('/scrape', methods=['POST'])
def scrape():
    keyword = (request.form.get('keyword') or '').strip()
    selected = set(request.form.getlist('site'))
    try:
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
    except (ValueError, KeyError):
        abort(400, "Format tanggal tidak valid.")
    try:
        max_articles = max(1, min(200, int(request.form.get('max_articles', 20))))
    except ValueError:
        max_articles = 20

    scraper = OnlineMediaScraper()
    try:
        for key, label, method_name, _tipe in SITES:
            if key in selected:
                getattr(scraper, method_name)(keyword, start_date, end_date, max_articles)
    finally:
        scraper.close()

    csv_name = None
    xlsx_name = None
    if scraper.data:
        scraper.save_to_csv(keyword.replace(' ', '_') or 'hasil')
        files = sorted(os.listdir(scraper.output_dir))
        csvs = [f for f in files if f.endswith('.csv')]
        xlsxs = [f for f in files if f.endswith('.xlsx')]
        if csvs:
            csv_name = csvs[-1]
        if xlsxs:
            xlsx_name = xlsxs[-1]

    per_platform = {}
    for a in scraper.data:
        per_platform[a['platform']] = per_platform.get(a['platform'], 0) + 1

    form = {'keyword': keyword, 'start_date': str(start_date),
            'end_date': str(end_date), 'max_articles': max_articles}
    return render_template_string(TEMPLATE, sites=SITES, selected=selected, did_run=True,
                                  form=form, results=scraper.data, per_platform=per_platform,
                                  csv_name=csv_name, xlsx_name=xlsx_name)


@app.route('/download/<path:filename>')
def download(filename):
    directory = os.path.abspath('scraped_media_data')
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == '__main__':
    # Catatan: di macOS port 5000 sering dipakai AirPlay, jadi default 5050.
    debug = os.environ.get('FLASK_DEBUG', '1') != '0'
    app.run(debug=debug, port=int(os.environ.get('PORT', 5050)))
