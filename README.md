# Who gets talked about?

Public attention on Wikipedia and parliamentary attention in the House of Commons to 1,425 UK towns and cities. Commons contributions from 2005 to 2025 that say "in" plus a place's name (Hansard, counted in *Mentioned in the House*) set against the English Wikipedia pageviews of the same places in 2024, linked through Wikidata with documented rules, and modelled with a pre-specified analysis plan (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/wiki-vs-hansard/
Paper: https://doi.org/10.5281/zenodo.24092583
Blog post: https://blog.tristanhotham.com/2026/10/31/wiki-vs-hansard/
Code and data: https://github.com/Tristan-Hotham/wiki-vs-hansard

## Headline results

- Matching: 1,634 of 1,661 Hansard place names (98.4%) matched to a Wikipedia article; 1,425 places in the main sample after removing ambiguous names, name collisions (e.g. Farnborough, Ripley) and suspect titles. Gibraltar and other non-UK territories in the Wikidata UK set are excluded.
- The two attentions agree broadly: Spearman 0.74. Pageview elasticity of mentions 0.54 (95% CI 0.46 to 0.62), holding population, region, distance from London and deprivation fixed (Poisson, SEs clustered by local authority): twice the views, 45% more mentions.
- Seat names: places whose name is part of a Commons seat name get 121% more mentions (90% to 158%); permutation p = 0.001. Within place, gaining a seat name goes with 109% more mentions, but the lead placebo fails (54%): those places were already rising, so this probably overstates the effect of the name. Names that appear only inside a longer seat name (no phrase overlap) still go with 67% more mentions (23% to 126%).
- No devolved-nation or northern deficit: Welsh places get 64% more mentions than English ones (38% to 96%), positive in all 20 checks; north/south and London contrasts vanish without London itself. Deprivation: -2.8% per SD (n.s.).
- Drifting apart: elasticity 0.63 for 2005 to 2014, 0.49 for 2015 to 2025; 2024 views track the debates of 1945 to 1979 best (exploratory).
- Most over-mentioned for their profile: Newtownards (6.9x), Redcar (5.8x), Kettering (4.8x), Dudley (3.6x), Newton Aycliffe (3.6x). Under-mentioned: Becontree, Broughty Ferry, Bamber Bridge, Litherland, Waltham Abbey, Ewell.

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
- Models: PPML with region fixed effects, SEs clustered by 2023 local authority; within-place panel PPML with place and year FE around the 2010 and 2024 boundary changes; 20 robustness checks, leave-one-region-out, permutation and lead placebos.

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

Hotham, T. (2026) Who gets talked about? Public attention on Wikipedia and parliamentary attention in the House of Commons to UK places, 2005 to 2025. Zenodo. 10.5281/zenodo.24092583

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
