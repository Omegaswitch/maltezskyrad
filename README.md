# maltezskyrad.cz

Website of the Czech Grand Priory of the Sovereign Military Hospitaller Order of St. John of Jerusalem of Rhodes and of Malta (České velkopřevorství Suverénního vojenského špitálního řádu svatého Jana Jeruzalémského, z Rhodu a z Malty).

The site is static. A Python script (standard library only) turns the files in `content/` into plain HTML in `dist/`. It has no CMS, no database and no packages to install.

## Commands

```sh
python3 build.py serve 8000      # preview build, then serve it at http://localhost:8000 (headers and redirects applied)
python3 build.py                 # preview build into dist/ (noindex, status labels shown)
python3 build.py --production    # production build (see docs/deployment.md)
python3 check.py                 # checks dist/: links, headings, descriptions, brand assets, acronyms
```

Add `--offline` to skip fetching the Grand Magistry news feed. CI (`.github/workflows/ci.yml`) runs the build and `check.py` on every push.

## Where things are

| Path | What |
|---|---|
| `content/pages/<url>/index.html` | Pages. Each file has JSON front matter between `---` lines, then HTML. |
| `content/news/YYYY/MM/DD/slug.html` | News posts. The URL matches the old WordPress URL. |
| `vercel.json` | Hosting settings, security headers (CSP, HSTS…) and legacy-URL redirects; the build copies them to `dist/_headers` and `dist/_redirects`. |
| `content/site.json` | Names, contact details, service times, menu, 2027 calendar files, AddCal calendar. |
| `content/i18n.json` | Interface strings in cs, en, fr, it and de. |
| `content/translations/<lang>.json` | Translated pages (en, fr, it, de), keyed by the Czech page URL: `url`, `title`, `description`, `body`. A page without an entry is simply not in that language's menu. |
| `content/calendar.json` | 2027 events, Order feasts, concert dates and Lent services in all five languages. |
| `static/` | CSS, JS, fonts, official brand files (`img/`), calendar PDFs (`files/`) and migrated media (`media/`). |
| `tools/import_wp.py` | One-off importer from the old WordPress site. Re-running it never overwrites a file marked `"imported": false`. |

## Editorial workflow

**Monthly church notice or concert**
1. Copy last month's file in `content/news/`. Give it a new date folder and slug.
2. Edit the front matter (`title`, `url`, `date`, `categories`, `excerpt`) and the HTML below it.
3. Put the PDF in `static/media/YYYY/MM/` and link it as `<p class="file"><a href="/media/…pdf">Stáhnout</a> (PDF)</p>`.

**Changing a page**
- Edit its file. Set `"imported": false` in the front matter so a re-import never overwrites it.
- Set `"status"` to show the review state in preview builds:
  - `existing`: carried over, not yet reviewed;
  - `new`: new text awaiting approval;
  - `approval`: needs sign-off;
  - remove the field once the page is approved.

**Service times, contacts, menu**
- Edit `content/site.json`.
- Calendar events live in AddCal (calendar `calendarGPB`) and appear on the site immediately, with no rebuild.

**Rules (from the Grand Magistry communications policy and coat-of-arms guidelines)**
- Use the full name of the Order at first mention, then "Suverénní maltézský řád" or "Maltézský řád".
- Never write "SMOM" or "Malta" on its own.
- Never add, redraw or recolour an emblem. Only the files listed in `docs/asset-manifest.md` may be used; `check.py` enforces this.
- Do not invent facts or figures. Link to orderofmalta.int for the Order's official texts.

**Publishing:** see `docs/deployment.md`. Production deployment needs the Grand Priory's authorisation.

## Documentation

- `PRODUCT.md`: purpose, audience, constraints.
- `DESIGN.md`: design system (tokens, type, components).
- `docs/content-inventory.md`: every page, its status, URL preservation and redirects.
- `docs/brand-compliance.md`: checklist against the official guidelines, deviations, open approvals.
- `docs/asset-manifest.md`: brand assets and what replaces each one.
- `docs/security-audit.md`: findings on the live site and the new implementation.
- `docs/qa-report.md`: what was tested and the results.
- `docs/deployment.md`: build, hosting, canonical host, launch checklist.
