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
ASSET_VERSION = datetime.now().strftime("%Y%m%d%H%M")
esc = lambda s: html.escape(str(s or ""), quote=True)


# ---------------------------------------------------------------- content


def read_doc(path):
    text = path.read_text(encoding="utf-8")
    _, meta, body = text.split("---\n", 2)
    fix = lambda v: v.replace("Fra´", "Fra’") if isinstance(v, str) else v  # legacy texts use the acute accent
    return {k: fix(v) for k, v in json.loads(meta).items()}, fix(body.strip())


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


def page_title(url):
    p = PAGES.get(url)
    return p["title"] if p else url


# navigation tree: url -> (node, parent_url)
NAV_INDEX = {}


def _index(nodes, parent=None, top=None):
    for n in nodes:
        n.setdefault("title", page_title(n["url"]))
        NAV_INDEX[n["url"]] = {"node": n, "parent": parent, "top": top or n["url"]}
        _index(n.get("children", []), n["url"], top or n["url"])


_index(SITE["nav"])


def breadcrumbs(url):
    trail = []
    while url in NAV_INDEX:
        trail.insert(0, (NAV_INDEX[url]["node"]["title"], url))
        url = NAV_INDEX[url]["parent"]
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


def lang_switch(lang, url):
    out = []
    for l in SITE["languages"]:
        href = "/" if l == "cs" else f"/{l}/"
        if l == "cs" and lang == "cs":
            href = url
        cur = ' aria-current="true"' if l == lang else ""
        out.append(f'<a href="{href}" lang="{l}" hreflang="{l}"{cur} title="{esc(I18N[l]["langName"])}">{l.upper()}</a>')
    return "".join(out)


def nav_html(lang, current_url):
    if lang != "cs":
        items = [(I18N[lang]["home"], f"/{lang}/"), (I18N[lang]["calendar"], f"/{lang}/#kalendar"), (I18N[lang]["contact"], f"/{lang}/#kontakt")]
        lis = "".join(f'<li><a href="{u}">{esc(t)}</a></li>' for t, u in items)
        return f'<ul class="nav-list">{lis}</ul>'
    top = NAV_INDEX.get(current_url, {}).get("top")
    if current_url.startswith("/aktuality/") or re.match(r"^/\d{4}/", current_url):
        top = "/aktuality/"
    lis = []
    for n in SITE["nav"]:
        cur = ' aria-current="page"' if n["url"] == current_url else (' class="is-active"' if n["url"] == top else "")
        kids = n.get("children", [])
        sub = ""
        if kids:
            sub_items = "".join(f'<li><a href="{c["url"]}">{esc(c["title"])}</a></li>' for c in kids)
            sub = (f'<button class="sub-toggle" type="button" aria-expanded="false" aria-label="{esc(n["title"])}: další stránky">'
                   f'<span aria-hidden="true"></span></button><ul class="sub">{sub_items}</ul>')
        lis.append(f'<li class="{"has-sub" if kids else ""}"><a href="{n["url"]}"{cur}>{esc(n["title"])}</a>{sub}</li>')
    return f'<ul class="nav-list">{"".join(lis)}</ul>'


def layout(*, lang, url, title, body, description="", image=None, status=None, alternates=None, main_class=""):
    t, names = I18N[lang], SITE["names"][lang]
    full_title = f"{title} | {names['site']}" if title != names["site"] else title
    canonical = SITE["baseUrl"] + url
    og_image = SITE["baseUrl"] + (image or "/media/2018/07/velkoprevorstvi.jpg")
    robots = "" if PRODUCTION else '<meta name="robots" content="noindex, nofollow">'
    alt_links = "".join(f'<link rel="alternate" hreflang="{l}" href="{SITE["baseUrl"]}{u}">' for l, u in (alternates or {}).items())
    preload = "".join(f'<link rel="preload" href="/fonts/{f}.woff2" as="font" type="font/woff2" crossorigin>' for f in FONTS_PRELOAD)
    status_bar = ""
    if status and not PRODUCTION:
        status_bar = f'<p class="content-status content-status--{esc(status)}"><span>{esc(t["status"].get(status, status))}</span></p>'
    social = "".join(f'<a href="{esc(s["url"])}" rel="noopener">{esc(s["label"])}</a>' for s in SITE["social"])
    footer_nav = "".join(f'<li><a href="{n["url"]}">{esc(n["title"])}</a></li>' for n in SITE["nav"]) if lang == "cs" else \
        f'<li><a href="/{lang}/">{esc(t["home"])}</a></li><li><a href="/">Čeština</a></li>'
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
  <a class="topbar-home" href="{'/' if lang == 'cs' else f'/{lang}/'}">{esc(names['orderActivities'])} · {esc(names['entity'])}</a>
  <span class="topbar-social">{social}</span>
  <nav class="lang" aria-label="{esc(t['langLabel'])}">{lang_switch(lang, url)}</nav>
 </div></div>
 <div class="banner"><div class="wrap">
  <a class="banner-home" href="{'/' if lang == 'cs' else f'/{lang}/'}"><span class="visually-hidden">{esc(names['site'])}</span></a>
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
  <p>{esc(address)} · <a href="mailto:{c['email']}">{c['email']}</a> · {' · '.join(c['phones'])}</p>
 </div></div>
 <div class="f-red"><div class="wrap">
  <p>{esc(names['orderShort'])}: <a href="{SITE['gm'].get(lang, SITE['gm']['en'])['home']}">www.orderofmalta.int</a></p>
  <p>Maltézská pomoc: <a href="https://maltezskapomoc.cz/">www.maltezskapomoc.cz</a></p>
  <p><a href="/ostatni/zasady-prijimani-daru/">{'Zásady přijímání darů' if lang == 'cs' else 'Gift acceptance policy (CZ)'}</a> · <a href="/ochrana-osobnich-udaju/">{esc(t['privacy'])}</a></p>
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


def services_list():
    rows = "".join(f'<div><dt>{esc(s["day"])}<span>{esc(s["what"])}</span></dt><dd>{esc(s["time"])}</dd></div>' for s in SITE["services"])
    return f'<dl class="services">{rows}</dl>'


def downloads_list():
    items = []
    for d in SITE["calendarFiles"]:
        files = "".join(f'<a href="{f}">{esc(label)} <span class="file-meta">PDF</span></a>' for label, f in d["files"])
        items.append(f'<li><b>{esc(d["title"])}</b><span class="dl-note">{esc(d["note"])}</span><span class="dl-files">{files}</span></li>')
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


def render_home():
    t = I18N["cs"]
    officers = "".join(f'<div><dt>{esc(o["role"])}</dt><dd>{esc(o["name"])}</dd></div>' for o in SITE["officers"])
    news = "".join(news_item(n, compact=True) for n in NEWS[:5])
    feed = gm_feed("cs")
    feed_html = ""
    if feed:
        feed_html = '<ul class="gm-feed">' + "".join(
            f'<li><time datetime="{f["date"]}">{short_date(f["date"]) if f["date"] else ""}</time><a href="{esc(f["link"])}" lang="en">{esc(f["title"])}</a></li>' for f in feed) + "</ul>"
    works = [
        ("Maltézská pomoc, o.p.s.", "Sociální služby a dobrovolnické programy pro seniory a lidi v nouzi, založena roku 2002.", "https://maltezskapomoc.cz/"),
        ("Pomoc seniorům a potřebným", "Jak velkopřevorství pomáhá seniorům, lidem se zdravotním postižením a lidem bez domova.", "/cinnosti-maltezskeho-radu-v-ceske-republice/pomoc-seniorum/"),
        ("Školy", "Vyšší odborná škola zdravotnická v Praze 3, Základní škola Maltézských rytířů v Kladně, gymnázium ve Skutči.", "/cinnosti-maltezskeho-radu-v-ceske-republice/skolstvi/"),
        ("Pouť do Lurd", "Každoroční řádová pouť s nemocnými poutníky, jejich zdravotníky a dobrovolníky.", "/cinnosti-maltezskeho-radu-v-ceske-republice/pout-do-lurd/"),
        ("Česká maltézská mládež a další aktivity", "Volnočasové a dobročinné aktivity pro mladé lidi s postižením, katedrální služba.", "/cinnosti-maltezskeho-radu-v-ceske-republice/dalsi-aktivity/"),
    ]
    works_html = "".join(f'<li><a href="{u}"><b>{esc(a)}</b><span>{esc(b)}</span></a></li>' for a, b, u in works)
    body = f"""
<section class="home-open" aria-labelledby="home-title"><div class="wrap home-intro">
 <div class="home-intro-main reveal">
  <h1 id="home-title" class="display">České velkopřevorství</h1>
  <p class="lead">{esc(SITE['names']['cs']['order'])} je v českých zemích přítomen od druhé poloviny 12. století, kdy kníže Vladislav II. daroval johanitům území u paty Juditina mostu. Po potlačení komunisty přežilo velkopřevorství v exilu; v Praze obnovilo činnost 1. dubna 1990.</p>
  <p>Členové velkopřevorství, jeho dobrovolníci a organizace, které založilo, slouží nemocným, seniorům a lidem v nouzi v duchu hesla Řádu <i lang="la">Tuitio fidei et obsequium pauperum</i> – ochrana víry a služba chudým a nemocným.</p>
 </div>
 <div class="home-intro-facts reveal">
  <dl class="facts">{officers}
   <div><dt>Sídlo</dt><dd>Velkopřevorský palác, Velkopřevorské náměstí 4</dd></div>
   <div><dt>Řádový kostel</dt><dd><a href="/radovy-kostel-panny-marie-pod-retezem/o-kostele/">Panna Maria pod řetězem, Lázeňská ulice</a></dd></div>
  </dl>
  <p class="text-links"><a href="/rad-a-jeho-instituce/historie-ceskeho-velkoprevorstvi/">Historie velkopřevorství</a><a href="/rad-a-jeho-instituce/predstavitele-ceskeho-velkoprevorstvi/">Představitelé</a><a href="/velkoprevorsky-palac/">Velkopřevorský palác</a></p>
 </div>
</div></section>

<section class="band band-grey" id="kalendar" aria-labelledby="cal-title"><div class="wrap">
 <div class="section-head"><h2 id="cal-title" class="display-m">Kalendář velkopřevorství</h2><p>{esc(t['calendarLead'])}</p></div>
 <div class="cal-grid">
  <div class="cal-side">
   <h3 class="display-s">{esc(t['regularServices'])}</h3>
   <p class="small">{esc(t['churchPlace'])}</p>
   {services_list()}
   <p><a class="link-strong" href="/kalendar/">Celý kalendář a odběr do telefonu</a></p>
  </div>
  {calendar_widget('cs', 'schedule')}
 </div>
 <div class="dl-block"><h3 class="display-s">{esc(t['calendar2027'])}</h3>{downloads_list()}</div>
</div></section>

<section class="band" aria-labelledby="works-title"><div class="wrap split">
 <div class="split-head"><h2 id="works-title" class="display-m">{esc(t['service'])}</h2><p>{esc(t['serviceText'])}</p><p><a class="link-strong" href="/cinnosti-maltezskeho-radu-v-ceske-republice/">Všechny činnosti</a></p></div>
 <ul class="works">{works_html}</ul>
</div></section>

<section class="band band-grey" aria-labelledby="news-title"><div class="wrap split">
 <div class="split-head"><h2 id="news-title" class="display-m">{esc(t['news'])}</h2><p><a class="link-strong" href="/aktuality/">{esc(t['allNews'])}</a></p></div>
 <ol class="news-list">{news}</ol>
</div></section>

<section class="band" aria-labelledby="order-title"><div class="wrap{' split' if feed_html else ''}">
 <div class="split-head"><h2 id="order-title" class="display-m">{esc(t['oneOrder'])}</h2><p>{esc(t['oneOrderText'])}</p><p><a class="link-strong" href="https://www.orderofmalta.int/">{esc(t['gmLink'])}</a></p></div>
 <div>{('<h3 class="display-s">' + esc(t['gmNews']) + '</h3>' + feed_html) if feed_html else ''}</div>
</div></section>
"""
    alts = {l: ("/" if l == "cs" else f"/{l}/") for l in SITE["languages"]}
    alts["x-default"] = "/"
    return layout(lang="cs", url="/", title=SITE["names"]["cs"]["site"], body=body, alternates=alts, status="new",
                  description="Oficiální web Českého velkopřevorství Suverénního maltézského řádu: historie, představitelé, kalendář bohoslužeb v kostele Panny Marie pod řetězem, činnosti a aktuality.")


def section_children_html(url):
    kids = NAV_INDEX.get(url, {}).get("node", {}).get("children", [])
    if not kids:
        return ""
    items = []
    for k in kids:
        p = PAGES.get(k["url"], {})
        desc = p.get("description") or plain(p.get("body", ""), 150)
        items.append(f'<li><a href="{k["url"]}"><b>{esc(k["title"])}</b>{f"<span>{esc(desc)}</span>" if desc else ""}</a></li>')
    return f'<ul class="index-list">{"".join(items)}</ul>'


def side_nav(url):
    info = NAV_INDEX.get(url)
    if not info:
        return ""
    top = NAV_INDEX[info["top"]]["node"]
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
    return (f'<nav class="side-nav" aria-label="{esc(I18N["cs"]["inSection"])}"><p class="label">'
            f'<a href="{top["url"]}">{esc(top["title"])}</a></p>{walk(top["children"])}</nav>')


def _descendants(node):
    out = set()
    for c in node.get("children", []):
        out.add(c["url"])
        out |= _descendants(c)
    return out


def crumbs_html(url, extra=None):
    trail = [("Úvod", "/")] + breadcrumbs(url) + (extra or [])
    if len(trail) < 2:
        return ""
    items = []
    for i, (t, u) in enumerate(trail):
        last = i == len(trail) - 1
        items.append(f'<li>{"<span aria-current=" + chr(34) + "page" + chr(34) + ">" + esc(t) + "</span>" if last else f"<a href={chr(34)}{u}{chr(34)}>{esc(t)}</a>"}</li>')
    return f'<nav class="crumbs" aria-label="Drobečková navigace"><ol>{"".join(items)}</ol></nav>'


EMBLEM_BLOCKS = {
    "armorial-bearing": lambda: (
        '<figure class="emblem"><picture><source type="image/webp" srcset="/img/emblems/armorial-bearing-420.webp 420w, /img/emblems/armorial-bearing-840.webp 840w" sizes="(max-width: 700px) 50vw, 210px">'
        + img("/img/emblems/armorial-bearing-420.webp", "Znak Suverénního vojenského špitálního řádu svatého Jana Jeruzalémského, z Rhodu a z Malty") + "</picture></figure>"),
}


def render_page(p):
    url = p["url"]
    is_section = p.get("section") or bool(NAV_INDEX.get(url, {}).get("node", {}).get("children"))
    lead_img = p.get("image")
    figure = ""
    if lead_img:
        figure = f'<figure class="page-figure">{img(lead_img, p.get("imageAlt") or p["title"], eager=True)}</figure>'
    emblem = EMBLEM_BLOCKS[p["emblem"]]() if p.get("emblem") in EMBLEM_BLOCKS else ""
    body = enhance_body(p["body"])
    children = section_children_html(url) if is_section else ""
    special = ""
    if url == "/kontakt/":
        special = contact_card("cs") + '<p class="small">Velvyslanectví Suverénního maltézského řádu v České republice: <a href="/diplomaticke-vztahy/velvyslanectvi-radu-v-ceske-republice/">kontakt</a>.</p>'
    if url == "/radovy-kostel-panny-marie-pod-retezem/bohosluzby/":
        special = f'<h2>{esc(I18N["cs"]["regularServices"])}</h2>' + services_list() + '<p><a class="link-strong" href="/kalendar/">Aktuální kalendář bohoslužeb a svátků</a></p>'
    side = side_nav(url)
    html_body = f"""
<div class="wrap">{crumbs_html(url)}</div>
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
    return layout(lang="cs", url=url, title=p["title"], body=html_body, description=p.get("description", ""),
                  image=lead_img, status=p.get("status"))


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


def render_calendar_page():
    t = I18N["cs"]
    body = f"""
<div class="wrap">{crumbs_html('/kalendar/')}</div>
<div class="wrap page page--calendar">
 <header class="page-head reveal"><h1 class="display">Kalendář</h1><p class="lead-s">{esc(t['calendarLead'])}</p></header>
 {calendar_widget('cs', 'month')}
 <p class="subscribe"><a class="btn" href="{SITE['addcal']['publicUrl']}">{esc(t['subscribe'])}</a><span class="small">Google, Apple, Outlook a další kalendáře; termíny se aktualizují samy.</span></p>
 <div class="cal-below">
  <section aria-labelledby="svc"><h2 id="svc" class="display-s">{esc(t['regularServices'])}</h2><p class="small">{esc(t['churchPlace'])}</p>{services_list()}</section>
  <section aria-labelledby="dl"><h2 id="dl" class="display-s">{esc(t['calendar2027'])}</h2>{downloads_list()}</section>
 </div>
</div>"""
    return layout(lang="cs", url="/kalendar/", title="Kalendář", body=body, status="new",
                  description="Kalendář bohoslužeb, svátků a akcí Českého velkopřevorství Maltézského řádu; Kalendář 2027 ke stažení.")


def render_foreign_home(lang):
    t, names, gm = I18N[lang], SITE["names"][lang], SITE["gm"][lang]
    official = "".join(f'<li><a href="{gm[k]}">{esc(label)}</a></li>' for k, label in t["links"].items() if k in gm)
    feed = gm_feed(lang)
    feed_html = ""
    if feed:
        feed_html = f'<h3 class="display-s">{esc(t["gmNews"])}</h3><ul class="gm-feed">' + "".join(
            f'<li><time datetime="{f["date"]}">{short_date(f["date"]) if f["date"] else ""}</time><a href="{esc(f["link"])}">{esc(f["title"])}</a></li>' for f in feed) + "</ul>"
    downloads = ""
    if lang == "en":
        en_files = "".join(f'<li><a href="{f}">{esc(label)} <span class="file-meta">PDF</span></a></li>' for d in SITE["calendarFiles"] for label, f in d["files"] if "English" in label)
        downloads = f'<div class="dl-block"><h3 class="display-s">{esc(t["calendar2027"])}</h3><ul class="plain-links">{en_files}</ul></div>'
    body = f"""
<section class="home-open"><div class="wrap home-intro home-intro--single">
 <div class="home-intro-main reveal">
  <h1 class="display">{esc(names['entity'])}</h1>
  <p class="lead">{esc(names['order'])}</p>
  <p class="notice">{esc(t['pendingTranslation'])}</p>
  <h2 class="display-s official-head">{esc(t['officialTexts'])}</h2>
  <ul class="plain-links">{official}</ul>
 </div>
</div></section>
<section class="band band-grey" id="kalendar"><div class="wrap">
 <div class="section-head"><h2 class="display-m">{esc(t['calendar'])}</h2><p>{esc(t['calendarLead'])}</p></div>
 {calendar_widget(lang, 'schedule')}
 <p class="subscribe"><a class="btn" href="{SITE['addcal']['publicUrl']}">{esc(t['subscribe'])}</a></p>
 {downloads}
</div></section>
<section class="band" id="kontakt"><div class="wrap split">
 <div class="split-head"><h2 class="display-m">{esc(t['contact'])}</h2></div>
 <div>{contact_card(lang)}{feed_html}</div>
</div></section>"""
    alts = {l: ("/" if l == "cs" else f"/{l}/") for l in SITE["languages"]}
    return layout(lang=lang, url=f"/{lang}/", title=names["entity"], body=body, alternates=alts, status="new",
                  description=f"{names['entity']} – {names['order']}.")


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


HEADERS = """/*
  Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.addcal.co; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://cdn.addcal.co https://addcal.co; font-src 'self' https://cdn.addcal.co; connect-src 'self' https://addcal.co https://cdn.addcal.co; frame-src https://addcal.co; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()
  Cross-Origin-Opener-Policy: same-origin
  X-Frame-Options: DENY
/fonts/*
  Cache-Control: public, max-age=31536000, immutable
/css/*
  Cache-Control: public, max-age=31536000, immutable
/js/*
  Cache-Control: public, max-age=31536000, immutable
/media/*
  Cache-Control: public, max-age=2592000
/img/*
  Cache-Control: public, max-age=2592000
"""


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(STATIC, DIST)
    write("/", render_home())
    for url, p in PAGES.items():
        write(url, render_page(p))
    for i, n in enumerate(NEWS):
        write(n["url"], render_article(n, NEWS[i + 1] if i + 1 < len(NEWS) else None, NEWS[i - 1] if i else None))
    write("/aktuality/", render_news_index(NEWS[:40]))
    for c in SITE["newsCategories"]:
        items = [n for n in NEWS if c in n.get("categories", [])]
        if items:
            write(f"/aktuality/{c}/", render_news_index(items, active=c, url=f"/aktuality/{c}/"))
    for y in sorted({n["date"][:4] for n in NEWS}):
        write(f"/aktuality/{y}/", render_news_index([n for n in NEWS if n["date"].startswith(y)], year=y, url=f"/aktuality/{y}/"))
    write("/kalendar/", render_calendar_page())
    for lang in SITE["languages"][1:]:
        write(f"/{lang}/", render_foreign_home(lang))
    write("/ochrana-osobnich-udaju/", render_simple("/ochrana-osobnich-udaju/", "Ochrana osobních údajů", PRIVACY, status="approval"))
    write("/404.html", render_simple("/404.html", I18N["cs"]["notFound"],
                                     f'<p>{esc(I18N["cs"]["notFoundText"])}</p><p><a class="link-strong" href="/">Úvodní stránka</a> · <a class="link-strong" href="/aktuality/">Aktuality</a> · <a class="link-strong" href="/kalendar/">Kalendář</a></p>'))
    urls = ["/", "/kalendar/", "/aktuality/"] + [f"/{l}/" for l in SITE["languages"][1:]] + list(PAGES) + [n["url"] for n in NEWS]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
                                      "".join(f"<url><loc>{SITE['baseUrl']}{u}</loc></url>" for u in urls) + "</urlset>", encoding="utf-8")
    (DIST / "robots.txt").write_text(("User-agent: *\nAllow: /\n\nSitemap: " + SITE["baseUrl"] + "/sitemap.xml\n") if PRODUCTION
                                     else "User-agent: *\nDisallow: /\n", encoding="utf-8")
    (DIST / "feed.xml").write_text(rss(), encoding="utf-8")
    (DIST / "_headers").write_text(HEADERS + ("" if PRODUCTION else "/*\n  X-Robots-Tag: noindex, nofollow\n"), encoding="utf-8")
    (DIST / "_redirects").write_text("".join(f"{a} {b} 301\n" for a, b in SITE["redirects"]), encoding="utf-8")
    print(f"built {len(PAGES)} pages, {len(NEWS)} news, {'production' if PRODUCTION else 'preview'} → {DIST}")


PRIVACY = """<p>Tento web neužívá analytické ani reklamní cookies a nesleduje návštěvníky. Písma a obrázky se načítají přímo z tohoto webu.</p>
<p>Na úvodní stránce, na stránce Kalendář a na úvodních stránkách cizojazyčných verzí se zobrazuje kalendář služby AddCal (addcal.co). Při jeho načtení prohlížeč odesílá službě AddCal technické údaje nutné k zobrazení (IP adresu a údaje o prohlížeči). Kalendář si můžete prohlédnout také přímo na adrese <a href="https://addcal.co/c/calendarGPB">addcal.co/c/calendarGPB</a>.</p>
<p>Správcem osobních údajů je České velkopřevorství, Velkopřevorské náměstí 4, 118 00 Praha 1. Dotazy k ochraně osobních údajů posílejte na <a href="mailto:gpb@smom.cz">gpb@smom.cz</a>.</p>"""


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
