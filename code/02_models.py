"""Step 2: the pre-specified models (NOTES.md, "Analysis plan"), robustness checks and the over/under-representation index.

Writes scratch/r2.json (merged into data/results.json by 03_results.py), data/models.csv (every coefficient of every model)
and data/index.csv (the observed/expected index per place)."""
import warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, pyfixest as pf
import statsmodels.api as sm
from scipy import stats
from common import *

D = pd.read_csv(f"{DATA}/places.csv")
D["disamb"] = D.title.fillna("").str.contains(r"[,(]").astype(int)
D["lv"] = np.log(D.views.where(D.views > 0))
D["lp"] = np.log(D.pop_main.where(D.pop_main > 0))
D["lp_wd"] = np.log(D.wd_pop.where(D.wd_pop > 0))
D["ldist"] = np.log1p(D.dist_london)
gb = D.region != "Northern Ireland"
mu, sd = D.loc[gb, "deprived2"].mean(), D.loc[gb, "deprived2"].std()
D["depr"] = ((D.deprived2 - mu) / sd).fillna(0.0)
D["lad"] = D.lad.astype(str)
D["region"] = D.region.replace({"Yorkshire and The Humber": "Yorkshire and the Humber"})
ENG = ["North East", "North West", "Yorkshire and the Humber", "East Midlands", "West Midlands", "East of England", "London", "South East", "South West"]
DEV = ["Scotland", "Wales", "Northern Ireland"]
NORTH, SOUTH = ["North East", "North West", "Yorkshire and the Humber"], ["South East", "South West", "East of England"]
ok = D.views.notna() & (D.views > 0) & D.hansard_flag.isna() & D.lp.notna()
MAIN = ok & (D.collide == 0) & (D.suspect_title == 0)
B = D[MAIN].copy().reset_index(drop=True)
R = {"n": {"main": int(len(B)), "lad_clusters": int(B.lad.nunique()), "by_region": B.region.value_counts().to_dict(),
           "by_nation": B.nation.value_counts().to_dict(), "seat_ever": int(B.seat_ever.sum()),
           "zero_mentions": int((B.in_05_25 == 0).sum()), "pop_src": B.pop_main_src.value_counts().to_dict()},
     "sample_flow": {"terms": int(len(D)), "matched_with_views": int((D.views.notna()).sum()),
                     "hansard_flag_removed": int((D.views.notna() & D.hansard_flag.notna()).sum()),
                     "collide_removed": int((ok & (D.collide == 1)).sum()), "suspect_removed": int((ok & (D.collide == 0) & (D.suspect_title == 1)).sum()),
                     "zero_views_removed": int((D.views == 0).sum())}}
COEFS = []
RHS = "lv + lp + seat_share + ldist + depr + disamb"
REG = "C(region, contr.treatment('South East'))"


def rname(r):
    return f"{REG}[T.{r}]"


def ppml(df, y, rhs=RHS, fe=None, vc=None, name=None, keep=True):
    f = f"{y} ~ {rhs}" + (f" | {fe}" if fe else "")
    m = pf.fepois(f, data=df, vcov=vc or {"CRV1": "lad"})
    if keep and name:
        t = m.tidy()
        for k, r in t.iterrows():
            COEFS.append(dict(model=name, term=k, b=r["Estimate"], se=r["Std. Error"], p=r["Pr(>|t|)"], n=int(m._N)))
    return m


def ci(m, k, tr=None):
    b, s = float(m.coef()[k]), float(m.se()[k])
    lo, hi = b - 1.96 * s, b + 1.96 * s
    f = (lambda x: x) if tr is None else tr
    return {"b": round(f(b), 4), "lo": round(f(lo), 4), "hi": round(f(hi), 4), "se": round(s, 4), "p": float(m.pvalue()[k])}


pc = lambda x: 100 * (np.exp(x) - 1)


def contrast(m, df, groupA, groupB):
    """N-weighted mean of region effects in group A minus group B (log scale), with its cluster-robust SE"""
    names = list(m.coef().index)
    V = m._vcov
    w = np.zeros(len(names))
    for grp, sign in ((groupA, 1), (groupB, -1)):
        cnt = df.region.value_counts()
        tot = sum(cnt.get(r, 0) for r in grp)
        for r in grp:
            if r == "South East":
                continue          # reference category: coefficient 0
            k = rname(r)
            if k in names and cnt.get(r, 0):
                w[names.index(k)] += sign * cnt[r] / tot
    b = float(w @ m.coef().values)
    s = float(np.sqrt(w @ V @ w))
    return {"b": round(pc(b), 2), "lo": round(pc(b - 1.96 * s), 2), "hi": round(pc(b + 1.96 * s), 2), "p": float(2 * stats.norm.sf(abs(b / s))), "log_b": round(b, 4), "log_se": round(s, 4)}


def summarise(m, df, label):
    out = {"n": int(m._N), "views": ci(m, "lv") if "lv" in m.coef().index else None, "pop": ci(m, "lp") if "lp" in m.coef().index else None}
    if "seat_share" in m.coef().index:
        out["seat"] = ci(m, "seat_share", pc)
    if any(k.startswith(REG) for k in m.coef().index):
        out["devolved_vs_england"] = contrast(m, df, DEV, ENG)
        for n in DEV:
            out[f"{n}_vs_england"] = contrast(m, df, [n], ENG)
        out["north_vs_south"] = contrast(m, df, NORTH, SOUTH)
        out["london_vs_rest_england"] = contrast(m, df, ["London"], [r for r in ENG if r != "London"])
    if "depr" in m.coef().index:
        out["depr"] = ci(m, "depr", pc)
    if "ldist" in m.coef().index:
        out["ldist"] = ci(m, "ldist")
    return out


# ---------- descriptive: how far the two attentions agree
R["desc"] = {"spearman_views_mentions": round(float(stats.spearmanr(B.views, B.in_05_25)[0]), 3),
             "spearman_pop_mentions": round(float(stats.spearmanr(B.lp, B.in_05_25)[0]), 3),
             "spearman_pop_views": round(float(stats.spearmanr(B.lp, B.views)[0]), 3),
             "pearson_log": round(float(np.corrcoef(B.lv, np.log1p(B.in_05_25))[0, 1]), 3)}
rv = stats.rankdata(B.views); rm_ = stats.rankdata(B.in_05_25); rp = stats.rankdata(B.lp)
res = lambda a, b: a - np.polyval(np.polyfit(b, a, 1), b)
R["desc"]["partial_spearman_given_pop"] = round(float(np.corrcoef(res(rv, rp), res(rm_, rp))[0, 1]), 3)
R["desc"]["mentions_total"] = int(B.in_05_25.sum())
R["desc"]["views_total"] = int(B.views.sum())
R["desc"]["median_mentions"] = float(B.in_05_25.median())
R["desc"]["median_views"] = float(B.views.median())
R["desc"]["median_pop"] = float(B.pop_main.median())

# ---------- M0 (no attention), M1 (main), statsmodels cross-check
m0 = ppml(B, "in_05_25", rhs=f"lp + seat_share + ldist + depr + disamb + {REG}", name="M0 no views")
R["M0"] = summarise(m0, B, "M0")
R["M0"]["views"] = None
m1 = ppml(B, "in_05_25", rhs=f"{RHS} + {REG}", name="M1 main")
R["M1"] = summarise(m1, B, "M1")
X = pd.get_dummies(B[["lv", "lp", "seat_share", "ldist", "depr", "disamb", "region"]], columns=["region"], drop_first=False, dtype=float).drop(columns=["region_South East"])
X = sm.add_constant(X)
g = sm.GLM(B.in_05_25, X, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(B.lad)[0]})
R["M1"]["statsmodels_check"] = {"views": round(float(g.params["lv"]), 4), "views_se": round(float(g.bse["lv"]), 4), "seat": round(float(g.params["seat_share"]), 4)}
assert abs(g.params["lv"] - m1.coef()["lv"]) < 1e-3
R["M1"]["pseudo_r2"] = round(float(1 - g.deviance / g.null_deviance), 3)
# without distance (H3 contrasts are conditional on distance in M1)
m1nd = ppml(B, "in_05_25", rhs=f"lv + lp + seat_share + depr + disamb + {REG}", name="M1 without distance")
R["M1_nodist"] = summarise(m1nd, B, "M1nd")
# exact seat name (the seat is called just this place)
m1x = ppml(B, "in_05_25", rhs=f"lv + lp + seat_exact_share + ldist + depr + disamb + {REG}", name="M1 exact seat name")
R["M1_exact"] = {"n": int(m1x._N), "seat_exact": ci(m1x, "seat_exact_share", pc)}
# review addition (exploratory): is the seat-name association a by-product of phrase matching? "in Bury North" also counts as
# "in Bury" (the seat name starts with the place); "in Leeds South West and Morley" does not count as "in Morley".
m1t = ppml(B, "in_05_25", rhs=f"lv + lp + seat_sub_share + seat_exo_share + seat_inn_share + ldist + depr + disamb + {REG}", name="M1 seat-name types")
R["M1_types"] = {"n": int(m1t._N), "sub": ci(m1t, "seat_sub_share", pc), "exact": ci(m1t, "seat_exo_share", pc), "inner": ci(m1t, "seat_inn_share", pc),
                 "n_sub": int((B.seat_sub_share > 0).sum()), "n_exact": int((B.seat_exo_share > 0).sum()), "n_inner": int((B.seat_inn_share > 0).sum())}

# ---------- M2: within place, the 2010 and 2024 boundary changes
P = pd.read_csv(f"{DATA}/place_years.csv")
P = P[P.term.isin(B.term)].merge(B[["term", "lad"]], on="term")
st = P.pivot(index="term", columns="year", values="seat")
for y in (2026, 2027):
    st[y] = st[2025]
lead = {(t, y): st.loc[t, y + 2] for t in st.index for y in range(Y0, Y1 + 1)}
P["seat_lead2"] = [lead[(t, y)] for t, y in zip(P.term, P.year)]
chg = st.loc[:, Y0:Y1].apply(lambda r: r.max() - r.min() > 0, axis=1)
R["M2_n"] = {"places": int(P.term.nunique()), "switchers": int(chg.sum()), "rows": int(len(P))}
sw = st.loc[chg]
R["M2_n"]["gain_2010"] = int(((sw[2009] == 0) & (sw[2012] == 1)).sum()); R["M2_n"]["lose_2010"] = int(((sw[2009] == 1) & (sw[2012] == 0)).sum())
R["M2_n"]["gain_2024"] = int(((sw[2023] == 0) & (sw[2025] == 1)).sum()); R["M2_n"]["lose_2024"] = int(((sw[2023] == 1) & (sw[2025] == 0)).sum())
m2 = ppml(P, "in_m", rhs="seat", fe="term + year", name="M2 within place")
R["M2"] = {"seat": ci(m2, "seat", pc), "n_obs": int(m2._N)}
# review addition (exploratory): within place, separating seat names that start with the place (phrase overlap) from the rest
P["seat_sub"] = (P.seat - P.seat_nosub).round(4)
m2t = ppml(P, "in_m", rhs="seat_sub + seat_nosub", fe="term + year", name="M2 seat-name types")
R["M2_types"] = {"sub": ci(m2t, "seat_sub", pc), "nosub": ci(m2t, "seat_nosub", pc), "n_obs": int(m2t._N)}
m2l = ppml(P, "in_m", rhs="seat + seat_lead2", fe="term + year", name="M2 lead placebo")
R["M2_lead"] = {"seat": ci(m2l, "seat", pc), "lead2": ci(m2l, "seat_lead2", pc), "n_obs": int(m2l._N)}
m2f = ppml(P, "in_m", rhs="seat_lead2", fe="term + year", name="M2 fake timing")
R["M2_fake"] = {"lead2": ci(m2f, "seat_lead2", pc)}
# England and Wales only, 2005 to 2023 (the 2010 change only)
P2 = P[P.year <= 2023]
m2a = ppml(P2, "in_m", rhs="seat", fe="term + year", name="M2 2005 to 2023")
R["M2_to2023"] = {"seat": ci(m2a, "seat", pc), "n_obs": int(m2a._N)}
m2al = ppml(P2, "in_m", rhs="seat + seat_lead2", fe="term + year", name="M2 2005 to 2023 lead placebo")
R["M2_to2023_lead"] = {"seat": ci(m2al, "seat", pc), "lead2": ci(m2al, "seat_lead2", pc)}
# event studies (added after the lead test failed; exploratory): places that gained a seat name at 2010 or at 2024,
# against places whose seat-name status never changed; reference year = the year before the change
never = st.index[~chg]
EV = {}
for yr, ya, yb in ((2010, 2005, 2023), (2024, 2015, 2025)):
    g = sw.index[(sw[yr - 1] == 0) & (sw[yb if yr == 2024 else yr + 2] == 1) & ((sw.loc[:, ya:yb].max(axis=1) - sw.loc[:, ya:yb].min(axis=1)) > 0)]
    if yr == 2010:
        g = [t for t in g if st.loc[t, 2023] == 1]          # kept the name until 2023
    E = P[(P.term.isin(list(g)) | P.term.isin(never)) & (P.year >= ya) & (P.year <= yb)].copy()
    ks = [k for k in range(ya - yr, yb - yr + 1) if k != -1]
    names = []
    for k in ks:
        nm = f"k{'m' if k < 0 else 'p'}{abs(k)}"
        E[nm] = ((E.term.isin(list(g))) & (E.year - yr == k)).astype(int)
        names.append(nm)
    me = ppml(E, "in_m", rhs=" + ".join(names), fe="term + year", name=f"E event {yr}")
    EV[str(yr)] = {"n_treated": int(len(g)), "n_control": int(len(never)), "coef": {str(k): ci(me, nm, pc) for k, nm in zip(ks, names)}}
R["event"] = EV

# ---------- H4: stability between 2005 to 2014 and 2015 to 2025
fits = {}
for per, y, s_ in (("p1", "in_05_14", "seat_share_05_14"), ("p2", "in_15_25", "seat_share_15_25")):
    m = ppml(B, y, rhs=f"lv + lp + {s_} + ldist + depr + disamb + {REG}", name=f"H4 {per}")
    mu_ = m.predict(type="response")
    fits[per] = {"m": m, "pr": (B[y] - mu_) / np.sqrt(mu_), "oe": np.log((B[y] + 0.5) / (mu_ + 0.5))}
    R[f"H4_{per}"] = {"views": ci(m, "lv"), "seat": ci(m, s_, pc), "n": int(m._N), "mentions": int(B[y].sum())}
R["H4"] = {"spearman_resid": round(float(stats.spearmanr(fits["p1"]["pr"], fits["p2"]["pr"])[0]), 3),
           "spearman_logoe": round(float(stats.spearmanr(fits["p1"]["oe"], fits["p2"]["oe"])[0]), 3),
           "spearman_mentions": round(float(stats.spearmanr(B.in_05_14, B.in_15_25)[0]), 3)}
# stacked model to test differences in coefficients between periods
S1 = B.assign(y=B.in_05_14, s=B.seat_share_05_14, per=0); S2 = B.assign(y=B.in_15_25, s=B.seat_share_15_25, per=1)
SS = pd.concat([S1, S2], ignore_index=True)
for v in ("lv", "lp", "s", "ldist", "depr", "disamb"):
    SS[v + "_x"] = SS[v] * SS.per
SS["rp"] = SS.region + "_" + SS.per.astype(str)
mst = ppml(SS, "y", rhs="lv + lp + s + ldist + depr + disamb + lv_x + lp_x + s_x + ldist_x + depr_x + disamb_x", fe="rp", name="H4 stacked")
R["H4"]["diff_views"] = ci(mst, "lv_x"); R["H4"]["diff_seat"] = ci(mst, "s_x")

# ---------- robustness
ROB = []
def rob(label, df, y="in_05_25", rhs=f"{RHS} + {REG}", group="", note=""):
    try:
        m = ppml(df, y, rhs=rhs, name="R " + label)
        s = summarise(m, df, label)
        ROB.append(dict(group=group, label=label, n=s["n"], views=s["views"], seat=s.get("seat"), dev=s.get("devolved_vs_england"),
                        ns=s.get("north_vs_south"), wales=s.get("Wales_vs_england"), london=s.get("london_vs_rest_england"), depr=s.get("depr"), note=note))
    except Exception as e:
        ROB.append(dict(group=group, label=label, n=len(df), error=str(e)[:200]))
# R1 alternative specifications
ols = pf.feols(f"np.log1p(in_05_25) ~ {RHS} + {REG}", data=B, vcov={"CRV1": "lad"})
for k, r in ols.tidy().iterrows():
    COEFS.append(dict(model="R1 OLS log(1+Y)", term=k, b=r["Estimate"], se=r["Std. Error"], p=r["Pr(>|t|)"], n=int(ols._N)))
o = summarise(ols, B, "ols")
ROB.append(dict(group="R1 specification", label="OLS of log(1 + mentions)", n=o["n"], views=o["views"],
                seat={k: (round(100 * v, 2) if k in ("b", "lo", "hi") else v) for k, v in ci(ols, "seat_share").items()},
                dev=o["devolved_vs_england"], ns=o["north_vs_south"], wales=o["Wales_vs_england"], london=o["london_vs_rest_england"], depr=o["depr"], note="contrasts as exp(b) - 1 of the log-scale OLS coefficients"))
rob("PPML, views and population only", B, rhs="lv + lp", group="R1 specification")
rob("PPML, views only", B, rhs="lv", group="R1 specification")
rob("No distance to London", B, rhs="lv + lp + seat_share + depr + disamb + " + REG, group="R1 specification")
# R3 outliers
q = B.views.quantile(.99); rob("Drop top 1% by views", B[B.views < q], group="R3 outliers")
q = B.in_05_25.quantile(.99); rob("Drop top 1% by mentions", B[B.in_05_25 < q], group="R3 outliers")
rob("Drop London (the city)", B[B.term != "London"], group="R3 outliers")
rob("Drop places in the London region", B[B.region != "London"], group="R3 outliers")
rob("Drop places in the London region, no distance", B[B.region != "London"], rhs="lv + lp + seat_share + depr + disamb + " + REG, group="R3 outliers")
# R5 measurement
rob("Outcome: 2024 only (same year as views)", B, y="in_2024", group="R5 measurement")
rob("Outcome: 2020 to 2025", B, y="in_20_25", group="R5 measurement")
A = D[D.views.notna() & (D.views > 0) & D.hansard_any_flag.isna() & D.lp.notna() & (D.collide == 0) & (D.suspect_title == 0)]
rob("Outcome: any mention 2005 to 2025 (incl. 'Member for')", A, y="any_05_25", group="R5 measurement", note="any-flag sample")
W_ = B[B.lp_wd.notna()].assign(lp=lambda d: d.lp_wd); rob("Population: Wikidata only", W_, group="R5 measurement")
rob("Drop places whose population sources disagree > 3x", B[B.pop_disagree == 0], group="R5 measurement")
rob("Ambiguity: strict namesake rule", B[B.collide_strict == 0], group="R5 measurement")
rob("Ambiguity: keep namesake collisions", D[ok & (D.suspect_title == 0)], group="R5 measurement")
rob("Drop ordinary-word names scaled for precision", B[B.factor >= 0.999], group="R5 measurement")
rob("Keep suspect titles", D[ok & (D.collide == 0)], group="R5 measurement")
rob("Drop long or unused name forms (added after reading the rankings)", B[B.name_form == 0], group="R5 measurement")
rob("Only exact title matches (no qualifier)", B[B.disamb == 0], rhs=f"lv + lp + seat_share + ldist + depr + {REG}", group="R5 measurement")
# R4 leave one region out
LORO = []
for r in sorted(B.region.unique()):
    df = B[B.region != r]
    m = ppml(df, "in_05_25", rhs=f"{RHS} + {REG}" if r != "South East" else f"{RHS} + C(region, contr.treatment('London'))", keep=False)
    if r == "South East":
        names = list(m.coef().index); rn = lambda x: f"C(region, contr.treatment('London'))[T.{x}]"
        V = m._vcov; cnt = df.region.value_counts(); w = np.zeros(len(names))
        dv = [x for x in DEV if x in cnt]; en = [x for x in ENG if x in cnt]
        for grp, sign in ((dv, 1), (en, -1)):
            tot = sum(cnt[x] for x in grp)
            for x in grp:
                if x != "London": w[names.index(rn(x))] += sign * cnt[x] / tot
        b = float(w @ m.coef().values); s_ = float(np.sqrt(w @ V @ w))
        dev = {"b": round(pc(b), 2), "lo": round(pc(b - 1.96 * s_), 2), "hi": round(pc(b + 1.96 * s_), 2)}
    else:
        dv = [x for x in DEV if x != r]
        dev = contrast(m, df, dv, ENG)
    LORO.append(dict(left_out=r, n=int(m._N), views=ci(m, "lv"), seat=ci(m, "seat_share", pc), dev=dev))
R["loro"] = LORO
R["loro_range"] = {"views": [min(x["views"]["b"] for x in LORO), max(x["views"]["b"] for x in LORO)],
                   "seat": [min(x["seat"]["b"] for x in LORO), max(x["seat"]["b"] for x in LORO)],
                   "dev": [min(x["dev"]["b"] for x in LORO), max(x["dev"]["b"] for x in LORO)]}
# R2 ranks are in R["desc"]; R6 permutation for the seat coefficient
rng = np.random.default_rng(20261109)
B["pq"] = B.groupby("region").lp.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
cells = B.groupby(["region", "pq"]).indices
perm = []
for _ in range(1000):
    s_ = B.seat_share.values.copy()
    for ix in cells.values():
        s_[ix] = rng.permutation(s_[ix])
    dfp = B.assign(seat_share=s_)
    m = pf.fepois(f"in_05_25 ~ {RHS} + {REG}", data=dfp, vcov="hetero")
    perm.append(float(m.coef()["seat_share"]))
perm = np.array(perm)
obs = float(m1.coef()["seat_share"])
R["perm"] = {"draws": 1000, "obs": round(obs, 4), "mean": round(float(perm.mean()), 4), "sd": round(float(perm.std()), 4),
             "p": float((np.sum(perm >= obs) + 1) / (len(perm) + 1)), "p95": round(float(np.percentile(perm, 95)), 4)}
R["robust"] = ROB

# ---------- exploratory: does 2024 attention track recent debate more than old debate?
EXP = {}
for lab, y in (("1945 to 1979", "in_1945_1979"), ("1980 to 2004", "in_1980_2004"), ("2005 to 2014", "in_05_14"), ("2015 to 2025", "in_15_25")):
    m = ppml(B, y, rhs=f"lv + lp + ldist + depr + disamb + {REG}", name=f"E gradient {lab}")
    EXP[lab] = ci(m, "lv")
R["exploratory_gradient"] = EXP

# ---------- the over/under-representation index (views and population only)
mi = pf.fepois("in_05_25 ~ lv + lp", data=B, vcov="hetero")
B["expected"] = mi.predict(type="response")
B["oe"] = (B.in_05_25 + 0.5) / (B.expected + 0.5)
R["index_model"] = {"views": ci(mi, "lv"), "pop": ci(mi, "lp"), "n": int(mi._N)}
# per head and per view benchmarks
B["per100k"] = 1e5 * B.in_05_25 / B.pop_main
B["per100kviews"] = 1e5 * B.in_05_25 / B.views
B[["term", "title", "nation", "region", "lat", "lon", "pop_main", "pop_main_src", "views", "in_05_25", "in_05_14", "in_15_25", "any_05_25",
   "seat_share", "seats", "expected", "oe", "per100k", "per100kviews", "lad_name", "deprived2", "name_form", "merged_from", "disamb"]].to_csv(f"{SCR}/index_main.csv", index=False)
pd.DataFrame(COEFS).to_csv(f"{DATA}/models.csv", index=False)
jsave(R, f"{SCR}/r2.json", indent=1, keepdash=True)
print(json.dumps({k: R[k] for k in ("H4", "M2_to2023_lead", "event", "H4_p1", "H4_p2", "perm", "loro_range", "exploratory_gradient", "index_model")}, indent=1, default=str)[:12000])
for r in ROB:
    print(r["group"], "|", r["label"], "| n", r["n"], "| views", r.get("views", {}).get("b") if r.get("views") else None, "| seat", (r.get("seat") or {}).get("b"), "| dev", (r.get("dev") or {}).get("b"), "| wales", (r.get("wales") or {}).get("b"), "| ns", (r.get("ns") or {}).get("b"), "| ldn", (r.get("london") or {}).get("b"), r.get("error", ""))
