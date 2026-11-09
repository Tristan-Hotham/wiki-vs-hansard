# wiki-vs-hansard: working notes

Brief: /home/claude/work/new11/BRIEFS.md section 6 (+ shared rules new8/new9/new10, house brief). Format refs: battle-moons, sea-sunsets.
Scratch: /home/claude/scratch/wiki-vs-hansard (delete at the end).

## Data construction (done before any outcome model)

- 01_data.py: Wikidata UK settlements 29,913; pageviews 5,191 titles (2024, user agent; 8 zeros, no errors).
  Non-UK: 81 items outside the UK LAD polygons (3 km snap) dropped, incl. Gibraltar, Cockburn Town, Road Town; also
  "Somerset" and "Greater London" (areas, not settlements).
- Hansard terms 1,661 (Mentioned in the House). Matching: base title (before comma or bracket, normalised) = term or alias,
  within 20 km, prefer with views, no bracket, nearest. overrides.csv: 16 aliases, 1 preferred (Cowbridge), 1 dropped (Barnet).
  1,634 matched (98.4%); 1,503 with 2024 views (others: Wikidata population missing or < 1,500, so views never fetched).
  Median distance 0.31 km, 95th pct 1.27 km. Unmatched list in data/match_log.csv (Margate, Rhondda, Saddleworth, Hayling
  Island, Ammanford ... are not in the Wikidata settlement set: a source gap, not fixable without new data).
- Whole match list read by eye (348 non-identical titles). Problems found: Hansard's own point sometimes sits at a minor
  namesake (Kennington -> Kent, Kensington -> Liverpool, Loughton -> Shropshire). Rule: `collide` = another UK settlement
  of the same name has >= 25% of the matched article's views (20 places in the clean set); `collide_strict` = any namesake
  with views (53). Kensington, Loughton have no views at the matched point and drop out anyway.
- Pageview anomalies: Moffat 0 views, Erskine 11, Brampton 76 (titles probably moved during 2024, so views split across
  titles). Rule (set before modelling): views < 2% of population => `suspect_title`, excluded.
- Population: Wikidata P1082 is messy (Morden 199,693; St Neots 1,752; Huntingdon 2,368). Rule: ONS BUA 2021 where the
  Hansard source has it (1,103 places), else Wikidata, else GeoNames. Flag sources disagreeing by > 3x (robustness drop).

## Analysis plan (written before running any outcome model)

Question: which places does the public look up and which does Parliament talk about, and how far do the two diverge?

Unit: a UK place: a Hansard place term matched to an English Wikipedia settlement article with 2024 pageviews.
Main sample: Hansard flag empty (not shared, namesake or low-precision word), not `collide`, not `suspect_title`,
population known. N reported everywhere.

Outcome (Y): Commons contributions 2005 to 2025 containing "in <place>" (precision-scaled counts from Mentioned in the
House). Chosen because it is not inflated by "the hon. Member for <seat>", division lists or surnames.

Exposure: log 2024 English Wikipedia user pageviews of the place's article (public attention).

Controls: log population; region fixed effects (9 English regions, Scotland, Wales, Northern Ireland; region from the
2010 constituency containing the point, Northern Ireland by nation); log distance to London (km); deprivation proxy
(2011 Census, % of households deprived in two or more of four dimensions, in the 2010 constituency containing the place;
GB only, NI absorbed by its fixed effect with the value set to the GB mean and a missing flag); disambiguated title
indicator (comma or bracket in the title: the bare name leads elsewhere, which lowers views); seat-name share.

Seat-name share: share of 2005 to 2025 (by boundary period: 2005-10, 2010-24, 2024-) in which the place's name formed
part of the name of a Commons seat (whole words; a name inside a longer place name in the same seat does not count).

Main specification (M1): Poisson pseudo-maximum likelihood (PPML) of Y on log views + log population + seat share +
log distance to London + deprivation + disambiguated title + region FE; standard errors clustered by local authority
district (2023). Effects: elasticities for logs; exp(b) - 1 for the seat share (full period as a seat name vs never)
and region contrasts, with 95% CIs.

Hypotheses and what would count against them:
- H1 attention: conditional on population, places the public looks up more are mentioned more (b_views > 0). Against:
  CI includes 0 or negative. Also report the raw Spearman rank correlation of views and mentions (divergence).
- H2 representation: places whose name is in a seat name get more "in <place>" mentions (b_seat > 0), cross-section
  (M1) and within place (M2: panel PPML, place and year FE, yearly counts 2005 to 2025, treatment = seat-name share of
  that year; identified from the 2010 and 2024 boundary changes). Against: CI including 0 in M2 (cross-section alone
  cannot separate seat-naming from importance).
- H3 geography: (a) conditional on attention and population, places in Scotland, Wales and Northern Ireland get fewer
  Commons mentions than places in England (devolution); (b) within England, a "voice deficit" view predicts northern
  (NE, NW, Yorkshire and the Humber) places get fewer mentions than southern (SE, SW, East) places, conditional on
  attention; a "problem attention" view predicts deprived places get more. Two-sided; report what we find.
  Against (a): devolved-nation contrast CI includes 0 or is positive.
- H4 stability: place-level over/under-representation (Pearson residuals from M1 refitted per period) is stable between
  2005 to 2014 and 2015 to 2025 (Spearman >= 0.6 counted as stable), and b_views, b_seat similar across periods.

Robustness (pre-specified):
- R1 alternative specification: OLS of log(1 + Y) with the same controls and clustering; PPML without controls.
- R2 rank: Spearman correlations (raw and partial on population).
- R3 outliers: drop the top 1% by views and by mentions; drop London.
- R4 leave-one-region-out for b_views, b_seat and the devolved-nation contrast.
- R5 measurement: outcome 2024 only (same year as views) and 2020 to 2025; any-mention measure (2005 to 2025, Hansard
  any-flag empty); Wikidata population only; strict collision rule; include collisions; drop places whose population
  sources disagree > 3x; include the scaled ordinary-word names.
- R6 placebo/falsification: (i) permutation test for b_seat (seat status shuffled within region x population quintile,
  1,000 draws); (ii) lead test in M2: seat-name status two years ahead added; its coefficient should be about 0;
  (iii) fake timing: boundary changes moved two years earlier.
- Over/under-representation index for the map and rankings: observed / expected mentions with expected from a PPML
  on log views and log population only; rankings only for places with expected >= 20 mentions.
- Everything else is exploratory and labelled so.

Design honesty: observational, correlational. Pageviews reflect tourism, news events and name collisions; Hansard
"in <place>" phrases are a sample of mentions; one year of views against twenty-one years of debate.

## References to verify (WebSearch/WebFetch; see refs.bib, drop any unconfirmed)
(tracked in code/refs.py with verification notes)

## Results (first run of the plan, then two data corrections)

- Main sample N = 1,425 places (353 LAD clusters). M1 (PPML): views elasticity 0.54 [0.46, 0.63]; population 0.59;
  seat-name share +125% [92, 164]; Wales vs England +63% [36, 95]; devolved vs England +34% [9, 63]; north vs south
  +32% [7, 63]; London region vs rest of England -39%; deprivation -3% [-9, +3] (n.s.); distance n.s.
- Corrections after reading the rankings (not after the models): (a) two unflagged Hansard terms matched to the same
  article were added together (Newark + Newark-on-Trent; Dereham + East Dereham); (b) a `name_form` flag (long formal
  names with joining words, "City of", Regis/Spa/Minster/Magna, or never once said after "in" since 1909) used to keep
  artefacts like Saltburn-by-the-Sea (film year), City of London, Newcastle upon Tyne out of the RANKINGS, and as an
  extra robustness check. The main model keeps them (as planned). Estimates moved in the third decimal.
- H2 within place: +82% [42, 134] but the lead placebo FAILS (status two years ahead +42% [17, 74]). Event study
  (exploratory): places newly named in 2024 were already drifting up (-50% at k=-9 to -20% at k=-2), then +55% (2024)
  and +97% (2025). 2010 changes alone: lead 23% [0, 53], seat 17% [-8, 47]. So the within-place estimate is an upper
  bound; cross-section and permutation (p = 0.001) are robust but cannot separate naming from importance.
- H3: devolved and north/south contrasts in M1 are driven by the single London observation (drop the city of London:
  -1% and -3%). Wales robust (+19% to +66% in every check). H3a (devolved deficit) not supported; H3b no voice deficit.
- H4 not supported by the pre-set criterion: Spearman of period residuals 0.47 (< 0.6); views elasticity fell from
  0.63 to 0.49 (diff -0.14 [-0.23, -0.05]); seat effect stable.
- Exploratory: 2024 views predict 1945 to 1979 mentions (0.75) better than 2015 to 2025 mentions (0.55).

## References: verification (WebSearch/WebFetch, 2026)
All 46 references in the paper were checked for authors, year, title, venue, volume/pages and DOI via publisher,
RePEc, PubMed/PMC mirrors, repository or library records. Pages not confirmed (cited with start page or none):
Eulau & Karps 1977 (LSQ 2(3), from 233; doi 10.2307/439340), Zittel, Nyhuis & Baumann 2019 (LSQ 44(4), from 681),
Hecht & Gergle 2010 (CSCW proceedings, pages not on paper). Dropped as unverifiable: Smith & Gustafson (POQ, Wikipedia
and elections). Journal limits checked: Parliamentary Affairs 8,000 words, no mandatory charge; Politics (PSA) 8,000
excl. refs, no fees; Policy & Internet 6,000 to 8,000 incl. refs.

## Deliverables
index.html + js/page.js; header.png; data/*; code/01..08; release/paper (PDF 22 pp, ~7,700 words before refs,
cover_note.md), release/blog (post.html, 6 figures, meta.json), release/zenodo; reddit/collage + GIF + post.md.
QA: qa/*.png, 0 console errors at 1280 and 390 px. Scratch deleted at the end.


## Independent review (2026)

Reproduction: the pipeline (01 to 03) was re-run from the raw inputs in a scratch copy and reproduced the submitted
results.json exactly (no differences). Every output was then regenerated from the corrected pipeline (01 to 08, collage, GIF).

Errors found and fixed:
1. Seat-name timeline (substantive). The seat list from Mentioned in the House (constituencies.csv, built from Members-API
   histories) misses seats whose members' histories were not returned: only 539 names cover 2005 to 2010 (of 646); Bath,
   Neath, Richmond (Yorks), Wantage, Witney and about 55 more start at 2015, 2016, 2017 or 2019 (by-elections and later
   members); Camberwell and Peckham, Warley, West Ham and Worsley and Eccles South are absent. This gave 62 places a wrong
   seat-name share and created false status changes at 2010 and 2024 in the within-place design (e.g. Maidenhead,
   Wokingham, Barking "gained" a seat name in 2024). Fix: seat names per boundary period from the contests of the 2005,
   2010 and 2024 general elections in Who Won Here? (Hotham 2026, doi 10.5281/zenodo.23761425; 646, 650, 650 seats).
   Note: this file is outside the brief's data list (it is the author's own published dataset, already used by the
   Hansard source for seat points); the coordinator should confirm.
2. Five whole-word seat matches naming a different place (checked by place-to-seat distance): Colne/Colne Valley,
   Conwy/Meirionnydd Nant Conwy, Derby/Liverpool West Derby, Leigh/Southend West and Leigh, Sutton/Plymouth Sutton.
3. Mechanical channel not handled: Hansard phrase search counts "in Bury North" as "in Bury", and "in Kettering" may mean
   the seat. Added (exploratory, labelled): seat-name share split into names that begin a longer seat name (211),
   seats called just the place (186) and names only inside a longer seat name (155): +111%,
   +133% and +67% [23, 126]. The last is free of both artefacts, so the
   association is not mainly mechanical; within place the two kinds of change give similar estimates.
4. Text: "within-place estimate is an upper bound" made conditional (holds only if the pre-trend would have continued);
   abstract "receive" changed to "are mentioned ... more often"; reverse causality and common news shocks paragraph added;
   event-study wording ("rising steadily" to "rising unevenly"); Ewell removed from "seats named after somewhere else"
   (it is in Epsom and Ewell); page period comparison now uses the same model for 1945 to 1979 and 2015 to 2025; figure
   alt texts now filled from results.json (they said +125%, +63%, 96 places); abstract trimmed to 248 words.
5. Collage: Kettering and Newtownards labels sat over land and dots; moved to sea positions found by a search for label
   boxes clear of land and data. README gains the author line.
6. References: Eulau and Karps 1977 completed (233 to 254, verified via a Taylor and Francis reference list); Zittel,
   Nyhuis and Baumann 2019 completed (681 to 711, verified via LMU Munich publication list); Hecht and Gergle 2010 removed
   (page range could not be verified; Crossref, ACM, dblp blocked). Who Won Here? added. 47 references.
7. Cover note rewritten: Political Studies (9,000 words excl. references, no fees: fits), Parliamentary Affairs (8,000,
   max 5 figures and tables: needs an online appendix), Politics (8,000 excl. references, no fees). Policy & Internet
   (6,000 to 8,000 incl. references) would need about 2,000 words cut. JLS and PSR author pages could not be reached.

Final numbers (N = 1,425, 353 LAD clusters): views elasticity 0.54 [0.46, 0.62];
seat-name share +121% [90, 158], permutation p = 0.001; Wales +64% [38, 96];
within place +109% [44, 201] but lead +54% [23, 93] (placebo still fails;
with the lead the contemporaneous term is +41% [-2, 102]); 127 switchers (87 gains at 2024).
H4: residual Spearman 0.471, views elasticity 0.63 to 0.49.

What a referee would still ask for:
- Time-matched attention: monthly pageviews and mentions for several years (2015 onwards) to test lead/lag and news
  shocks directly; one year of views against 21 years of debate cannot order the two.
- Counts of the seat-name phrases themselves ("in Bury North") from the Hansard API, to subtract the overlap rather than
  bound it, and a sample of "in <seat name>" contributions coded for town versus constituency referent.
- MP-level controls in the panel (new MP, frontbench role, majority, party), since the 2024 change coincides with a
  large new intake; a design using seats renamed without boundary change.
- A non-English-Wikipedia attention measure for Wales (Welsh Wikipedia, Google Trends) before reading the Welsh effect.
- Negative binomial or quasi-Poisson comparison and wild-cluster bootstrap for the 12 region effects (few NI places).
- Shorter version for Parliamentary Affairs (online appendix) and a pre-registration timestamp for the plan.
