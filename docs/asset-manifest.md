# Asset manifest and replacement list

Every brand asset is referenced from one place. To replace one, keep the path (or change it in the file named) and rebuild. `check.py` rejects any image under `/img/` that is not listed here.

| ID | Asset | Path | Used by | Source today | Status | Replace with |
|---|---|---|---|---|---|---|
| BAN-01 | Banner photograph with the "ORDER OF MALTA" lockup | `static/img/banner/banner-order-of-malta.webp` | `.banner` in `static/css/site.css` | Grand Magistry Entities Theme, `header_orderofmalta.psd` composite (2546×218, uncropped, centred at native height like the theme) | Official, generic | The personalised Czech lockup from the Grand Magistry ("ORDER OF MALTA / České velkopřevorství" or the approved Czech wording) |
| EMB-01 | Armorial bearing (institutional emblem) | `static/img/emblems/armorial-bearing-420.webp`, `-840.webp` | `EMBLEM_BLOCKS` in `build.py`, used where a page sets `"emblem": "armorial-bearing"` | Extracted from the CoA guidelines PDF p. 21, CMYK converted to sRGB, resized | Official artwork from a document, not the master file | The RGB master (PNG/SVG) from the Grand Magistry |
| EMB-02 | Red shield (activities emblem) | Only inside BAN-01 and FAV-01 | — | Official | Official | The activities lockup with "Maltézský řád", if the Grand Priory wants it on activity pages |
| TRC-01 | Opening outline trace | `static/img/emblems/coa-trace.svg` | `layout()` in `build.py`, switched by `openingTrace` in `content/site.json` | Traced (potrace) from EMB-01's silhouette | Client-approved deviation (brand compliance row 13) | Delete it, or keep it switched off, if the Grand Magistry objects |
| FAV-01 | Favicons (16, 32, 180, 192 px and `favicon.ico`) | `static/img/favicon/*`, `static/favicon.ico` | `layout()` in `build.py` | Grand Magistry Entities Theme favicon set | Official | — |
| FNT-01 | Asap, EB Garamond | `static/fonts/*.woff2` | `@font-face` in `site.css` | Fontsource builds, SIL Open Font License | Licensed | — (EB Garamond pending confirmation, compliance row 4) |
| CAL-01 | 2027 calendar PDFs (cs and en; monthly, A4 and A3 overview) | `static/files/kalendar-2027/` | `calendarFiles` in `content/site.json` | Supplied by the client (Kalendar_2027.zip) | Final | Next year's files: add a new folder and update `calendarFiles` |
| PH-* | Photographs | `static/media/YYYY/MM/*` | Page and post front matter (`image`) and bodies | Imported from the current maltezskyrad.cz media library | Rights inherited from the current site | Confirm usage rights. Confirm consent for identifiable people, especially portraits and minors (e.g. Lourdes pilgrimage and school photos). |

Not on the site, and not to be created: officer portraits, logos of related organisations (Maltézská pomoc, schools), invented icons or emblems.
