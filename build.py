#!/usr/bin/env python3
"""Static site generator for maltezskyrad.cz. Python 3.10+, standard library only.

    python3 build.py                 preview build into dist/ (noindex, content-status labels shown)
    python3 build.py --production    production build (indexable, no status labels)
    python3 build.py serve [port]    preview build, then serve dist/ with _headers and _redirects applied
"""
import html
import json
import re
import shutil
import struct
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT, STATIC, DIST = ROOT / "content", ROOT / "static", ROOT / "dist"
PRODUCTION = "--production" in sys.argv
SITE = json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))
I18N = json.loads((CONTENT / "i18n.json").read_text(encoding="utf-8"))
CAL = json.loads((CONTENT / "calendar.json").read_text(encoding="utf-8"))
ASSET_VERSION = datetime.now().strftime("%Y%m%d%H%M")
esc = lambda s: html.escape(str(s or ""), quote=True)


# ---------------------------------------------------------------- content


def _fix(v):
    return re.sub("Fra[´‘]", "Fra’", v) if isinstance(v, str) else v  # legacy texts use the acute accent or a left quote


def read_doc(path):
    text = path.read_text(encoding="utf-8")
    _, meta, body = text.split("---\n", 2)
    return {k: _fix(v) for k, v in json.loads(meta).items()}, _fix(body.strip())


def load_pages():
    pages = {}
    for f in sorted((CONTENT / "pages").rglob("index.html")):
        meta, body = read_doc(f)
        pages[meta["url"]] = {**meta, "body": body}
    return pages


def load_news():
    news = []
    for f in (CONTENT / "news").rglob("*.html"):
        meta, body = read_doc(f)
        news.append({**meta, "body": body})
    return sorted(news, key=lambda n: n["date"], reverse=True)


PAGES, NEWS = load_pages(), load_news()
LANGS = SITE["languages"]
# translations: content/translations/<lang>.json maps a Czech URL to {url, title, description, body}
TR = {l: json.loads((CONTENT / "translations" / f"{l}.json").read_text(encoding="utf-8")) for l in LANGS[1:]}
for _l, _entries in TR.items():
    for _src, _e in _entries.items():
        _e["source"] = _src
        _e["body"] = _fix(_e.get("body", ""))
# url -> {lang: url} for the language switch and hreflang
ALT = {}
for _l, _entries in TR.items():
    for _src, _e in _entries.items():
        ALT.setdefault(_src, {"cs": _src})[_l] = _e["url"]
for _src in list(ALT):
    for _u in ALT[_src].values():
        ALT[_u] = ALT[_src]


def page_title(url):
    p = PAGES.get(url)
    return p["title"] if p else url




def localized_nav(lang):
    """The Czech menu tree with each node replaced by its translation; untranslated pages drop out."""
    if lang == "cs":
        return SITE["nav"]
    tr = TR[lang]
    def walk(nodes):
        out = []
        for n in nodes:
            e = tr.get(n["url"])
            if n["url"] == "/aktuality/":
                out.append({"url": "/aktuality/", "title": I18N[lang]["newsCzech"]})
            elif e:
                out.append({"url": e["url"], "title": e.get("navTitle") or e["title"], "children": walk(n.get("children", []))})
        return out
    return walk(SITE["nav"])


# navigation index per language: url -> {node, parent, top}
def _index(index, nodes, parent=None, top=None):
    for n in nodes:
        n.setdefault("title", page_title(n["url"]))
        index[n["url"]] = {"node": n, "parent": parent, "top": top or n["url"]}
        _index(index, n.get("children", []), n["url"], top or n["url"])


NAVS = {l: localized_nav(l) for l in LANGS}
NAV_INDEX = {l: {} for l in LANGS}
for _l in LANGS:
    _index(NAV_INDEX[_l], NAVS[_l])


def breadcrumbs(url, lang="cs"):
    trail, idx = [], NAV_INDEX[lang]
    while url in idx:
        trail.insert(0, (idx[url]["node"]["title"], url))
        url = idx[url]["parent"]
    return trail


# ---------------------------------------------------------------- helpers


def image_size(rel_url):
    """Width/height of a local JPEG, PNG or WebP (for layout-stable <img>)."""
    f = STATIC / rel_url.lstrip("/").replace("%20", " ")
    if not f.exists():
        from urllib.parse import unquote
        f = STATIC / unquote(rel_url.lstrip("/"))
    try:
        b = f.read_bytes()[:65536]
    except OSError:
        return None
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24])
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        c = b[12:16]
        if c == b"VP8 ":
            w, h = struct.unpack("<HH", b[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if c == b"VP8L":
            v = int.from_bytes(b[21:25], "little")
            return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
        if c == b"VP8X":
            return int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            marker, length = b[i + 1], struct.unpack(">H", b[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return w, h
            i += 2 + length
    return None


def img(src, alt, cls="", sizes=None, eager=False, srcset=None):
    wh = image_size(src)
    dims = f' width="{wh[0]}" height="{wh[1]}"' if wh else ""
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    responsive = f' srcset="{esc(srcset)}" sizes="{esc(sizes)}"' if srcset and sizes else ""
    return f'<img class="ph-img {cls}" src="{esc(src)}"{responsive} alt="{esc(alt)}"{dims} {load} decoding="async">'


def enhance_body(body):
    """Layout-stable lazy images and scrollable tables in imported content."""
    def fix_img(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        if not src:
            return tag
        wh = image_size(html.unescape(src.group(1))) if src.group(1).startswith("/") else None
        extra = f' width="{wh[0]}" height="{wh[1]}"' if wh else ""
        return tag[:-1] + f'{extra} loading="lazy" decoding="async" class="ph-img">'
    body = re.sub(r"<img [^>]+>", fix_img, body)
    body = re.sub(r"<table>", '<div class="table-wrap" tabindex="0"><table>', body)
    return body.replace("</table>", "</table></div>")


def plain(html_text, n=180):
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", html_text))).strip()
    return t if len(t) <= n else t[: t.rfind(" ", 0, n)] + "…"


def fmt_date(iso, lang="cs"):
    d = datetime.fromisoformat(iso[:10])
    m = I18N[lang]["months"][d.month - 1]
    if lang == "cs":
        return f"{d.day}. {m} {d.year}"
    if lang == "en":
        return f"{d.day} {m} {d.year}"
    if lang == "de":
        return f"{d.day}. {m} {d.year}"
    return f"{d.day} {m} {d.year}"


def short_date(iso):
    d = datetime.fromisoformat(iso[:10])
    return f"{d.day}. {d.month}. {d.year}"


# ---------------------------------------------------------------- Grand Magistry feed


def gm_feed(lang, limit=3):
    """Latest Grand Magistry headlines at build time. Text only; links must stay on orderofmalta.int."""
    url = SITE["gm"].get(lang, SITE["gm"]["en"]).get("feed")
    if not url or "--offline" in sys.argv:
        return []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "maltezskyrad.cz site build (+https://www.maltezskyrad.cz)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read(2_000_000)
        items = []
        for it in ET.fromstring(data).iter("item"):
            link, title, date = it.findtext("link", ""), it.findtext("title", ""), it.findtext("pubDate", "")
            if link.startswith("https://www.orderofmalta.int/") and title:
                d = datetime.strptime(date[:16], "%a, %d %b %Y").date().isoformat() if date else ""
                items.append({"title": title.strip(), "link": link.strip(), "date": d})
            if len(items) >= limit:
                break
        return items
    except Exception as e:
        print(f"  (Grand Magistry feed unavailable: {e})")
        return []


# ---------------------------------------------------------------- layout

FONTS_PRELOAD = ["asap-latin-ext-400-normal", "asap-latin-400-normal", "eb-garamond-latin-500-normal", "eb-garamond-latin-ext-500-normal"]


def home_url(lang):
    return "/" if lang == "cs" else f"/{lang}/"


def lang_switch(lang, url):
    out = []
    for l in LANGS:
        href = ALT.get(url, {}).get(l) or (url if l == lang else home_url(l))
        cur = ' aria-current="true"' if l == lang else ""
        out.append(f'<a href="{href}" lang="{l}" hreflang="{l}"{cur} title="{esc(I18N[l]["langName"])}">{l.upper()}</a>')
    return "".join(out)


def nav_html(lang, current_url):
    top = NAV_INDEX[lang].get(current_url, {}).get("top")
    if current_url.startswith("/aktuality/") or re.match(r"^/\d{4}/", current_url):
        top = "/aktuality/"
    lis = []
    for n in NAVS[lang]:
        cur = ' aria-current="page"' if n["url"] == current_url else (' class="is-active"' if n["url"] == top else "")
        kids = n.get("children", [])
        sub = ""
        if kids:
            sub_items = "".join(f'<li><a href="{c["url"]}">{esc(c["title"])}</a></li>' for c in kids)
            sub = (f'<button class="sub-toggle" type="button" aria-expanded="false" aria-label="{esc(n["title"])}: {esc(I18N[lang]["morePages"])}">'
                   f'<span aria-hidden="true"></span></button><ul class="sub">{sub_items}</ul>')
        lis.append(f'<li class="{"has-sub" if kids else ""}"><a href="{n["url"]}"{cur}>{esc(n["title"])}</a>{sub}</li>')
    return f'<ul class="nav-list">{"".join(lis)}</ul>'


def layout(*, lang, url, title, body, description="", image=None, status=None, alternates=None, main_class=""):
    t, names = I18N[lang], SITE["names"][lang]
    full_title = f"{title} | {names['site']}" if title != names["site"] else title
    canonical = SITE["baseUrl"] + url
    og_image = SITE["baseUrl"] + (image or "/media/2018/07/velkoprevorstvi.jpg")
    robots = "" if PRODUCTION else '<meta name="robots" content="noindex, nofollow">'
    alternates = alternates or ({**ALT[url], "x-default": ALT[url]["cs"]} if url in ALT else None)
    alt_links = "".join(f'<link rel="alternate" hreflang="{l}" href="{SITE["baseUrl"]}{u}">' for l, u in (alternates or {}).items())
    preload = "".join(f'<link rel="preload" href="/fonts/{f}.woff2" as="font" type="font/woff2" crossorigin>' for f in FONTS_PRELOAD)
    ld = ""
    if url == home_url(lang):  # who we are, for search engines (data only, not executed)
        c = SITE["contact"]
        ld = '<script type="application/ld+json">' + json.dumps({
            "@context": "https://schema.org", "@type": "Organization",
            "name": f"{names['order']} – {names['entity']}", "url": canonical, "email": c["email"], "telephone": c["phones"][0],
            "identifier": {"@type": "PropertyValue", "propertyID": "IČO", "value": c["ico"]},
            "address": {"@type": "PostalAddress", "streetAddress": "Velkopřevorské náměstí 485/4", "postalCode": "118 00", "addressLocality": "Praha 1", "addressCountry": "CZ"},
            "sameAs": [s["url"] for s in SITE["social"] if s["owner"] == "České velkopřevorství"],
            "parentOrganization": {"@type": "Organization", "name": names["order"], "url": SITE["gm"][lang]["home"]},
        }, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    status_bar = ""
    if status and not PRODUCTION:
        status_bar = f'<p class="content-status content-status--{esc(status)}"><span>{esc(t["status"].get(status, status))}</span></p>'
    social = "".join(f'<a href="{esc(s["url"])}" rel="noopener">{esc(s["label"])}</a>' for s in SITE["social"])
    footer_nav = "".join(f'<li><a href="{n["url"]}">{esc(n["title"])}</a></li>' for n in NAVS[lang])
    c = SITE["contact"]
    address = c["address"] if lang == "cs" else c["addressIntl"]
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description or plain(body, 160))}">
{robots}
<link rel="canonical" href="{canonical}">
{alt_links}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(names['site'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description or plain(body, 160))}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:locale" content="{ {'cs': 'cs_CZ', 'en': 'en_GB', 'fr': 'fr_FR', 'it': 'it_IT', 'de': 'de_DE'}[lang] }">
<meta name="twitter:card" content="summary_large_image">
{ld}
<meta name="theme-color" content="#e31a18">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/img/favicon/favicon-16x16.png">
<link rel="apple-touch-icon" href="/img/favicon/apple-touch-icon-180x180.png">
<link rel="alternate" type="application/rss+xml" title="{esc(names['site'])}" href="/feed.xml">
{preload}
<link rel="stylesheet" href="/css/site.css?v={ASSET_VERSION}">
<script src="/js/head.js?v={ASSET_VERSION}"></script>
<script src="/js/site.js?v={ASSET_VERSION}" defer></script>
</head>
<body>
<a class="skip" href="#main">{esc(t['skip'])}</a>
<header class="site-header">
 <div class="topbar"><div class="wrap">
  <a class="topbar-home" href="{home_url(lang)}">{esc(names['orderActivities'])} · {esc(names['entity'])}</a>
  <span class="topbar-social">{social}</span>
  <nav class="lang" aria-label="{esc(t['langLabel'])}">{lang_switch(lang, url)}</nav>
 </div></div>
 <div class="banner"><div class="wrap">
  <a class="banner-home" href="{home_url(lang)}"><span class="visually-hidden">{esc(names['site'])}</span></a>
  <p class="fullname">{esc(names['order'])}<span>{esc(names['entity'])}</span></p>
 </div></div>
 <nav class="mainnav" aria-label="{esc(t['menu'])}"><div class="wrap">
  <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="menu">{esc(t['menu'])}</button>
  <div id="menu" class="menu">{nav_html(lang, url)}</div>
 </div></nav>
</header>
<main id="main" class="{main_class}" tabindex="-1">
{status_bar}
{body}
</main>
<footer class="site-footer">
 <div class="f-nav"><div class="wrap"><ul>{footer_nav}</ul></div></div>
 <div class="f-id"><div class="wrap">
  <p class="f-name">{esc(names['order'])} – {esc(names['entity'])}</p>
  <p>{esc(address)} · {esc(t['ico'])} {c['ico']} · <a href="mailto:{c['email']}">{c['email']}</a> · {' · '.join(c['phones'])}</p>
 </div></div>
 <div class="f-red"><div class="wrap">
  <p>{esc(names['orderShort'])}: <a href="{SITE['gm'].get(lang, SITE['gm']['en'])['home']}">www.orderofmalta.int</a></p>
  <p>Maltézská pomoc: <a href="https://maltezskapomoc.cz/">www.maltezskapomoc.cz</a></p>
  <p><a href="{localized('/ostatni/zasady-prijimani-daru/', lang)}">{esc(t['giftPolicy'])}</a> · <a href="{localized('/ochrana-osobnich-udaju/', lang)}">{esc(t['privacy'])}</a></p>
 </div></div>
</footer>
</body>
</html>
"""


# ---------------------------------------------------------------- shared blocks


def calendar_widget(lang, view="month"):
    a = SITE["addcal"]
    t = I18N[lang]
    return f"""<div class="cal-widget" data-state="loading">
 <div class="skeleton cal-skeleton" aria-hidden="true">{''.join('<span></span>' for _ in range(7))}</div>
 <addcal-calendar class="addcal-host" data-calendar-uid="{a['calendarUid']}" data-lang="{lang}" data-initial-view="{view}" data-first-day="1" data-timezone="Europe/Prague" data-theme="light" data-accent-color="#e31a18" data-time-format="24"></addcal-calendar>
 <p class="cal-loading" role="status">{esc(t['calendarLoading'])}</p>
 <p class="cal-fallback">{esc(t['calendarFallback'])} <a href="{a['publicUrl']}">{a['publicUrl'].replace('https://', '')}</a></p>
</div>"""


def services_list(lang="cs", lent=False):
    rows = [(s["day"][lang], s["what"][lang], s["time"]) for s in SITE["services"]]
    if lent:
        rows += [(CAL["lentDay"][lang], x["title"][lang], x["time"]) for x in CAL["lent"]]
    return '<dl class="services">' + "".join(f'<div><dt>{esc(d)}<span>{esc(w)}</span></dt><dd>{esc(t)}</dd></div>' for d, w, t in rows) + "</dl>"


def day_month(iso, lang):
    """'11. ledna', '11 January', '11 janvier', '11 gennaio', '11. Januar'."""
    d = datetime.fromisoformat(iso)
    m = I18N[lang]["months"][d.month - 1]
    return f"{d.day}. {m}" if lang in ("cs", "de") else f"{d.day} {m}"


def date_span(start, end, lang):
    if not end:
        return day_month(start, lang)
    a, b = datetime.fromisoformat(start), datetime.fromisoformat(end)
    if a.month == b.month:
        return f"{a.day}.–{day_month(end, lang)}" if lang in ("cs", "de") else f"{a.day}–{day_month(end, lang)}"
    return f"{day_month(start, lang)} – {day_month(end, lang)}"


def dated_list(rows):
    """rows: (iso date, label html, detail text)"""
    return '<ul class="dated-list">' + "".join(
        f'<li><time datetime="{d}">{lbl}</time><div><b>{title}</b>{f"<span>{esc(det)}</span>" if det else ""}</div></li>' for d, lbl, title, det in rows) + "</ul>"


def year_events(lang):
    rows = []
    for e in CAL["events"]:
        place = e.get("place")
        place = CAL["church"][lang] if place == "church" else (place.get(lang) if isinstance(place, dict) else place)
        detail = " · ".join(x for x in (place, e.get("time"), (e.get("note") or {}).get(lang)) if x)
        rows.append((e["date"], esc(date_span(e["date"], e.get("end"), lang)), esc(e["title"][lang]), detail))
    return dated_list(rows)


def order_feasts(lang):
    y = CAL["year"]
    return dated_list([(f"{y}-{md}", esc(day_month(f"{y}-{md}", lang)),
                        (f"<strong>{esc(t[lang])}</strong>" if len(f) > 2 else esc(t[lang])), "") for f in CAL["feasts"] for md, t in [f[:2]]])


def concerts(lang):
    c = CAL["concerts"]
    return dated_list([(d, esc(day_month(d, lang)), esc(c["title"][lang]), f'{CAL["church"][lang]} · {c["time"]}') for d in c["dates"]])


def downloads_list(lang="cs"):
    items = []
    for d, key in zip(SITE["calendarFiles"], ("calMonthly", "calYear")):
        pairs = d["files"] if lang == "cs" else [(lbl, f) for lbl, f in d["files"] if "English" in lbl]
        files = "".join(f'<a href="{f}">{esc(label)} <span class="file-meta">PDF</span></a>' for label, f in pairs)
        note = d["note"] if lang == "cs" else I18N[lang]["pdfEnglish"]
        items.append(f'<li><b>{esc(I18N[lang][key])}</b><span class="dl-note">{esc(note)}</span><span class="dl-files">{files}</span></li>')
    return f'<ul class="downloads">{"".join(items)}</ul>'


def contact_card(lang):
    c, t = SITE["contact"], I18N[lang]
    addr = c["address"] if lang == "cs" else c["addressIntl"]
    phones = "<br>".join(f'<a href="tel:{p.replace(" ", "")}">{p}</a>' for p in c["phones"])
    return f"""<dl class="contact-card">
 <div><dt>{esc(t['address'])}</dt><dd>{esc(addr)}<br><a href="{esc(c['mapUrl'])}">{esc(t['map'])}</a></dd></div>
 <div><dt>{esc(t['phone'])}</dt><dd>{phones}</dd></div>
 <div><dt>{esc(t['email'])}</dt><dd><a href="mailto:{c['email']}">{c['email']}</a></dd></div>
</dl>"""


def news_item(n, lang="cs", compact=False):
    excerpt = "" if compact or not n.get("excerpt") else f'<p class="n-excerpt">{esc(n["excerpt"])}</p>'
    return (f'<li class="n-item"><time datetime="{n["date"][:10]}">{short_date(n["date"])}</time>'
            f'<div><a href="{n["url"]}">{esc(n["title"])}</a>{excerpt}</div></li>')


# ---------------------------------------------------------------- pages


def localized(url, lang):
    """Link target for a Czech URL in another language (falls back to the Czech page)."""
    return url if url.startswith("http") else ALT.get(url, {}).get(lang, url)


def render_home(lang="cs"):
    t, names = I18N[lang], SITE["names"][lang]
    officers = "".join(f'<div><dt>{esc(t["princeGrandPrior"])}</dt><dd>{esc(o["name"])}</dd></div>' for o in SITE["officers"])
    links = zip(t["homeLinks"], ("/rad-a-jeho-instituce/historie-ceskeho-velkoprevorstvi/", "/rad-a-jeho-instituce/predstavitele-ceskeho-velkoprevorstvi/", "/velkoprevorsky-palac/"))
    links_html = "".join(f'<a href="{localized(u, lang)}">{esc(label)}</a>' for label, u in links)
    feed = gm_feed(lang)
    feed_html = ""
    if feed:
        feed_html = '<ul class="gm-feed">' + "".join(
            f'<li><time datetime="{f["date"]}">{short_date(f["date"]) if f["date"] else ""}</time><a href="{esc(f["link"])}"{" lang=" + chr(34) + "en" + chr(34) if lang == "cs" else ""}>{esc(f["title"])}</a></li>' for f in feed) + "</ul>"
    works_html = "".join(f'<li><a href="{localized(u, lang)}"><b>{esc(a)}</b><span>{esc(b)}</span></a></li>' for a, b, u in t["works"])
    cal_url, act_url = localized("/kalendar/", lang), localized("/cinnosti-maltezskeho-radu-v-ceske-republice/", lang)
    if lang == "cs":
        news_band = f"""<section class="band band-grey" aria-labelledby="news-title"><div class="wrap split">
 <div class="split-head"><h2 id="news-title" class="display-m">{esc(t['news'])}</h2><p><a class="link-strong" href="/aktuality/">{esc(t['allNews'])}</a></p></div>
 <ol class="news-list">{"".join(news_item(n, compact=True) for n in NEWS[:5])}</ol>
</div></section>"""
    else:
        news_band = f"""<section class="band band-grey" aria-labelledby="news-title"><div class="wrap">
 <div class="split-head"><h2 id="news-title" class="display-m">{esc(t['news'])}</h2><p>{esc(t['newsInCzech'])} <a class="link-strong" href="/aktuality/" hreflang="cs">{esc(t['newsCzech'])}</a></p></div>
</div></section>"""
    body = f"""
<section class="home-open" aria-labelledby="home-title"><div class="wrap home-intro">
 <div class="home-intro-main reveal">
  <h1 id="home-title" class="display">{esc(names['entity'])}</h1>
  <p class="lead">{esc(t['homeLead'])}</p>
  <p>{t['homeText']}</p>
 </div>
 <div class="home-intro-facts reveal">
  <dl class="facts">{officers}
   <div><dt>{esc(t['seat'])}</dt><dd>{esc(t['seatValue'])}</dd></div>
   <div><dt>{esc(t['orderChurch'])}</dt><dd><a href="{localized('/radovy-kostel-panny-marie-pod-retezem/o-kostele/', lang)}">{esc(t['orderChurchValue'])}</a></dd></div>
  </dl>
  <p class="text-links">{links_html}</p>
 </div>
</div></section>

<section class="band band-grey" id="kalendar" aria-labelledby="cal-title"><div class="wrap">
 <div class="section-head"><h2 id="cal-title" class="display-m">{esc(t['calendarTitle'])}</h2><p>{esc(t['calendarLead'])}</p></div>
 <div class="cal-grid">
  <div class="cal-side">
   <h3 class="display-s">{esc(t['regularServices'])}</h3>
   <p class="small">{esc(t['churchPlace'])}</p>
   {services_list(lang)}
   <p><a class="link-strong" href="{cal_url}">{esc(t['fullCalendar'])}</a></p>
  </div>
  {calendar_widget(lang, 'schedule')}
 </div>
 <div class="dl-block"><h3 class="display-s">{esc(t['calendar2027'])}</h3>{downloads_list(lang)}</div>
</div></section>

<section class="band" aria-labelledby="works-title"><div class="wrap split">
 <div class="split-head"><h2 id="works-title" class="display-m">{esc(t['service'])}</h2><p>{esc(t['serviceText'])}</p><p><a class="link-strong" href="{act_url}">{esc(t['allActivities'])}</a></p></div>
 <ul class="works">{works_html}</ul>
</div></section>

{news_band}

<section class="band" aria-labelledby="order-title"><div class="wrap{' split' if feed_html else ''}">
 <div class="split-head"><h2 id="order-title" class="display-m">{esc(t['oneOrder'])}</h2><p>{esc(t['oneOrderText'])}</p><p><a class="link-strong" href="{SITE['gm'][lang]['home']}">{esc(t['gmLink'])}</a></p></div>
 <div>{('<h3 class="display-s">' + esc(t['gmNews']) + '</h3>' + feed_html) if feed_html else ''}</div>
</div></section>
"""
    alts = {l: home_url(l) for l in LANGS}
    alts["x-default"] = "/"
    return layout(lang=lang, url=home_url(lang), title=names["site"], body=body, alternates=alts, status="new" if lang == "cs" else "translation",
                  description=t.get("homeDescription") or f"{names['entity']} – {names['order']}.")


def page_for(url, lang):
    """The page record behind a URL in a language (a translation entry or a Czech page)."""
    if lang == "cs":
        return PAGES.get(url, {})
    return next((e for e in TR[lang].values() if e["url"] == url), {})


def section_children_html(url, lang="cs"):
    kids = NAV_INDEX[lang].get(url, {}).get("node", {}).get("children", [])
    if not kids:
        return ""
    items = []
    for k in kids:
        p = page_for(k["url"], lang)
        desc = p.get("description") or plain(p.get("body", ""), 150)
        items.append(f'<li><a href="{k["url"]}"><b>{esc(k["title"])}</b>{f"<span>{esc(desc)}</span>" if desc else ""}</a></li>')
    return f'<ul class="index-list">{"".join(items)}</ul>'


def side_nav(url, lang="cs"):
    info = NAV_INDEX[lang].get(url)
    if not info:
        return ""
    top = NAV_INDEX[lang][info["top"]]["node"]
    def walk(nodes, depth=0):
        out = []
        for n in nodes:
            cur = ' aria-current="page"' if n["url"] == url else ""
            sub = ""
            if n.get("children") and (n["url"] == url or url in _descendants(n)):
                sub = walk(n["children"], depth + 1)
            out.append(f'<li><a href="{n["url"]}"{cur}>{esc(n["title"])}</a>{sub}</li>')
        return f'<ul>{"".join(out)}</ul>'
    if not top.get("children") or info["top"] == url:  # a section's own page already lists its children
        return ""
    return (f'<nav class="side-nav" aria-label="{esc(I18N[lang]["inSection"])}"><p class="label">'
            f'<a href="{top["url"]}">{esc(top["title"])}</a></p>{walk(top["children"])}</nav>')


def _descendants(node):
    out = set()
    for c in node.get("children", []):
        out.add(c["url"])
        out |= _descendants(c)
    return out


def crumbs_html(url, extra=None, lang="cs"):
    trail = [(I18N[lang]["home"], home_url(lang))] + breadcrumbs(url, lang) + (extra or [])
    if len(trail) < 2:
        return ""
    items = []
    for i, (t, u) in enumerate(trail):
        last = i == len(trail) - 1
        items.append(f'<li>{"<span aria-current=" + chr(34) + "page" + chr(34) + ">" + esc(t) + "</span>" if last else f"<a href={chr(34)}{u}{chr(34)}>{esc(t)}</a>"}</li>')
    return f'<nav class="crumbs" aria-label="{esc(I18N[lang]["breadcrumb"])}"><ol>{"".join(items)}</ol></nav>'


EMBLEM_BLOCKS = {
    "armorial-bearing": lambda lang: (
        '<figure class="emblem"><picture><source type="image/webp" srcset="/img/emblems/armorial-bearing-420.webp 420w, /img/emblems/armorial-bearing-840.webp 840w" sizes="(max-width: 700px) 50vw, 210px">'
        + img("/img/emblems/armorial-bearing-420.webp", I18N[lang]["armsAlt"]) + "</picture></figure>"),
}


def render_page(p, lang="cs"):
    url, src, t = p["url"], p.get("source", p["url"]), I18N[lang]
    cs = PAGES.get(src, {})
    is_section = cs.get("section") or bool(NAV_INDEX[lang].get(url, {}).get("node", {}).get("children"))
    lead_img = p.get("image", cs.get("image"))
    figure = ""
    if lead_img:
        figure = f'<figure class="page-figure">{img(lead_img, p.get("imageAlt") or p["title"], eager=True)}</figure>'
    emblem_key = cs.get("emblem")
    emblem = EMBLEM_BLOCKS[emblem_key](lang) if emblem_key in EMBLEM_BLOCKS else ""
    body = enhance_body(p["body"])
    children = section_children_html(url, lang) if is_section else ""
    cal_url = ALT.get("/kalendar/", {}).get(lang, "/kalendar/")
    special = ""
    if src == "/kontakt/":
        emb = ALT.get("/diplomaticke-vztahy/velvyslanectvi-radu-v-ceske-republice/", {}).get(lang, "/diplomaticke-vztahy/velvyslanectvi-radu-v-ceske-republice/")
        special = contact_card(lang) + f'<p class="small">{esc(t["embassyNote"])} <a href="{emb}">{esc(t["contact"])}</a>.</p>'
    if src == "/radovy-kostel-panny-marie-pod-retezem/bohosluzby/":
        special = (f'<h2>{esc(t["regularServices"])}</h2><p class="small">{esc(t["churchPlace"])}</p>' + services_list(lang, lent=True)
                   + f'<p><a class="link-strong" href="{cal_url}">{esc(t["fullCalendar"])}</a></p>'
                   + f'<h2>{esc(t["feasts"])}</h2><p class="small">{esc(t["feastsLead"])}</p>' + order_feasts(lang))
    if src == "/koncerty/":
        special = f'<h2>{esc(t["concerts"])}</h2><p class="small">{esc(t["concertsLead"])}</p>' + concerts(lang)
    side = side_nav(url, lang)
    html_body = f"""
<div class="wrap">{crumbs_html(url, lang=lang)}</div>
<article class="wrap page{' page--with-side' if side else ''}">
 <header class="page-head reveal">
  {emblem}
  <h1 class="display">{esc(p['title'])}</h1>
 </header>
 <div class="page-main">
  {figure}
  <div class="prose">{body}</div>
  {special}
  {children}
 </div>
 {f'<div class="page-side">{side}</div>' if side else ''}
</article>"""
    return layout(lang=lang, url=url, title=p["title"], body=html_body, description=p.get("description", ""),
                  image=lead_img, status=p.get("status", "translation" if lang != "cs" else None))


GENERIC_IMAGES = {"/media/2018/06/koncert.jpg", "/media/2018/06/ob%C4%8Dasn%C3%ADk.png", "/media/2018/06/občasník.png"}


def render_article(n, prev_n, next_n):
    cats = SITE["newsCategories"]
    cat_links = " · ".join(f'<a href="/aktuality/{c}/">{esc(cats.get(c, c))}</a>' for c in n.get("categories", []) if c in cats)
    figure = ""
    if n.get("image") and n["image"] not in GENERIC_IMAGES:
        figure = f'<figure class="page-figure">{img(n["image"], n["title"], eager=True)}</figure>'
    pager = ""
    if prev_n or next_n:
        pager = '<nav class="pager" aria-label="Další články">' + \
            (f'<a class="pager-prev" href="{next_n["url"]}"><span>Novější</span>{esc(next_n["title"])}</a>' if next_n else "<span></span>") + \
            (f'<a class="pager-next" href="{prev_n["url"]}"><span>Starší</span>{esc(prev_n["title"])}</a>' if prev_n else "") + "</nav>"
    body = f"""
<div class="wrap">{crumbs_html('/aktuality/', [(n['title'], n['url'])])}</div>
<article class="wrap page page--article">
 <header class="page-head reveal">
  <h1 class="display">{esc(n['title'])}</h1>
  <p class="byline"><time datetime="{n['date'][:10]}">{fmt_date(n['date'])}</time>{(' · ' + cat_links) if cat_links else ''}</p>
 </header>
 <div class="page-main">
  {figure}
  <div class="prose">{enhance_body(n['body'])}</div>
  <p><a class="link-strong" href="/aktuality/">{esc(I18N['cs']['backToNews'])}</a></p>
  {pager}
 </div>
</article>"""
    return layout(lang="cs", url=n["url"], title=n["title"], body=body, description=n.get("excerpt", ""),
                  image=n.get("image") if n.get("image") not in GENERIC_IMAGES else None, status=n.get("status"))


def render_news_index(items, active="", year=None, url="/aktuality/"):
    cats = SITE["newsCategories"]
    counts = {c: sum(1 for n in NEWS if c in n.get("categories", [])) for c in cats}
    tabs = [f'<a href="/aktuality/"{" aria-current=" + chr(34) + "page" + chr(34) if not active and not year else ""}>{esc(I18N["cs"]["allCategories"])}</a>']
    for c, label in cats.items():
        if counts[c]:
            cur = ' aria-current="page"' if active == c else ""
            tabs.append(f'<a href="/aktuality/{c}/"{cur}>{esc(label)} <span class="count">{counts[c]}</span></a>')
    years = sorted({n["date"][:4] for n in NEWS}, reverse=True)
    year_links = "".join(f'<a href="/aktuality/{y}/"{" aria-current=" + chr(34) + "page" + chr(34) if year == y else ""}>{y}</a>' for y in years)
    groups, cur_year = [], None
    for n in items:
        y = n["date"][:4]
        if y != cur_year:
            if cur_year:
                groups.append("</ol></section>")
            groups.append(f'<section class="year-group"><h2 class="year">{y}</h2><ol class="news-list news-list--full">')
            cur_year = y
        groups.append(news_item(n))
    if cur_year:
        groups.append("</ol></section>")
    title = "Aktuality" + (f": {cats[active]}" if active else "") + (f" {year}" if year else "")
    body = f"""
<div class="wrap">{crumbs_html('/aktuality/', [(title, url)] if url != '/aktuality/' else None)}</div>
<div class="wrap page page--news">
 <header class="page-head reveal"><h1 class="display">{esc(title)}</h1>
  <p class="lead-s">Zprávy o činnosti Českého velkopřevorství, provozu řádového kostela a koncertech. Zprávy Řádu z celého světa najdete na <a href="https://www.orderofmalta.int/news/">orderofmalta.int</a>.</p></header>
 <nav class="tabs" aria-label="{esc(I18N['cs']['category'])}">{''.join(tabs)}</nav>
 <nav class="years" aria-label="{esc(I18N['cs']['year'])}">{year_links}</nav>
 {''.join(groups) or '<p class="empty">V této rubrice zatím nejsou žádné zprávy.</p>'}
</div>"""
    return layout(lang="cs", url=url, title=title, body=body,
                  description="Aktuality Českého velkopřevorství Maltézského řádu: zprávy, koncerty a provoz řádového kostela.")


def render_calendar_page(lang="cs"):
    t = I18N[lang]
    e = TR[lang]["/kalendar/"] if lang != "cs" else {"url": "/kalendar/", "title": "Kalendář", "description": "Kalendář bohoslužeb, svátků a akcí Českého velkopřevorství Maltézského řádu; Kalendář 2027 ke stažení."}
    body = f"""
<div class="wrap">{crumbs_html(e['url'], lang=lang)}</div>
<div class="wrap page page--calendar">
 <header class="page-head reveal"><h1 class="display">{esc(e['title'])}</h1><p class="lead-s">{esc(t['calendarLead'])}</p></header>
 {calendar_widget(lang, 'month')}
 <p class="subscribe"><a class="btn" href="{SITE['addcal']['publicUrl']}">{esc(t['subscribe'])}</a><span class="small">{esc(t['subscribeNote'])}</span></p>
 <div class="cal-below">
  <section aria-labelledby="svc"><h2 id="svc" class="display-s">{esc(t['regularServices'])}</h2><p class="small">{esc(t['churchPlace'])}</p>{services_list(lang, lent=True)}</section>
  <section aria-labelledby="dl"><h2 id="dl" class="display-s">{esc(t['calendar2027'])}</h2>{downloads_list(lang)}</section>
 </div>
 <section class="cal-year" aria-labelledby="yr"><h2 id="yr" class="display-s">{esc(t['yearEvents'])}</h2><p class="small">{esc(t['yearEventsLead'])}</p>{year_events(lang)}</section>
</div>"""
    return layout(lang=lang, url=e["url"], title=e["title"], body=body, status="new" if lang == "cs" else "translation", description=e["description"])


def render_simple(url, title, inner, lang="cs", status=None):
    body = f'<div class="wrap page page--simple"><header class="page-head"><h1 class="display">{esc(title)}</h1></header><div class="prose">{inner}</div></div>'
    return layout(lang=lang, url=url, title=title, body=body, status=status)


# ---------------------------------------------------------------- output


def write(url, html_text):
    path = DIST / url.lstrip("/") / "index.html" if url.endswith("/") else DIST / url.lstrip("/")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")


def rss():
    items = "".join(
        f"<item><title>{esc(n['title'])}</title><link>{SITE['baseUrl']}{n['url']}</link><guid>{SITE['baseUrl']}{n['url']}</guid>"
        f"<pubDate>{datetime.fromisoformat(n['date']).strftime('%a, %d %b %Y %H:%M:00 +0100')}</pubDate><description>{esc(n.get('excerpt', ''))}</description></item>"
        for n in NEWS[:30])
    return (f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(SITE["names"]["cs"]["site"])}</title>'
            f'<link>{SITE["baseUrl"]}/</link><description>Aktuality Českého velkopřevorství</description><language>cs</language>{items}</channel></rss>')


VERCEL = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))  # headers and redirects live here; other hosts get _headers and _redirects
HEADERS = "".join(h["source"].replace("(.*)", "*") + "\n" + "".join(f"  {x['key']}: {x['value']}\n" for x in h["headers"]) for h in VERCEL["headers"])
REDIRECTS = [(r["source"].replace(":path*", "*"), r["destination"].replace(":path*", ":splat")) for r in VERCEL["redirects"]]


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(STATIC, DIST)
    for lang in LANGS:
        write(home_url(lang), render_home(lang))
        write(TR[lang]["/kalendar/"]["url"] if lang != "cs" else "/kalendar/", render_calendar_page(lang))
    for url, p in PAGES.items():
        write(url, render_page(p))
    for lang, entries in TR.items():
        for src, e in entries.items():
            if src in ("/kalendar/", "/ochrana-osobnich-udaju/"):
                continue
            write(e["url"], render_page(e, lang))
        pv = entries["/ochrana-osobnich-udaju/"]
        write(pv["url"], render_simple(pv["url"], pv["title"], pv["body"], lang=lang, status="translation"))
    for i, n in enumerate(NEWS):
        write(n["url"], render_article(n, NEWS[i + 1] if i + 1 < len(NEWS) else None, NEWS[i - 1] if i else None))
    write("/aktuality/", render_news_index(NEWS[:40]))
    for c in SITE["newsCategories"]:
        items = [n for n in NEWS if c in n.get("categories", [])]
        if items:
            write(f"/aktuality/{c}/", render_news_index(items, active=c, url=f"/aktuality/{c}/"))
    for y in sorted({n["date"][:4] for n in NEWS}):
        write(f"/aktuality/{y}/", render_news_index([n for n in NEWS if n["date"].startswith(y)], year=y, url=f"/aktuality/{y}/"))
    write("/ochrana-osobnich-udaju/", render_simple("/ochrana-osobnich-udaju/", "Ochrana osobních údajů", PRIVACY, status="approval"))
    write("/404.html", render_simple("/404.html", I18N["cs"]["notFound"],
                                     f'<p>{esc(I18N["cs"]["notFoundText"])}</p><p><a class="link-strong" href="/">Úvodní stránka</a> · <a class="link-strong" href="/aktuality/">Aktuality</a> · <a class="link-strong" href="/kalendar/">Kalendář</a></p>'))
    urls = ["/", "/kalendar/", "/aktuality/", "/ochrana-osobnich-udaju/"] + [f"/{l}/" for l in LANGS[1:]] + list(PAGES) + [n["url"] for n in NEWS] + \
        [e["url"] for entries in TR.values() for e in entries.values()]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
                                      "".join(f"<url><loc>{SITE['baseUrl']}{u}</loc></url>" for u in urls) + "</urlset>", encoding="utf-8")
    (DIST / "robots.txt").write_text(("User-agent: *\nAllow: /\n\nSitemap: " + SITE["baseUrl"] + "/sitemap.xml\n") if PRODUCTION
                                     else "User-agent: *\nDisallow: /\n", encoding="utf-8")
    (DIST / "feed.xml").write_text(rss(), encoding="utf-8")
    (DIST / "_headers").write_text(HEADERS + ("" if PRODUCTION else "/*\n  X-Robots-Tag: noindex, nofollow\n"), encoding="utf-8")
    (DIST / "_redirects").write_text("".join(f"{a} {b} 301\n" for a, b in REDIRECTS), encoding="utf-8")
    print(f"built {len(PAGES)} pages, {len(NEWS)} news, translations {', '.join(f'{l} {len(e)}' for l, e in TR.items())}, {'production' if PRODUCTION else 'preview'} → {DIST}")


PRIVACY = """<h2>Správce</h2>
<p>Správcem osobních údajů je Suverénní řád maltézských rytířů – České velkopřevorství, IČO 00569623, se sídlem Velkopřevorské náměstí 485/4, 118 00 Praha 1 – Malá Strana. Dotazy a žádosti týkající se osobních údajů posílejte na <a href="mailto:gpb@smom.cz">gpb@smom.cz</a> nebo na uvedenou adresu.</p>
<h2>Cookies a měření návštěvnosti</h2>
<p>Tento web nepoužívá cookies ani analytické a reklamní nástroje a nesleduje návštěvníky. Písma a obrázky se načítají přímo z tohoto webu.</p>
<h2>Provoz webu</h2>
<p>Web běží na serverech společnosti Vercel Inc. (USA). Při každé návštěvě zpracují údaje nutné k doručení stránky a k ochraně webu před zneužitím (IP adresa, čas a adresa požadavku, údaje o prohlížeči). Právním základem je náš oprávněný zájem na bezpečném provozu webu (čl. 6 odst. 1 písm. f) GDPR). Záznamy se uchovávají jen krátce, nejsou-li potřeba k vyřešení bezpečnostního incidentu. Předání do USA se řídí rámcem EU–USA pro ochranu osobních údajů (Data Privacy Framework). Více v <a href="https://vercel.com/legal/privacy-notice">zásadách ochrany soukromí Vercel</a>.</p>
<h2>Kalendář AddCal</h2>
<p>Na úvodních stránkách a stránkách Kalendáře ve všech jazykových verzích se zobrazuje kalendář služby AddCal (AddCal Pty Ltd, Austrálie). Načte se, až když k němu na stránce dojdete. Prohlížeč přitom odešle službě AddCal technické údaje nutné k zobrazení (IP adresu a údaje o prohlížeči). Kalendář si do úložiště prohlížeče uloží seznam časových pásem, aby se příště načetl rychleji; tento seznam neobsahuje osobní údaje. Právním základem je náš oprávněný zájem na zveřejnění programu Velkopřevorství. Pro předání údajů mimo EU používá AddCal standardní smluvní doložky. Více v <a href="https://addcal.co/privacy-policy">zásadách ochrany soukromí AddCal</a>. Kalendář si můžete prohlédnout také přímo na adrese <a href="https://addcal.co/c/calendarGPB">addcal.co/c/calendarGPB</a>.</p>
<h2>E-mail a telefon</h2>
<p>Napíšete-li nám nebo zavoláte-li, použijeme vaše údaje jen k vyřízení vaší zprávy a uchováme je po dobu, kterou to vyžaduje. Právním základem je náš oprávněný zájem odpovídat na dotazy.</p>
<h2>Odkazy na jiné weby</h2>
<p>Odkazy na Facebook, YouTube, LinkedIn a další weby jsou obyčejné odkazy: dokud na ně neklepnete, těmto službám se nic nepředává. Poté platí jejich zásady ochrany soukromí.</p>
<h2>Vaše práva</h2>
<p>Máte právo na přístup ke svým osobním údajům, na jejich opravu nebo výmaz, na omezení zpracování a na přenositelnost údajů a právo vznést námitku proti zpracování založenému na oprávněném zájmu. Máte také právo podat stížnost u Úřadu pro ochranu osobních údajů, Pplk. Sochora 27, 170 00 Praha 7, <a href="https://uoou.gov.cz/">uoou.gov.cz</a>.</p>
<p>Poslední aktualizace: 15. října 2026.</p>"""


# ---------------------------------------------------------------- local preview server


def serve(port=8000):
    import http.server
    import functools
    rules = [l.split() for l in (DIST / "_redirects").read_text().splitlines() if l.strip()]
    headers = {}
    block = None
    for line in (DIST / "_headers").read_text().splitlines():
        if line and not line.startswith(" "):
            block = line.strip()
        elif line.strip() and block == "/*":
            k, v = line.strip().split(":", 1)
            headers[k] = v.strip()

    class H(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            for k, v in headers.items():
                if k == "Strict-Transport-Security":
                    continue  # local server is plain HTTP
                if k == "Content-Security-Policy":
                    v = v.replace("; upgrade-insecure-requests", "")
                self.send_header(k, v)
            super().end_headers()

        def do_GET(self):
            path = self.path.split("?")[0]
            for src, dst, _ in rules:
                if src.endswith("*") and path.startswith(src[:-1]):
                    dst = dst.replace(":splat", path[len(src) - 1:])
                elif src != path:
                    continue
                self.send_response(301)
                self.send_header("Location", dst)
                self.end_headers()
                return
            if not (DIST / path.lstrip("/")).exists() and not (DIST / path.lstrip("/") / "index.html").exists():
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write((DIST / "404.html").read_bytes())
                return
            super().do_GET()

        do_HEAD = do_GET

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(H, directory=str(DIST)))
    print(f"serving http://127.0.0.1:{port}/")
    httpd.serve_forever()


if __name__ == "__main__":
    build()
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve(int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8000)
