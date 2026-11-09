"""Step 1: build the analysis data set.

Hansard place terms (Mentioned in the House) are matched to English Wikipedia articles through Wikidata UK settlements:
  1. candidates: Wikidata settlements whose title, without any ", qualifier" or "(qualifier)", equals the Hansard term
     (normalised: case, accents, apostrophes, hyphens, "Saint" = "St"), or the term's alias (code/overrides.csv and the
     short forms used in Hansard such as Hull, Southend, Stockton);
  2. only candidates within MATCH_KM of the Hansard point;
  3. among those, prefer one with a 2024 pageview count, then a title without a "(...)" qualifier, then the nearest.
Every match is logged in data/match_log.csv with the distance, the number of candidates and the reason.
Non-UK territories in the Wikidata set (Gibraltar, the Isle of Man, the Channel Islands, anything outside the UK local
authority polygons) are dropped before matching.
Writes data/places.csv (one row per Hansard term with all variables), data/match_log.csv, data/place_years.csv
(the panel used in the within-place design) and scratch/wd_uk.csv (UK Wikidata settlements with views, for the page).
"""
import csv, gzip
from collections import defaultdict
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point
from common import *

R1 = {}
# ---------- Wikidata settlements and pageviews
rows = []
with gzip.open(f"{RAW}/uk_settlements_enwiki.tsv.gz", "rt", encoding="utf-8") as f:
    next(f)
    for line in f:
        q, t, pp, c = line.rstrip("\n").split("\t")
        t = re.match(r'^"(.*)"@en$', t).group(1)
        m = re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", c)
        rows.append(dict(qid=q.split("/")[-1].rstrip(">"), title=t, wd_pop=float(pp) if pp else np.nan,
                         lon=float(m.group(1)) if m else np.nan, lat=float(m.group(2)) if m else np.nan))
S = pd.DataFrame(rows)
PV = jload(f"{RAW}/pageviews_2024.json")
S["views"] = S.title.map(PV)
R1["wd_n"] = len(S)
R1["pv_n"] = len(PV)
R1["pv_zero"] = int(sum(1 for v in PV.values() if v == 0))
R1["pv_err"] = int(sum(1 for v in PV.values() if v < 0))
# UK land mask: local authority districts (incl. Northern Ireland); points up to 3 km offshore snap to the nearest
LAD = gpd.read_file(f"{GEO}/lad23_bsc.geojson")[["LAD23CD", "LAD23NM", "geometry"]]
G = gpd.GeoDataFrame(S, geometry=[Point(xy) if xy[0] == xy[0] else None for xy in zip(S.lon, S.lat)], crs=4326)
G = G[G.geometry.notna()]
j = gpd.sjoin_nearest(G.to_crs(27700), LAD.to_crs(27700), how="left", max_distance=3000, distance_col="lad_m")
j = j[~j.index.duplicated()]
S["lad"] = j["LAD23CD"].reindex(S.index)
S["in_uk"] = S.lad.notna()
out = S[~S.in_uk]
R1["wd_non_uk"] = int(len(out))
R1["wd_non_uk_with_views"] = int(out.views.notna().sum())
R1["wd_non_uk_examples"] = out[out.views.notna()].sort_values("views", ascending=False).title.head(8).tolist()
assert "Gibraltar" in set(out.title), "Gibraltar must be excluded"
# areas, not settlements, that Wikidata lists among UK settlements (counties, regions): excluded from the public ranking
NOT_SETTLEMENT = {"Somerset", "Greater London", "City of London"}  # City of London is kept separate from London on purpose
S.loc[S.title.isin(NOT_SETTLEMENT - {"City of London"}), "in_uk"] = False
UK = S[S.in_uk].copy()
UK[UK.views.notna()][["qid", "title", "wd_pop", "lat", "lon", "views", "lad"]].to_csv(f"{SCR}/wd_uk.csv", index=False)
R1["wd_uk_with_views"] = int(UK.views.notna().sum())

# ---------- Hansard places
P = pd.read_csv(f"{HP}/places.csv")
OV = {r["term"]: r for r in csv.DictReader(open(os.path.join(ROOT, "code", "overrides.csv"), encoding="utf-8"))}
SHORT = {"Londonderry": "Derry", "Newcastle": "Newcastle upon Tyne", "Southend": "Southend-on-Sea", "Stockton": "Stockton-on-Tees",
         "Tunbridge Wells": "Royal Tunbridge Wells", "Wootton Bassett": "Royal Wootton Bassett", "Newark": "Newark-on-Trent",
         "Berwick": "Berwick-upon-Tweed", "Clacton": "Clacton-on-Sea", "Bexhill": "Bexhill-on-Sea", "Henley": "Henley-on-Thames",
         "Bognor": "Bognor Regis", "Merthyr": "Merthyr Tydfil", "Hull": "Kingston upon Hull", "Stoke": "Stoke-on-Trent"}
idx = defaultdict(list)
for i, t in UK.title.items():
    idx[base_title(t)].append(i)
log = []
for _, r in P.iterrows():
    t = r.term
    o = OV.get(t)
    names = {norm(t)}
    if t in SHORT:
        names.add(norm(SHORT[t]))
    rec = dict(term=t, hansard_flag=r.flag if isinstance(r.flag, str) else "", title="", qid="", km=None, n_cand=0, n_near=0,
               near_titles="", rule="", has_views=False)
    if o and o["action"] == "drop":
        rec["rule"] = "dropped by hand: " + o["why"]
        log.append(rec); continue
    if o and o["action"] == "alias":
        cand = [i for i in UK.index[UK.title == o["title"]]]
        rule = "alias by hand: " + o["why"]
    else:
        cand = sorted({i for n in names for i in idx.get(n, [])})
        rule = "name and distance"
    rec["n_cand"] = len(cand)
    near = [(km(r.lat, r.lon, UK.lat[i], UK.lon[i]), i) for i in cand]
    if not (o and o["action"] == "alias"):
        near = [x for x in near if x[0] <= MATCH_KM]
    rec["n_near"] = len(near)
    rec["near_titles"] = "; ".join(f"{UK.title[i]} ({d:.1f} km)" for d, i in sorted(near)[:5])
    if not near:
        rec["rule"] = "no Wikidata settlement of that name within %d km" % MATCH_KM if cand else "no Wikidata settlement of that name"
        log.append(rec); continue
    near.sort(key=lambda x: (UK.views[x[1]] != UK.views[x[1]], "(" in UK.title[x[1]], x[0]))
    d, i = near[0]
    if o and o["action"] == "prefer":
        i = UK.index[UK.title == o["title"]][0]; d = km(r.lat, r.lon, UK.lat[i], UK.lon[i]); rule = "preferred by hand: " + o["why"]
    elif len({UK.title[k] for _, k in near}) > 1:
        rule = "nearest of several (with views first)"
    rec.update(title=UK.title[i], qid=UK.qid[i], km=round(d, 2), rule=rule, has_views=bool(UK.views[i] == UK.views[i]))
    # namesakes anywhere in the UK: other settlements with the same name, and how prominent the most viewed one is
    allc = sorted({k for n in names for k in idx.get(n, [])} - {i})
    vv = [(UK.views[k], UK.title[k]) for k in allc if UK.views[k] == UK.views[k]]
    rec["n_namesakes"] = len(allc)
    rec["n_namesakes_views"] = len(vv)
    if vv:
        mv, mt = max(vv)
        rec["top_namesake"], rec["top_namesake_views"] = mt, mv
    log.append(rec)
L = pd.DataFrame(log)
L.to_csv(f"{DATA}/match_log.csv", index=False)
P = P.merge(L[["term", "title", "qid", "km", "n_near", "rule", "has_views", "n_namesakes", "n_namesakes_views", "top_namesake", "top_namesake_views"]], on="term", how="left")
P = P.merge(UK[["title", "wd_pop", "views"]].drop_duplicates("title"), on="title", how="left")
# name collision: another UK settlement of the same name has at least a quarter of the matched article's views, so
# "in <name>" in Hansard may well mean that one (main rule); the strict rule flags any namesake with an article in the set
P["namesake_ratio"] = P.top_namesake_views / P.views
P["collide"] = (P.namesake_ratio >= 0.25).astype(int)
P["collide_strict"] = (P.n_namesakes_views.fillna(0) > 0).astype(int)
# pageview anomalies: an article with views below 2% of the population was probably renamed during 2024 (views split)
P["suspect_title"] = ((P.views < 0.02 * P.wd_pop) & P.views.notna()).astype(int)
# population: ONS built-up area 2021 where the Hansard source has it, else Wikidata, else GeoNames
P["pop_main"] = np.where(P.pop_src == "ONS BUA 2021", P["pop"], np.where(P.wd_pop > 0, P.wd_pop, P["pop"]))
P["pop_main_src"] = np.where(P.pop_src == "ONS BUA 2021", "ONS BUA 2021", np.where(P.wd_pop > 0, "Wikidata", np.where(P["pop"] > 0, "GeoNames", "")))
P["pop_disagree"] = ((P.wd_pop > 0) & (P["pop"] > 0) & ((P.wd_pop / P["pop"] > 3) | (P["pop"] / P.wd_pop > 3))).astype(int)
P.loc[P.title == "", "title"] = np.nan
R1["n_terms"] = len(P)
R1["n_matched"] = int(P.title.notna().sum())
R1["n_matched_views"] = int(P.views.notna().sum())
R1["n_alias"] = int(L.rule.str.startswith("alias").sum())
R1["n_dropped_hand"] = int(L.rule.str.startswith("dropped").sum())
R1["n_several"] = int((L.rule.str.startswith("nearest of several") | L.rule.str.startswith("preferred")).sum())
R1["n_no_name"] = int((L.rule == "no Wikidata settlement of that name").sum())
R1["n_too_far"] = int(L.rule.str.startswith("no Wikidata settlement of that name within").sum())
R1["n_matched_noviews"] = int((P.title.notna() & P.views.isna()).sum())
R1["km_median"] = round(float(P.km.median()), 2)
R1["km_p95"] = round(float(P.km.quantile(.95)), 2)
R1["km_over5"] = int((P.km > 5).sum())
M = P[P.views.notna() & P.flag.isna()]
R1["n_collide"] = int(M.collide.sum())
R1["n_collide_strict"] = int(M.collide_strict.sum())
R1["n_suspect"] = int(M.suspect_title.sum())
R1["suspect_titles"] = M[M.suspect_title == 1].title.tolist()
R1["n_pop_disagree"] = int(M.pop_disagree.sum())

# ---------- geography: 2010 constituency (census and region), local authority, distance to London
pts = gpd.GeoDataFrame(P[["term"]].copy(), geometry=[Point(xy) for xy in zip(P.lon, P.lat)], crs=4326).to_crs(27700)
W = gpd.read_file(f"{RAW}/wpc2010_gb.json")[["PCON13CD", "geometry"]].to_crs(27700)
jw = gpd.sjoin_nearest(pts, W, how="left", max_distance=5000)
jw = jw[~jw.index.duplicated()]
P["pcon"] = jw["PCON13CD"].values
jl = gpd.sjoin_nearest(pts, LAD.to_crs(27700), how="left", max_distance=5000)
jl = jl[~jl.index.duplicated()]
P["lad"], P["lad_name"] = jl["LAD23CD"].values, jl["LAD23NM"].values
C = pd.read_csv(f"{RAW}/census_11.csv").copy()
C["deprived2"] = C.deprived_2 + C.deprived_3 + C.deprived_4         # % households deprived in 2+ of 4 dimensions
C["routine"] = C.nssecsemi_routine + C.nssecroutine
C = C.rename(columns={"ons_const_id": "pcon", "qual_none": "noqual", "degree": "degree", "unemployed": "unemp"})
P = P.merge(C[["pcon", "region", "constituency_name", "deprived2", "noqual", "degree", "unemp", "routine", "population_density"]], on="pcon", how="left")
P.loc[P.nation == "Northern Ireland", "region"] = "Northern Ireland"
assert P.region.notna().all(), P[P.region.isna()].term.tolist()
assert (P.nation[P.region == "Scotland"] == "Scotland").all() and (P.nation[P.region == "Wales"] == "Wales").all()
P["dist_london"] = [km(a, b, *LONDON) for a, b in zip(P.lat, P.lon)]
R1["n_no_lad"] = int(P.lad.isna().sum())

# ---------- mentions by period from the yearly counts (already prefix-corrected; times the precision factor)
Y = pd.read_csv(f"{HP}/place_years.csv")
Y = Y.merge(P[["term", "factor"]], on="term")
Y["inm"] = (Y.in_mentions * Y.factor)
def per(a, b, col="inm"):
    s = Y[(Y.year >= a) & (Y.year <= b)].groupby("term")[col].sum()
    return P.term.map(s).fillna(0)
P["in_05_25"] = per(Y0, Y1).round()
assert (P.in_05_25 == P.in_2005_2025).all()
P["in_05_14"] = per(Y0, SPLIT - 1).round()
P["in_15_25"] = per(SPLIT, Y1).round()
P["in_2024"] = per(2024, 2024).round()
P["in_20_25"] = per(2020, 2025).round()
P["in_1945_1979"] = per(1945, 1979).round()
P["in_1980_2004"] = per(1980, 2004).round()

# ---------- seat names: is the place's name part of a Commons seat name, and for what share of 2005 to 2025?
# Seat names by boundary period are the constituencies contested at the 2005, 2010 and 2024 general elections (Who
# Won Here?, Hotham 2026, doi 10.5281/zenodo.23761425: 646, 650 and 650 seats). Review correction: the first version took the periods from the
# Members-API seat list in Mentioned in the House (constituencies.csv), which misses seats whose members' histories were
# not returned (only 539 names cover 2005 to 2010; Bath, Neath and Richmond (Yorks) start in 2015, Camberwell and
# Peckham, Warley and West Ham are absent), creating false seat-name changes at 2010, 2015, 2017 and 2019.
EL = pd.read_csv(ELEC)
EL["election"] = EL.election.astype(str)
SEATS = {k: sorted(set(EL.constituency[EL.election == e])) for k, e in enumerate(("2005", "2010", "2024"))}
assert [len(SEATS[k]) for k in range(3)] == [646, 650, 650], [len(SEATS[k]) for k in range(3)]
PER = [("2005-05-05", "2010-05-06"), ("2010-05-06", "2024-07-04"), ("2024-07-04", "2026-10-28")]
terms = {t: norm(t).split() for t in P.term}
def find(seq, toks):
    n = len(seq)
    return [(i, i + n) for i in range(len(toks) - n + 1) if toks[i:i + n] == seq]
# whole-word matches that name a different place (checked by distance from the place to the seat, review): excluded
SEAT_NOT = {("Colne", "Colne Valley"), ("Conwy", "Meirionnydd Nant Conwy"), ("Derby", "Liverpool West Derby"),
            ("Derby", "Liverpool, West Derby"), ("Leigh", "Southend West and Leigh"), ("Sutton", "Plymouth, Sutton"),
            ("Sutton", "Plymouth Sutton"), ("Sutton", "Plymouth, Sutton and Devonport"), ("Sutton", "Plymouth Sutton and Devonport"),
            ("Stoke", "Hackney North and Stoke Newington")}
seat_of = defaultdict(set)     # term -> set of (period, seat)
seat_exact = defaultdict(set)  # the seat is called just this place
seat_init = defaultdict(set)   # the seat name starts with the place and goes on ("Bury North"): "in Bury North" contains "in Bury"
seat_inner = defaultdict(set)  # the place is not the first word(s) ("Leeds South West and Morley"): no "in <place>" substring
for k, names in SEATS.items():
    for seat in names:
        toks = norm(seat).split()
        hits = []
        for t, seq in terms.items():
            for sp in find(seq, toks):
                hits.append((t, sp))
        keep = [(t, sp) for t, sp in hits if not any(sp2[0] <= sp[0] and sp[1] <= sp2[1] and (sp2[1] - sp2[0]) > (sp[1] - sp[0]) for _, sp2 in hits)]
        for t, sp in keep:
            if (t, seat) in SEAT_NOT:
                continue
            seat_of[t].add((k, seat))
            if toks == terms[t]:
                seat_exact[t].add((k, seat))
            elif sp[0] == 0:
                seat_init[t].add((k, seat))
            else:
                seat_inner[t].add((k, seat))
# mutually exclusive seat-name types by period, for the mechanical-match check: "sub" = some seat starts with the name
# (the "in <seat>" phrase also counts as "in <place>"); "exact" = the seat is just the name (no substring, but "in
# <name>" may mean the constituency); "inner" = the name only appears inside seat names (neither)
seat_sub, seat_exo, seat_inn = defaultdict(set), defaultdict(set), defaultdict(set)
for t in terms:
    for k in range(3):
        if any(kk == k for kk, _ in seat_init.get(t, ())):
            seat_sub[t].add((k, ""))
        elif any(kk == k for kk, _ in seat_exact.get(t, ())):
            seat_exo[t].add((k, ""))
        elif any(kk == k for kk, _ in seat_inner.get(t, ())):
            seat_inn[t].add((k, ""))
# year weights of each boundary period within 2005 to 2025
def yw(y):
    w = np.zeros(3)
    for k, (a, b) in enumerate(PER):
        a_, b_ = max(pd.Timestamp(a), pd.Timestamp(f"{y}-01-01")), min(pd.Timestamp(b), pd.Timestamp(f"{y}-12-31"))
        w[k] = max(0, (b_ - a_).days)
    if y < 2005 or w.sum() == 0:
        return w
    if y == 2005:  # January to May 2005 belongs to the 2001 Parliament: treat as the 2005 boundaries (same names in E/W/NI)
        w = np.array([1.0, 0, 0])
    return w / w.sum()
YW = {y: yw(y) for y in range(Y0, 2027)}
def share(t, d, years):
    ks = {k for k, _ in d.get(t, set())}
    return float(np.mean([sum(YW[y][k] for k in ks) for y in years]))
yrs = range(Y0, Y1 + 1)
P["seat_share"] = [share(t, seat_of, yrs) for t in P.term]
P["seat_exact_share"] = [share(t, seat_exact, yrs) for t in P.term]
P["seat_sub_share"] = [share(t, seat_sub, yrs) for t in P.term]
P["seat_exo_share"] = [share(t, seat_exo, yrs) for t in P.term]
P["seat_inn_share"] = [share(t, seat_inn, yrs) for t in P.term]
P["seat_ever"] = (P.seat_share > 0).astype(int)
P["seat_share_05_14"] = [share(t, seat_of, range(Y0, SPLIT)) for t in P.term]
P["seat_share_15_25"] = [share(t, seat_of, range(SPLIT, Y1 + 1)) for t in P.term]
P["seats"] = ["; ".join(sorted({s for _, s in seat_of.get(t, set())})) for t in P.term]
P["seat_n"] = [len({s for k, s in seat_of.get(t, set()) if k == 1}) for t in P.term]   # seats bearing the name 2010 to 2024
# panel: place by year, 2005 to 2025, with the seat-name share of that year
pan = []
for t in P.term:
    ks = {k for k, _ in seat_of.get(t, set())}
    kn = {k for k, _ in seat_sub.get(t, set())}
    for y in range(Y0, Y1 + 1):
        pan.append((t, y, round(float(sum(YW[y][k] for k in ks)), 4), round(float(sum(YW[y][k] for k in ks - kn)), 4)))
PAN = pd.DataFrame(pan, columns=["term", "year", "seat", "seat_nosub"])
PAN = PAN.merge(Y[["term", "year", "inm", "any_mentions"]].rename(columns={"inm": "in_m", "any_mentions": "any_m"}), on=["term", "year"], how="left")
PAN["in_m"] = PAN.in_m.fillna(0).round(2)
# two unflagged Hansard terms for the same article (Newark and Newark-on-Trent; Dereham and East Dereham): the longer
# name's counts were already subtracted from the shorter one's, so the two are added and kept under the more used term
P["merged_from"] = ""
for title, grp in P[P.title.notna() & P.flag.isna()].groupby("title"):
    if len(grp) < 2:
        continue
    k = grp.in_05_25.idxmax()
    for j in grp.index.drop(k):
        for c in ("in_05_25", "in_05_14", "in_15_25", "in_2024", "in_20_25", "in_1945_1979", "in_1980_2004", "in_1909_2025"):
            P.loc[k, c] += P.loc[j, c]
        for c in ("seat_share", "seat_exact_share", "seat_sub_share", "seat_exo_share", "seat_inn_share", "seat_ever", "seat_share_05_14", "seat_share_15_25"):
            P.loc[k, c] = max(P.loc[k, c], P.loc[j, c])
        P.loc[k, "merged_from"] = P.loc[j, "term"]
        P.loc[j, "flag"] = "merged"
        a = PAN[PAN.term == P.loc[j, "term"]].set_index("year")
        ix = PAN.term == P.loc[k, "term"]
        PAN.loc[ix, "in_m"] = PAN.loc[ix, "in_m"].values + a.in_m.reindex(PAN.loc[ix, "year"]).fillna(0).values
        PAN.loc[ix, "seat"] = np.maximum(PAN.loc[ix, "seat"].values, a.seat.reindex(PAN.loc[ix, "year"]).fillna(0).values)
        PAN.loc[ix, "seat_nosub"] = np.maximum(PAN.loc[ix, "seat_nosub"].values, a.seat_nosub.reindex(PAN.loc[ix, "year"]).fillna(0).values)
R1["merged"] = [[a, b] for a, b in zip(P.term[P.merged_from != ""], P.merged_from[P.merged_from != ""])]
# name form: Hansard counts the exact phrase "in <term>", Wikipedia uses the formal title. Long formal names (joining
# words such as on, upon, by, le, in; Regis, Spa, Minster, Magna; "City of") are often shortened in speech (Saltburn,
# Burton, Walton), and terms never once found after "in" from 1909 to 2025 are likely spelling forms not used in debate.
JOIN = r"(?:^|[ -])(?:on|upon|by|under|le|la|de|in|super|next|cum|en)(?:[ -])|^City of |[ ](?:Minster|Regis|Spa|Magna|Parva)$"
P["name_form"] = (P.term.str.contains(JOIN, case=False, regex=True) | P.term.str.contains("'") | (P.in_1909_2025 == 0)).astype(int)   # apostrophes: punctuation-sensitive phrase search
R1["n_name_form"] = int(P.loc[P.views.notna() & P.flag.isna(), "name_form"].sum())
PAN.to_csv(f"{DATA}/place_years.csv", index=False)
R1["seat_terms_ever"] = int(P.seat_ever.sum())
R1["seat_terms_change"] = int(((P.seat_share > 0) & (P.seat_share < 0.999)).sum())
R1["n_seats_names"] = int(len(set(SEATS[0]) | set(SEATS[1]) | set(SEATS[2])))

keep = ["term", "title", "qid", "km", "rule", "nation", "region", "lad", "lad_name", "pcon", "constituency_name", "lat", "lon",
        "pop", "pop_src", "wd_pop", "pop_main", "pop_main_src", "pop_disagree", "views", "suspect_title", "n_namesakes_views", "top_namesake", "top_namesake_views", "collide", "collide_strict", "flag", "any_flag", "factor", "in_05_25", "in_05_14", "in_15_25", "in_2024", "in_20_25",
        "in_1945_1979", "in_1980_2004", "in_1909_2025", "any_2005_2025", "merged_from", "name_form", "seat_share", "seat_exact_share", "seat_sub_share", "seat_exo_share", "seat_inn_share", "seat_ever", "seat_share_05_14",
        "seat_share_15_25", "seat_n", "seats", "dist_london", "deprived2", "noqual", "degree", "unemp", "routine", "population_density"]
P[keep].rename(columns={"pop": "hansard_pop", "pop_src": "hansard_pop_src", "flag": "hansard_flag", "any_flag": "hansard_any_flag",
                        "any_2005_2025": "any_05_25"}).to_csv(f"{DATA}/places.csv", index=False)
jsave(R1, f"{SCR}/r1.json", indent=1)
print(json.dumps(R1, indent=1))
