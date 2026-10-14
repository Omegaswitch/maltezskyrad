# QA report

Date: 14 October 2026.

Method:
- Builds were served locally with `python3 build.py serve`-equivalent headers and redirects.
- Pages were tested in headless Chromium (Playwright).
- Automated accessibility checks used axe-core 4.10.2.

## Automated checks (`check.py`, runs in CI)

262 HTML pages checked, 0 problems. Every page has:
- exactly one `<h1>`;
- a `<title>`;
- a meta description (404 excepted);
- internal links and images that resolve to a file or a redirect;
- no `javascript:` URLs;
- only approved brand files under `/img/`;
- no "SMOM" acronym.

The importer's sanitiser self-test runs too. The check was proven to fail on injected defects (broken link, unknown image, acronym, second `<h1>`, missing description) before being trusted.

## Responsive and visual

| Page | 390 | 768 | 1024 | 1440 | 1920 |
|---|---|---|---|---|---|
| Homepage | ✅ | ✅ | ✅ | ✅ | ✅ |
| Inner page (history) | ✅ | | | ✅ | |
| Section page (Činnosti) | ✅ | | | ✅ | |
| News index with tabs and years | ✅ | | | ✅ | |
| Article | ✅ | | | ✅ | |
| Kalendář | ✅ | | | ✅ | |
| English entry page | ✅ | | | ✅ | |
| 404 | ✅ | | | ✅ | |

✅ means no horizontal overflow, one `<h1>`, no console errors other than the local-HTTP COOP warning, and a manual screenshot review.

The opening trace was captured at 0.4, 1.0, 1.7 and 2.6 s. It draws, fades out and leaves the page by about 2 s.

Fixed during QA:
- The banner shield overlapped the full name on mobile and tablet.
- The section menu sat above the page title on mobile.
- Download-only posts showed raw file names as excerpts.
- The importer re-created retired pages.
- Spacing on the English page.
- A full-height portrait on article pages.
- The footer did not reach the bottom of short pages.
- "Fra´" was spelled with an acute accent.
- Uppercase eyebrow labels were turned into real headings.
- The calendar showed 12-hour time.

## Accessibility (WCAG 2.2 AA)

**axe-core** (rule sets wcag2a/aa, wcag21a/aa, wcag22aa, best-practice) ran at 390 and 1440 on the homepage, history, Činnosti, Aktuality, an article, Kalendář, English, Kontakt and 404.
- 0 violations in the site's own markup after two fixes: the tab counter contrast, and the `<aside>` landmark nested inside `<article>`.
- Remaining violations are all inside the third-party AddCal widget's shadow DOM, which the site cannot style:
  - the subscribe button is icon-only, with no name, on mobile;
  - some weekday and day numbers, and the "events" meta text, fall below contrast;
  - event chips in month view are below 24 px target size.

  Report these to AddCal. The same information stays available without the widget: service times and downloadable PDFs on the same page, and the public calendar link.

**Keyboard** (scripted):
- The first Tab focuses the skip link, and Enter moves focus to `<main>`.
- Focusing a menu item opens its submenu; Escape closes it.
- The focus ring is a 2 px solid outline.
- On mobile, the menu button toggles `aria-expanded` and opens the menu.

**Motion:**
- Under `prefers-reduced-motion` the opening trace never plays, and view transitions, the skeleton shimmer and the reveal animation are disabled.
- The trace can be skipped with any key or tap.

## Performance

Measured on localhost (390 px), so timings show render cost, not network.

| Page | Own bytes | Third-party | Requests | LCP | CLS |
|---|---|---|---|---|---|
| Homepage | 453 KB | 0 (AddCal loads lazily, on scroll) | 18 | 136 ms | 0.001 |
| Kalendář | 321 KB | 386 KB (AddCal) | 19 | 96 ms | 0.000 |
| Article | 481 KB | 0 | 18 | 116 ms | 0.001 |
| Aktuality | 270 KB | 0 | 16 | 128 ms | 0.000 |

- Fonts are self-hosted WOFF2, subset to latin and latin-ext, and the weights used above the fold are preloaded.
- CSS and JS are each one small file, cache-busted per build.
- Images are lazy-loaded with explicit dimensions, behind skeleton placeholders.
- The largest single asset is the imported palace photograph (170 KB, 800×470 JPEG). Re-encoding the media library to WebP would save roughly a third; it is not done because these are the original files.

## Design finish review (Impeccable)

An independent reviewer checked the build against the chosen direction (G) and the craft floor. It ran two rounds: the first asked for 8 fixes; the second scored 5 resolved, 2 partial and 1 unresolved. Open:
- **AddCal event colours** (saturated blue) come from each event's colour in the AddCal account, not from the site.
- **AddCal event titles** joining four languages are cut off on the Czech pages. This is calendar data.
- **Banner at very wide screens (≥1600 px):** the official photograph has visible start and end edges against the sky-colour fill. Fixing it means extending or mirroring the official photo, which needs the Grand Magistry's personalised banner (BAN-01) or their consent.

## Not tested

- Real devices and Safari/Firefox engines; only Chromium was tested.
- Screen readers (NVDA, VoiceOver) by a human.
- Production hosting headers on the final host.
- Native-speaker review of FR/IT/DE strings.

All of these belong before launch.
