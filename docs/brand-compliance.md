# Brand compliance report

Checked against:

- **CP**: *Sovereign Order of Malta Worldwide Communications Policy and Guide* (Rome, February 2025);
- **CoA**: *Guidelines for correct use of the two emblems and of the flags of the Order of Malta* (v3.3, 1 September 2023);
- **Theme**: the Grand Magistry *Entities Theme* package (March 2025).

Status values: ✅ complies · ⚠️ complies with a caveat or needs a decision · ❌ deviation, approved by the client.

## Checklist

| # | Requirement | Source | Status | How the site meets it |
|---|---|---|---|---|
| 1 | Top banner, colours and general layout follow the Grand Magistry website | CP, Theme | ✅ | Red top bar (social links and language switch), official banner photograph with the "ORDER OF MALTA" lockup, full name in white caps, `#454545` menu bar, grey / white / red footer bands. |
| 2 | Colours `#e31818`, `#f3f3f3`, `#c7c7c7`, `#454545`, `#000` | Theme spec | ⚠️ | All are used. The theme's own CSS uses `#e31a18` rather than the spec's `#e31818`; the site follows the CSS. Small red text uses the darker `#c80e00` to reach 4.5:1 contrast. Ask the Grand Magistry which red value is canonical. |
| 3 | Font Asap | Theme spec | ✅ | Asap is self-hosted (OFL) and used for all interface text and body text. |
| 4 | Display serif | — | ⚠️ | Headings use EB Garamond (OFL). The theme does not specify a serif. Confirm with the Grand Magistry, or switch headings to Asap: one token (`--display`) in `site.css`. |
| 5 | Full official name at first mention and in the banner | CP | ✅ | The banner and footer use "Suverénní vojenský špitální řád svatého Jana Jeruzalémského, z Rhodu a z Malty". Shorter forms are used afterwards. |
| 6 | No acronyms (SMOM etc.) and never "Malta" alone | CP | ✅ | Enforced by `check.py` on every built page. |
| 7 | Footer links to www.orderofmalta.int | CP | ✅ | Red footer band on every page. Each language page also links to the Grand Magistry's own pages in that language. |
| 8 | Official texts (mission, spirituality, government, history, Grand Master, FAQ) come from the Grand Magistry | CP | ✅ | The site links to orderofmalta.int pages rather than rewriting them. Legacy local pages on these topics are kept, marked "existing", for editorial review. |
| 9 | Only the two official emblems; none created or redrawn | CoA | ✅ | Only the official armorial bearing (on the Grand Priory page) and the official red shield (the banner lockup and the official favicon set) appear. `check.py` fails the build if any other file under `/img/` is referenced. The old site's "znak" images were dropped during import. |
| 10 | Institutional use takes the armorial bearing; activities take the shield | CoA | ⚠️ | The Grand Priory page shows the armorial bearing. The banner uses the shield lockup because the Grand Magistry theme does; the CoA guideline for institutional internet use points the other way. Ask the Grand Magistry. |
| 11 | Personalised lockup ("ORDER OF MALTA" + entity name) | CoA, Theme | ⚠️ | The generic "ORDER OF MALTA" banner is used, with the Czech name set as live text beside it. The personalised Czech lockup must be requested from the Grand Magistry (asset `BAN-01`). |
| 12 | Emblem files are originals, not approximations | CoA | ⚠️ | The armorial bearing was extracted from the CoA PDF (p. 21, CMYK → sRGB, resized only). Replace it with the RGB master when it is supplied (asset `EMB-01`). |
| 13 | Opening animation of the emblem | CoA (no alteration, no animation of the emblems) | ❌ | A thin red outline trace of the armorial-bearing silhouette plays once per session (about 2 s; never with reduced motion; any key or tap skips it). The client asked for it knowing it is a deviation (14 Oct 2026). Turn it off with `"openingTrace": false` in `content/site.json`; nothing else changes. |
| 14 | Apolitical, neutral, no invented facts | CP | ✅ | New texts state only facts found in the existing site, the Grand Magistry site or the 2027 calendar. New texts are labelled "new" until approved. |
| 15 | Images | Theme (basic image 800×470) | ⚠️ | Only real photographs from the existing site are used. Usage rights and consent for identifiable people still need confirming (`docs/asset-manifest.md`). |
| 16 | Social links | CP | ⚠️ | The site links to Facebook (the Grand Priory) and to the Grand Magistry's YouTube and LinkedIn. CP p. 74 swaps the X handles of two entities, so X is omitted until that is resolved. |
| 17 | Terminology from the Honours booklet | Client | ✅ | The booklet is used only to check the forms of words. No names, lists or details from it appear anywhere in the repository's site content. |

## Open approvals (for the Grand Magistry or the Grand Priory)

1. The canonical red value (`#e31818` or `#e31a18`).
2. EB Garamond for headings, or Asap only.
3. Shield lockup or armorial bearing in the banner of an institutional site.
4. The personalised Czech banner lockup (`BAN-01`) and the RGB master of the armorial bearing (`EMB-01`).
5. Keeping the opening trace (row 13). It is the client's call and can be switched off in one line.
6. Native-speaker review of the FR, IT and DE interface strings (`content/i18n.json`) and of the EN entry page.
7. Approval of every page marked "new", and the privacy notice (marked "approval").
