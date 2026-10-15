# Security and privacy audit

Date: 14 October 2026. Scope: the live site (read-only observation; nothing was changed) and the new static implementation on this branch.

## Live site (maltezskyrad.cz, WordPress): findings

| # | Severity | Finding | Evidence | Recommendation |
|---|---|---|---|---|
| L1 | **High** (availability and trust) | `https://maltezskyrad.cz/` and `https://www.maltezskyrad.cz/` answer `301 → https://cvp.maltezskyrad.cz/`, and that host's TLS certificate does not cover the name `cvp.maltezskyrad.cz`. Browsers show a certificate error after the redirect. | `curl` reports "no alternative certificate subject name matches target host name 'cvp.maltezskyrad.cz'" (re-checked 15 Oct 2026: unchanged). | Fix it now, independent of the redesign: either remove the redirect to `cvp.` or issue a certificate that includes it. The new site's canonical host is `https://www.maltezskyrad.cz` (`baseUrl` in `content/site.json`). |
| L2 | Medium | The WordPress REST user list (`/wp-json/wp/v2/users`) is public and exposes the administrator's login slug. | HTTP 200 with one entry. | Block the endpoint, or remove the site at launch. Use a strong password and 2FA for the account until then. |
| L3 | Medium | The theme loads jQuery 1.10.2 (2013; known XSS issues, CVE-2015-9251 and CVE-2019-11358 family) next to WordPress's jQuery 3.7.1. | `jquery-1.10.2.min.js` is in the page source. | Becomes moot at launch. Until then, remove the theme's bundled copy. |
| L4 | Low | No `Content-Security-Policy` or `Strict-Transport-Security` headers. | Response headers show `server: openresty` and neither header. | The new site ships both (below). |
| L5 | Low (privacy) | The public AddCal calendar embedded on the new site (`calendarGPB`) contains a private-looking entry on 24 Oct 2026, 10:45 to 13:30 ("Leave for Ceske Budejovice"). Its description is a pasted calendar invitation naming participants. | Visible in the widget and the public calendar feed. | The calendar owner should make the entry private or delete it, then check the calendar for similar entries. Not changed by us; the client decides. |

## New implementation

**Architecture**
- Static HTML, CSS and JS generated at build time.
- No server-side code, database, admin login, forms or cookies.
- Nothing on the server is executable, so most WordPress attack classes no longer apply.

**Content handling**
- Imported WordPress HTML passes an allowlist sanitiser (`tools/import_wp.py`), which has a self-test that also runs in CI.
- It keeps only structural tags and the `href`, `src` and `alt` attributes, plus `colspan`/`rowspan` on table cells.
- It removes scripts, styles, event handlers, iframes (they become plain links), `javascript:` and other unsafe URL schemes.
- `check.py` fails the build on any `javascript:` link.

**Security headers** (defined in `vercel.json`, also written to `dist/_headers`; applied to every path)

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'`; scripts only from self and `https://cdn.addcal.co`; `object-src 'none'`; `base-uri 'self'`; `form-action 'self'`; `frame-ancestors 'none'`; `upgrade-insecure-requests` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Denies camera, microphone, geolocation, payment and USB |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `X-Frame-Options` | `DENY` |

- `style-src` allows `'unsafe-inline'` because the AddCal web component injects styles. No inline scripts are used; the only `<script>` without `src` is the JSON-LD data block on the home pages (`application/ld+json`, never executed).
- Preview builds add `X-Robots-Tag: noindex, nofollow` and a `Disallow: /` robots.txt.

**Third parties**
- The only third party is AddCal (calendar widget). Its script loads only when a calendar scrolls near the viewport, and only on the homepage, `/kalendar/` and the language pages. It contacts `addcal.co` and `cdn.addcal.co`.
- **Subresource Integrity is not used.** AddCal publishes a moving `v3` URL, so a hash would break on every vendor update. The CSP host allowlist is the control.
- Fonts are self-hosted; there are no Google Fonts or analytics requests.
- The Grand Magistry news list is fetched at build time, not in the visitor's browser. Its links are restricted to `https://www.orderofmalta.int/`.

**Privacy**
- No cookies and no analytics.
- The privacy notice (`/ochrana-osobnich-udaju/`, all five languages) was rewritten on 15 Oct 2026 against Art. 13 GDPR, using the Grand Magistry's notice as a model. It covers: the controller (full legal name, IČO 00569623, seat), no cookies or tracking, hosting logs at Vercel Inc. (EU–U.S. Data Privacy Framework), the AddCal calendar (AddCal Pty Ltd, Australia; standard contractual clauses), email and telephone, plain links to social networks, data-subject rights and the right to complain to ÚOOÚ. It is marked "approval" and needs sign-off by the Grand Priory.
- The AddCal widget stores a time-zone list in `localStorage` (no personal data, no cookies; checked in a browser on 15 Oct 2026). The notice says so.

**Secrets**
- The repository and build contain no credentials, keys or tokens.

**Supply chain**
- Zero runtime and build dependencies: Python standard library only. CI uses pinned major versions of `actions/checkout` and `actions/setup-python` with `permissions: contents: read`.

## Re-check, 15 October 2026

- Secrets: no credentials, keys or tokens in the tree or in git history (pattern scan for private keys, cloud and API tokens).
- Build output (398 pages): no inline scripts, no event-handler attributes, no `javascript:` URLs, no iframes, forms or embeds. The only scripts are `/js/head.js` and `/js/site.js`; AddCal is loaded by `site.js` from `cdn.addcal.co`.
- Translation HTML (`content/translations/*.json`, written by hand, not through the importer's sanitiser): scanned for scripts, styles, handlers and unsafe URLs: none.
- **Fixed:** the Vercel deployment served none of the security headers or redirects, because Vercel ignores `_headers` and `_redirects`. Both now live in `vercel.json`, and the build derives `_headers` and `_redirects` from it, so every host gets the same values (the generated files are byte-identical to the previous ones).
- Live site: L1 (certificate for `cvp.maltezskyrad.cz`) and L2 (public WordPress user list) are still open.

## Residual risks

- AddCal is a third party with script access to pages that embed it. Mitigations: lazy loading on three page types only, a CSP host allowlist, and pages that work without it (the downloads and service times are static).
- The CSP `'unsafe-inline'` in `style-src` is required by the vendor widget.
