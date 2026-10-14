---
target: homepage hero photo integration
total_score: 20
max_score: 32
na_heuristics: 7,10
p0_count: 2
p1_count: 3
target_identity: "file:/home/user/maltezskyrad/dist/index.html"
target_fingerprint: "sha256:67d333c1cd28224a5800ba938bdd0ca733539c8dd7c4a6542c2ad76a93c06210"
target_path: /home/user/maltezskyrad/dist/index.html
timestamp: 2026-10-14T20-12-31Z
slug: dist-index-html
---
# Critique: homepage hero photo integration

Method: dual-agent (A: design review · B: detector + browser evidence)

## Design Health Score
| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | While loading, the masked skeleton shimmer is a large grey cloud behind the text |
| 2 | Match system / real world | 3 | Photo has no caption; nothing says it is the palace named in "Sídlo" |
| 3 | User control and freedom | 3 | — |
| 4 | Consistency and standards | 1 | Breaks DESIGN.md and the contract: captioned 800:470 photos, no text over photos; red link fails AA here only |
| 5 | Error prevention | 3 | — |
| 6 | Recognition rather than recall | 3 | Uncaptioned building |
| 7 | Flexibility and efficiency | n/a | Read-only landing intro |
| 8 | Aesthetic and minimalist design | 1 | Four-sided fog, ghost facade behind the facts table, white smudge |
| 9 | Error recovery | 3 | — |
| 10 | Help and documentation | n/a | Landing orientation section |
| Total | | 20/32 | Acceptable structure, weak photo treatment |

## Design specificity
The content is specific to the institution (H1, dated lead, facts list of Grand Prior, seat, church). The photo treatment is generic "soft edges" builder styling. Its tell: an undersized image hidden rather than presented. A cream building faded into a white page has no edge, so it turns to warm-grey mud. Two gradient shapes fight: a rectangular mask product and an elliptical white vignette. The detector found nothing in the hero (11 findings, all elsewhere); it cannot see this. The problem is compositional.

## Priority issues
1. [P0] Fog: a four-sided mask plus a radial white vignette dissolve the photo into the page. Only about 29% of the photo box is fully opaque (46% × 64% of the mask ramps). Fix: drop the vignette. Fade at most one edge (the side facing the text) and hard-crop the other three. Suggested: /impeccable quieter.
2. [P0] Text over the photo: the text column sits 41–44% over the photo at 1024/1440. The red link "Velkopřevorský palác" measures 3.73:1 (1024) and 3.81:1 (1440), failing AA. Fix: the photo starts at least 48–72px after the text column, so text sits on pure white (links 4.70:1). Suggested: /impeccable layout.
3. [P1] Upscaling: rendered at 1.35–1.48× CSS (about 2.9× device px on retina). The code comment's "≤1.25×" claim is false. At 1024 it crops to a near-square sliver. Fix: cap at about 1.2×, shorten the box to 560–600px, crop on the building axis, and switch to the stacked layout below 1200px. Suggested: /impeccable adapt.
4. [P1] System drift: the photo has no caption and is not 800:470, contradicting DESIGN.md and the contract. Fix: restore a 0.8rem muted caption (wording to be verified), and update DESIGN.md to the shipped layout. Suggested: /impeccable polish.
5. [P1] Banner name legibility (measured by B): white caps over the light sky of the new full banner measure 1.6–2.3:1 without the text shadow at 1440/1920. The legibility depends entirely on the glow. Fix: darken the right-hand overlay gradient behind the name (e.g. rgba(14,28,46,.55) from 55%). Suggested: /impeccable polish.
6. [P2] Two sky photographs stacked: the banner sky, then the palace sky fading into the pale-blue status strip. Fix: crop the palace sky to a hard top edge just above the ridge. At 390 the photo top is also a hard line against the status strip. Suggested: /impeccable layout.

## Persona red flags
- Older parishioner on a 1366×768 laptop: the haze reads as "washed out". Ghost windows sit behind the address rows. A red link is below AA. The facts and links sit below the fold under the 336px frame.
- Journalist: no caption or credit. The only palace image is feathered and soft, and the same 800×470 file is the og:image.
- First-time visitor on desktop: the fog plus serif reads "event venue brochure", not "sovereign religious order". The blurry building upstages the text.

## Minor observations
- The hero-in 0.9s fade lengthens the fog phase.
- The skeleton shimmer runs inside the masked box.
- The photo may show the garden facade; verify before captioning.
- The mobile negative margin pulls the H1 into the faded doorway.
- The photo's right edge runs to the viewport while the banner and wrap stop at the 1180 column.
- The pale-blue preview status strip is outside the palette.
- The detector produced 11 non-hero findings: 9 cramped-padding (false positives), 1 dark-glow (banner name; the glow is load-bearing), and 1 print-only colour (false positive).

## Questions
- Is the wish atmosphere or just "bigger"? A hard-edged bleed shows more photo than a feathered one, which throws away about 70% of its box.
- Can the Priory, the palace office or the photographer supply the camera original of velkoprevorstvi.jpg (the 2018 file was resized in GIMP)?
- Does the hero need a building photograph at all, given the full-bleed banner photo directly above it?
