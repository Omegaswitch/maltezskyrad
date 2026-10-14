#!/usr/bin/env python3
"""Checks the built site in dist/. Run after build.py; exits non-zero on any failure.

    python3 build.py --offline && python3 check.py
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
sys.path.insert(0, str(ROOT / "tools"))

# Only these official emblem/brand files may appear; anything else under /img/ is a new, unapproved mark.
BRAND_FILES = re.compile(r"^/img/(emblems/armorial-bearing-(420|840)\.webp|banner/banner-order-of-malta\.webp|favicon/[\w.-]+)$")
# The communications policy forbids the acronym; legacy texts are flagged, not rewritten.
ACRONYM = re.compile(r"\bS\.?\s?M\.?\s?O\.?\s?M\b")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.h1, self.title, self.desc, self._in_title = [], 0, "", None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta" and a.get("name") == "description":
            self.desc = a.get("content") or ""
        for k in ("href", "src"):
            if a.get(k):
                self.refs.append(a[k])
        for part in (a.get("srcset") or "").split(","):
            if part.strip():
                self.refs.append(part.split()[0])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def redirect_sources():
    f = DIST / "_redirects"
    return [line.split()[0] for line in f.read_text().splitlines() if line.strip() and not line.startswith("#")] if f.exists() else []


def resolves(path, sources):
    p = unquote(path)
    target = DIST / p.lstrip("/")
    if target.is_file() or (target / "index.html").is_file():
        return True
    return any(s == path or (s.endswith("*") and path.startswith(s[:-1])) for s in sources)


def main():
    if not (DIST / "index.html").exists():
        sys.exit("dist/ is empty; run build.py first")
    import import_wp
    import_wp._self_test()

    sources, errors, pages = redirect_sources(), [], 0
    for f in sorted(DIST.rglob("*.html")):
        rel = "/" + str(f.relative_to(DIST))
        page = Page()
        text = f.read_text(encoding="utf-8")
        page.feed(text)
        pages += 1
        if page.h1 != 1:
            errors.append(f"{rel}: {page.h1} <h1> elements")
        if not page.title.strip():
            errors.append(f"{rel}: empty <title>")
        if f.name != "404.html" and not (page.desc or "").strip():
            errors.append(f"{rel}: missing meta description")
        for ref in page.refs:
            u = urlsplit(ref)
            if ref.strip().lower().startswith("javascript:"):
                errors.append(f"{rel}: javascript: URL")
            if u.scheme or u.netloc or not u.path.startswith("/"):
                continue  # external, mailto, tel, fragment
            if not resolves(u.path, sources):
                errors.append(f"{rel}: broken link {ref}")
            if u.path.startswith("/img/") and not BRAND_FILES.match(u.path):
                errors.append(f"{rel}: unapproved brand asset {u.path}")
        body = re.sub(r"<(script|style)\b.*?</\1>", "", text, flags=re.S)
        if ACRONYM.search(re.sub(r"<[^>]+>", " ", body)):
            errors.append(f"{rel}: forbidden acronym SMOM")

    for e in errors:
        print("FAIL", e)
    print(f"checked {pages} pages: {len(errors)} problems")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
