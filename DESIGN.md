---
name: maltezskyrad.cz
description: Official site of the Czech Grand Priory of the Sovereign Order of Malta, inside the Grand Magistry frame
colors:
  magistry-red: "#e31a18"
  magistry-red-pressed: "#c41513"
  magistry-red-text: "#c80e00"
  menu-graphite: "#454545"
  menu-graphite-hover: "#383838"
  menu-graphite-active: "#2f2f2f"
  footer-slate: "#6f6f6f"
  ink-strong: "#111111"
  ink: "#454545"
  ink-lead: "#333333"
  muted: "#5f5f5f"
  paper: "#ffffff"
  ground-grey: "#f3f3f3"
  hairline: "#c7c7c7"
  banner-sky: "#a7b7d5"
  banner-sky-left: "#9baed0"
  status-existing-bg: "#fbf3d9"
  status-existing-text: "#5b4700"
  status-new-bg: "#e8eef7"
  status-new-text: "#1f3a63"
  status-approval-bg: "#fde4e2"
  status-approval-text: "#7a1410"
  status-verified-bg: "#e5f2e8"
  status-verified-text: "#1d4d2b"
typography:
  display:
    fontFamily: "EB Garamond, Garamond, Times New Roman, serif"
    fontSize: "clamp(2.05rem, 4.2vw, 3.1rem)"
    fontWeight: 500
    lineHeight: 1.06
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "EB Garamond, Garamond, Times New Roman, serif"
    fontSize: "clamp(1.6rem, 2.8vw, 2.15rem)"
    fontWeight: 500
    lineHeight: 1.12
  title:
    fontFamily: "EB Garamond, Garamond, Times New Roman, serif"
    fontSize: "1.15rem"
    fontWeight: 500
    lineHeight: 1.3
  lead:
    fontFamily: "Asap, Segoe UI, Arial, sans-serif"
    fontSize: "clamp(1.08rem, 1.6vw, 1.2rem)"
    fontWeight: 400
    lineHeight: 1.6
  body:
    fontFamily: "Asap, Segoe UI, Arial, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.65
  subhead:
    fontFamily: "Asap, Segoe UI, Arial, sans-serif"
    fontSize: "1.1rem"
    fontWeight: 600
    lineHeight: 1.35
  label:
    fontFamily: "Asap, Segoe UI, Arial, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.07em"
  nav:
    fontFamily: "Asap, Segoe UI, Arial, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 400
    letterSpacing: "0.07em"
rounded:
  hairline: "2px"
spacing:
  s1: "4px"
  s2: "8px"
  s3: "12px"
  s4: "16px"
  s5: "24px"
  s6: "32px"
  s7: "48px"
  s8: "64px"
  s9: "96px"
  wrap: "1180px"
  gutter: "clamp(16px, 3vw, 32px)"
components:
  button-primary:
    backgroundColor: "{colors.magistry-red}"
    textColor: "{colors.paper}"
    rounded: "{rounded.hairline}"
    padding: "0 24px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.magistry-red-pressed}"
    textColor: "{colors.paper}"
  topbar:
    backgroundColor: "{colors.magistry-red}"
    textColor: "{colors.paper}"
    height: "36px"
  lang-switch-current:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.magistry-red}"
    rounded: "{rounded.hairline}"
    height: "28px"
  mainnav:
    backgroundColor: "{colors.menu-graphite}"
    textColor: "{colors.paper}"
    typography: "{typography.nav}"
    padding: "13px 10px"
  mainnav-active:
    backgroundColor: "{colors.menu-graphite-active}"
    textColor: "{colors.paper}"
  tab:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.hairline}"
    padding: "0 14px"
    height: "38px"
  tab-current:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  footer-nav:
    backgroundColor: "{colors.footer-slate}"
    textColor: "{colors.paper}"
  footer-red:
    backgroundColor: "{colors.magistry-red}"
    textColor: "{colors.paper}"
  file-badge:
    textColor: "{colors.muted}"
    rounded: "{rounded.hairline}"
    padding: "0 4px"
---

# Design System: maltezskyrad.cz

## Overview

**Creative North Star: "The Priory Register"**

The site is a quiet institutional register set inside a mandatory frame. The frame (red top bar, the official flag banner photograph with the full Czech name in white capitals, the graphite menu bar, and the grey / white / red footer) is the Grand Magistry "Entities Theme": it is brand, not a design choice, and it is reproduced, never reinterpreted. Inside the frame the Grand Priory speaks plainly: white and pale-grey bands, hairline-ruled definition lists, EB Garamond headings and Asap text, real photographs at the Order's 800×470 basic image ratio.

Information is set as records rather than cards: facts, service times, works, news and downloads are all rows between 1px hairlines, with a label column and a value column. Density is moderate and generous to older readers (17px body, 1.65 leading, 44px targets). Red is the Order's colour and is kept scarce inside the frame: links, the single filled button, the active-state underline and focus rings.

The system rejects the charity-landing vocabulary (hero slogan, donate button, card grid) and any ornament standing in for the Order's identity. Dignity comes from structure, type and authentic photography.

**Key Characteristics:**
- Mandatory Grand Magistry frame, reproduced exactly on every page.
- White / #f3f3f3 alternating bands, flat, separated only by tone and hairlines.
- Rows, not cards: two-column definition lists between hairline rules.
- EB Garamond for headings and row titles; Asap for everything functional.
- Red reserved for frame, links, the one filled button, active state and focus.
- Motion is short, settling and fully suppressed under reduced motion.

## Colors

A white-and-grey institutional palette framed by the Order's red and a graphite menu, with red used as signal rather than surface inside the frame.

### Primary
- **Magistry Red** (`magistry-red`): Grand Magistry web red (theme CSS value; the spec sheet lists #e31818). Fills only: top bar, red footer band, primary button, active-menu underline, side-nav top rule, submenu top border, focus ring, selection. Links on white use it too (4.7:1 on white).
- **Pressed Red** (`magistry-red-pressed`): hover fill of the primary button.
- **Text Red** (`magistry-red-text`): the darker theme red for text on the grey ground and for hover colour of dark links and row titles. Required wherever red text sits on #f3f3f3, where Magistry Red falls below AA.

### Neutral
- **Menu Graphite** (`menu-graphite`, with `-hover` and `-active` steps): the main menu bar; it is also the body text colour (`ink`), per the Grand Magistry theme.
- **Footer Slate** (`footer-slate`): the footer navigation band.
- **Ink Strong** (`ink-strong`): headings, row values, link text in lists.
- **Ink Lead** (`ink-lead`): lead paragraphs and pull quotes.
- **Muted** (`muted`): captions, dates, row labels, breadcrumbs, side-nav labels.
- **Paper** (`paper`) and **Ground Grey** (`ground-grey`): the two band grounds, alternating down the page.
- **Hairline** (`hairline`): every rule, row divider, table border and the outline of tabs, file badges and the calendar frame.
- **Banner Sky** (`banner-sky`, `banner-sky-left`): sampled from the edges of the official banner photograph; used only to extend that photograph to full width. Not a palette colour for content.

### Content-status (preview only)
- Four tinted bars (`status-existing`, `status-new`, `status-approval`, `status-verified`, each bg/text pair) mark the editorial state of a page in preview builds. They are workflow tooling, are hidden in print, and never appear as decoration or as content colour.

### Named Rules
**The Red Is Signal Rule.** Inside the frame, red appears only as link text, the single filled button per page, an active-state underline or rule, and focus. Never as a band, a card fill or a heading colour.

**The Grey Ground Rule.** On a #f3f3f3 band, every red text link switches to Text Red. Magistry Red text on grey fails AA.

## Typography

**Display Font:** EB Garamond (with Garamond, Times New Roman, serif), pending Grand Magistry confirmation; swapping `--display` to the UI stack removes it in one place.
**Body Font:** Asap (with Segoe UI, Arial, sans-serif), the Grand Magistry font.

**Character:** A bookish Garalde for the Priory's own voice, set against the Order's plain humanist sans for everything that is navigation, data or instruction. Both are self-hosted (OFL), latin and latin-ext subsets for Czech diacritics.

### Hierarchy
- **Display** (EB Garamond 500, clamp 2.05–3.1rem, 1.06, -0.01em): the single page H1.
- **Headline** (EB Garamond 500, clamp 1.6–2.15rem, 1.12): section heads on the home page; prose H2 and year headings run at 1.6rem/1.2.
- **Title** (EB Garamond 500, 1.15–1.45rem, 1.2–1.3): row titles in works, index lists and downloads; small display heads.
- **Lead** (Asap 400, clamp 1.08–1.2rem, 1.6, #333): opening paragraph under an H1, max ~66ch.
- **Body** (Asap 400, 1.0625rem / 1rem below 640px, 1.65): prose capped at 68ch.
- **Subhead** (Asap 600, 1.1rem, 1.35): prose H3; prose H4 is Asap 600 1rem.
- **Label** (Asap 600, 0.8rem, 0.07em, uppercase, muted): navigational section labels (side-nav heading) only.
- **Nav** (Asap 400, 0.8rem, 0.07em, uppercase, white): main menu items; the footer nav uses Asap 700 0.82rem, 0.05em, uppercase.

### Named Rules
**The Two Voices Rule.** Garamond speaks for the Priory (headings, row titles, the calendar years, pull quotes in italic). Asap carries everything a visitor operates or scans: menus, dates, times, labels, buttons, tables. Never set Garamond in uppercase or in UI chrome.

**The Tabular Times Rule.** Service times, dates and table numbers use tabular figures.

## Layout

A single centred column (max 1180px) with a fluid gutter (16–32px, safe-area aware). Pages are stacks of full-bleed bands alternating white and #f3f3f3, each padded 48–96px vertically (clamped to 7vw). Within a band, content sits in asymmetric two-column grids: the home opening is a 36rem text column on white with the palace photograph filling the band's right side to the screen edge (clean top, right and bottom edges, one 14% fade facing the text, never under text, capped at 1.2× its 800×470 source, muted caption below); below 1200px the photograph stacks above the text at its true 800:470 shape; section bands are 0.8fr heading column / 1.2fr record column; inner pages are a fluid main column with a 270px sticky side navigation. Readable measure is capped at 65–68ch.

Spacing follows a 4px-based scale (4, 8, 12, 16, 24, 32, 48, 64, 96). Rows are padded 10–16px vertically.

Breakpoints: at 960px all multi-column grids collapse to one column, the menu becomes a disclosure with per-item submenu toggles, and the banner photograph pins to a 128px strip fading into the graphite menu. At 640px label/value rows stack, download grids go single-column, and body drops to 1rem.

## Elevation & Depth

Flat. Depth is carried by tone (white against #f3f3f3 bands, graphite menu against the banner) and by 1px hairlines. The one shadow in the system belongs to the desktop dropdown submenu, which floats over content.

### Shadow Vocabulary
- **Dropdown** (`box-shadow: 0 10px 30px rgba(0,0,0,.14)`): desktop submenu panel only.

### Named Rules
**The Hairline, Not Shadow Rule.** Separate content with 1px #c7c7c7 rules and band tone. Cards, raised panels and hover lifts are not part of this system.

## Shapes

Square. Corners are 0 except a 2px softening on the few bounded controls (button, language chips, tabs, file badges, skeleton bars, focus ring). Accent geometry is linear: a 3px red top rule on the side navigation and dropdown, a 3px inset red underline for the active menu item, a 2px inset red left rule for the current side-nav item, and a 1px red left rule on pull quotes. Photographs are unrounded and unframed.

## Components

### Buttons
Rare and decisive: one filled action per surface (calendar subscription).
- **Shape:** near-square (2px), min-height 44px, 0 24px padding, Asap 600.
- **Primary:** Magistry Red fill, white text.
- **Hover / Active:** fill deepens to Pressed Red; presses down 1px on active. Focus is the global 2px red outline at 3px offset.
- **Text links** are the default action: Asap 600, no underline, underline on hover. Links in prose are underlined (1px, 0.18em offset), 2px on hover.

### Record rows (signature)
The system's core pattern for facts, services, contacts, works, news and the Grand Magistry feed.
- A 1px hairline above the list and below every row; no backgrounds, no borders at the sides.
- Two columns: a muted label/date column (7.5–15em) and a value column in Ink Strong; services align the time right in bold tabular figures.
- Linked rows (works, index lists) take a left-to-right grey wash and a 12px indent on hover, with the Garamond title turning Text Red.
- Below 640px the columns stack.

### Navigation
- **Top bar:** Magistry Red, 36px, white 0.8rem links; language switch as small chips, current language reversed (white chip, red bold text).
- **Main menu:** Menu Graphite bar, evenly distributed uppercase items divided by faint white rules; hover steps darker; current item darkest with a 3px red underline. Desktop submenus drop as white panels with a 3px red top rule and the dropdown shadow.
- **Mobile (≤960px):** "Menu" toggle with a CSS-drawn three-bar mark that rotates 90° when open; the list expands via a grid-row transition; submenus open with chevron toggles into a #3c3c3c panel.
- **Side navigation:** sticky, 3px red top rule, muted uppercase label, hairline-separated links; current item bold with a 2px red inset left rule.
- **Breadcrumbs:** 0.82rem muted, slash separators in hairline grey.
- **Tabs (news archive):** outlined 2px-radius chips, 38px tall; current tab filled Menu Graphite with white text. Year filters are plain text with a 2px red underline on the current year.

### Footer
Three stacked bands from the Grand Magistry theme: Footer Slate navigation (four columns of white uppercase bold links), a white identity block (full name, address, Text Red links), and a Magistry Red legal band in three columns.

### Calendar block
A hairline-framed white panel (min 420px; 360px on small screens) hosting the AddCal embed, loaded only near the viewport. While loading it shows skeleton bars and a muted status line; on failure it falls back to plain links. The vendor widget's own internal colours belong to AddCal and are not system colours.

### Loading
Images and the calendar show a soft grey shimmer (#ececec to #f7f7f7, 1.4s) until loaded, then fade in over 280ms. Skeletons are the only placeholder treatment; spinners are not used.

### Content-status bar (preview only)
A thin full-width tinted bar under the menu stating the page's editorial state in 0.8rem Asap 500. Preview tooling, not a design element.

### Opening trace (client-approved exception)
A once-per-session outline trace of the armorial bearing's silhouette over a 94% white veil, ending at 1.45s + 0.45s fade, cancelled by any key or tap, never shown under reduced motion. It is a knowingly approved deviation from the Grand Magistry guidelines, switched by `openingTrace` in content/site.json, and is removed if the Grand Magistry objects. It is not a pattern for other surfaces.

### Motion
Easing `cubic-bezier(.22,.61,.36,1)`; 160ms for state changes, 280ms for disclosure and fades. Cross-document view transitions (180ms out, 260ms in, 4–6px drift) with the header and footer held in place. Page heads settle in from 8px over 0.5s, starting visible. `prefers-reduced-motion` collapses all animation and transition and disables the opening trace.

## Do's and Don'ts

### Do:
- **Do** reproduce the Grand Magistry frame (top bar, official banner photograph with full Czech name, graphite menu, grey / white / red footer) unchanged on every page.
- **Do** set lists of facts, times, works and news as hairline-ruled rows with a muted label column.
- **Do** switch red link text to Text Red on #f3f3f3 bands.
- **Do** use EB Garamond 500 for headings and row titles and Asap for all UI, data and body text.
- **Do** use real photographs at the 800×470 basic image ratio, with a muted 0.8rem caption.
- **Do** keep targets at least 44px for primary actions and 32px for inline file links.
- **Do** show skeleton shimmer for images and the calendar, and respect reduced motion everywhere.

### Don't:
- **Don't** create, redraw, approximate or restyle any emblem. Only the two official emblems (armorial bearing, red shield for activities) may appear, from approved originals; until supplied, use labelled placeholders. check.py fails the build for any file under /img/ outside the approved brand set (armorial-bearing 420/840, coa-trace.svg, the official banner, favicons).
- **Don't** extend the opening trace exception: no other animated, outlined or stylised use of the emblem.
- **Don't** build the charity-landing pattern: hero slogan over a photo, donate button, card grids.
- **Don't** use red as a band, card fill or heading colour inside the frame.
- **Don't** add cards, raised panels, hover lifts or shadows beyond the desktop dropdown.
- **Don't** put kicker or eyebrow labels above headings; uppercase labels are for navigation only.
- **Don't** treat the content-status tints or the AddCal widget colours as palette colours.
- **Don't** use the acronym SMOM or "Malta" alone in text; check.py flags the acronym.
