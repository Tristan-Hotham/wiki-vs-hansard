"""Step 8: README.md, LICENSE and reddit/post.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
M1, P, M1T = R["M1"], R["prose"], R["M1_types"]
ov = ", ".join(f"{r['term']} ({r['oe']:.1f}x)" for r in R["rank"]["over"][:5])
un = ", ".join(r["term"] for r in R["rank"]["under"][:6])
readme = f"""# Who gets talked about?

Public attention on Wikipedia and parliamentary attention in the House of Commons to {R['n']['main']:,} UK towns and cities. Commons contributions from 2005 to 2025 that say "in" plus a place's name (Hansard, counted in *Mentioned in the House*) set against the English Wikipedia pageviews of the same places in 2024, linked through Wikidata with documented rules, and modelled with a pre-specified analysis plan (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/wiki-vs-hansard/
Paper: {{https://doi.org/10.5281/zenodo.24092583}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/wiki-vs-hansard/}}
Code and data: https://github.com/Tristan-Hotham/wiki-vs-hansard

## Headline results

- Matching: {R['data']['n_matched']:,} of {R['data']['n_terms']:,} Hansard place names ({R['data']['match_rate_pc']}%) matched to a Wikipedia article; {R['n']['main']:,} places in the main sample after removing ambiguous names, name collisions (e.g. Farnborough, Ripley) and suspect titles. Gibraltar and other non-UK territories in the Wikidata UK set are excluded.
- The two attentions agree broadly: Spearman {R['desc']['spearman_views_mentions']:.2f}. Pageview elasticity of mentions {M1['views']['b']:.2f} (95% CI {M1['views']['lo']:.2f} to {M1['views']['hi']:.2f}), holding population, region, distance from London and deprivation fixed (Poisson, SEs clustered by local authority): twice the views, {P['views_double']}% more mentions.
- Seat names: places whose name is part of a Commons seat name get {M1['seat']['b']:.0f}% more mentions ({M1['seat']['lo']:.0f}% to {M1['seat']['hi']:.0f}%); permutation p = {R['perm']['p']:.3f}. Within place, gaining a seat name goes with {R['M2']['seat']['b']:.0f}% more mentions, but the lead placebo fails ({R['M2_lead']['lead2']['b']:.0f}%): those places were already rising, so this probably overstates the effect of the name. Names that appear only inside a longer seat name (no phrase overlap) still go with {M1T["inner"]["b"]:.0f}% more mentions ({M1T["inner"]["lo"]:.0f}% to {M1T["inner"]["hi"]:.0f}%).
- No devolved-nation or northern deficit: Welsh places get {M1['Wales_vs_england']['b']:.0f}% more mentions than English ones ({M1['Wales_vs_england']['lo']:.0f}% to {M1['Wales_vs_england']['hi']:.0f}%), positive in all {R['robust_range']['n_checks']} checks; north/south and London contrasts vanish without London itself. Deprivation: {M1['depr']['b']:.1f}% per SD (n.s.).
- Drifting apart: elasticity {R['H4_p1']['views']['b']:.2f} for 2005 to 2014, {R['H4_p2']['views']['b']:.2f} for 2015 to 2025; 2024 views track the debates of 1945 to 1979 best (exploratory).
- Most over-mentioned for their profile: {ov}. Under-mentioned: {un}.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; places coloured by mentions against expectation, by mentions or by views; search, layers, full screen, popups. |
| `header.png` | Social card, 1200 x 630. |
| `data/places.csv` | Every Hansard place term (1,661): matched title, Wikidata id, distance, rule, region, LAD, 2010 constituency, populations, 2024 views, flags, mentions by period, seat-name shares and seat names, distance to London, 2011 Census covariates. |
| `data/index.csv` | Main sample with expected mentions and the observed/expected index. |
| `data/match_log.csv` | The matching decision for every term, with candidate titles and namesakes. |
| `data/place_years.csv` | Place by year panel 2005 to 2025: "in" mentions (scaled), any mentions, seat-name share. |
| `data/models.csv` | Every coefficient of every model. |
| `data/results.json` | Every number quoted anywhere. `data/site.json`: page data. |
| `code/` | Scripts in order, templates, `overrides.csv` (hand aliases), `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, looping GIF, scripts and post text. |
| `NOTES.md` | Working notes and the analysis plan, written before the models were run. |

## Method in brief

- Parliament: Commons spoken contributions containing "in <place>", 2005 to 2025, from *Mentioned in the House* (prefix-corrected, precision-scaled for word names; shared and namesake names excluded).
- Public: English Wikipedia user pageviews, 2024, for the article each place's Wikidata item links to (settlements with population of 1,500 or more).
- Matching: title without qualifier = Hansard term (normalised) within 20 km; 16 hand aliases; collisions (a namesake with 25% or more of the views) and suspect titles excluded; duplicates merged.
- Models: PPML with region fixed effects, SEs clustered by 2023 local authority; within-place panel PPML with place and year FE around the 2010 and 2024 boundary changes; {R['robust_range']['n_checks']} robustness checks, leave-one-region-out, permutation and lead placebos.

## How to rerun

Needs Python 3 with pandas, geopandas, shapely, pyfixest, statsmodels, scipy, matplotlib, Pillow; xelatex; node with Playwright for QA.

```
python3 code/01_data.py       # matching and variables
python3 code/02_models.py     # models and robustness (about a minute)
python3 code/03_results.py    # results.json, index, page data
python3 code/04_figures.py    # figures and header
python3 code/05_build_site.py # index.html
python3 code/06_paper.py      # paper PDF (DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py; python3 reddit/gif.py
python3 code/08_readme.py     # README, LICENSE, Reddit post
python3 code/07_release.py    # blog post, Zenodo files
```

## Sources and licences

- Hansard, House of Commons, via the UK Parliament Hansard API: contains Parliamentary information licensed under the Open Parliament Licence v3.0. Counts from Hotham (2026) *Mentioned in the House*, doi:10.5281/zenodo.23761431.
- Seat names of each boundary period (2005, 2010 and 2024 general elections) from Hotham (2026) *Who Won Here?*, doi:10.5281/zenodo.23761425.
- English Wikipedia pageviews (Wikimedia, CC0). Wikidata (CC0), via QLever.
- ONS 2011 Census by constituency, constituency and local authority boundaries, Census 2021 built-up areas: Open Government Licence v3.0.
- Base map: OpenFreeMap Positron (OpenStreetMap contributors, ODbL). MapLibre GL JS (BSD 3-Clause).
- Text, figures and derived data CC BY 4.0; code MIT.

## Citation

Hotham, T. (2026) Who gets talked about? Public attention on Wikipedia and parliamentary attention in the House of Commons to UK places, 2005 to 2025. Zenodo. {{10.5281/zenodo.24092583}}

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = open("/home/claude/studies/renamed-world/LICENSE", encoding="utf-8").read().replace(
    "Code (code/, js/, reddit/collage.py)", "Code (code/, js/, reddit/collage.py, reddit/gif.py)").replace(
    "Derived data (data/): CC0 1.0, like its source, Wikidata.", "Derived data (data/): CC BY 4.0. Sources: Hansard (Open Parliament Licence v3.0), Wikidata and Wikimedia pageviews (CC0), ONS (Open Government Licence v3.0).")
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""**Title:** [OC] Who gets talked about in Parliament? A UK town with a Commons seat named after it gets {P['seat_x']:.2f}x the mentions of a town with the same Wikipedia views and population

**Body:**

I set a year of Wikipedia reading (2024 pageviews) against twenty-one years of House of Commons debate (speeches saying "in <place>", 2005 to 2025) for {R['n']['main']:,} UK towns and cities.

- The two mostly agree (rank correlation {R['desc']['spearman_views_mentions']:.2f}), but not one for one: twice the Wikipedia views goes with only {P['views_double']}% more Commons mentions.
- A seat named after the town: {P['seat_x']:.2f}x the mentions. Towns that gained a seat name in 2024 were already on the rise, though.
- No sign the edges are forgotten: Welsh places get {M1['Wales_vs_england']['b']:.0f}% more mentions than English ones with the same attention.
- Most over-mentioned for their profile: {ov}.

Interactive map (search your town): https://maps.tristanhotham.com/wiki-vs-hansard/

**Source comment:**

Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); English Wikipedia pageviews (Wikimedia); Wikidata (CC0); ONS. Tools: Python (pandas, geopandas, pyfixest, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/wiki-vs-hansard
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme, post):
    for bad in ("—", "–", "DSIT", "DCMS", "civil serv"):
        assert bad not in t, bad
print("readme", len(readme.split()), "words")
