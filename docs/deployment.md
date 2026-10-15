# Deployment

**Production deployment and any change to the live maltezskyrad.cz require explicit authorisation from the Grand Priory.** Nothing in this repository deploys automatically to production.

## Build

```sh
python3 build.py                 # preview: noindex everywhere, content-status labels shown
python3 build.py --production    # production: indexable, no labels
python3 build.py --offline       # either mode, without fetching the Grand Magistry news feed
python3 check.py                 # must print "0 problems" before anything is published
```

The only requirement is Python 3.10 or newer, with no packages. The output is `dist/`, a plain static folder: HTML, CSS, JS, fonts, media, `sitemap.xml`, `feed.xml`, `robots.txt`, `_headers` and `_redirects`.

The Grand Magistry news list on the homepage is fetched at build time from `orderofmalta.int`. If the fetch fails, the build still succeeds and the block is left out. Rebuild at least daily, for example with a scheduled CI job, to keep it current.

## Hosting

Any static host works. Security headers and legacy redirects are defined once, in `vercel.json` (`headers`, `redirects`); the build also writes them as `dist/_headers` and `dist/_redirects` (Netlify / Cloudflare Pages format) for other hosts and the local preview server.

| Host | `_headers` (CSP, HSTS…) | `_redirects` (legacy URLs) | Notes |
|---|---|---|---|
| Netlify | ✅ native | ✅ native | Build `python3 build.py --production`, publish `dist`. |
| Cloudflare Pages | ✅ native | ✅ native | Same. |
| Vercel (`vercel.json`) | ✅ from `vercel.json` | ✅ from `vercel.json` | The build command is `python3 build.py --offline` (a preview build: `noindex` meta and a `Disallow: /` robots.txt). For production change it to `python3 build.py --production`. |
| nginx / Apache (own server) | translate | translate | See below. |

### nginx translation

```nginx
server {
  server_name www.maltezskyrad.cz;
  root /var/www/maltezskyrad/dist;
  error_page 404 /404.html;

  add_header Content-Security-Policy "<value from dist/_headers>" always;
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
  add_header X-Content-Type-Options nosniff always;
  add_header Referrer-Policy strict-origin-when-cross-origin always;
  add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()" always;
  add_header Cross-Origin-Opener-Policy same-origin always;
  add_header X-Frame-Options DENY always;

  location ~ ^/(fonts|css|js)/ { add_header Cache-Control "public, max-age=31536000, immutable"; }

  # one line per entry in dist/_redirects, e.g.
  location = /sekce-pro-cleny/ { return 301 /kontakt/; }
  location ^~ /wp-content/uploads/ { rewrite ^/wp-content/uploads/(.*)$ /media/$1 permanent; }
  location ^~ /category/ { return 301 /aktuality/; }
}
server {  # canonical host
  server_name maltezskyrad.cz cvp.maltezskyrad.cz;
  return 301 https://www.maltezskyrad.cz$request_uri;
}
```

Repeat the `add_header` lines in any `location` block that also sets its own `add_header`; nginx does not inherit them.

## Canonical host and the current certificate fault

The new site's canonical URL is `https://www.maltezskyrad.cz` (`baseUrl` in `content/site.json`).

Today the apex and `www` hosts redirect to `cvp.maltezskyrad.cz`, which has no valid certificate (`docs/security-audit.md`, L1). At launch:

1. Serve the site on `www`.
2. Redirect the apex and `cvp.` hosts to it.
3. Make sure the certificate covers every one of those names.

## Launch checklist

1. Resolve the open approvals in `docs/brand-compliance.md`, and approve every page labelled "new" and the privacy notice.
2. Get written authorisation to replace the live site.
3. Run `python3 build.py --production && python3 check.py`.
4. Deploy `dist/` with the headers and redirects active on the host. Verify:
   - `curl -I https://www.maltezskyrad.cz/` shows the CSP and HSTS headers;
   - `curl -I https://www.maltezskyrad.cz/sekce-pro-cleny/` returns 301.
5. Submit `https://www.maltezskyrad.cz/sitemap.xml` in Google Search Console.
6. Retire WordPress. Keep a full backup (database and `wp-content`) offline, and remove the public `/wp-json/` API.
