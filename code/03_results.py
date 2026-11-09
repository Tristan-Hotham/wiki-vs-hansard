"""Step 3: data/results.json (every number quoted anywhere), data/index.csv and the page data (data/site.json)."""
import numpy as np, pandas as pd
from common import *

R1 = jload(f"{SCR}/r1.json")
R2 = jload(f"{SCR}/r2.json")
R = {"data": R1}
R.update(R2)
d = R["data"]
d["match_rate_pc"] = round(100 * d["n_matched"] / d["n_terms"], 1)
d["views_rate_pc"] = round(100 * d["n_matched_views"] / d["n_terms"], 1)
I = pd.read_csv(f"{SCR}/index_main.csv")
I["log2oe"] = np.log2(I.oe)
I["ranked"] = ((I.expected >= 20) & (I.name_form == 0)).astype(int)
I.round({"expected": 1, "oe": 3, "per100k": 2, "per100kviews": 2, "log2oe": 3}).to_csv(f"{DATA}/index.csv", index=False)
E = I[I.ranked == 1].sort_values("oe", ascending=False)
row = lambda r: {"term": r.term, "region": r.region, "views": int(r.views), "mentions": int(r.in_05_25), "expected": round(float(r.expected), 1),
                 "oe": round(float(r.oe), 2), "seat": bool(r.seat_share > 0), "pop": int(r.pop_main)}
R["rank"] = {"n": int(len(E)), "over": [row(r) for r in E.head(15).itertuples()], "under": [row(r) for r in E.tail(15).iloc[::-1].itertuples()],
             "seat_share_top25_pc": round(100 * float((E.head(25).seat_share > 0).mean())), "seat_share_bottom25_pc": round(100 * float((E.tail(25).seat_share > 0).mean())),
             "seat_share_all_pc": round(100 * float((E.seat_share > 0).mean())),
             "over2x": int((E.oe >= 2).sum()), "under_half": int((E.oe <= 0.5).sum())}
R["big"] = [row(r) for r in I.sort_values("views", ascending=False).head(20).itertuples() if r.name_form == 0][:14]
cases = {}
for t in ("London", "Glasgow", "Cardiff", "Birmingham", "Edinburgh", "Saltburn-by-the-Sea", "City of London", "Newcastle upon Tyne", "Kettering",
          "Redcar", "Newtownards", "Thirsk", "Port Talbot", "Wrexham", "Bath", "Stoke-on-Trent", "York", "Southport", "Becontree", "Broughty Ferry"):
    r = I[I.term == t]
    if len(r):
        cases[t] = row(r.iloc[0])
R["cases"] = cases
# robustness summaries (ranges across every check)
rb = [x for x in R["robust"] if "views" in x and x["views"] and x["label"] != "PPML, views only"]
def rng(key):
    v = [x[key]["b"] for x in rb if x.get(key)]
    return [round(min(v), 2), round(max(v), 2)]
R["robust_range"] = {"views": rng("views"), "seat": [round(min(x["seat"]["b"] for x in rb if x.get("seat") and "any mention" not in x["label"]), 1),
                                                    round(max(x["seat"]["b"] for x in rb if x.get("seat") and "any mention" not in x["label"]), 1)],
                     "wales": rng("wales"), "dev": rng("dev"), "ns": rng("ns"), "n_checks": len(R["robust"])}
R["robust_any_seat"] = next(x["seat"]["b"] for x in R["robust"] if "any mention" in x["label"])
R["robust_drop_london"] = next(x for x in R["robust"] if x["label"] == "Drop London (the city)")
R["robust_namefirm"] = next(x for x in R["robust"] if x["label"].startswith("Drop long"))
# handy derived numbers for prose
M1 = R["M1"]
R["prose"] = {"views_10pc": round(100 * (1.1 ** M1["views"]["b"] - 1), 1), "views_double": round(100 * (2 ** M1["views"]["b"] - 1)),
              "views_double_lo": round(100 * (2 ** M1["views"]["lo"] - 1)), "views_double_hi": round(100 * (2 ** M1["views"]["hi"] - 1)),
              "pop_double": round(100 * (2 ** M1["pop"]["b"] - 1)),
              "seat_x": round(1 + M1["seat"]["b"] / 100, 2), "wales_x": round(1 + M1["Wales_vs_england"]["b"] / 100, 2),
              "within_x": round(1 + R["M2"]["seat"]["b"] / 100, 2),
              "ev24_k0": round(R["event"]["2024"]["coef"]["0"]["b"]), "ev24_k1": round(R["event"]["2024"]["coef"]["1"]["b"]),
              "ev24_km2": round(R["event"]["2024"]["coef"]["-2"]["b"]), "ev24_km9": round(R["event"]["2024"]["coef"]["-9"]["b"]),
              "share_seat_main_pc": round(100 * R["n"]["seat_ever"] / R["n"]["main"]),
              "london_mentions_pc": round(100 * I.loc[I.term == "London", "in_05_25"].iloc[0] / I.in_05_25.sum(), 1),
              "london_views_pc": round(100 * I.loc[I.term == "London", "views"].iloc[0] / I.views.sum(), 1)}
# checks of claims made in words
assert M1["views"]["lo"] > 0 and M1["views"]["hi"] < 1, "elasticity between 0 and 1"
assert M1["seat"]["lo"] > 0 and R["perm"]["p"] < 0.01
assert R["M2_lead"]["lead2"]["lo"] > 0, "lead placebo fails (text says so)"
assert M1["Wales_vs_england"]["lo"] > 0 and R["robust_range"]["wales"][0] > 0
assert abs(R["robust_drop_london"]["dev"]["b"]) < 10 and abs(R["robust_drop_london"]["ns"]["b"]) < 10
assert R["H4"]["spearman_resid"] < 0.6 and R["H4"]["diff_views"]["hi"] < 0
assert M1["depr"]["lo"] < 0 < M1["depr"]["hi"]
assert R["exploratory_gradient"]["1945 to 1979"]["b"] > R["exploratory_gradient"]["2015 to 2025"]["b"]
jsave(R, f"{DATA}/results.json", indent=1, keepdash=True)

# ---------- page data: every matched Hansard place with views (main sample coloured, others grey with the reason)
P = pd.read_csv(f"{DATA}/places.csv")
ix = I.set_index("term")
out = []
for r in P[P.views.notna()].itertuples():
    why = ""
    if isinstance(r.hansard_flag, str):
        why = {"shared": "name shared by two UK places in Hansard", "namesake": "name also used for a better-known place or thing",
               "word": "ordinary word, too imprecise to count", "merged": "counted together with " + str(P.loc[P.merged_from == r.term, "term"].iloc[0]) if (P.merged_from == r.term).any() else "merged"}.get(r.hansard_flag, r.hansard_flag)
    elif r.collide == 1:
        why = f"another place of this name ({r.top_namesake}) is about as well known"
    elif r.suspect_title == 1:
        why = "Wikipedia title probably moved during 2024"
    elif r.views == 0:
        why = "no views recorded"
    rec = {"n": r.term, "t": r.title, "la": round(r.lat, 4), "lo": round(r.lon, 4), "r": r.region, "v": int(r.views), "m": int(r.in_05_25),
           "m1": int(r.in_05_14), "m2": int(r.in_15_25), "p": int(r.pop_main) if r.pop_main == r.pop_main else None, "ps": r.pop_main_src}
    if r.term in ix.index and not why:
        q = ix.loc[r.term]
        rec.update({"e": round(float(q.expected), 1), "o": round(float(q.log2oe), 3), "k": int(q.ranked), "s": r.seats if isinstance(r.seats, str) else ""})
        if q.name_form:
            rec["f"] = "long or unusual name form: speakers may use a shorter name"
    else:
        rec["x"] = why or "not in the main sample"
    out.append(rec)
site = {"places": out, "n_main": R["n"]["main"], "fit": {"a": None}}
jsave(site, f"{DATA}/site.json")
print("results.json and site.json:", len(out), "places;", R["rank"]["n"], "ranked; robust", R["robust_range"])
